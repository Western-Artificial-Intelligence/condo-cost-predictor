"""
XGBoost_scaffold.py
Author: <Guojia La>
Toronto Condo Affordability Predictor
--------------------------------------------
Train quantile regression models (τ = 0.1, 0.5, 0.9)
to predict condo price ranges.
"""

import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import joblib

# === Configuration ===
RANDOM_SEED = 42
TEST_SIZE = 0.2
TARGET_COL = "price_median"  # observed median price or log-price
QUANTILES = [0.1, 0.5, 0.9]

# === 1. Load & Preprocess ===
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df

def preprocess(df: pd.DataFrame):
    features = [
        "lat", "lon", "distance_to_ttc",
        "median_income", "population_density",
        "housing_starts_3m_lag", "price_index_yoy",
        "unemployment_rate"
    ]
    X = df[features].fillna(df[features].median())
    y = df[TARGET_COL]
    return X, y

# === 2. Define Quantile Loss ===
def quantile_loss(q, y, y_pred):
    """Pinball loss for quantile q."""
    e = y - y_pred
    return np.where(e >= 0, q * e, (q - 1) * e)

def xgb_quantile_objective(q):
    """Custom objective function for XGBoost."""
    def _quantile_obj(y_true, y_pred):
        grad = np.where(y_true - y_pred > 0, -q, 1 - q)
        hess = np.ones_like(grad)
        return grad, hess
    return _quantile_obj

# === 3. Train per quantile ===
def train_quantile_models(X_train, y_train):
    models = {}
    for q in QUANTILES:
        print(f"\nTraining quantile model for τ = {q}")
        model = XGBRegressor(
            n_estimators=600,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=RANDOM_SEED,
            tree_method="hist",
        )
        model.fit(
            X_train,
            y_train,
            obj=xgb_quantile_objective(q),
            eval_metric=lambda y_true, y_pred: (
                "quantile", np.mean(quantile_loss(q, y_true, y_pred))
            ),
            verbose=True
        )
        models[q] = model
    return models

# === 4. Evaluate ===
def evaluate(models, X_test, y_test):
    preds = {q: model.predict(X_test) for q, model in models.items()}
    mae_median = mean_absolute_error(y_test, preds[0.5])
    print(f"\nMedian (τ=0.5) MAE: ${mae_median:,.0f}")
    print("Sample predictions:")
    sample = pd.DataFrame({
        "true": y_test.values[:5],
        "p10": preds[0.1][:5],
        "p50": preds[0.5][:5],
        "p90": preds[0.9][:5],
    })
    print(sample)
    return preds

# === 5. Save Models ===
def save_models(models, prefix="models/xgb_quantile_"):
    for q, model in models.items():
        path = f"{prefix}{q}.pkl"
        joblib.dump(model, path)
        print(f"Saved τ={q} model to {path}")

# === 6. Main Script ===
if __name__ == "__main__":
    df = load_data("Insert Path to data here")
    X, y = preprocess(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED
    )
    models = train_quantile_models(X_train, y_train)
    preds = evaluate(models, X_test, y_test)
    save_models(models)
