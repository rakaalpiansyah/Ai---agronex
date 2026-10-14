from fastapi import APIRouter, Depends
from datetime import datetime, timezone
from config.settings import Settings, get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def check_health(settings: Settings = Depends(get_settings)):
    """Liveness probe verifying service operational state and storage directory access."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "storage_initialized": settings.bronze_dir.exists() and settings.silver_dir.exists()
    }
