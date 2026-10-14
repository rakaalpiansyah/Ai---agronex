from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from src.ingestion.schemas import TelemetryBatchPayload, TelemetryItemPayload
from src.processing.pipeline import MedallionPipeline
from src.domain.enums import SoilType
from src.api.dependencies import get_medallion_pipeline

router = APIRouter(prefix="/telemetry", tags=["Telemetry Ingestion"])


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
def ingest_telemetry_batch(
    payload: TelemetryBatchPayload,
    soil_type: SoilType = SoilType.LOAM,
    pipeline: MedallionPipeline = Depends(get_medallion_pipeline)
) -> Dict[str, Any]:
    """Ingests sensor batch into Bronze immutable store and executes Silver calibration."""
    if not payload.records:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payload must contain at least one telemetry record"
        )

    site_id = payload.records[0].site_id
    raw_dicts = [record.model_dump() for record in payload.records]

    try:
        bronze_file, silver_file = pipeline.process_raw_batch(
            site_id=site_id,
            records=raw_dicts,
            soil_type=soil_type
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process telemetry pipeline: {str(exc)}"
        )

    return {
        "status": "success",
        "site_id": site_id,
        "processed_records": len(payload.records),
        "bronze_path": str(bronze_file),
        "silver_path": str(silver_file),
    }
