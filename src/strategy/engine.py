from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import numpy as np

from config.settings import Settings, get_settings
from src.domain.enums import ConfidenceLevel, RecommendationStatus, FAOClass
from src.domain.entities import (
    CropParameterProfile,
    AgronomicFeatureVector,
    CropRecommendation,
    RecommendationReport
)
from src.ml.predictor import CropPredictor
from src.strategy.economics import EconomicCalculator
from src.strategy.calendar import PlantingCalendarPlanner
from src.strategy.prescriptions import AgronomicPrescriptionEngine
from src.strategy.narrative import GroundedNarrativeGenerator
from src.strategy.llm_narrative import LLMNarrativeEngine


class StrategyEngine:
    """Multi-criteria decision engine for ranking candidates and formulating strategies."""

    def __init__(
        self,
        crop_catalog: List[CropParameterProfile],
        economic_catalog: Dict[str, Any],
        settings: Settings | None = None
    ) -> None:
        self.settings = settings or get_settings()
        self.crop_catalog = crop_catalog
        self.predictor = CropPredictor(crop_catalog)
        self.economic_calc = EconomicCalculator(economic_catalog)
        self.calendar_planner = PlantingCalendarPlanner()
        self.prescription_engine = AgronomicPrescriptionEngine()
        self.narrative_gen = GroundedNarrativeGenerator()
        self.llm_narrative_gen = LLMNarrativeEngine()

    def evaluate_land_parcel(
        self,
        features: AgronomicFeatureVector,
        data_completeness_ratio: float,
        use_llm: bool = False
    ) -> RecommendationReport:
        """Executes full evaluation: suitability scoring, economics, prescriptions, and ranking."""
        raw_candidates = self.predictor.evaluate_candidates(features)

        # Pre-calculate normal profits for min-max normalization
        profits = []
        for crop, csi, conf, yield_est, _, _ in raw_candidates:
            econ = self.economic_calc.calculate_projection(crop, yield_est)
            profits.append(econ.normal_profit_idr)

        min_profit = min(profits) if profits else 0.0
        max_profit = max(profits) if profits else 1.0
        profit_range = max(1.0, max_profit - min_profit)

        scored_recommendations: List[CropRecommendation] = []

        for crop, csi, conf, yield_est, supporting, inhibiting in raw_candidates:
            econ = self.economic_calc.calculate_projection(crop, yield_est)
            sowing_window = self.calendar_planner.determine_sowing_window(features, crop)
            prescription = self.prescription_engine.generate_prescription(
                features, crop, sowing_window
            )

            # Normalized profit score (0.0 to 1.0)
            norm_profit = (econ.normal_profit_idr - min_profit) / profit_range

            # Risk penalty: 0.15 per identified risk factor (capped at 0.60)
            risk_penalty = min(0.60, len(prescription.identified_risks) * 0.15)
            if "Profil risiko agroklimat terpantau rendah dan aman." in prescription.identified_risks:
                risk_penalty = 0.0

            # Realizable economic benefit scaled by biological suitability
            # Nominal high market profit cannot be harvested if agronomic conditions inhibit crop development
            realizable_profit_score = csi.overall_score * norm_profit

            # Composite multi-criteria formula
            w_suit = self.settings.weight_suitability
            w_prof = self.settings.weight_profit
            w_risk = self.settings.weight_risk

            composite_score = round(
                (w_suit * csi.overall_score) + (w_prof * realizable_profit_score) - (w_risk * risk_penalty),
                3
            )

            rec = CropRecommendation(
                rank=0,  # Assigned after sorting
                crop_id=crop.crop_id,
                crop_name=crop.name,
                composite_score=composite_score,
                suitability=csi,
                economics=econ,
                prescription=prescription,
                narrative_explanation="",
                supporting_factors=supporting,
                inhibiting_factors=inhibiting
            )
            rec.narrative_explanation = self.narrative_gen.generate_recommendation_narrative(
                features.site_id, rec
            )
            scored_recommendations.append(rec)

        # Sort descending by composite multi-criteria score
        scored_recommendations.sort(key=lambda r: r.composite_score, reverse=True)

        # Assign final ordinal ranks
        for idx, rec in enumerate(scored_recommendations, start=1):
            rec.rank = idx

        # Quality & Confidence Gates
        notes: List[str] = []
        if data_completeness_ratio < self.settings.min_data_completeness_ratio:
            confidence = ConfidenceLevel.LOW
            status = RecommendationStatus.NEEDS_AGRONOMIST_REVIEW
            notes.append(
                f"Kelengkapan data sensor ({data_completeness_ratio * 100:.1f}%) "
                f"di bawah ambang batas minimal {self.settings.min_data_completeness_ratio * 100:.0f}%. "
                f"Rekomendasi memerlukan verifikasi agronom."
            )
        else:
            primary_score = scored_recommendations[0].suitability.overall_score if scored_recommendations else 0.0
            if primary_score >= 0.70:
                confidence = ConfidenceLevel.HIGH
                status = RecommendationStatus.APPROVED
            elif primary_score >= 0.50:
                confidence = ConfidenceLevel.MEDIUM
                status = RecommendationStatus.APPROVED
            else:
                confidence = ConfidenceLevel.LOW
                status = RecommendationStatus.NEEDS_AGRONOMIST_REVIEW
                notes.append("Skor kecocokan tanaman terbaik berada pada kategori marginal. Perlu tinjauan agronom.")

        primary = scored_recommendations[0] if scored_recommendations else None
        alternatives = scored_recommendations[1:3] if len(scored_recommendations) > 1 else []

        if use_llm and primary:
            primary.narrative_explanation = self.llm_narrative_gen.generate_narrative(
                features.site_id, primary, confidence.value
            )

        return RecommendationReport(
            site_id=features.site_id,
            generated_at=datetime.now(timezone.utc),
            data_completeness_ratio=data_completeness_ratio,
            confidence_level=confidence,
            status=status,
            model_version=self.settings.app_version,
            primary_recommendation=primary,
            alternatives=alternatives,
            all_evaluations=scored_recommendations,
            system_notes=notes
        )
