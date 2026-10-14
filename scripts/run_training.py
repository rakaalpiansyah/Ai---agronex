from pathlib import Path
import pandas as pd
from config.settings import get_settings
from src.ml.trainer import ModelTrainer


def train_models() -> None:
    """Trains production crop suitability classifier and yield regressor."""
    settings = get_settings()
    data_path = settings.data_dir / "historical_crop_harvests.parquet"

    if not data_path.exists():
        print(f"Dataset not found at {data_path}. Running generator first...")
        from scripts.generate_synthetic_data import generate_synthetic_iot_data
        generate_synthetic_iot_data()

    print(f"Loading training data from {data_path}...")
    df = pd.read_parquet(data_path)
    print(f"Dataset shape: {df.shape}, Unique sites: {df['site_id'].nunique()}, Classes: {df['crop_id'].unique()}")

    trainer = ModelTrainer()

    # 1. Train Crop Classifier
    print("\n--- Training Random Forest Crop Classifier with Spatial CV ---")
    clf, clf_metrics = trainer.train_crop_classifier(df, target_col="crop_id", group_col="site_id")
    print(f"Spatial CV Mean Accuracy: {clf_metrics['spatial_cv_mean_accuracy']:.3f}")
    print(f"Spatial CV Mean F1-Macro: {clf_metrics['spatial_cv_mean_f1_macro']:.3f}")

    # 2. Train Yield Regressor
    print("\n--- Training Yield Regressor ---")
    reg, reg_metrics = trainer.train_yield_regressor(df, yield_col="actual_yield_ton_ha")
    print(f"Yield MAE: {reg_metrics['mae']:.3f} ton/ha")
    print(f"Yield R2 Score: {reg_metrics['r2']:.3f}")

    print("\nModels successfully saved to 'models/' directory.")


if __name__ == "__main__":
    train_models()
