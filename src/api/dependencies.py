from functools import lru_cache
from typing import List, Dict, Any

from config.settings import Settings, get_settings
from src.domain.entities import CropParameterProfile
from src.agronomy.catalog_loader import CatalogLoader
from src.processing.pipeline import MedallionPipeline
from src.strategy.engine import StrategyEngine


@lru_cache
def get_crop_catalog() -> List[CropParameterProfile]:
    return CatalogLoader.load_crop_catalog()


@lru_cache
def get_economic_catalog() -> Dict[str, Any]:
    return CatalogLoader.load_economic_catalog()


@lru_cache
def get_medallion_pipeline() -> MedallionPipeline:
    return MedallionPipeline(get_settings())


@lru_cache
def get_strategy_engine() -> StrategyEngine:
    return StrategyEngine(
        crop_catalog=get_crop_catalog(),
        economic_catalog=get_economic_catalog(),
        settings=get_settings()
    )
