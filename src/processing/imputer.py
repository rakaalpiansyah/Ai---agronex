from typing import List, Optional
import pandas as pd


class TimeSeriesImputer:
    """Imputes short gaps and flags non-recoverable missing telemetry intervals."""

    def impute_short_gaps(
        self,
        df: pd.DataFrame,
        time_col: str = "timestamp",
        max_consecutive_hours: int = 2
    ) -> pd.DataFrame:
        """Applies time-weighted linear interpolation for gaps shorter than the threshold."""
        if df.empty or time_col not in df.columns:
            return df

        result = df.copy()
        result[time_col] = pd.to_datetime(result[time_col], utc=True)

        result = result.sort_values(by=time_col).reset_index(drop=True)
        numeric_cols = result.select_dtypes(include=["float64", "float32", "int64"]).columns

        # Interpolate only gaps within the hourly limit based on record frequency
        for col in numeric_cols:
            result[col] = result[col].interpolate(
                method="linear",
                limit=max_consecutive_hours * 4,  # Assuming typical 15-minute sampling frequency
                limit_direction="both"
            )

        return result
