from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from datetime import date
from pydantic import BaseModel, Field

from src.domain.entities import AgronomicFeatureVector, CropParameterProfile
from src.domain.enums import SoilType
from src.strategy.engine import StrategyEngine
from src.processing.pipeline import MedallionPipeline
from src.agronomy.indices import AgronomicIndicesCalculator
from src.agronomy.stress import AgronomicStressEvaluator
from src.api.dependencies import (
    get_strategy_engine,
    get_medallion_pipeline,
    get_crop_catalog
)

router = APIRouter(prefix="/recommendations", tags=["Crop Recommendations"])


class DirectEvaluationRequest(BaseModel):
    """Request schema for evaluating land suitability directly from environmental features."""
    site_id: str = Field(..., json_schema_extra={"example": "LAHAN-A07-LAMPUNG"})
    mean_air_temp: float = Field(27.0, ge=-5.0, le=55.0, description="Mean temperature in Celsius")
    min_air_temp: float = Field(22.0, ge=-10.0, le=50.0)
    max_air_temp: float = Field(32.0, ge=-5.0, le=60.0)
    mean_rh: float = Field(75.0, ge=10.0, le=100.0, description="Mean relative humidity percentage")
    mean_soil_vwc: float = Field(45.0, ge=0.0, le=100.0, description="Mean volumetric water content percentage")
    mean_soil_temp: float = Field(26.0, ge=0.0, le=50.0)
    mean_soil_ph: float = Field(6.3, ge=3.0, le=10.0, description="Soil pH level")
    mean_soil_ec: float = Field(1.0, ge=0.0, le=20.0, description="Soil EC in dS/m")
    total_rainfall: float = Field(350.0, ge=0.0, description="Seasonal or 30-day cumulative rainfall in mm")
    mean_solar_radiation: float = Field(450.0, ge=0.0, description="Solar radiation in W/m2")
    mean_wind_speed: float = Field(1.8, ge=0.0, le=40.0, description="Wind speed in m/s")
    mean_soil_n: float = Field(110.0, ge=0.0, description="Available Nitrogen in kg/ha")
    mean_soil_p: float = Field(35.0, ge=0.0, description="Available Phosphorus in kg/ha")
    mean_soil_k: float = Field(130.0, ge=0.0, description="Available Potassium in kg/ha")
    observation_days: int = Field(30, ge=1, le=365)
    use_llm: bool = Field(False, description="Enable LLM narrative generation for advisory notes")


@router.post("/evaluate")
def evaluate_recommendation(
    payload: DirectEvaluationRequest,
    engine: StrategyEngine = Depends(get_strategy_engine)
) -> Dict[str, Any]:
    """Evaluates crop suitability, projected economics, and prescriptions from feature metrics."""
    # Compute derived agronomic indices
    vpd = AgronomicIndicesCalculator.calculate_vapor_pressure_deficit(
        payload.mean_air_temp, payload.mean_rh
    )
    gdd = AgronomicIndicesCalculator.calculate_growing_degree_days(
        payload.max_air_temp, payload.min_air_temp, t_base_c=10.0
    ) * payload.observation_days

    et0 = AgronomicIndicesCalculator.calculate_fao56_penman_monteith_et0(
        mean_air_temp_c=payload.mean_air_temp,
        relative_humidity_percent=payload.mean_rh,
        solar_radiation_w_m2=payload.mean_solar_radiation,
        wind_speed_m_s=payload.mean_wind_speed
    ) * payload.observation_days

    water_balance = round(payload.total_rainfall - et0, 2)

    # Heuristic stress day estimators for direct features
    moisture_stress = 3 if payload.mean_soil_vwc < 25.0 else 0
    waterlogging = 3 if payload.mean_soil_vwc > 80.0 else 0
    heat_stress = 2 if payload.max_air_temp > 35.0 else 0

    vector = AgronomicFeatureVector(
        site_id=payload.site_id,
        period_start=date.today(),
        period_end=date.today(),
        observation_days=payload.observation_days,
        mean_air_temp=payload.mean_air_temp,
        min_air_temp=payload.min_air_temp,
        max_air_temp=payload.max_air_temp,
        mean_rh=payload.mean_rh,
        mean_soil_vwc=payload.mean_soil_vwc,
        mean_soil_temp=payload.mean_soil_temp,
        mean_soil_ph=payload.mean_soil_ph,
        mean_soil_ec=payload.mean_soil_ec,
        total_rainfall=payload.total_rainfall,
        mean_solar_radiation=payload.mean_solar_radiation,
        mean_wind_speed=payload.mean_wind_speed,
        mean_soil_n=payload.mean_soil_n,
        mean_soil_p=payload.mean_soil_p,
        mean_soil_k=payload.mean_soil_k,
        mean_vpd_kpa=vpd,
        cumulative_gdd=gdd,
        reference_et0_mm=et0,
        water_balance_mm=water_balance,
        moisture_stress_days=moisture_stress,
        waterlogging_days=waterlogging,
        heat_stress_days=heat_stress
    )

    data_completeness = min(1.0, payload.observation_days / 30.0)
    report = engine.evaluate_land_parcel(vector, data_completeness, use_llm=payload.use_llm)

    # Format response dictionary cleanly
    primary_data = None
    if report.primary_recommendation:
        pr = report.primary_recommendation
        primary_data = {
            "rank": pr.rank,
            "crop_id": pr.crop_id,
            "crop_name": pr.crop_name,
            "composite_score": pr.composite_score,
            "suitability_score": pr.suitability.overall_score,
            "fao_class": pr.suitability.fao_class.value,
            "fao_label": pr.suitability.fao_class.label_id,
            "limiting_factor": pr.suitability.limiting_factor,
            "factor_scores": pr.suitability.factor_scores,
            "yield_estimate_ton_ha": pr.economics.estimated_yield_ton_ha,
            "yield_range_ton_ha": list(pr.economics.yield_range_ton_ha),
            "projected_profit_normal_idr": pr.economics.normal_profit_idr,
            "projected_profit_range_idr": [
                pr.economics.pessimistic_profit_idr,
                pr.economics.optimistic_profit_idr
            ],
            "prescriptions": {
                "sowing_window": pr.prescription.recommended_sowing_window,
                "irrigation_advice": pr.prescription.irrigation_advice,
                "fertilizer_prescription_kg_ha": pr.prescription.fertilizer_prescription_kg_ha,
                "soil_amendment_advice": pr.prescription.soil_amendment_advice,
                "identified_risks": pr.prescription.identified_risks
            },
            "supporting_factors": pr.supporting_factors,
            "inhibiting_factors": pr.inhibiting_factors,
            "narrative_explanation": pr.narrative_explanation
        }

    alternatives_data = []
    for alt in report.alternatives:
        alternatives_data.append({
            "rank": alt.rank,
            "crop_id": alt.crop_id,
            "crop_name": alt.crop_name,
            "composite_score": alt.composite_score,
            "suitability_score": alt.suitability.overall_score,
            "fao_class": alt.suitability.fao_class.value,
            "limiting_factor": alt.suitability.limiting_factor,
            "projected_profit_normal_idr": alt.economics.normal_profit_idr
        })

    all_evaluations_data = []
    for item in report.all_evaluations:
        all_evaluations_data.append({
            "rank": item.rank,
            "crop_id": item.crop_id,
            "crop_name": item.crop_name,
            "composite_score": item.composite_score,
            "suitability_score": item.suitability.overall_score,
            "fao_class": item.suitability.fao_class.value,
            "fao_label": item.suitability.fao_class.label_id,
            "limiting_factor": item.suitability.limiting_factor,
            "yield_estimate_ton_ha": item.economics.estimated_yield_ton_ha,
            "projected_profit_normal_idr": item.economics.normal_profit_idr
        })

    return {
        "site_id": report.site_id,
        "evaluated_at": report.generated_at.isoformat(),
        "data_completeness_ratio": report.data_completeness_ratio,
        "confidence_level": report.confidence_level.value,
        "recommendation_status": report.status.value,
        "model_version": report.model_version,
        "agronomic_indices": {
            "vpd_kpa": round(vpd, 2),
            "cumulative_gdd": round(gdd, 1),
            "reference_et0_mm": round(et0, 1),
            "water_balance_mm": round(water_balance, 1)
        },
        "primary_recommendation": primary_data,
        "alternatives": alternatives_data,
        "all_evaluations": all_evaluations_data,
        "system_notes": report.system_notes
    }


