from pathlib import Path
from typing import List, Dict, Any, Tuple
import pandas as pd
from datetime import datetime, timezone

from config.settings import Settings, get_settings
from src.domain.enums import SoilType
from src.domain.entities import AgronomicFeatureVector
from src.ingestion.quality_checker import QualityChecker
from src.ingestion.calibrator import SensorCalibrator
from src.processing.imputer import TimeSeriesImputer
from src.processing.aggregator import TemporalAggregator


class MedallionPipeline:
    """Orchestrates Bronze, Silver, and Gold storage layer transformations."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.checker = QualityChecker()
        self.calibrator = SensorCalibrator()
        self.imputer = TimeSeriesImputer()
        self.aggregator = TemporalAggregator()

    def process_raw_batch(
        self,
        site_id: str,
        records: List[Dict[str, Any]],
        soil_type: SoilType = SoilType.LOAM
    ) -> Tuple[Path, Path]:
        """Ingests raw records into Bronze and transforms into clean Silver storage."""
        if not records:
            raise ValueError("No records provided for processing")

        # 1. Bronze ingestion (append-only)
        raw_df = pd.DataFrame(records)
        raw_df["timestamp"] = pd.to_datetime(raw_df["timestamp"], utc=True)
        raw_df["ingested_at"] = datetime.now(timezone.utc)
        bronze_file = self.settings.bronze_dir / f"{site_id}_raw.parquet"

        if bronze_file.exists():
            existing = pd.read_parquet(bronze_file)
            existing["timestamp"] = pd.to_datetime(existing["timestamp"], utc=True)
            raw_df = pd.concat([existing, raw_df], ignore_index=True)
            # Remove exact timestamp duplicates
            raw_df = raw_df.drop_duplicates(subset=["device_id", "timestamp"]).reset_index(drop=True)

        raw_df.to_parquet(bronze_file, index=False)

        # 2. Silver transformation (calibration & filtering)
        clean_rows = []
        for _, row in raw_df.iterrows():
            metrics = row.get("metrics", {})
            if not isinstance(metrics, dict):
                continue

            val_res = self.checker.validate_reading(metrics)
            if not val_res.is_valid:
                continue

            cleaned = dict(val_res.sanitized_metrics)
            temp_c = cleaned.get("soil_temperature", cleaned.get("air_temperature", 25.0))

            if "soil_ec" in cleaned:
                cleaned["soil_ec"] = self.calibrator.normalize_ec_to_25c(cleaned["soil_ec"], temp_c)
            if "soil_moisture_vwc" in cleaned:
                cleaned["soil_moisture_vwc"] = self.calibrator.calibrate_soil_moisture(
                    cleaned["soil_moisture_vwc"], soil_type
                )
            if "soil_ph" in cleaned:
                cleaned["soil_ph"] = self.calibrator.compensate_ph_temperature(cleaned["soil_ph"], temp_c)

            cleaned["timestamp"] = row["timestamp"]
            cleaned["device_id"] = row["device_id"]
            cleaned["site_id"] = site_id
            clean_rows.append(cleaned)

        silver_df = pd.DataFrame(clean_rows)
        if not silver_df.empty and "timestamp" in silver_df.columns:
            silver_df["timestamp"] = pd.to_datetime(silver_df["timestamp"], utc=True)
        silver_df = self.imputer.impute_short_gaps(silver_df, time_col="timestamp")
        silver_file = self.settings.silver_dir / f"{site_id}_clean.parquet"
        silver_df.to_parquet(silver_file, index=False)

        return bronze_file, silver_file

    def generate_gold_features(
        self,
        site_id: str
    ) -> Tuple[AgronomicFeatureVector, float]:
        """Reads Silver data, computes daily aggregates, and returns the Gold feature vector."""
        silver_file = self.settings.silver_dir / f"{site_id}_clean.parquet"
        if not silver_file.exists():
            raise FileNotFoundError(f"Clean silver dataset not found for site: {site_id}")

        silver_df = pd.read_parquet(silver_file)
        daily_df = self.aggregator.aggregate_daily(silver_df, time_col="timestamp")

        gold_file = self.settings.gold_dir / f"{site_id}_daily.parquet"
        daily_df.to_parquet(gold_file, index=False)

        return self.aggregator.build_feature_vector(daily_df, site_id)
