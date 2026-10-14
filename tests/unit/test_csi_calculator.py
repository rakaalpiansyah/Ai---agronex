import pytest
from datetime import date
from src.domain.enums import FAOClass
from src.domain.entities import TrapezoidLimits, CropParameterProfile, AgronomicFeatureVector
from src.agronomy.csi_calculator import CropSuitabilityCalculator


@pytest.fixture
def dummy_crop():
    return CropParameterProfile(
        crop_id="test_crop",
        name="Test Crop",
        scientific_name="Testus cropus",
        category="Test",
        temperature_c=TrapezoidLimits(min_abs=15.0, min_opt=22.0, max_opt=30.0, max_abs=38.0),
        soil_ph=TrapezoidLimits(min_abs=5.0, min_opt=6.0, max_opt=7.0, max_abs=8.0),
        soil_moisture_vwc=TrapezoidLimits(min_abs=20.0, min_opt=40.0, max_opt=70.0, max_abs=85.0),
        seasonal_rainfall_mm=TrapezoidLimits(min_abs=400.0, min_opt=600.0, max_opt=1200.0, max_abs=2000.0),
        max_ec_ds_m=2.5,
        t_base_c=10.0,
        maturity_gdd=1400.0,
        kc_initial=0.4,
        kc_mid=1.2,
        kc_late=0.6,
        n_demand_kg_ha=120.0,
        p_demand_kg_ha=50.0,
        k_demand_kg_ha=60.0,
        yield_pessimistic_ton_ha=4.0,
        yield_normal_ton_ha=6.0,
        yield_optimistic_ton_ha=8.0,
        growth_duration_days=100
    )


def test_trapezoid_evaluation():
    limits = TrapezoidLimits(min_abs=10.0, min_opt=20.0, max_opt=30.0, max_abs=40.0)

    # Within optimal plateau
    assert CropSuitabilityCalculator.evaluate_trapezoid(25.0, limits) == 1.0

    # Outside absolute bounds
    assert CropSuitabilityCalculator.evaluate_trapezoid(5.0, limits) == 0.0
    assert CropSuitabilityCalculator.evaluate_trapezoid(45.0, limits) == 0.0

    # Shoulder linear interpolation
    # Midpoint of 10 to 20 is 15 -> score 0.5
    assert CropSuitabilityCalculator.evaluate_trapezoid(15.0, limits) == 0.5
    # Midpoint of 30 to 40 is 35 -> score 0.5
    assert CropSuitabilityCalculator.evaluate_trapezoid(35.0, limits) == 0.5


def test_csi_calculation_optimal_conditions(dummy_crop):
    calc = CropSuitabilityCalculator()
    features = AgronomicFeatureVector(
        site_id="SITE-OPT",
        period_start=date.today(),
        period_end=date.today(),
        observation_days=30,
        mean_air_temp=26.0,  # inside [22, 30]
        min_air_temp=22.0,
        max_air_temp=30.0,
        mean_rh=75.0,
        mean_soil_vwc=55.0,  # inside [40, 70]
        mean_soil_temp=25.0,
        mean_soil_ph=6.5,    # inside [6.0, 7.0]
        mean_soil_ec=0.8,    # well below 2.5
        total_rainfall=300.0,  # 300 * (90/30) = 900 mm -> inside [600, 1200]
        mean_solar_radiation=450.0,
        mean_wind_speed=1.5,
        mean_soil_n=100.0,
        mean_soil_p=40.0,
        mean_soil_k=60.0
    )

    score = calc.calculate_crop_csi(features, dummy_crop)
    assert score.overall_score >= 0.80
    assert score.fao_class == FAOClass.S1
    assert score.liebig_score == 1.0


def test_liebig_minimum_law(dummy_crop):
    calc = CropSuitabilityCalculator()
    # Soil pH is severely acidic (pH 4.0, outside min_abs 5.0)
    features = AgronomicFeatureVector(
        site_id="SITE-ACID",
        period_start=date.today(),
        period_end=date.today(),
        observation_days=30,
        mean_air_temp=26.0,
        min_air_temp=22.0,
        max_air_temp=30.0,
        mean_rh=75.0,
        mean_soil_vwc=55.0,
        mean_soil_temp=25.0,
        mean_soil_ph=4.0,  # Outside absolute limit
        mean_soil_ec=0.8,
        total_rainfall=300.0,
        mean_solar_radiation=450.0,
        mean_wind_speed=1.5,
        mean_soil_n=100.0,
        mean_soil_p=40.0,
        mean_soil_k=60.0
    )

    score = calc.calculate_crop_csi(features, dummy_crop)
    assert score.factor_scores["soil_ph"] == 0.0
    assert score.liebig_score == 0.0
    assert score.limiting_factor == "soil_ph"
    assert score.fao_class == FAOClass.N
