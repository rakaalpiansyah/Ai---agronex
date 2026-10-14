from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class TelemetryItemPayload(BaseModel):
    """Payload schema for an individual sensor reading submission."""
    device_id: str = Field(..., min_length=2, max_length=64, description="Unique IoT device identifier")
    site_id: str = Field(..., min_length=2, max_length=64, description="Target land parcel identifier")
    timestamp: datetime = Field(..., description="Observation timestamp in UTC (ISO 8601)")
    metrics: Dict[str, float] = Field(..., description="Key-value mapping of metric name to physical value")
    firmware_version: str = Field("v1.0.0", max_length=32)

    @field_validator("timestamp")
    @classmethod
    def validate_not_future(cls, v: datetime) -> datetime:
        # Prevent erroneous clock forward-drift beyond 10 minutes tolerance
        now_utc = datetime.now(v.tzinfo) if v.tzinfo else datetime.now(timezone.utc)
        if (v - now_utc).total_seconds() > 600:
            raise ValueError("Observation timestamp cannot be in the future")
        return v


class TelemetryBatchPayload(BaseModel):
    """Batch payload schema for bulk ingestion from field gateways."""
    batch_id: Optional[str] = None
    records: List[TelemetryItemPayload] = Field(..., min_length=1)
