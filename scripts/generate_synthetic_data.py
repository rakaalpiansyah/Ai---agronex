import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

from config.settings import get_settings
from src.domain.enums import SoilType
from src.processing.pipeline import MedallionPipeline
from src.agronomy.indices import AgronomicIndicesCalculator


def generate_synthetic_iot_data() -> None:
    """Generates realistic 30-day IoT telemetry streams for distinct agricultural land parcels."""
    settings = get_settings()
    pipeline = MedallionPipeline(settings)

    print("Generating realistic synthetic IoT telemetry...")

    site_profiles = [
        {
            "site_id": "SITE-LOWLAND-PADI-01",
            "soil_type": SoilType.CLAY,
            "target_crop": "padi_sawah",
            "base_temp": 28.0,
            "base_vwc": 70.0,
            "base_ph": 6.2,
            "base_ec": 1.1,
            "base_n": 130.0,
            "base_p": 48.0,
            "base_k": 70.0,
            "base_rain_prob": 0.35
        },
        {
            "site_id": "SITE-UPLAND-CORN-02",
            "soil_type": SoilType.LOAM,
            "target_crop": "jagung_hibrida",
            "base_temp": 27.0,
            "base_vwc": 48.0,
            "base_ph": 6.5,
            "base_ec": 0.8,
            "base_n": 140.0,
            "base_p": 55.0,
            "base_k": 75.0,
            "base_rain_prob": 0.20
        },
        {
            "site_id": "SITE-HIGHLAND-HORTI-03",
            "soil_type": SoilType.SANDY_LOAM,
            "target_crop": "cabai_merah",
            "base_temp": 22.0,
            "base_vwc": 52.0,
            "base_ph": 6.1,
            "base_ec": 1.2,
            "base_n": 170.0,
            "base_p": 110.0,
            "base_k": 145.0,
            "base_rain_prob": 0.25
        }
    ]

    start_time = datetime.utcnow() - timedelta(days=30)
    harvest_records = []

    for profile in site_profiles:
        site_id = profile["site_id"]
        records = []
        current_time = start_time

        # Generate hourly readings over 30 days (720 observations)
        for hour_idx in range(720):
            current_time = start_time + timedelta(hours=hour_idx)
            hour_of_day = current_time.hour

            # Diurnal temperature and humidity cycle
            temp_variation = 4.0 * np.sin((hour_of_day - 9) * np.pi / 12)
            t_air = float(profile["base_temp"] + temp_variation + random.gauss(0, 0.5))
            rh_air = float(min(98.0, max(45.0, 85.0 - (temp_variation * 3.5) + random.gauss(0, 2.0))))

            # Solar radiation peaks around 12:00 PM
            if 6 <= hour_of_day <= 18:
                sol_rad = float(max(0.0, 800.0 * np.sin((hour_of_day - 6) * np.pi / 12) + random.gauss(0, 30)))
            else:
                sol_rad = 0.0

            # Rainfall simulation
            is_raining = random.random() < profile["base_rain_prob"] and (13 <= hour_of_day <= 17)
            rainfall = float(round(random.uniform(2.0, 25.0), 1) if is_raining else 0.0)

            # Soil metrics
            soil_vwc = float(min(95.0, max(15.0, profile["base_vwc"] + (rainfall * 0.4) + random.gauss(0, 0.8))))
            soil_temp = float(t_air - 1.5 + random.gauss(0, 0.2))
            soil_ph = float(profile["base_ph"] + random.gauss(0, 0.05))
            soil_ec = float(profile["base_ec"] + random.gauss(0, 0.02))
            wind_speed = float(max(0.2, 1.8 + random.gauss(0, 0.5)))

            payload_metrics = {
                "air_temperature": round(t_air, 1),
                "air_humidity": round(rh_air, 1),
                "solar_radiation": round(sol_rad, 1),
                "rainfall": round(rainfall, 1),
                "soil_moisture_vwc": round(soil_vwc, 1),
                "soil_temperature": round(soil_temp, 1),
                "soil_ph": round(soil_ph, 2),
                "soil_ec": round(soil_ec, 2),
                "wind_speed": round(wind_speed, 1),
                "soil_n": round(profile["base_n"] + random.gauss(0, 2.0), 1),
                "soil_p": round(profile["base_p"] + random.gauss(0, 1.0), 1),
                "soil_k": round(profile["base_k"] + random.gauss(0, 2.0), 1)
            }

            records.append({
                "device_id": f"DEV-{site_id[-7:]}",
                "site_id": site_id,
                "timestamp": current_time.isoformat(),
                "metrics": payload_metrics
            })

        # Save to Medallion Bronze and Silver
        pipeline.process_raw_batch(site_id, records, soil_type=profile["soil_type"])
        print(f"Ingested {len(records)} records for {site_id}")

    # Generate multi-site historical dataset for training
    print("Generating historical labeled harvest dataset...")
    crops = [
        "padi_sawah", "jagung_hibrida", "kedelai", "kacang_tanah",
        "cabai_merah", "tomat", "sawi_hijau", "bawang_merah",
        "singkong", "kentang", "cabai_rawit", "kacang_hijau",
        "terung", "kangkung", "kubis", "wortel", "semangka"
    ]
    labeled_rows = []

    for i in range(450):
        c_choice = random.choice(crops)
        site_num = (i % 25) + 1
        s_id = f"SITE-HIST-{site_num:02d}"

        # Assign agro parameters suitable for chosen crop
        if c_choice == "padi_sawah":
            temp = random.uniform(25.0, 31.0)
            vwc = random.uniform(55.0, 85.0)
            ph = random.uniform(5.8, 6.8)
            rain = random.uniform(800.0, 1600.0)
            actual_yield = random.uniform(5.5, 7.8)
        elif c_choice == "jagung_hibrida":
            temp = random.uniform(24.0, 30.0)
            vwc = random.uniform(38.0, 65.0)
            ph = random.uniform(5.8, 7.2)
            rain = random.uniform(500.0, 1100.0)
            actual_yield = random.uniform(6.0, 9.2)
        elif c_choice in ["kedelai", "kacang_tanah", "kacang_hijau"]:
            temp = random.uniform(23.0, 30.0)
            vwc = random.uniform(28.0, 52.0)
            ph = random.uniform(6.0, 7.0)
            rain = random.uniform(350.0, 750.0)
            actual_yield = random.uniform(1.4, 2.5)
        elif c_choice == "sawi_hijau":
            temp = random.uniform(18.0, 26.0)
            vwc = random.uniform(50.0, 75.0)
            ph = random.uniform(6.0, 6.8)
            rain = random.uniform(400.0, 900.0)
            actual_yield = random.uniform(14.0, 22.0)
        elif c_choice == "kangkung":
            temp = random.uniform(25.0, 33.0)
            vwc = random.uniform(50.0, 78.0)
            ph = random.uniform(6.0, 7.0)
            rain = random.uniform(300.0, 800.0)
            actual_yield = random.uniform(12.0, 20.0)
        elif c_choice == "bawang_merah":
            temp = random.uniform(25.0, 32.0)
            vwc = random.uniform(35.0, 55.0)
            ph = random.uniform(6.0, 6.8)
            rain = random.uniform(300.0, 650.0)
            actual_yield = random.uniform(8.0, 14.0)
        elif c_choice == "singkong":
            temp = random.uniform(23.0, 32.0)
            vwc = random.uniform(25.0, 50.0)
            ph = random.uniform(5.2, 6.8)
            rain = random.uniform(500.0, 1400.0)
            actual_yield = random.uniform(18.0, 35.0)
        elif c_choice in ["kentang", "kubis", "wortel"]:
            temp = random.uniform(14.0, 20.5)
            vwc = random.uniform(45.0, 68.0)
            ph = random.uniform(5.6, 6.6)
            rain = random.uniform(450.0, 850.0)
            actual_yield = random.uniform(18.0, 32.0)
        elif c_choice == "semangka":
            temp = random.uniform(24.0, 32.0)
            vwc = random.uniform(30.0, 52.0)
            ph = random.uniform(5.8, 6.8)
            rain = random.uniform(350.0, 700.0)
            actual_yield = random.uniform(20.0, 38.0)
        elif c_choice in ["cabai_rawit", "cabai_merah"]:
            temp = random.uniform(21.0, 29.0)
            vwc = random.uniform(38.0, 62.0)
            ph = random.uniform(6.0, 6.8)
            rain = random.uniform(500.0, 1100.0)
            actual_yield = random.uniform(8.0, 16.0)
        else:  # Tomat & Terung
            temp = random.uniform(20.0, 28.0)
            vwc = random.uniform(42.0, 68.0)
            ph = random.uniform(6.0, 6.8)
            rain = random.uniform(500.0, 1000.0)
            actual_yield = random.uniform(18.0, 30.0)

        rh = random.uniform(70.0, 88.0)
        vpd = AgronomicIndicesCalculator.calculate_vapor_pressure_deficit(temp, rh)
        et0 = AgronomicIndicesCalculator.calculate_fao56_penman_monteith_et0(temp, rh, 420.0, 1.5) * 30

        labeled_rows.append({
            "site_id": s_id,
            "season_year": random.choice([2024, 2025, 2026]),
            "crop_id": c_choice,
            "mean_air_temp": round(temp, 1),
            "min_air_temp": round(temp - 4.5, 1),
            "max_air_temp": round(temp + 4.5, 1),
            "mean_rh": round(rh, 1),
            "mean_soil_vwc": round(vwc, 1),
            "mean_soil_temp": round(temp - 1.0, 1),
            "mean_soil_ph": round(ph, 2),
            "mean_soil_ec": round(random.uniform(0.6, 1.6), 2),
            "total_rainfall": round(rain, 1),
            "mean_solar_radiation": round(random.uniform(350.0, 550.0), 1),
            "mean_wind_speed": round(random.uniform(1.0, 2.8), 1),
            "mean_soil_n": round(random.uniform(80.0, 180.0), 1),
            "mean_soil_p": round(random.uniform(30.0, 90.0), 1),
            "mean_soil_k": round(random.uniform(80.0, 160.0), 1),
            "mean_vpd_kpa": vpd,
            "cumulative_gdd": round((temp - 10.0) * 30, 1),
            "reference_et0_mm": round(et0, 1),
            "water_balance_mm": round(rain - et0, 1),
            "moisture_stress_days": 1 if vwc < 25.0 else 0,
            "waterlogging_days": 1 if vwc > 85.0 else 0,
            "heat_stress_days": 1 if temp > 34.0 else 0,
            "actual_yield_ton_ha": round(actual_yield, 2)
        })

    hist_df = pd.DataFrame(labeled_rows)
    hist_path = settings.data_dir / "historical_crop_harvests.parquet"
    hist_df.to_parquet(hist_path, index=False)
    print(f"Saved {len(hist_df)} historical training records to {hist_path}")


if __name__ == "__main__":
    generate_synthetic_iot_data()