@router.post("/evaluate-site/{site_id}")
def evaluate_stored_site(
    site_id: str,
    pipeline: MedallionPipeline = Depends(get_medallion_pipeline),
    engine: StrategyEngine = Depends(get_strategy_engine)
) -> Dict[str, Any]:
    """Generates recommendation from historical telemetry stored in the Gold lake for a site."""
    try:
        vector, completeness = pipeline.generate_gold_features(site_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry data found for site: {site_id}"
        )

    report = engine.evaluate_land_parcel(vector, completeness)
    # Reuse formatting
    return evaluate_recommendation(
        payload=DirectEvaluationRequest(
            site_id=vector.site_id,
            mean_air_temp=vector.mean_air_temp,
            min_air_temp=vector.min_air_temp,
            max_air_temp=vector.max_air_temp,
            mean_rh=vector.mean_rh,
            mean_soil_vwc=vector.mean_soil_vwc,
            mean_soil_temp=vector.mean_soil_temp,
            mean_soil_ph=vector.mean_soil_ph,
            mean_soil_ec=vector.mean_soil_ec,
            total_rainfall=vector.total_rainfall,
            mean_solar_radiation=vector.mean_solar_radiation,
            mean_wind_speed=vector.mean_wind_speed,
            mean_soil_n=vector.mean_soil_n,
            mean_soil_p=vector.mean_soil_p,
            mean_soil_k=vector.mean_soil_k,
            observation_days=vector.observation_days
        ),
        engine=engine
    )


@router.get("/catalog")
def list_crop_catalog(
    catalog: List[CropParameterProfile] = Depends(get_crop_catalog)
) -> List[Dict[str, Any]]:
    """Returns the registered crops and agronomic parameter boundaries in the knowledge base."""
    return [
        {
            "crop_id": c.crop_id,
            "name": c.name,
            "scientific_name": c.scientific_name,
            "category": c.category,
            "optimal_temp_c": [c.temperature_c.min_opt, c.temperature_c.max_opt],
            "optimal_ph": [c.soil_ph.min_opt, c.soil_ph.max_opt],
            "optimal_moisture_vwc": [c.soil_moisture_vwc.min_opt, c.soil_moisture_vwc.max_opt],
            "max_tolerated_ec_ds_m": c.max_ec_ds_m,
            "maturity_gdd": c.maturity_gdd,
            "growth_duration_days": c.growth_duration_days,
            "yield_normal_ton_ha": c.yield_normal_ton_ha
        }
        for c in catalog
    ]
