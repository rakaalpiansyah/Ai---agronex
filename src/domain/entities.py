from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional
from src.domain.enums import FAOClass, RiskLevel, ConfidenceLevel, RecommendationStatus, SoilType


@dataclass(frozen=True)
class TelemetryRecord:
    device_id: str
    site_id: str
    timestamp: datetime
    metric: str
    value: float
    unit: str
    firmware_version: str = "v1.0.0"


@dataclass(frozen=True)
class LandProfile:
    site_id: str
    name: str
    latitude: float
    longitude: float
    elevation_m: float
    area_hectares: float
    soil_type: SoilType = SoilType.LOAM


@dataclass
class AgronomicFeatureVector:
    site_id: str
    period_start: date
    period_end: date
    observation_days: int
    mean_air_temp: float
    min_air_temp: float
    max_air_temp: float
    mean_rh: float
    mean_soil_vwc: float
    mean_soil_temp: float
    mean_soil_ph: float
    mean_soil_ec: float
    total_rainfall: float
    mean_solar_radiation: float
    mean_wind_speed: float
    mean_soil_n: float
    mean_soil_p: float
    mean_soil_k: float

    # Derived indices
    mean_vpd_kpa: float = 0.0
    cumulative_gdd: float = 0.0
    reference_et0_mm: float = 0.0
    water_balance_mm: float = 0.0
    moisture_stress_days: int = 0
    waterlogging_days: int = 0
    heat_stress_days: int = 0


@dataclass(frozen=True)
class TrapezoidLimits:
    min_abs: float
    min_opt: float
    max_opt: float
    max_abs: float


@dataclass(frozen=True)
class CropParameterProfile:
    crop_id: str
    name: str
    scientific_name: str
    category: str
    temperature_c: TrapezoidLimits
    soil_ph: TrapezoidLimits
    soil_moisture_vwc: TrapezoidLimits
    seasonal_rainfall_mm: TrapezoidLimits
    max_ec_ds_m: float
    t_base_c: float
    maturity_gdd: float
    kc_initial: float
    kc_mid: float
    kc_late: float
    n_demand_kg_ha: float
    p_demand_kg_ha: float
    k_demand_kg_ha: float
    yield_pessimistic_ton_ha: float
    yield_normal_ton_ha: float
    yield_optimistic_ton_ha: float
    growth_duration_days: int


@dataclass
class CropSuitabilityScore:
    crop_id: str
    crop_name: str
    overall_score: float
    liebig_score: float
    geometric_score: float
    fao_class: FAOClass
    factor_scores: Dict[str, float]
    limiting_factor: str


@dataclass
class EconomicProjection:
    estimated_yield_ton_ha: float
    yield_range_ton_ha: tuple[float, float]
    pessimistic_profit_idr: float
    normal_profit_idr: float
    optimistic_profit_idr: float
    production_cost_idr: float


@dataclass
class CultivationPrescription:
    recommended_sowing_window: str
    irrigation_advice: str
    irrigation_volume_mm_week: float
    fertilizer_prescription_kg_ha: Dict[str, float]
    soil_amendment_advice: Optional[str]
    identified_risks: List[str]


@dataclass
class CropRecommendation:
    rank: int
    crop_id: str
    crop_name: str
    composite_score: float
    suitability: CropSuitabilityScore
    economics: EconomicProjection
    prescription: CultivationPrescription
    narrative_explanation: str
    supporting_factors: List[str]
    inhibiting_factors: List[str]


@dataclass
class RecommendationReport:
    site_id: str
    generated_at: datetime
    data_completeness_ratio: float
    confidence_level: ConfidenceLevel
    status: RecommendationStatus
    model_version: str
    primary_recommendation: Optional[CropRecommendation]
    alternatives: List[CropRecommendation] = field(default_factory=list)
    all_evaluations: List[CropRecommendation] = field(default_factory=list)
    system_notes: List[str] = field(default_factory=list)
