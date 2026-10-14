from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd
from src.domain.entities import CropParameterProfile, AgronomicFeatureVector
from src.agronomy.csi_calculator import CropSuitabilityCalculator


class CSIRuleBasedBaseline:
    """Baseline decision model ranking crops strictly by FAO EcoCrop suitability."""

    def __init__(self, crop_catalog: List[CropParameterProfile]) -> None:
        self.crop_catalog = crop_catalog
        self.calculator = CropSuitabilityCalculator()
        self.classes_ = np.array([c.crop_id for c in self.crop_catalog])

    def predict_suitability_scores(
        self,
        features: AgronomicFeatureVector
    ) -> Dict[str, float]:
        """Calculates raw suitability score for each crop in the catalog."""
        scores: Dict[str, float] = {}
        for crop in self.crop_catalog:
            res = self.calculator.calculate_crop_csi(features, crop)
            scores[crop.crop_id] = res.overall_score
        return scores

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Converts tabular feature rows into a normalized softmax-like suitability distribution."""
        proba_rows = []
        for _, row in X.iterrows():
            vec = AgronomicFeatureVector(
                site_id=str(row.get("site_id", "SITE-01")),
                period_start=row.get("period_start", None),
                period_end=row.get("period_end", None),
                observation_days=int(row.get("observation_days", 30)),
                mean_air_temp=float(row.get("mean_air_temp", 27.0)),
                min_air_temp=float(row.get("min_air_temp", 22.0)),
                max_air_temp=float(row.get("max_air_temp", 32.0)),
                mean_rh=float(row.get("mean_rh", 75.0)),
                mean_soil_vwc=float(row.get("mean_soil_vwc", 45.0)),
                mean_soil_temp=float(row.get("soil_temperature", 26.0)),
                mean_soil_ph=float(row.get("mean_soil_ph", 6.2)),
                mean_soil_ec=float(row.get("mean_soil_ec", 1.0)),
                total_rainfall=float(row.get("total_rainfall", 300.0)),
                mean_solar_radiation=float(row.get("mean_solar_radiation", 400.0)),
                mean_wind_speed=float(row.get("mean_wind_speed", 1.5)),
                mean_soil_n=float(row.get("mean_soil_n", 90.0)),
                mean_soil_p=float(row.get("mean_soil_p", 35.0)),
                mean_soil_k=float(row.get("mean_soil_k", 120.0)),
            )

            scores_map = self.predict_suitability_scores(vec)
            raw_scores = np.array([scores_map.get(cid, 0.0) for cid in self.classes_])
            total = float(np.sum(raw_scores))
            if total > 0:
                normalized = raw_scores / total
            else:
                normalized = np.ones(len(self.classes_)) / len(self.classes_)

            proba_rows.append(normalized)

        return np.array(proba_rows)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predicts the highest-ranking crop ID for each sample."""
        probas = self.predict_proba(X)
        best_indices = np.argmax(probas, axis=1)
        return self.classes_[best_indices]
