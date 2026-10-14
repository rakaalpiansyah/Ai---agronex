from typing import Dict, List, Tuple, Optional
from src.domain.entities import (
    CropParameterProfile,
    AgronomicFeatureVector,
    CultivationPrescription
)


class AgronomicPrescriptionEngine:
    """Generates dynamic irrigation, fertilization, and risk mitigation prescriptions."""

    def generate_prescription(
        self,
        features: AgronomicFeatureVector,
        crop: CropParameterProfile,
        sowing_window: str
    ) -> CultivationPrescription:
        """Formulates field prescriptions grounded in soil nutrient deficits and water balance."""
        # 1. Irrigation Prescription
        vwc = features.mean_soil_vwc
        min_opt_vwc = crop.soil_moisture_vwc.min_opt
        water_deficit = max(0.0, min_opt_vwc - vwc)

        if water_deficit > 0:
            irrigation_vol = round(water_deficit * 0.8, 1)  # Approximate mm water depth per week
            irrigation_advice = (
                f"Lakukan irigasi suplemen sekitar {irrigation_vol} mm/minggu "
                f"untuk menaikkan kelembapan tanah ke ambang optimal {min_opt_vwc:.0f}%."
            )
        elif features.waterlogging_days > 0 or vwc > crop.soil_moisture_vwc.max_opt:
            irrigation_vol = 0.0
            irrigation_advice = (
                "Hentikan irigasi dan perbaiki parit drainase untuk menghindari pembusukan akar."
            )
        else:
            irrigation_vol = 0.0
            irrigation_advice = "Ketersediaan air tanah memadai. Lakukan monitoring kelembapan rutin."

        # 2. Fertilizer Prescription (deficits in kg/ha)
        n_deficit = max(0.0, crop.n_demand_kg_ha - features.mean_soil_n)
        p_deficit = max(0.0, crop.p_demand_kg_ha - features.mean_soil_p)
        k_deficit = max(0.0, crop.k_demand_kg_ha - features.mean_soil_k)

        fertilizer_kg_ha = {
            "urea_n": round(n_deficit * 2.17, 1),  # Urea contains ~46% N
            "sp36_p": round(p_deficit * 2.78, 1),  # SP-36 contains ~36% P2O5
            "kcl_k": round(k_deficit * 1.67, 1),   # KCl contains ~60% K2O
        }

        # 3. Soil Amendment (Liming)
        amendment_advice = None
        if features.mean_soil_ph < crop.soil_ph.min_opt:
            ph_deficit = crop.soil_ph.min_opt - features.mean_soil_ph
            lime_ton_ha = round(ph_deficit * 2.0, 1)  # Rule of thumb for agricultural dolomitic lime
            amendment_advice = (
                f"Tanah masam (pH {features.mean_soil_ph:.1f}). "
                f"Aplikasi kapur pertanian (Dolomit) sekitar {lime_ton_ha} ton/ha "
                f"minimal 2 minggu sebelum tanam."
            )

        # 4. Risk Identification
        risks: List[str] = []
        if features.moisture_stress_days > 0 or features.water_balance_mm < -50.0:
            risks.append("Risiko kekeringan: tercatat hari stres air tanah pada fase vegetatif.")
        if features.waterlogging_days > 0:
            risks.append("Risiko genangan air: potensi aerasi tanah terhambat dan busuk perakaran.")
        if features.heat_stress_days > 2:
            risks.append(f"Risiko stres panas: terdapat {features.heat_stress_days} hari dengan suhu di atas batas toleransi.")
        if features.mean_soil_ec > crop.max_ec_ds_m * 0.8:
            risks.append(f"Risiko salinitas tinggi: EC tanah mendekati batas toleransi tanaman ({crop.max_ec_ds_m} dS/m).")
        if features.mean_vpd_kpa > 1.8:
            risks.append("Defisit tekanan uap (VPD) tinggi: laju transpirasi berlebih memicu layu semu.")

        if not risks:
            risks.append("Profil risiko agroklimat terpantau rendah dan aman.")

        return CultivationPrescription(
            recommended_sowing_window=sowing_window,
            irrigation_advice=irrigation_advice,
            irrigation_volume_mm_week=irrigation_vol,
            fertilizer_prescription_kg_ha=fertilizer_kg_ha,
            soil_amendment_advice=amendment_advice,
            identified_risks=risks
        )
