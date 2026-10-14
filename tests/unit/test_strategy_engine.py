import pytest
from datetime import date
from src.domain.enums import ConfidenceLevel, RecommendationStatus, FAOClass
from src.domain.entities import AgronomicFeatureVector
from src.agronomy.catalog_loader import CatalogLoader
from src.strategy.engine import StrategyEngine


@pytest.fixture
def test_engine():
    crop_cat = CatalogLoader.load_crop_catalog()
    econ_cat = CatalogLoader.load_economic_catalog()
    return StrategyEngine(crop_catalog=crop_cat, economic_catalog=econ_cat)


def test_strategy_engine_ranking(test_engine):
    # Features tailored for Padi Sawah (wetland, high moisture)
    features = AgronomicFeatureVector(
        site_id="SITE-TEST-01",
        period_start=date.today(),
        period_end=date.today(),
        observation_days=30,
        mean_air_temp=28.0,
        min_air_temp=23.0,
        max_air_temp=32.0,
        mean_rh=82.0,
        mean_soil_vwc=72.0,
        mean_soil_temp=27.0,
        mean_soil_ph=6.3,
        mean_soil_ec=1.0,
        total_rainfall=500.0,
        mean_solar_radiation=450.0,
        mean_wind_speed=1.5,
        mean_soil_n=120.0,
        mean_soil_p=45.0,
        mean_soil_k=60.0
    )

    report = test_engine.evaluate_land_parcel(features, data_completeness_ratio=1.0)

    assert report.site_id == "SITE-TEST-01"
    assert report.confidence_level == ConfidenceLevel.HIGH
    assert report.status == RecommendationStatus.APPROVED
    assert report.primary_recommendation is not None
    assert report.primary_recommendation.rank == 1
    # Padi sawah should rank at the top given high moisture and temperature
    assert report.primary_recommendation.crop_id == "padi_sawah"
    assert report.primary_recommendation.economics.normal_profit_idr > 0
    assert len(report.alternatives) >= 1


def test_confidence_gate_on_low_data(test_engine):
    features = AgronomicFeatureVector(
        site_id="SITE-LOW-DATA",
        period_start=date.today(),
        period_end=date.today(),
        observation_days=10,  # Only 10 days of observations
        mean_air_temp=27.0,
        min_air_temp=22.0,
        max_air_temp=32.0,
        mean_rh=75.0,
        mean_soil_vwc=50.0,
        mean_soil_temp=26.0,
        mean_soil_ph=6.2,
        mean_soil_ec=1.0,
        total_rainfall=150.0,
        mean_solar_radiation=400.0,
        mean_wind_speed=1.5,
        mean_soil_n=90.0,
        mean_soil_p=35.0,
        mean_soil_k=120.0
    )

    # 10 days out of 30 -> completeness 0.33 (< 0.70 threshold)
    report = test_engine.evaluate_land_parcel(features, data_completeness_ratio=0.33)

    assert report.confidence_level == ConfidenceLevel.LOW
    assert report.status == RecommendationStatus.NEEDS_AGRONOMIST_REVIEW
    assert len(report.system_notes) > 0
