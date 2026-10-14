import pytest
from src.ingestion.quality_checker import QualityChecker


def test_physical_range_validation():
    checker = QualityChecker()

    valid_reading = {
        "air_temperature": 28.5,
        "soil_moisture_vwc": 45.0,
        "soil_ph": 6.5,
        "soil_ec": 1.2
    }
    result = checker.validate_reading(valid_reading)
    assert result.is_valid
    assert len(result.anomalies) == 0

    invalid_reading = {
        "air_temperature": 85.0,   # Impossibly hot for open agricultural fields
        "soil_moisture_vwc": -5.0,  # Negative moisture
        "soil_ph": 13.0             # Extreme alkaline caustic
    }
    invalid_result = checker.validate_reading(invalid_reading)
    assert not invalid_result.is_valid
    assert len(invalid_result.anomalies) == 3


def test_stuck_sensor_detection():
    checker = QualityChecker()

    # Dynamic metric stuck at exactly 25.0 across 10 observations
    stuck_series = [25.0] * 10
    is_stuck = checker.detect_stuck_sensor(stuck_series, "air_temperature")
    assert is_stuck

    # Naturally varying series
    healthy_series = [24.8, 25.1, 25.4, 25.2, 24.9, 25.0, 25.3]
    assert not checker.detect_stuck_sensor(healthy_series, "air_temperature")


def test_hampel_spike_filter():
    checker = QualityChecker()

    # Normal series with an isolated sensor spike at index 4
    series = [25.0, 25.1, 25.0, 25.2, 85.0, 25.1, 25.0, 25.2, 25.1]
    filtered, outlier_indices = checker.apply_hampel_filter(series, window_size=5, n_sigmas=3.0)

    assert 4 in outlier_indices
    # Outlier at index 4 should be replaced with a median value (~25.1)
    assert filtered[4] < 30.0
