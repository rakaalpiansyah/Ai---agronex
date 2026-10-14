from fastapi.testclient import TestClient
from datetime import datetime, timezone
from src.api.app import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_catalog_endpoint():
    response = client.get("/api/v1/recommendations/catalog")
    assert response.status_code == 200
    crops = response.json()
    assert len(crops) >= 6
    crop_ids = [c["crop_id"] for c in crops]
    assert "padi_sawah" in crop_ids
    assert "jagung_hibrida" in crop_ids


def test_telemetry_ingest_and_recommendation_flow():
    # 1. Ingest telemetry batch
    payload = {
        "batch_id": "BATCH-001",
        "records": [
            {
                "device_id": "DEV-INT-01",
                "site_id": "SITE-INTEGRATION-A01",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metrics": {
                    "air_temperature": 27.5,
                    "air_humidity": 76.0,
                    "soil_moisture_vwc": 48.0,
                    "soil_temperature": 26.0,
                    "soil_ph": 6.4,
                    "soil_ec": 0.9,
                    "rainfall": 5.0,
                    "solar_radiation": 500.0,
                    "wind_speed": 1.5,
                    "soil_n": 120.0,
                    "soil_p": 45.0,
                    "soil_k": 70.0
                },
                "firmware_version": "v2.0"
            }
        ]
    }
    ingest_res = client.post("/api/v1/telemetry/ingest", json=payload)
    assert ingest_res.status_code == 201
    assert ingest_res.json()["status"] == "success"

    # 2. Direct evaluation test
    eval_payload = {
        "site_id": "SITE-INTEGRATION-A01",
        "mean_air_temp": 27.5,
        "min_air_temp": 22.0,
        "max_air_temp": 32.0,
        "mean_rh": 76.0,
        "mean_soil_vwc": 48.0,
        "mean_soil_temp": 26.0,
        "mean_soil_ph": 6.4,
        "mean_soil_ec": 0.9,
        "total_rainfall": 400.0,
        "mean_solar_radiation": 500.0,
        "mean_wind_speed": 1.5,
        "mean_soil_n": 120.0,
        "mean_soil_p": 45.0,
        "mean_soil_k": 70.0,
        "observation_days": 30
    }
    eval_res = client.post("/api/v1/recommendations/evaluate", json=eval_payload)
    assert eval_res.status_code == 200
    result = eval_res.json()

    assert result["site_id"] == "SITE-INTEGRATION-A01"
    assert result["recommendation_status"] == "APPROVED"
    assert result["primary_recommendation"] is not None
    assert result["primary_recommendation"]["rank"] == 1
    assert "narrative_explanation" in result["primary_recommendation"]
    assert len(result["primary_recommendation"]["narrative_explanation"]) > 50
