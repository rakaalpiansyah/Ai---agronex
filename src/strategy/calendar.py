from datetime import date, timedelta
from typing import Dict, Any
from src.domain.entities import CropParameterProfile, AgronomicFeatureVector


class PlantingCalendarPlanner:
    """Plans sowing windows by reconciling heat accumulation and moisture conditions."""

    def determine_sowing_window(
        self,
        features: AgronomicFeatureVector,
        crop: CropParameterProfile
    ) -> str:
        """Determines the optimal 2-week planting window."""
        today = date.today()

        # If soil moisture is currently sufficient (> 35%) and no waterlogging
        if features.mean_soil_vwc >= 35.0 and features.waterlogging_days == 0:
            start_date = today + timedelta(days=7)
            end_date = start_date + timedelta(days=14)
            return (
                f"Minggu ke-{((start_date.day - 1) // 7) + 1} "
                f"{start_date.strftime('%B %Y')} (Target: {start_date.strftime('%d %b')} s.d. {end_date.strftime('%d %b')})"
            )

        # If currently dry, suggest waiting for rainfall onset
        if features.mean_soil_vwc < 30.0:
            suggested = today + timedelta(days=21)
            return (
                f"Tunda tanam hingga kelembapan tanah > 35%. "
                f"Prakiraan jendela berikutnya: akhir {suggested.strftime('%B %Y')}"
            )

        # If saturated/waterlogged, suggest waiting for field drainage
        suggested = today + timedelta(days=14)
        return f"Tunggu pengeringan lahan/drainase. Estimasi jadwal tanam: {suggested.strftime('%d %B %Y')}"
