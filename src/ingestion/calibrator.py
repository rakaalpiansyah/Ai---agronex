from src.domain.enums import SoilType


class SensorCalibrator:
    """Applies physics-based and empirical corrections to raw sensor signals."""

    # Standard FAO temperature coefficient for electrical conductivity
    ALPHA_EC: float = 0.0191

    # Soil texture specific polynomial coefficients for capacitive sensors
    SOIL_VWC_CALIBRATION = {
        SoilType.CLAY: {"intercept": -0.05, "slope": 1.08},
        SoilType.LOAM: {"intercept": 0.0, "slope": 1.00},
        SoilType.SANDY_LOAM: {"intercept": 0.02, "slope": 0.95},
        SoilType.SAND: {"intercept": 0.04, "slope": 0.90},
    }

    def normalize_ec_to_25c(self, raw_ec: float, temperature_c: float) -> float:
        """Normalizes electrical conductivity to standard 25 degrees Celsius reference."""
        if raw_ec <= 0.0:
            return 0.0

        denominator = 1.0 + self.ALPHA_EC * (temperature_c - 25.0)
        if denominator <= 0.0:
            return raw_ec

        return round(raw_ec / denominator, 3)

    def calibrate_soil_moisture(self, raw_vwc: float, soil_type: SoilType) -> float:
        """Calibrates capacitive volumetric water content using soil texture curves."""
        params = self.SOIL_VWC_CALIBRATION.get(
            soil_type, self.SOIL_VWC_CALIBRATION[SoilType.LOAM]
        )
        corrected = params["intercept"] + (params["slope"] * raw_vwc)
        return float(min(100.0, max(0.0, round(corrected, 2))))

    def compensate_ph_temperature(self, raw_ph: float, temperature_c: float) -> float:
        """Applies Nernst equation temperature offset around neutral point (pH 7.0)."""
        temp_diff = temperature_c - 25.0
        # pH electrode slope changes ~0.0033 per pH unit deviation from pH 7.0 per °C
        delta_ph = raw_ph - 7.0
        correction = -0.0033 * delta_ph * (temp_diff / 10.0)
        return float(min(14.0, max(0.0, round(raw_ph + correction, 2))))
