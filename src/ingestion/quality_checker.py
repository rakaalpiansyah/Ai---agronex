from dataclasses import dataclass
from typing import Dict, List, Tuple
import numpy as np
from src.domain.enums import SensorMetric


@dataclass
class QualityValidationResult:
    is_valid: bool
    sanitized_metrics: Dict[str, float]
    anomalies: List[str]


class QualityChecker:
    """Validates physical limits, detects stuck sensors, and quarantines outliers."""

    # Physical plausibility limits for tropical agricultural environments
    PHYSICAL_RANGES: Dict[str, Tuple[float, float]] = {
        SensorMetric.SOIL_MOISTURE_VWC.value: (0.0, 100.0),
        SensorMetric.SOIL_TEMPERATURE.value: (-5.0, 60.0),
        SensorMetric.SOIL_PH.value: (3.0, 10.0),
        SensorMetric.SOIL_EC.value: (0.0, 20.0),
        SensorMetric.SOIL_N.value: (0.0, 500.0),
        SensorMetric.SOIL_P.value: (0.0, 500.0),
        SensorMetric.SOIL_K.value: (0.0, 800.0),
        SensorMetric.AIR_TEMPERATURE.value: (-10.0, 60.0),
        SensorMetric.AIR_HUMIDITY.value: (0.0, 100.0),
        SensorMetric.RAINFALL.value: (0.0, 300.0),
        SensorMetric.SOLAR_RADIATION.value: (0.0, 1500.0),
        SensorMetric.WIND_SPEED.value: (0.0, 60.0),
    }

    # Metrics that exhibit natural environmental variation and should not remain static
    DYNAMIC_METRICS = {
        SensorMetric.AIR_TEMPERATURE.value,
        SensorMetric.AIR_HUMIDITY.value,
        SensorMetric.SOIL_MOISTURE_VWC.value,
        SensorMetric.SOLAR_RADIATION.value,
    }

    def validate_reading(self, metrics: Dict[str, float]) -> QualityValidationResult:
        """Validates a single point in time reading against physical range boundaries."""
        sanitized: Dict[str, float] = {}
        anomalies: List[str] = []

        for metric, value in metrics.items():
            if value is None or np.isnan(value):
                anomalies.append(f"{metric}: value is null/NaN")
                continue

            if metric in self.PHYSICAL_RANGES:
                min_val, max_val = self.PHYSICAL_RANGES[metric]
                if not (min_val <= value <= max_val):
                    anomalies.append(
                        f"{metric}: value {value} out of physical range [{min_val}, {max_val}]"
                    )
                    continue

            sanitized[metric] = float(value)

        return QualityValidationResult(
            is_valid=len(anomalies) == 0,
            sanitized_metrics=sanitized,
            anomalies=anomalies
        )

    def detect_stuck_sensor(
        self,
        recent_values: List[float],
        metric_name: str,
        threshold_std: float = 1e-4
    ) -> bool:
        """Flags sensors reporting unchanging values across a consecutive window."""
        if metric_name not in self.DYNAMIC_METRICS or len(recent_values) < 6:
            return False

        std_dev = float(np.std(recent_values))
        return std_dev < threshold_std

    def apply_hampel_filter(
        self,
        series: List[float],
        window_size: int = 5,
        n_sigmas: float = 3.0
    ) -> Tuple[List[float], List[int]]:
        """Replaces sudden spike anomalies using the median absolute deviation (MAD)."""
        n = len(series)
        filtered = list(series)
        outlier_indices: List[int] = []

        if n < window_size:
            return filtered, outlier_indices

        k = 1.4826  # Scale factor for normal distribution consistency
        half_window = window_size // 2

        for i in range(half_window, n - half_window):
            window = series[i - half_window : i + half_window + 1]
            median = np.median(window)
            mad = k * np.median(np.abs(window - median))

            if mad == 0:
                continue

            difference = np.abs(series[i] - median)
            if difference > n_sigmas * mad:
                filtered[i] = float(median)
                outlier_indices.append(i)

        return filtered, outlier_indices
