from typing import Dict, Any, Tuple
import pandas as pd
from datetime import date
from src.domain.entities import AgronomicFeatureVector


class TemporalAggregator:
    """Aggregates multi-frequency time-series telemetry into daily and seasonal vectors."""

    REQUIRED_METRICS = [
        "air_temperature",
        "air_humidity",
        "soil_moisture_vwc",
        "soil_temperature",
        "soil_ph",
        "soil_ec",
        "rainfall",
        "solar_radiation",
        "wind_speed"
    ]

    def aggregate_daily(
        self,
        df: pd.DataFrame,
        time_col: str = "timestamp"
    ) -> pd.DataFrame:
        """Computes daily mean, extrema, and rainfall totals."""
        if df.empty:
            return pd.DataFrame()

        data = df.copy()
        data[time_col] = pd.to_datetime(data[time_col], utc=True)

        data["date"] = data[time_col].dt.date

        agg_rules: Dict[str, Any] = {}
        if "air_temperature" in data.columns:
            agg_rules["air_temperature"] = ["mean", "min", "max"]
        if "air_humidity" in data.columns:
            agg_rules["air_humidity"] = "mean"
        if "soil_moisture_vwc" in data.columns:
            agg_rules["soil_moisture_vwc"] = "mean"
        if "soil_temperature" in data.columns:
            agg_rules["soil_temperature"] = "mean"
        if "soil_ph" in data.columns:
            agg_rules["soil_ph"] = "mean"
        if "soil_ec" in data.columns:
            agg_rules["soil_ec"] = "mean"
        if "soil_n" in data.columns:
            agg_rules["soil_n"] = "mean"
        if "soil_p" in data.columns:
            agg_rules["soil_p"] = "mean"
        if "soil_k" in data.columns:
            agg_rules["soil_k"] = "mean"
        if "rainfall" in data.columns:
            agg_rules["rainfall"] = "sum"
        if "solar_radiation" in data.columns:
            agg_rules["solar_radiation"] = "mean"
        if "wind_speed" in data.columns:
            agg_rules["wind_speed"] = "mean"

        daily_df = data.groupby("date").agg(agg_rules)
        # Flatten MultiIndex columns
        daily_df.columns = [
            f"{col}_{stat}" if isinstance(stat, str) and stat in ["min", "max", "sum"] else col
            for col, stat in daily_df.columns
        ]
        return daily_df.reset_index()

    def build_feature_vector(
        self,
        daily_df: pd.DataFrame,
        site_id: str
    ) -> Tuple[AgronomicFeatureVector, float]:
        """Synthesizes a 30-day summary agronomic feature vector and completeness ratio."""
        if daily_df.empty:
            raise ValueError(f"No daily records available for site {site_id}")

        n_days = len(daily_df)
        period_start = daily_df["date"].min()
        period_end = daily_df["date"].max()

        # Expected 30 days window for seasonal decision baseline
        completeness_ratio = min(1.0, round(n_days / 30.0, 3))

        vector = AgronomicFeatureVector(
            site_id=site_id,
            period_start=period_start if isinstance(period_start, date) else date.today(),
            period_end=period_end if isinstance(period_end, date) else date.today(),
            observation_days=n_days,
            mean_air_temp=float(daily_df.get("air_temperature", [27.0]).mean()),
            min_air_temp=float(daily_df.get("air_temperature_min", [22.0]).min()),
            max_air_temp=float(daily_df.get("air_temperature_max", [32.0]).max()),
            mean_rh=float(daily_df.get("air_humidity", [75.0]).mean()),
            mean_soil_vwc=float(daily_df.get("soil_moisture_vwc", [45.0]).mean()),
            mean_soil_temp=float(daily_df.get("soil_temperature", [26.0]).mean()),
            mean_soil_ph=float(daily_df.get("soil_ph", [6.2]).mean()),
            mean_soil_ec=float(daily_df.get("soil_ec", [1.0]).mean()),
            total_rainfall=float(daily_df.get("rainfall_sum", [0.0]).sum()),
            mean_solar_radiation=float(daily_df.get("solar_radiation", [400.0]).mean()),
            mean_wind_speed=float(daily_df.get("wind_speed", [1.5]).mean()),
            mean_soil_n=float(daily_df.get("soil_n", [90.0]).mean()),
            mean_soil_p=float(daily_df.get("soil_p", [35.0]).mean()),
            mean_soil_k=float(daily_df.get("soil_k", [120.0]).mean()),
        )

        return vector, completeness_ratio
