from typing import List
from src.domain.entities import (
    CropRecommendation,
    EconomicProjection,
    CultivationPrescription,
    CropSuitabilityScore
)


class GroundedNarrativeGenerator:
    """Generates deterministic, hallucination-free Indonesian agronomic narratives."""

    def generate_recommendation_narrative(
        self,
        site_id: str,
        rec: CropRecommendation
    ) -> str:
        """Synthesizes structured recommendation data into a cohesive professional explanation."""
        suit = rec.suitability
        econ = rec.economics
        presc = rec.prescription

        # Format currency in millions of Rupiah
        pess_mio = round(econ.pessimistic_profit_idr / 1_000_000, 1)
        norm_mio = round(econ.normal_profit_idr / 1_000_000, 1)
        opt_mio = round(econ.optimistic_profit_idr / 1_000_000, 1)

        # Synthesize supporting and inhibiting reasons
        supporting_text = ", ".join(rec.supporting_factors) if rec.supporting_factors else "Kondisi agroklimat berada pada rentang yang dapat diterima."
        inhibiting_text = ", ".join(rec.inhibiting_factors) if rec.inhibiting_factors else "Tidak terdeteksi faktor pembatas lingkungan yang kritis."

        amendment_line = f" {presc.soil_amendment_advice}" if presc.soil_amendment_advice else ""

        narrative = (
            f"Rekomendasi Utama untuk Lahan {site_id}: {rec.crop_name}, "
            f"skor kecocokan {suit.overall_score:.2f} ({suit.fao_class.value} - {suit.fao_class.label_id}).\n\n"
            f"Alasan Agronomi: {supporting_text}. "
            f"Faktor pembatas utama adalah {suit.limiting_factor} ({inhibiting_text}).\n\n"
            f"Estimasi Hasil & Ekonomi: Potensi hasil panen {econ.yield_range_ton_ha[0]:.1f} s.d. {econ.yield_range_ton_ha[1]:.1f} ton/ha "
            f"(rata-rata {econ.estimated_yield_ton_ha:.1f} ton/ha). "
            f"Proyeksi laba bersih: Rp {norm_mio} juta/ha pada kondisi normal "
            f"(rentang skenario Rp {pess_mio} s.d. Rp {opt_mio} juta/ha).\n\n"
            f"Strategi Budidaya: Jadwal tanam disarankan pada {presc.recommended_sowing_window}. "
            f"{presc.irrigation_advice}{amendment_line} "
            f"Kebutuhan pupuk dasar/susulan: Urea ~{presc.fertilizer_prescription_kg_ha.get('urea_n', 0)} kg/ha, "
            f"SP-36 ~{presc.fertilizer_prescription_kg_ha.get('sp36_p', 0)} kg/ha, "
            f"KCl ~{presc.fertilizer_prescription_kg_ha.get('kcl_k', 0)} kg/ha."
        )

        return narrative
