from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import joblib
import pandas as pd
import numpy as np

from config.settings import get_settings
from src.domain.entities import (
    AgronomicFeatureVector,
    CropParameterProfile,
    CropSuitabilityScore
)
from src.agronomy.csi_calculator import CropSuitabilityCalculator
from src.ml.dataset import MLDatasetBuilder
from src.ml.explainer import AgronomicExplainer


class CropPredictor:
    """Combines rule-based agronomy baseline with trained ML inference."""

    def __init__(
        self,
        crop_catalog: List[CropParameterProfile],
        model_dir: Path | None = None
    ) -> None:
        self.settings = get_settings()
        self.crop_catalog = crop_catalog
        self.calculator = CropSuitabilityCalculator()
        self.model_dir = model_dir or (self.settings.base_dir / "models")

        self.classifier = None
        self.regressor = None
        self._load_models_if_available()
        self.explainer = AgronomicExplainer(self.classifier)

    def _load_models_if_available(self) -> None:
        clf_path = self.model_dir / "crop_classifier.joblib"
        if clf_path.exists():
            try:
                self.classifier = joblib.load(clf_path)
            except Exception:
                self.classifier = None

        reg_path = self.model_dir / "yield_regressor.joblib"
        if reg_path.exists():
            try:
                self.regressor = joblib.load(reg_path)
            except Exception:
                self.regressor = None

    def evaluate_candidates(
        self,
        features: AgronomicFeatureVector
    ) -> List[Tuple[CropParameterProfile, CropSuitabilityScore, float, float, List[str], List[str]]]:
        """Evaluates every crop in the catalog and returns suitability, proba, and yield.

        Returns tuples of (crop, csi_score, ml_confidence, predicted_yield, supporting, inhibiting).
        """
        results = []
        feat_dict = MLDatasetBuilder.vector_to_feature_dict(features)
        df_sample = pd.DataFrame([feat_dict])

        # Get ML probabilities if classifier is available
        ml_probas: Dict[str, float] = {}
        if self.classifier is not None and hasattr(self.classifier, "classes_"):
            try:
                probas = self.classifier.predict_proba(df_sample)[0]
                for cls_name, prob in zip(self.classifier.classes_, probas):
                    ml_probas[cls_name] = float(prob)
            except Exception:
                pass

        for idx, crop in enumerate(self.crop_catalog):
            csi = self.calculator.calculate_crop_csi(features, crop)
            confidence = ml_probas.get(crop.crop_id, csi.overall_score)

            # Predict yield: use ML regressor if available, else scale by CSI score
            predicted_yield = crop.yield_normal_ton_ha
            if self.regressor is not None:
                try:
                    df_crop = df_sample.copy()
                    predicted_yield = float(self.regressor.predict(df_crop)[0])
                except Exception:
                    predicted_yield = crop.yield_normal_ton_ha * max(0.4, csi.overall_score)
            else:
                predicted_yield = crop.yield_normal_ton_ha * max(0.4, csi.overall_score)

            supporting, inhibiting = self.explainer.explain_prediction(
                features, target_crop_idx=idx
            )

            results.append((crop, csi, round(confidence, 3), round(predicted_yield, 2), supporting, inhibiting))

        return results
