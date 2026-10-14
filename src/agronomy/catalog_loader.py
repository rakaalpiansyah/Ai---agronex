import json
from pathlib import Path
from typing import List, Dict, Any

from config.settings import get_settings
from src.domain.entities import CropParameterProfile, TrapezoidLimits


class CatalogLoader:
    """Loads and deserializes FAO EcoCrop and economic parameters from JSON catalogs."""

    @staticmethod
    def load_crop_catalog(path: Path | None = None) -> List[CropParameterProfile]:
        """Loads and converts crop profiles into strongly typed domain entities."""
        catalog_path = path or get_settings().crop_catalog_path
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        profiles: List[CropParameterProfile] = []
        for item in data.get("crops", []):
            profile = CropParameterProfile(
                crop_id=item["crop_id"],
                name=item["name"],
                scientific_name=item["scientific_name"],
                category=item["category"],
                temperature_c=TrapezoidLimits(**item["temperature_c"]),
                soil_ph=TrapezoidLimits(**item["soil_ph"]),
                soil_moisture_vwc=TrapezoidLimits(**item["soil_moisture_vwc"]),
                seasonal_rainfall_mm=TrapezoidLimits(**item["seasonal_rainfall_mm"]),
                max_ec_ds_m=float(item["max_ec_ds_m"]),
                t_base_c=float(item["gdd"]["t_base"]),
                maturity_gdd=float(item["gdd"]["maturity_gdd"]),
                kc_initial=float(item["kc"]["initial"]),
                kc_mid=float(item["kc"]["mid"]),
                kc_late=float(item["kc"]["late"]),
                n_demand_kg_ha=float(item["nutrient_demand_kg_ha"]["n"]),
                p_demand_kg_ha=float(item["nutrient_demand_kg_ha"]["p"]),
                k_demand_kg_ha=float(item["nutrient_demand_kg_ha"]["k"]),
                yield_pessimistic_ton_ha=float(item["yield_potential_ton_ha"]["pessimistic"]),
                yield_normal_ton_ha=float(item["yield_potential_ton_ha"]["normal"]),
                yield_optimistic_ton_ha=float(item["yield_potential_ton_ha"]["optimistic"]),
                growth_duration_days=int(item["growth_duration_days"])
            )
            profiles.append(profile)

        return profiles

    @staticmethod
    def load_economic_catalog(path: Path | None = None) -> Dict[str, Any]:
        """Loads economic cost and commodity market projections."""
        catalog_path = path or get_settings().economic_catalog_path
        with open(catalog_path, "r", encoding="utf-8") as f:
            return json.load(f)
