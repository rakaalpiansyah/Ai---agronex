import os
import json
from typing import Dict, Any, Optional
import urllib.request
import urllib.error

from src.domain.entities import CropRecommendation
from src.strategy.narrative import GroundedNarrativeGenerator


class LLMNarrativeEngine:
    """Transforms structured recommendation JSON into fluent agronomic narrative via LLM.

    Strictly complies with Section 7.3 of the technical guide:
    LLM only narrates pre-calculated facts, never invents numbers or unapproved agronomic advice.
    """

    SYSTEM_PROMPT = (
        "Anda adalah Konsultan Agronomi AI Senior profesional. Tugas Anda adalah mengubah data "
        "rekomendasi terstruktur (JSON) menjadi narasi penjelasan komprehensif, santun, dan mudah "
        "dipahami oleh petani atau manajer perkebunan di Indonesia.\n\n"
        "ATURAN MUTLAK:\n"
        "1. DILARANG MENGARANG ANGKA BARU. Gunakan HANYA angka skor kecocokan, estimasi yield, "
        "dan proyeksi laba yang ada di data input.\n"
        "2. DILARANG MENGUBAH NAMA TANAMAN UTAMA atau REKOMENDASI PUPUK/IRIGASI yang sudah dihitung.\n"
        "3. Sertakan batas keyakinan (tinggi/sedang/rendah) dan peringatan risiko yang tercatat.\n"
        "4. Gunakan bahasa Indonesia yang lugas, profesional, dan solutif."
    )

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash") -> None:
        self.api_key = api_key or os.getenv("LLM_API_KEY", os.getenv("GEMINI_API_KEY", ""))
        self.model = model
        self.fallback_generator = GroundedNarrativeGenerator()

    def generate_narrative(
        self,
        site_id: str,
        rec: CropRecommendation,
        confidence_level: str = "HIGH"
    ) -> str:
        """Generates narrative using LLM if configured; otherwise uses deterministic grounded template."""
        if not self.api_key:
            # Deterministic zero-hallucination fallback
            return self.fallback_generator.generate_recommendation_narrative(site_id, rec)

        payload_context = {
            "site_id": site_id,
            "crop_name": rec.crop_name,
            "suitability_score": rec.suitability.overall_score,
            "fao_class": f"{rec.suitability.fao_class.value} ({rec.suitability.fao_class.label_id})",
            "limiting_factor": rec.suitability.limiting_factor,
            "supporting_factors": rec.supporting_factors,
            "inhibiting_factors": rec.inhibiting_factors,
            "yield_estimate_ton_ha": rec.economics.estimated_yield_ton_ha,
            "yield_range_ton_ha": list(rec.economics.yield_range_ton_ha),
            "normal_profit_idr": rec.economics.normal_profit_idr,
            "pessimistic_profit_idr": rec.economics.pessimistic_profit_idr,
            "optimistic_profit_idr": rec.economics.optimistic_profit_idr,
            "sowing_window": rec.prescription.recommended_sowing_window,
            "irrigation_advice": rec.prescription.irrigation_advice,
            "fertilizer_prescription_kg_ha": rec.prescription.fertilizer_prescription_kg_ha,
            "soil_amendment_advice": rec.prescription.soil_amendment_advice,
            "identified_risks": rec.prescription.identified_risks,
            "confidence_level": confidence_level
        }

        user_content = (
            f"Berikut adalah data hasil analisis lahan pertanian:\n"
            f"```json\n{json.dumps(payload_context, ensure_ascii=False, indent=2)}\n```\n\n"
            f"Tolong susun laporan narasi agronomi resmi untuk petani berdasarkan data di atas."
        )

        try:
            return self._call_gemini_api(user_content)
        except Exception:
            # If network or API fails, cleanly fallback to deterministic narrative
            return self.fallback_generator.generate_recommendation_narrative(site_id, rec)

    def _call_gemini_api(self, prompt: str) -> str:
        """Invokes Google Gemini REST API without external client library dependencies."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        body = {
            "system_instruction": {"parts": [{"text": self.SYSTEM_PROMPT}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}  # Low temperature for factual precision
        }

        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            candidates = result.get("candidates", [])
            if candidates:
                text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                if text:
                    return text.strip()

        raise RuntimeError("Empty response received from LLM API")
