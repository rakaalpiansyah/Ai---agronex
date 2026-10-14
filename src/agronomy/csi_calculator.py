import math
from typing import Dict, List, Optional
from src.domain.enums import FAOClass
from src.domain.entities import (
    CropParameterProfile,
    CropSuitabilityScore,
    AgronomicFeatureVector,
    TrapezoidLimits
)


class CropSuitabilityCalculator:
    """Calculates Crop Suitability Index (CSI) using FAO EcoCrop trapezoidal logic."""

    # Default AHP agronomic factor weights (sum to 1.0)
    DEFAULT_WEIGHTS = {
        "temperature": 0.25,
        "soil_ph": 0.20,
        "soil_moisture": 0.25,
        "rainfall": 0.15,
        "soil_ec": 0.15
    }

    @staticmethod
    def evaluate_trapezoid(value: float, limits: TrapezoidLimits) -> float:
        """Evaluates trapezoidal membership score Si between 0.0 and 1.0."""
        if value < limits.min_abs or value > limits.max_abs:
            return 0.0

        if limits.min_opt <= value <= limits.max_opt:
            return 1.0

        if limits.min_abs <= value < limits.min_opt:
            span = limits.min_opt - limits.min_abs
            return 1.0 if span <= 0 else (value - limits.min_abs) / span

        if limits.max_opt < value <= limits.max_abs:
            span = limits.max_abs - limits.max_opt
            return 1.0 if span <= 0 else (limits.max_abs - value) / span

        return 0.0

    @staticmethod
    def evaluate_ec_tolerance(observed_ec: float, max_tolerated_ec: float) -> float:
        """Evaluates unilateral electrical conductivity penalty."""
        if observed_ec <= 0.0:
            return 1.0
        if observed_ec >= max_tolerated_ec:
            return 0.0
        # Optimal threshold is up to 50% of maximum tolerated EC
        optimal_ec = max_tolerated_ec * 0.50
        if observed_ec <= optimal_ec:
            return 1.0
        return (max_tolerated_ec - observed_ec) / (max_tolerated_ec - optimal_ec)

    def calculate_crop_csi(
        self,
        features: AgronomicFeatureVector,
        crop: CropParameterProfile,
        weights: Optional[Dict[str, float]] = None
    ) -> CropSuitabilityScore:
        """Evaluates multi-factor suitability using Liebig minimum and geometric mean."""
        w = weights or self.DEFAULT_WEIGHTS

        # Scale observation rainfall to 90-day equivalent if observation period is shorter
        duration_factor = 90.0 / max(1, features.observation_days)
        projected_seasonal_rain = features.total_rainfall * duration_factor

        s_temp = self.evaluate_trapezoid(features.mean_air_temp, crop.temperature_c)
        s_ph = self.evaluate_trapezoid(features.mean_soil_ph, crop.soil_ph)
        s_vwc = self.evaluate_trapezoid(features.mean_soil_vwc, crop.soil_moisture_vwc)
        s_rain = self.evaluate_trapezoid(projected_seasonal_rain, crop.seasonal_rainfall_mm)
        s_ec = self.evaluate_ec_tolerance(features.mean_soil_ec, crop.max_ec_ds_m)

        factor_scores = {
            "temperature": round(s_temp, 3),
            "soil_ph": round(s_ph, 3),
            "soil_moisture": round(s_vwc, 3),
            "rainfall": round(s_rain, 3),
            "soil_ec": round(s_ec, 3)
        }

        # 1. Liebig's Law of the Minimum
        liebig_score = min(factor_scores.values())

        # 2. Weighted Geometric Mean (with floor epsilon to prevent log-domain divergence)
        log_sum = 0.0
        total_w = sum(w.values())
        for factor, score in factor_scores.items():
            weight = w.get(factor, 0.20) / total_w
            clamped_score = max(0.01, score)
            log_sum += weight * math.log(clamped_score)

        geometric_score = round(math.exp(log_sum), 3)

        # Composite overall score balances geometric stability with Liebig limiting constraint
        composite = round(0.60 * geometric_score + 0.40 * liebig_score, 3)
        fao_class = FAOClass.from_score(composite)

        # Find limiting factor (minimum score)
        limiting_factor = min(factor_scores, key=factor_scores.get)

        return CropSuitabilityScore(
            crop_id=crop.crop_id,
            crop_name=crop.name,
            overall_score=composite,
            liebig_score=round(liebig_score, 3),
            geometric_score=geometric_score,
            fao_class=fao_class,
            factor_scores=factor_scores,
            limiting_factor=limiting_factor
        )
