"""Ablation study: train the full pipeline with and without CLASSIFICATION_CODE.

Reuses the same search configs, CV strategies, and bootstrap procedure from
train_tier_classifier.py but runs two experiments:
  1. All 21 features (baseline — matches the main pipeline)
  2. 20 features (CLASSIFICATION_CODE dropped)

Prints a side-by-side comparison table at the end.
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    TimeSeriesSplit,
)
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed_data"
MODEL_DIR = PROJECT_ROOT / "models"

RANDOM_SEED = 42
TARGET = "TARGET_TIER_2YR"
TIER_LABELS = {1: "Budget", 2: "Moderate", 3: "Expensive", 4: "Premium"}

NUMERIC_FEATURES = [
    "area_sq_meters", "perimeter_meters", "park_count",
    "ASSAULT_RATE", "AUTOTHEFT_RATE", "ROBBERY_RATE", "THEFTOVER_RATE",
    "POPULATION", "total_stop_count", "avg_stop_frequency",
    "max_stop_frequency", "total_line_length_meters",
    "transit_line_density", "distinct_route_count",
]

ENGINEERED_FEATURES = [
    "park_density", "pop_density", "transit_per_capita",
    "total_crime_rate", "compactness", "routes_per_stop",
]

SEARCH_CONFIGS = {
    "RandomForest": {
        "estimator": RandomForestClassifier(random_state=RANDOM_SEED),
        "param_distributions": {
            "n_estimators": [200, 300, 500, 700],
            "max_depth": [6, 8, 10, 12, 15, None],
            "min_samples_leaf": [3, 5, 8, 12],
            "min_samples_split": [2, 5, 10],
            "max_features": ["sqrt", "log2", 0.5, 0.7],
            "class_weight": ["balanced", "balanced_subsample"],
        },
    },
    "XGBoost": {
        "estimator": XGBClassifier(
            objective="multi:softprob", num_class=4,
            eval_metric="mlogloss", tree_method="hist",
            verbosity=0, random_state=RANDOM_SEED,
        ),
        "param_distributions": {
            "max_depth": [3, 4, 5, 6, 8],
            "n_estimators": [200, 300, 500, 700],
            "learning_rate": [0.01, 0.03, 0.05, 0.1],
            "subsample": [0.7, 0.8, 0.9, 1.0],
            "colsample_bytree": [0.6, 0.7, 0.8, 0.9],
            "min_child_weight": [1, 3, 5, 7],
            "reg_alpha": [0.0, 0.01, 0.1, 0.5],
            "reg_lambda": [0.5, 1.0, 2.0, 5.0],
        },
    },
    "GradientBoosting": {
        "estimator": GradientBoostingClassifier(random_state=RANDOM_SEED),
        "param_distributions": {
            "n_estimators": [200, 300, 500, 700],
            "max_depth": [3, 4, 5, 6, 8],
            "learning_rate": [0.01, 0.03, 0.05, 0.1],
            "min_samples_leaf": [3, 5, 8, 12],
            "subsample": [0.7, 0.8, 0.9, 1.0],
        },
    },
}

N_ITER = 10


def engineer_features(df):
    df = df.copy()
    df["park_density"] = df["park_count"] / df["area_sq_meters"].clip(lower=1e-10)
    df["pop_density"] = df["POPULATION"] / df["area_sq_meters"].clip(lower=1e-10)
    df["transit_per_capita"] = df["total_stop_count"] / df["POPULATION"].clip(lower=1)
    df["total_crime_rate"] = df[
        ["ASSAULT_RATE", "AUTOTHEFT_RATE", "ROBBERY_RATE", "THEFTOVER_RATE"]
    ].sum(axis=1)
    df["compactness"] = (df["perimeter_meters"] ** 2) / df["area_sq_meters"].clip(lower=1e-10)
    df["routes_per_stop"] = df["distinct_route_count"] / df["total_stop_count"].clip(lower=1)
    return df


def run_experiment(X_train, y_train, X_test, y_test, train_df, label):
    """Run the full search + bootstrap for one feature set configuration."""
    ts = lambda: datetime.now().strftime("%H:%M:%S")

    y_train_0 = y_train - 1
    y_test_0 = y_test - 1

    sort_idx = train_df.sort_values("YEAR").index
    X_sorted = X_train.loc[sort_idx].reset_index(drop=True)
    y_sorted = y_train_0.loc[sort_idx].reset_index(drop=True)

    cv_strat = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    cv_time = TimeSeriesSplit(n_splits=5)

    best_score = -1.0
    best_model = None
    best_meta = {}

    print(f"\n{'='*60}", flush=True)
    print(f"  EXPERIMENT: {label} ({X_train.shape[1]} features)", flush=True)
    print(f"{'='*60}", flush=True)

    for cv_name, cv_obj in [("StratifiedKFold", cv_strat), ("TimeSeriesSplit", cv_time)]:
        X_cv = X_sorted if cv_name == "TimeSeriesSplit" else X_train
        y_cv = y_sorted if cv_name == "TimeSeriesSplit" else y_train_0

        for model_name, config in SEARCH_CONFIGS.items():
            print(f"  [{ts()}] {cv_name} / {model_name}...", end=" ", flush=True)
            search = RandomizedSearchCV(
                estimator=config["estimator"],
                param_distributions=config["param_distributions"],
                n_iter=N_ITER, cv=cv_obj, scoring="f1_macro",
                random_state=RANDOM_SEED, n_jobs=1, verbose=0,
                return_train_score=False, error_score="raise",
            )
            search.fit(X_cv, y_cv)
            print(f"best CV F1={search.best_score_:.4f}", flush=True)

            if search.best_score_ > best_score:
                best_score = search.best_score_
                best_model = search.best_estimator_
                best_meta = {
                    "model": model_name, "cv": cv_name,
                    "cv_f1": search.best_score_,
                    "cv_std": float(search.cv_results_["std_test_score"][search.best_index_]),
                }

    # Evaluate on test
    y_pred = best_model.predict(X_test)
    acc = accuracy_score(y_test_0, y_pred)
    macro_f1 = f1_score(y_test_0, y_pred, average="macro")
    per_class = f1_score(y_test_0, y_pred, labels=[0, 1, 2, 3], average=None)

    # Bootstrap
    rng = np.random.RandomState(RANDOM_SEED)
    n = len(y_test_0)
    boot_f1s = np.empty(2000)
    boot_accs = np.empty(2000)
    for b in range(2000):
        idx = rng.choice(n, size=n, replace=True)
        bp = best_model.predict(X_test.iloc[idx])
        boot_accs[b] = accuracy_score(y_test_0.iloc[idx], bp)
        boot_f1s[b] = f1_score(y_test_0.iloc[idx], bp, average="macro", zero_division=0)

    result = {
        "label": label,
        "n_features": X_train.shape[1],
        "best_model": best_meta["model"],
        "best_cv": best_meta["cv"],
        "cv_f1": best_meta["cv_f1"],
        "cv_std": best_meta["cv_std"],
        "test_acc": acc,
        "test_f1": macro_f1,
        "test_f1_ci": (float(np.percentile(boot_f1s, 2.5)), float(np.percentile(boot_f1s, 97.5))),
        "test_acc_ci": (float(np.percentile(boot_accs, 2.5)), float(np.percentile(boot_accs, 97.5))),
        "per_class_f1": {TIER_LABELS[i+1]: float(per_class[i]) for i in range(4)},
    }

    print(f"\n  Best: {result['best_model']} ({result['best_cv']})")
    print(f"  CV F1:   {result['cv_f1']:.4f} +/- {result['cv_std']:.4f}")
    print(f"  Test F1: {result['test_f1']:.4f} (95% CI: [{result['test_f1_ci'][0]:.4f}, {result['test_f1_ci'][1]:.4f}])")
    print(f"  Test Acc: {result['test_acc']:.4f} (95% CI: [{result['test_acc_ci'][0]:.4f}, {result['test_acc_ci'][1]:.4f}])")
    for tier, f1 in result["per_class_f1"].items():
        print(f"    {tier}: F1={f1:.3f}")

    return result


def main():
    train_df = pd.read_csv(DATA_DIR / "train_v2.csv")
    test_df = pd.read_csv(DATA_DIR / "test_v2.csv")
    train_df = engineer_features(train_df)
    test_df = engineer_features(test_df)

    le = LabelEncoder()
    all_codes = pd.concat([train_df["CLASSIFICATION_CODE"], test_df["CLASSIFICATION_CODE"]]).fillna("UNKNOWN")
    le.fit(all_codes)
    train_df["CLASSIFICATION_CODE"] = le.transform(train_df["CLASSIFICATION_CODE"].fillna("UNKNOWN"))
    test_df["CLASSIFICATION_CODE"] = le.transform(test_df["CLASSIFICATION_CODE"].fillna("UNKNOWN"))

    y_train = train_df[TARGET]
    y_test = test_df[TARGET]

    # --- Experiment 1: All 21 features (with CLASSIFICATION_CODE) ---
    feat_with = NUMERIC_FEATURES + ENGINEERED_FEATURES + ["CLASSIFICATION_CODE"]
    r_with = run_experiment(
        train_df[feat_with], y_train, test_df[feat_with], y_test,
        train_df, "With CLASSIFICATION_CODE"
    )

    # --- Experiment 2: 20 features (without CLASSIFICATION_CODE) ---
    feat_without = NUMERIC_FEATURES + ENGINEERED_FEATURES
    r_without = run_experiment(
        train_df[feat_without], y_train, test_df[feat_without], y_test,
        train_df, "Without CLASSIFICATION_CODE"
    )

    # --- Comparison ---
    print(f"\n\n{'='*70}")
    print("ABLATION STUDY: CLASSIFICATION_CODE")
    print(f"{'='*70}")
    print(f"  {'':>35s}  {'With CC':>12s}  {'Without CC':>12s}  {'Delta':>8s}")
    print(f"  {'-'*70}")
    print(f"  {'Features':>35s}  {r_with['n_features']:>12d}  {r_without['n_features']:>12d}  {'':>8s}")
    print(f"  {'Best model':>35s}  {r_with['best_model']:>12s}  {r_without['best_model']:>12s}  {'':>8s}")
    print(f"  {'CV F1':>35s}  {r_with['cv_f1']:>12.4f}  {r_without['cv_f1']:>12.4f}  {r_without['cv_f1']-r_with['cv_f1']:>+8.4f}")
    print(f"  {'Test Accuracy':>35s}  {r_with['test_acc']:>11.1%}  {r_without['test_acc']:>11.1%}  {(r_without['test_acc']-r_with['test_acc'])*100:>+7.1f}pp")
    print(f"  {'Test Macro F1':>35s}  {r_with['test_f1']:>12.4f}  {r_without['test_f1']:>12.4f}  {r_without['test_f1']-r_with['test_f1']:>+8.4f}")
    print(f"  {'Test F1 95% CI':>35s}  [{r_with['test_f1_ci'][0]:.3f},{r_with['test_f1_ci'][1]:.3f}]  [{r_without['test_f1_ci'][0]:.3f},{r_without['test_f1_ci'][1]:.3f}]")
    print(f"\n  Per-class F1:")
    for tier in TIER_LABELS.values():
        w = r_with["per_class_f1"][tier]
        wo = r_without["per_class_f1"][tier]
        print(f"    {tier:>12s}  {w:>12.3f}  {wo:>12.3f}  {wo-w:>+8.3f}")

    # Save results
    ablation = {"with_classification_code": r_with, "without_classification_code": r_without}
    out_path = MODEL_DIR / "ablation_classification_code.json"
    with open(out_path, "w") as f:
        json.dump(ablation, f, indent=2, default=str)
    print(f"\n  Results saved to {out_path}")


if __name__ == "__main__":
    main()
