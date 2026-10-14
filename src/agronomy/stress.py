from typing import Dict, List
import pandas as pd


class AgronomicStressEvaluator:
    """Evaluates crop abiotic stress factors across observation windows."""

    def evaluate_daily_stresses(
        self,
        daily_df: pd.DataFrame,
        wilting_point_vwc: float = 20.0,
        field_capacity_vwc: float = 75.0,
        heat_threshold_c: float = 35.0,
        max_ec_tolerated: float = 2.0
    ) -> Dict[str, Any]:
        """Calculates cumulative stress day metrics from daily timeseries."""
        if daily_df.empty:
            return {
                "moisture_stress_days": 0,
                "waterlogging_days": 0,
                "heat_stress_days": 0,
                "salinity_stress_ratio": 0.0,
            }

        vwc = daily_df.get("soil_moisture_vwc", pd.Series([45.0] * len(daily_df)))
        t_max = daily_df.get("air_temperature_max", daily_df.get("air_temperature", pd.Series([28.0] * len(daily_df))))
        ec = daily_df.get("soil_ec", pd.Series([1.0] * len(daily_df)))

        moisture_stress = int((vwc < wilting_point_vwc).sum())
        waterlogging = int((vwc > field_capacity_vwc).sum())
        heat_stress = int((t_max > heat_threshold_c).sum())
        mean_ec = float(ec.mean())
        salinity_ratio = round(max(0.0, mean_ec / max_ec_tolerated), 2) if max_ec_tolerated > 0 else 0.0

        return {
            "moisture_stress_days": moisture_stress,
            "waterlogging_days": waterlogging,
            "heat_stress_days": heat_stress,
            "salinity_stress_ratio": salinity_ratio,
        }

    def evaluate_nutrient_sufficiency(
        self,
        soil_n: float,
        soil_p: float,
        soil_k: float,
        crop_n_demand: float,
        crop_p_demand: float,
        crop_k_demand: float
    ) -> Dict[str, float]:
        """Calculates the ratio of available soil nutrients to seasonal crop requirements."""
        return {
            "n_sufficiency": round(min(1.5, soil_n / max(1.0, crop_n_demand)), 2),
            "p_sufficiency": round(min(1.5, soil_p / max(1.0, crop_p_demand)), 2),
            "k_sufficiency": round(min(1.5, soil_k / max(1.0, crop_k_demand)), 2),
        }
