import pytest
import math
# pyrefly: ignore [missing-import]
from src.agronomy.indices import AgronomicIndicesCalculator


def test_saturation_vapor_pressure():
    # At 25°C, Tetens equation yields es ≈ 3.167 kPa
    es_25 = AgronomicIndicesCalculator.calculate_saturation_vapor_pressure(25.0)
    assert math.isclose(es_25, 3.167, rel_tol=1e-2)


def test_vapor_pressure_deficit():
    # At 25°C and 60% RH, VPD = es * (1 - 0.6) = 3.167 * 0.4 ≈ 1.267 kPa
    vpd = AgronomicIndicesCalculator.calculate_vapor_pressure_deficit(25.0, 60.0)
    assert math.isclose(vpd, 1.267, rel_tol=1e-2)

    # At 100% RH, VPD should be zero
    vpd_saturated = AgronomicIndicesCalculator.calculate_vapor_pressure_deficit(30.0, 100.0)
    assert vpd_saturated == 0.0


def test_growing_degree_days():
    # Tmax = 30°C, Tmin = 20°C, Tmean = 25°C, Tbase = 10°C -> GDD = 15.0
    gdd = AgronomicIndicesCalculator.calculate_growing_degree_days(30.0, 20.0, t_base_c=10.0)
    assert gdd == 15.0

    # Below base temperature -> GDD = 0.0
    gdd_cold = AgronomicIndicesCalculator.calculate_growing_degree_days(8.0, 4.0, t_base_c=10.0)
    assert gdd_cold == 0.0


def test_fao56_penman_monteith_et0():
    et0 = AgronomicIndicesCalculator.calculate_fao56_penman_monteith_et0(
        mean_air_temp_c=27.0,
        relative_humidity_percent=75.0,
        solar_radiation_w_m2=200.0,
        wind_speed_m_s=1.5,
        elevation_m=50.0
    )
    # Typical tropical daily ET0 ranges between 3.0 and 6.0 mm/day
    assert 3.0 <= et0 <= 6.0


def test_crop_water_balance():
    # Rain = 100 mm, Irrigation = 20 mm, ET0 = 50 mm, Kc = 1.2 -> ETc = 60 mm -> Balance = 120 - 60 = 60 mm
    wb = AgronomicIndicesCalculator.calculate_crop_water_balance(
        precipitation_mm=100.0,
        irrigation_mm=20.0,
        et0_mm=50.0,
        crop_kc=1.2
    )
    assert wb == 60.0
