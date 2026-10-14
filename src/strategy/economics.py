from typing import Dict, Any
from src.domain.entities import CropParameterProfile, EconomicProjection


class EconomicCalculator:
    """Calculates scenario-based crop profitability (pessimistic, normal, optimistic)."""

    def __init__(self, economic_catalog: Dict[str, Any]) -> None:
        self.commodities = economic_catalog.get("commodities", {})

    def calculate_projection(
        self,
        crop: CropParameterProfile,
        predicted_yield_ton_ha: float
    ) -> EconomicProjection:
        """Projects profitability per hectare based on commodity market pricing."""
        econ = self.commodities.get(crop.crop_id, {})
        prices = econ.get("price_per_ton", {
            "pessimistic": 5000000.0,
            "normal": 6000000.0,
            "optimistic": 7000000.0
        })
        cost = econ.get("production_cost_per_ha", 15000000.0)

        # Scale yield scenarios based on predicted yield
        scale = max(0.5, predicted_yield_ton_ha / max(0.1, crop.yield_normal_ton_ha))
        y_pess = round(crop.yield_pessimistic_ton_ha * scale, 2)
        y_norm = round(predicted_yield_ton_ha, 2)
        y_opt = round(crop.yield_optimistic_ton_ha * scale, 2)

        profit_pess = round((y_pess * prices["pessimistic"]) - cost, 0)
        profit_norm = round((y_norm * prices["normal"]) - cost, 0)
        profit_opt = round((y_opt * prices["optimistic"]) - cost, 0)

        return EconomicProjection(
            estimated_yield_ton_ha=y_norm,
            yield_range_ton_ha=(y_pess, y_opt),
            pessimistic_profit_idr=profit_pess,
            normal_profit_idr=profit_norm,
            optimistic_profit_idr=profit_opt,
            production_cost_idr=cost
        )
