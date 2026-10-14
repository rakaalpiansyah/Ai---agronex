from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application and engine configuration settings."""

    app_name: str = "IoT Crop Recommendation Engine"
    app_version: str = "1.0.0"
    debug: bool = False

    base_dir: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = base_dir / "data"
    bronze_dir: Path = base_dir / "data" / "lake" / "bronze"
    silver_dir: Path = base_dir / "data" / "lake" / "silver"
    gold_dir: Path = base_dir / "data" / "lake" / "gold"

    crop_catalog_path: Path = base_dir / "config" / "crop_catalog.json"
    economic_catalog_path: Path = base_dir / "config" / "economic_catalog.json"

    # Ingestion quality thresholds
    min_data_completeness_ratio: float = 0.70
    stuck_sensor_window_size: int = 12
    stuck_sensor_max_std: float = 1e-4

    # Multi-criteria strategy scoring weights
    weight_suitability: float = 0.50
    weight_profit: float = 0.30
    weight_risk: float = 0.20
    confidence_gate_threshold: float = 0.65

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def ensure_directories(self) -> None:
        """Create storage directories if they do not exist."""
        for path in (self.bronze_dir, self.silver_dir, self.gold_dir):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
