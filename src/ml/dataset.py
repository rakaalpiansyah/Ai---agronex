from typing import List, Tuple, Dict, Any, Generator
import pandas as pd
import numpy as np
from sklearn.model_selection import GroupKFold
from src.domain.entities import AgronomicFeatureVector


class MLDatasetBuilder:
    """Builds tabular feature matrices and enforces spatial-temporal cross-validation."""

    FEATURE_COLUMNS: List[str] = [
        "mean_air_temp",
        "min_air_temp",
        "max_air_temp",
        "mean_rh",
        "mean_soil_vwc",
        "mean_soil_temp",
        "mean_soil_ph",
        "mean_soil_ec",
        "total_rainfall",
        "mean_solar_radiation",
        "mean_wind_speed",
        "mean_soil_n",
        "mean_soil_p",
        "mean_soil_k",
        "mean_vpd_kpa",
        "cumulative_gdd",
        "reference_et0_mm",
        "water_balance_mm",
        "moisture_stress_days",
        "waterlogging_days",
        "heat_stress_days",
    ]

    @classmethod
    def vector_to_feature_dict(cls, vector: AgronomicFeatureVector) -> Dict[str, float]:
        """Converts an AgronomicFeatureVector instance into a flat feature dictionary."""
        return {col: float(getattr(vector, col, 0.0)) for col in cls.FEATURE_COLUMNS}

    @classmethod
    def dataframe_to_xy(
        cls,
        df: pd.DataFrame,
        target_col: str = "crop_label"
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """Extracts feature matrix X and target label Series y from a DataFrame."""
        available_features = [col for col in cls.FEATURE_COLUMNS if col in df.columns]
        X = df[available_features].copy()
        y = df[target_col].copy()
        return X, y

    @staticmethod
    def get_spatial_kfold_splits(
        df: pd.DataFrame,
        group_col: str = "site_id",
        n_splits: int = 4
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """Yields train and test index partitions ensuring entire sites are held out together."""
        unique_groups = df[group_col].nunique()
        actual_splits = min(n_splits, unique_groups)
        if actual_splits < 2:
            raise ValueError(f"At least 2 distinct sites required for spatial cross-validation. Found: {unique_groups}")

        gkf = GroupKFold(n_splits=actual_splits)
        groups = df[group_col].values
        X = df.drop(columns=[group_col])
        return gkf.split(X, groups=groups)

    @staticmethod
    def get_time_based_split(
        df: pd.DataFrame,
        time_col: str = "season_year",
        cutoff_year: int = 2025
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Splits records chronologically to evaluate generalization on future growing seasons."""
        train_df = df[df[time_col] <= cutoff_year].copy()
        test_df = df[df[time_col] > cutoff_year].copy()
        return train_df, test_df
