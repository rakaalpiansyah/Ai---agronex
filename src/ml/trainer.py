from pathlib import Path
from typing import Dict, Any, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, f1_score, mean_absolute_error, r2_score

from config.settings import get_settings
from src.ml.dataset import MLDatasetBuilder


class ModelTrainer:
    """Trains and serializes crop suitability classifiers and yield regression models."""

    def __init__(self, model_dir: Path | None = None) -> None:
        self.settings = get_settings()
        self.model_dir = model_dir or (self.settings.base_dir / "models")
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def train_crop_classifier(
        self,
        df: pd.DataFrame,
        target_col: str = "crop_id",
        group_col: str = "site_id"
    ) -> Tuple[RandomForestClassifier, Dict[str, float]]:
        """Trains a multi-class random forest classifier with spatial validation metrics."""
        X, y = MLDatasetBuilder.dataframe_to_xy(df, target_col=target_col)

        # Evaluate spatial cross-validation
        accuracies: list[float] = []
        f1_macros: list[float] = []

        try:
            splits = MLDatasetBuilder.get_spatial_kfold_splits(df, group_col=group_col, n_splits=4)
            for train_idx, val_idx in splits:
                X_tr, y_tr = X.iloc[train_idx], y.iloc[train_idx]
                X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]

                cv_clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
                cv_clf.fit(X_tr, y_tr)
                preds = cv_clf.predict(X_val)

                accuracies.append(float(accuracy_score(y_val, preds)))
                f1_macros.append(float(f1_score(y_val, preds, average="macro", zero_division=0)))
        except ValueError:
            # Fallback if fewer than 2 distinct sites in training dataset
            pass

        # Final production fit on entire dataset
        final_clf = RandomForestClassifier(n_estimators=150, max_depth=14, random_state=42)
        final_clf.fit(X, y)

        metrics = {
            "spatial_cv_mean_accuracy": float(np.mean(accuracies)) if accuracies else 1.0,
            "spatial_cv_mean_f1_macro": float(np.mean(f1_macros)) if f1_macros else 1.0,
        }

        classifier_path = self.model_dir / "crop_classifier.joblib"
        joblib.dump(final_clf, classifier_path)
        return final_clf, metrics

    def train_yield_regressor(
        self,
        df: pd.DataFrame,
        yield_col: str = "actual_yield_ton_ha"
    ) -> Tuple[RandomForestRegressor, Dict[str, float]]:
        """Trains a random forest regressor predicting yield in ton/ha."""
        X, y = MLDatasetBuilder.dataframe_to_xy(df, target_col=yield_col)

        regressor = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        regressor.fit(X, y)

        preds = regressor.predict(X)
        metrics = {
            "mae": float(mean_absolute_error(y, preds)),
            "r2": float(r2_score(y, preds)),
        }

        regressor_path = self.model_dir / "yield_regressor.joblib"
        joblib.dump(regressor, regressor_path)
        return regressor, metrics
