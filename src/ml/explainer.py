from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier

from src.domain.entities import AgronomicFeatureVector, CropParameterProfile
from src.ml.dataset import MLDatasetBuilder


class AgronomicExplainer:
    """Computes SHAP feature attributions and generates evidence-based explanations."""

    # Human-readable agronomic names and units
    METRIC_LABELS: Dict[str, str] = {
        "mean_air_temp": "Suhu udara rata-rata (C)",
        "mean_soil_ph": "pH tanah",
        "mean_soil_vwc": "Kelembapan tanah VWC (%)",
        "mean_soil_ec": "Salinitas tanah EC (dS/m)",
        "total_rainfall": "Akumulasi curah hujan (mm)",
        "mean_soil_n": "Ketersediaan Nitrogen (N)",
        "mean_soil_p": "Ketersediaan Fosfor (P)",
        "mean_soil_k": "Ketersediaan Kalium (K)",
        "mean_vpd_kpa": "Defisit Tekanan Uap VPD (kPa)",
        "moisture_stress_days": "Hari stres kekeringan",
        "heat_stress_days": "Hari stres suhu panas",
        "waterlogging_days": "Hari genangan air",
    }

    def __init__(self, classifier: RandomForestClassifier | None = None) -> None:
        self.classifier = classifier
        self.explainer: shap.TreeExplainer | None = None
        if classifier is not None:
            self.explainer = shap.TreeExplainer(classifier)

    def explain_prediction(
        self,
        features: AgronomicFeatureVector,
        target_crop_idx: int = 0,
        top_k: int = 3
    ) -> Tuple[List[str], List[str]]:
        """Extracts top supporting and inhibiting environmental factors."""
        feat_dict = MLDatasetBuilder.vector_to_feature_dict(features)
        X_sample = pd.DataFrame([feat_dict])

        supporting: List[str] = []
        inhibiting: List[str] = []

        if self.explainer is not None:
            try:
                shap_values = self.explainer.shap_values(X_sample)
                crop_shap = None
                if isinstance(shap_values, list) and target_crop_idx < len(shap_values):
                    crop_shap = shap_values[target_crop_idx][0]
                elif hasattr(shap_values, "shape") and len(shap_values.shape) == 3 and target_crop_idx < shap_values.shape[2]:
                    crop_shap = shap_values[0, :, target_crop_idx]
                elif hasattr(shap_values, "shape") and len(shap_values.shape) == 2:
                    crop_shap = shap_values[0]

                if crop_shap is not None:
                    feature_names = list(feat_dict.keys())
                    sorted_indices = np.argsort(crop_shap)

                    # Factors with most negative attribution (inhibiting)
                    for idx in sorted_indices[:top_k]:
                        val = crop_shap[idx]
                        if val < -0.01:
                            fname = feature_names[idx]
                            label = self.METRIC_LABELS.get(fname, fname)
                            actual_val = round(feat_dict[fname], 1)
                            inhibiting.append(f"{label} ({actual_val}) menekan kecocokan")

                    # Factors with most positive attribution (supporting)
                    for idx in sorted_indices[::-1][:top_k]:
                        val = crop_shap[idx]
                        if val > 0.01:
                            fname = feature_names[idx]
                            label = self.METRIC_LABELS.get(fname, fname)
                            actual_val = round(feat_dict[fname], 1)
                            supporting.append(f"{label} ({actual_val}) mendukung pertumbuhan optimal")
            except Exception:
                pass

        # Heuristic agronomic fallback if SHAP tree values are inconclusive
        if not supporting:
            if 20.0 <= features.mean_air_temp <= 32.0:
                supporting.append(f"Suhu udara rata-rata {features.mean_air_temp:.1f} C dalam batas optimal")
            if 5.5 <= features.mean_soil_ph <= 7.0:
                supporting.append(f"Tingkat keasaman tanah pH {features.mean_soil_ph:.1f} netral dan optimal")
            if features.moisture_stress_days == 0:
                supporting.append("Ketersediaan air tanah stabil tanpa hari stres kekeringan")

        if not inhibiting:
            if features.mean_soil_p < 40.0:
                inhibiting.append(f"Kadar fosfor tanah rendah ({features.mean_soil_p:.1f} mg/kg)")
            if features.mean_soil_ec > 1.8:
                inhibiting.append(f"Salinitas tanah tergolong tinggi ({features.mean_soil_ec:.2f} dS/m)")
            if features.heat_stress_days > 2:
                inhibiting.append(f"Terjadi {features.heat_stress_days} hari stres suhu panas ekstrem")

        return supporting, inhibiting
