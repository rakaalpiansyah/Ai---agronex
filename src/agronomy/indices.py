import math
from typing import Dict, Any


class AgronomicIndicesCalculator:
    """Computes micrometeorological and agronomic indices according to FAO-56 standards."""

    @staticmethod
    def calculate_saturation_vapor_pressure(temperature_c: float) -> float:
        """Calculates saturation vapor pressure (es) in kPa using the Tetens equation."""
        return 0.6108 * math.exp((17.27 * temperature_c) / (temperature_c + 237.3))

    @staticmethod
    def calculate_vapor_pressure_deficit(air_temperature_c: float, relative_humidity_percent: float) -> float:
        """Calculates Vapor Pressure Deficit (VPD) in kPa.

        Higher VPD indicates higher atmospheric evaporative demand and transpiration stress.
        """
        es = AgronomicIndicesCalculator.calculate_saturation_vapor_pressure(air_temperature_c)
        rh_clamped = min(100.0, max(0.0, relative_humidity_percent))
        ea = es * (rh_clamped / 100.0)
        return max(0.0, round(es - ea, 3))

    @staticmethod
    def calculate_growing_degree_days(
        t_max_c: float,
        t_min_c: float,
        t_base_c: float = 10.0,
        t_cutoff_c: float = 35.0
    ) -> float:
        """Calculates daily Growing Degree Days (GDD) with base and upper threshold cutoffs."""
        # Standard agronomic cutoff clamp
        t_max_clamped = min(t_cutoff_c, max(t_base_c, t_max_c))
        t_min_clamped = max(t_base_c, t_min_c)
        t_mean = (t_max_clamped + t_min_clamped) / 2.0
        return max(0.0, round(t_mean - t_base_c, 2))

    @staticmethod
    def calculate_fao56_penman_monteith_et0(
        mean_air_temp_c: float,
        relative_humidity_percent: float,
        solar_radiation_w_m2: float,
        wind_speed_m_s: float,
        elevation_m: float = 100.0
    ) -> float:
        """Calculates daily reference evapotranspiration (ET0) in mm/day via FAO-56 Penman-Monteith."""
        t = mean_air_temp_c
        u2 = max(0.1, wind_speed_m_s)
        rh = min(100.0, max(1.0, relative_humidity_percent))

        # Atmospheric pressure (kPa) based on elevation
        p = 101.3 * math.pow((293.0 - 0.0065 * elevation_m) / 293.0, 5.26)
        # Psychrometric constant (kPa / °C)
        gamma = 0.000665 * p

        # Vapor pressures
        es = AgronomicIndicesCalculator.calculate_saturation_vapor_pressure(t)
        ea = es * (rh / 100.0)

        # Slope of saturation vapor pressure curve (kPa / °C)
        delta = (4098.0 * es) / math.pow(t + 237.3, 2)

        # Net radiation approximation (MJ/m2/day) from solar radiation (W/m2)
        # Conversion: 1 W/m2 = 0.0864 MJ/m2/day, default canopy albedo = 0.23
        rn = max(0.0, solar_radiation_w_m2 * 0.0864 * (1.0 - 0.23))
        g = 0.0  # Daily soil heat flux density is negligible

        numerator = 0.408 * delta * (rn - g) + gamma * (900.0 / (t + 273.0)) * u2 * (es - ea)
        denominator = delta + gamma * (1.0 + 0.34 * u2)

        if denominator <= 0:
            return 3.5  # Typical tropical fallback default

        et0 = numerator / denominator
        return max(0.5, round(et0, 2))

    @staticmethod
    def calculate_crop_water_balance(
        precipitation_mm: float,
        irrigation_mm: float,
        et0_mm: float,
        crop_kc: float
    ) -> float:
        """Calculates water balance: precipitation + irrigation - crop evapotranspiration (ETc)."""
        etc = crop_kc * et0_mm
        return round((precipitation_mm + irrigation_mm) - etc, 2)

    @staticmethod
    def calculate_aridity_index(total_precipitation_mm: float, total_et0_mm: float) -> float:
        """Calculates UNEP Aridity Index (P / ET0)."""
        if total_et0_mm <= 0:
            return 1.0
        return round(total_precipitation_mm / total_et0_mm, 3)
