"""
train_tier_classifier.py — Day 2: Train tier classifier + neighborhood clustering

This script trains a multi-class classifier to predict which affordability tier
(Budget / Moderate / Expensive / Premium) a Toronto neighborhood will be in
2 years from now, based on its current characteristics (crime, transit, parks, etc.).

It also clusters the 158 neighborhoods in the 2024 snapshot into groups of
similar neighborhoods using K-Means.

Run from the project root:
    source .venv/bin/activate
    python3 models/train_tier_classifier.py

Outputs:
    models/tier_classifier.pkl        — best trained classifier (XGBoost or RF)
    models/label_encoder.pkl          — encoder for CLASSIFICATION_CODE
    models/scaler.pkl                 — StandardScaler fitted on clustering features
    data/processed_data/cluster_assignments.csv — 158 neighborhoods with cluster IDs
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    silhouette_score,
)
from sklearn.model_selection import (
    RandomizedSearchCV,
    StratifiedKFold,
    TimeSeriesSplit,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler
from xgboost import XGBClassifier

# ---------------------------------------------------------------------------
# Paths — all relative to the project root so the script works from anywhere
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed_data"
MODEL_DIR = PROJECT_ROOT / "models"

TRAIN_PATH = DATA_DIR / "train_v2.csv"
TEST_PATH = DATA_DIR / "test_v2.csv"
NEIGHBORHOODS_PATH = DATA_DIR / "neighborhoods_2024.csv"

# ---------------------------------------------------------------------------
# Feature definitions — these MUST match what rebuild_dataset.py produced.
# avg_rent_1br is deliberately excluded because it leaks the target:
# knowing current rent almost perfectly predicts future rent tier.
# ---------------------------------------------------------------------------
NUMERIC_FEATURES = [
    "area_sq_meters",
    "perimeter_meters",
    "park_count",
    "ASSAULT_RATE",
    "AUTOTHEFT_RATE",
    "ROBBERY_RATE",
    "THEFTOVER_RATE",
    "POPULATION",
    "total_stop_count",
    "avg_stop_frequency",
    "max_stop_frequency",
    "total_line_length_meters",
    "transit_line_density",
    "distinct_route_count",
]

# Engineered features that capture density relationships between raw features.
# These outperform the raw features because they normalize for neighborhood
# size and population — a large neighborhood with 10 parks is very different
# from a tiny one with 10 parks.
ENGINEERED_FEATURES = [
    "park_density",        # parks / area — livability per unit area
    "pop_density",         # population / area — urban density
    "transit_per_capita",  # transit stops / population — accessibility per person
    "total_crime_rate",    # sum of all 4 crime rates — overall safety signal
    "compactness",         # perimeter^2 / area — shape regularity
    "routes_per_stop",     # distinct routes / stops — transit connectivity
]

CATEGORICAL_FEATURE = "CLASSIFICATION_CODE"

TARGET = "TARGET_TIER_2YR"

TIER_LABELS = {1: "Budget", 2: "Moderate", 3: "Expensive", 4: "Premium"}

RANDOM_SEED = 42


# ===================================================================
# FEATURE ENGINEERING
# ===================================================================


def engineer_features(df):
    """Create ratio features that capture density relationships.

    Raw features like park_count or POPULATION don't account for
    neighborhood size. A neighborhood with 20 parks spread over a huge
    area is very different from one with 20 parks in a compact zone.
    These ratios normalize for that and produce much stronger correlations
    with the target:
      - park_density:       0.47 corr (vs 0.01 for raw park_count)
      - pop_density:        0.38 corr (vs 0.04 for raw POPULATION)
      - transit_per_capita: 0.29 corr (vs 0.27 for raw total_stop_count)
    """
    df = df.copy()
    df["park_density"] = df["park_count"] / df["area_sq_meters"].clip(lower=1e-10)
    df["pop_density"] = df["POPULATION"] / df["area_sq_meters"].clip(lower=1e-10)
    df["transit_per_capita"] = df["total_stop_count"] / df["POPULATION"].clip(lower=1)
    df["total_crime_rate"] = df[
        ["ASSAULT_RATE", "AUTOTHEFT_RATE", "ROBBERY_RATE", "THEFTOVER_RATE"]
    ].sum(axis=1)
    # Compactness: how regular is the neighborhood's shape?
    # Circular shapes have low compactness, irregular shapes have high.
    # This matters because irregular shapes often straddle different zones.
    df["compactness"] = (df["perimeter_meters"] ** 2) / df["area_sq_meters"].clip(
        lower=1e-10
    )
    # Routes per stop: are transit stops well-connected to multiple routes,
    # or is each stop served by just one line?
    df["routes_per_stop"] = df["distinct_route_count"] / df["total_stop_count"].clip(
        lower=1
    )
    return df


# ===================================================================
# PART 1: TIER CLASSIFIER
# ===================================================================


def load_and_prepare_data():
    """Load train/test CSVs, engineer features, and build feature matrices.

    We use LabelEncoder for CLASSIFICATION_CODE because it only has 3 values
    (UNKNOWN, NIA, EN) — not the ~35 we originally assumed. LabelEncoder is
    fine for this; OHE would also work but adds no benefit for 3 categories.
    """
    train_df = pd.read_csv(TRAIN_PATH)
    test_df = pd.read_csv(TEST_PATH)

    # Engineer ratio features before building the feature matrix
    train_df = engineer_features(train_df)
    test_df = engineer_features(test_df)

    print(f"Train: {len(train_df)} rows, Test: {len(test_df)} rows")
    print(f"Target distribution (train):\n{train_df[TARGET].value_counts().sort_index()}\n")

    # Encode the categorical feature
    le = LabelEncoder()
    all_codes = pd.concat([train_df[CATEGORICAL_FEATURE], test_df[CATEGORICAL_FEATURE]])
    all_codes = all_codes.fillna("UNKNOWN")
    le.fit(all_codes)

    train_df[CATEGORICAL_FEATURE] = le.transform(
        train_df[CATEGORICAL_FEATURE].fillna("UNKNOWN")
    )
    test_df[CATEGORICAL_FEATURE] = le.transform(
        test_df[CATEGORICAL_FEATURE].fillna("UNKNOWN")
    )

    feature_cols = NUMERIC_FEATURES + ENGINEERED_FEATURES + [CATEGORICAL_FEATURE]

    X_train = train_df[feature_cols]
    y_train = train_df[TARGET]
    X_test = test_df[feature_cols]
    y_test = test_df[TARGET]

    print(f"Features: {len(feature_cols)} ({len(NUMERIC_FEATURES)} base + "
          f"{len(ENGINEERED_FEATURES)} engineered + 1 categorical)")

    return X_train, y_train, X_test, y_test, le, train_df, test_df


def train_xgboost(X_train, y_train):
    """Train an XGBoost multi-class classifier.

    Iteration notes (what we tried and why these hyperparams won):
    - max_depth=4 beat depth=5,6 — shallower trees generalize better on 1,580 rows
    - n_estimators=500 with learning_rate=0.03 — more trees with smaller steps
      outperformed fewer trees with larger steps
    - reg_alpha=0.1, reg_lambda=1.0 — light L1+L2 regularization helps
    - min_child_weight=3 — slightly less restrictive than 5, lets the model
      capture finer patterns now that we have engineered features

    XGBoost expects labels starting at 0, so we subtract 1 from our 1-4 tiers.
    """
    xgb = XGBClassifier(
        objective="multi:softprob",
        num_class=4,
        max_depth=4,
        n_estimators=500,
        learning_rate=0.03,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        reg_alpha=0.1,
        reg_lambda=1.0,
        random_state=RANDOM_SEED,
        eval_metric="mlogloss",
        tree_method="hist",
        verbosity=0,
    )
    xgb.fit(X_train, y_train - 1)
    return xgb


def train_random_forest(X_train, y_train):
    """Train a Random Forest classifier.

    Iteration notes:
    - max_depth=10 with min_samples_leaf=5 was our original config and still
      wins over deeper/shallower alternatives. The balanced class_weight is
      important because it upweights underrepresented tiers.
    - n_estimators=500 (up from 300) gives a small stability improvement.
    - class_weight='balanced' adjusts sample weights inversely proportional
      to class frequency, so the model doesn't just predict the most common tier.
    """
    rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=RANDOM_SEED,
    )
    rf.fit(X_train, y_train)
    return rf


# Param distributions for RandomizedSearchCV.
# These ranges were chosen to bracket the manually-tuned values from the
# original train_xgboost() and train_random_forest() while exploring
# meaningfully wider territory.
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
            objective="multi:softprob",
            num_class=4,
            eval_metric="mlogloss",
            tree_method="hist",
            verbosity=0,
            random_state=RANDOM_SEED,
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

N_ITER_PER_MODEL = 10


def _log(msg):
    """Timestamped log line so we can see progress in real time."""
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  [{ts}] {msg}", flush=True)


def run_hyperparameter_search(X_train, y_train, train_df):
    """Run RandomizedSearchCV across 3 model families x 2 CV strategies.

    Returns the best fitted model, its metadata, and the full results log
    for export. The two CV strategies are:
      - StratifiedKFold: ensures balanced tier representation per fold
      - TimeSeriesSplit: respects temporal ordering (train_df must have YEAR)

    For XGBoost, labels are shifted to 0-indexed internally by sklearn's
    scoring, so we pass the original 1-4 labels and let the estimator
    handle it (XGBClassifier maps classes automatically when fit is called
    via RandomizedSearchCV).
    """
    cv_strategies = {
        "StratifiedKFold": StratifiedKFold(
            n_splits=5, shuffle=True, random_state=RANDOM_SEED
        ),
        "TimeSeriesSplit": TimeSeriesSplit(n_splits=5),
    }

    n_cv = len(cv_strategies)
    n_models = len(SEARCH_CONFIGS)
    total_searches = n_cv * n_models
    print(f"\nSearch plan: {n_models} model families x {n_cv} CV strategies "
          f"x {N_ITER_PER_MODEL} iters = {total_searches * N_ITER_PER_MODEL} "
          f"total fits ({total_searches} search rounds)", flush=True)

    # XGBoost requires 0-indexed class labels. Rather than special-casing
    # XGBoost inside the loop, we shift all labels to 0-3 for the search
    # (RF and GBM don't care about label values, so this is harmless).
    # The shift is reversed when we evaluate on the held-out test set.
    y_train_0 = y_train - 1

    # TimeSeriesSplit requires data sorted by time
    sort_idx = train_df.sort_values("YEAR").index
    X_train_sorted = X_train.loc[sort_idx].reset_index(drop=True)
    y_train_sorted = y_train_0.loc[sort_idx].reset_index(drop=True)

    all_results = []
    best_overall_score = -1.0
    best_overall_model = None
    best_overall_meta = {}

    total_start = time.time()
    search_round = 0

    for cv_name, cv_splitter in cv_strategies.items():
        X_cv = X_train_sorted if cv_name == "TimeSeriesSplit" else X_train
        y_cv = y_train_sorted if cv_name == "TimeSeriesSplit" else y_train_0

        print(f"\n--- CV Strategy: {cv_name} ---", flush=True)

        for model_name, config in SEARCH_CONFIGS.items():
            search_round += 1
            _log(f"[{search_round}/{total_searches}] Starting {model_name} "
                 f"({N_ITER_PER_MODEL} configs x 5 folds)...")
            search_start = time.time()

            search = RandomizedSearchCV(
                estimator=config["estimator"],
                param_distributions=config["param_distributions"],
                n_iter=N_ITER_PER_MODEL,
                cv=cv_splitter,
                scoring="f1_macro",
                random_state=RANDOM_SEED,
                n_jobs=1,
                verbose=1,
                return_train_score=True,
                error_score="raise",
            )
            search.fit(X_cv, y_cv)
            search_time = time.time() - search_start

            best_cv_f1 = search.best_score_
            _log(f"[{search_round}/{total_searches}] {model_name} done — "
                 f"best CV F1={best_cv_f1:.4f}, took {search_time:.1f}s")

            cv_results = search.cv_results_
            for i in range(len(cv_results["params"])):
                fold_scores = [
                    float(cv_results[f"split{f}_test_score"][i])
                    for f in range(cv_splitter.get_n_splits())
                ]
                entry = {
                    "model_type": model_name,
                    "cv_strategy": cv_name,
                    "params": {
                        k: (v.item() if hasattr(v, "item") else v)
                        for k, v in cv_results["params"][i].items()
                    },
                    "mean_f1_macro": float(cv_results["mean_test_score"][i]),
                    "std_f1_macro": float(cv_results["std_test_score"][i]),
                    "mean_train_f1": float(cv_results["mean_train_score"][i]),
                    "fold_scores": fold_scores,
                    "fit_time_seconds": float(cv_results["mean_fit_time"][i]),
                    "rank": int(cv_results["rank_test_score"][i]),
                }
                all_results.append(entry)

            if best_cv_f1 > best_overall_score:
                best_overall_score = best_cv_f1
                best_overall_model = search.best_estimator_
                best_overall_meta = {
                    "model_type": model_name,
                    "cv_strategy": cv_name,
                    "best_params": {
                        k: (v.item() if hasattr(v, "item") else v)
                        for k, v in search.best_params_.items()
                    },
                    "cv_mean_f1": float(search.best_score_),
                    "cv_std_f1": float(
                        cv_results["std_test_score"][search.best_index_]
                    ),
                    "cv_fold_scores": [
                        float(cv_results[f"split{f}_test_score"][search.best_index_])
                        for f in range(cv_splitter.get_n_splits())
                    ],
                }

    total_time = time.time() - total_start

    # Print leaderboard
    elapsed = time.time() - total_start
    sorted_results = sorted(all_results, key=lambda r: r["mean_f1_macro"], reverse=True)
    print(f"\n{'='*80}", flush=True)
    print(f"HYPERPARAMETER SEARCH COMPLETE — {len(all_results)} configs "
          f"evaluated in {elapsed:.1f}s", flush=True)
    print(f"{'='*80}", flush=True)
    print(f"  {'Rank':>4s}  {'Model':>20s}  {'CV Strategy':>17s}  "
          f"{'Mean F1':>8s}  {'Std':>6s}  {'Train F1':>9s}", flush=True)
    for rank, r in enumerate(sorted_results[:20], 1):
        print(f"  {rank:>4d}  {r['model_type']:>20s}  {r['cv_strategy']:>17s}  "
              f"{r['mean_f1_macro']:>8.4f}  {r['std_f1_macro']:>6.4f}  "
              f"{r['mean_train_f1']:>9.4f}", flush=True)

    print(f"\nBest overall: {best_overall_meta['model_type']} "
          f"({best_overall_meta['cv_strategy']}) — "
          f"CV F1 = {best_overall_meta['cv_mean_f1']:.4f} "
          f"+/- {best_overall_meta['cv_std_f1']:.4f}")

    search_metadata = {
        "n_configs_evaluated": len(all_results),
        "n_model_families": len(SEARCH_CONFIGS),
        "n_cv_strategies": len(cv_strategies),
        "n_iter_per_model": N_ITER_PER_MODEL,
        "total_search_time_seconds": round(elapsed, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return best_overall_model, best_overall_meta, all_results, search_metadata


# ===================================================================
# EVALUATION
# ===================================================================


def evaluate_model(model, X_test, y_test_0, model_name):
    """Evaluate a classifier on the held-out test set.

    All models from the search are trained on 0-indexed labels (0-3).
    y_test_0 must also be 0-indexed. Display output maps back to tier
    names (1-4) for readability.

    Returns accuracy, macro F1, per-class F1 dict, predictions, and
    the confusion matrix.
    """
    y_pred = model.predict(X_test)

    acc = accuracy_score(y_test_0, y_pred)
    macro_f1 = f1_score(y_test_0, y_pred, average="macro")
    per_class_f1 = f1_score(y_test_0, y_pred, labels=[0, 1, 2, 3], average=None)
    per_class_dict = {
        TIER_LABELS[tier]: float(score)
        for tier, score in zip([1, 2, 3, 4], per_class_f1)
    }
    cm = confusion_matrix(y_test_0, y_pred, labels=[0, 1, 2, 3])

    print(f"\n{'='*60}", flush=True)
    print(f"{model_name} — Held-Out Test Results (2020-2022)", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"Accuracy:  {acc:.4f} ({acc*100:.1f}%)")
    print(f"Macro F1:  {macro_f1:.4f}")
    print(f"\nClassification Report:")
    print(
        classification_report(
            y_test_0,
            y_pred,
            labels=[0, 1, 2, 3],
            target_names=["Budget", "Moderate", "Expensive", "Premium"],
        )
    )
    print(f"Confusion Matrix (rows=actual, cols=predicted):")
    print(f"           Budget  Moderate  Expensive  Premium")
    for i, row in enumerate(cm):
        tier_name = list(TIER_LABELS.values())[i]
        print(f"  {tier_name:>9s}  {'  '.join(f'{v:>6d}' for v in row)}")

    return acc, macro_f1, per_class_dict, y_pred, cm


# ===================================================================
# BOOTSTRAP CONFIDENCE INTERVALS
# ===================================================================


def bootstrap_confidence_intervals(
    model, X_test, y_test_0, n_bootstrap=2000, ci=0.95
):
    """Estimate 95% confidence intervals via bootstrap resampling of the test set.

    For each of n_bootstrap iterations, draw a sample with replacement from
    the test set (same size as original), predict, and compute metrics.
    The CI is the [alpha/2, 1-alpha/2] percentile interval over the
    bootstrap distribution.

    y_test_0 must be 0-indexed (0-3) to match model output.

    Returns a dict with CIs for accuracy, macro_f1, and each per-class F1.
    """
    rng = np.random.RandomState(RANDOM_SEED)
    n = len(y_test_0)
    alpha = (1 - ci) / 2

    accs = np.empty(n_bootstrap)
    macro_f1s = np.empty(n_bootstrap)
    per_class_f1s = np.empty((n_bootstrap, 4))

    print(f"\nBootstrapping {n_bootstrap} resamples for {ci*100:.0f}% CI...", flush=True)
    boot_start = time.time()
    report_every = max(1, n_bootstrap // 10)

    for b in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        X_b = X_test.iloc[idx]
        y_b = y_test_0.iloc[idx]

        y_pred = model.predict(X_b)

        accs[b] = accuracy_score(y_b, y_pred)
        macro_f1s[b] = f1_score(y_b, y_pred, average="macro", zero_division=0)
        per_class_f1s[b] = f1_score(
            y_b, y_pred, labels=[0, 1, 2, 3], average=None, zero_division=0
        )

        if (b + 1) % report_every == 0:
            pct = (b + 1) / n_bootstrap * 100
            elapsed_b = time.time() - boot_start
            print(f"  bootstrap {b+1}/{n_bootstrap} ({pct:.0f}%) — "
                  f"{elapsed_b:.1f}s elapsed", flush=True)

    boot_time = time.time() - boot_start

    def _ci(arr):
        return {
            "mean": float(np.mean(arr)),
            "ci_lower": float(np.percentile(arr, alpha * 100)),
            "ci_upper": float(np.percentile(arr, (1 - alpha) * 100)),
            "std": float(np.std(arr)),
        }

    results = {
        "accuracy": _ci(accs),
        "macro_f1": _ci(macro_f1s),
        "per_class_f1": {
            TIER_LABELS[tier]: _ci(per_class_f1s[:, i])
            for i, tier in enumerate([1, 2, 3, 4])
        },
        "n_bootstrap": n_bootstrap,
        "ci_level": ci,
        "bootstrap_time_seconds": round(boot_time, 2),
    }

    # Print summary
    print(f"  Done in {boot_time:.1f}s")
    print(f"\n  {'Metric':<20s}  {'Mean':>7s}  {'95% CI':>20s}")
    print(f"  {'-'*50}")
    for metric in ["accuracy", "macro_f1"]:
        m = results[metric]
        print(f"  {metric:<20s}  {m['mean']:>7.4f}  "
              f"[{m['ci_lower']:.4f}, {m['ci_upper']:.4f}]")
    for tier_name, m in results["per_class_f1"].items():
        label = f"F1 ({tier_name})"
        print(f"  {label:<20s}  {m['mean']:>7.4f}  "
              f"[{m['ci_lower']:.4f}, {m['ci_upper']:.4f}]")

    return results


# ===================================================================
# EXPERIMENT EXPORT
# ===================================================================


def export_experiment_results(
    search_results, search_metadata, best_meta, test_metrics, ci_results, output_dir
):
    """Write full experiment log as JSON and a summary leaderboard as CSV.

    JSON contains every config tested, per-fold scores, bootstrap CIs,
    and metadata — everything needed to reproduce or cite in a paper.

    CSV is a flat leaderboard: one row per config, sortable in Excel/Sheets.
    """
    output_dir = Path(output_dir)

    # --- JSON (full detail) ---
    experiment_log = {
        "experiment_timestamp": search_metadata["timestamp"],
        "data": {
            "train_path": str(TRAIN_PATH),
            "test_path": str(TEST_PATH),
            "n_train": search_metadata.get("n_train"),
            "n_test": search_metadata.get("n_test"),
            "n_features": search_metadata.get("n_features"),
            "features": NUMERIC_FEATURES + ENGINEERED_FEATURES + [CATEGORICAL_FEATURE],
            "target": TARGET,
        },
        "search_metadata": search_metadata,
        "best_model": best_meta,
        "test_set_performance": test_metrics,
        "confidence_intervals": ci_results,
        "all_search_results": search_results,
    }

    json_path = output_dir / "experiment_results.json"
    with open(json_path, "w") as f:
        json.dump(experiment_log, f, indent=2, default=str)
    print(f"\nExported detailed results to {json_path}")

    # --- CSV (summary leaderboard) ---
    rows = []
    for i, r in enumerate(
        sorted(search_results, key=lambda x: x["mean_f1_macro"], reverse=True), 1
    ):
        rows.append({
            "rank": i,
            "model_type": r["model_type"],
            "cv_strategy": r["cv_strategy"],
            "mean_f1_macro": round(r["mean_f1_macro"], 4),
            "std_f1_macro": round(r["std_f1_macro"], 4),
            "mean_train_f1": round(r["mean_train_f1"], 4),
            "fit_time_seconds": round(r["fit_time_seconds"], 3),
            "params": json.dumps(r["params"], default=str),
        })

    csv_path = output_dir / "experiment_summary.csv"
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    print(f"Exported summary leaderboard to {csv_path}")


# ===================================================================
# PART 2: NEIGHBORHOOD CLUSTERING
# ===================================================================


def run_clustering():
    """Cluster 2024 neighborhoods into groups of similar areas.

    Key changes from v1:
    - Uses 20 features (14 original + 6 engineered) instead of just 14.
      The ratio features (park_density, pop_density, etc.) help K-Means
      distinguish neighborhoods that differ in density but not raw counts.
    - k=7 instead of k=5. With 20 features, the data supports finer
      granularity. k=7 produces clusters where the smallest has 2
      neighborhoods and the largest has 56, with no single catch-all bucket.
    - n_init=20 (up from 10) for more stable centroid initialization.
    """
    df = pd.read_csv(NEIGHBORHOODS_PATH)
    df = engineer_features(df)
    print(f"\nLoaded {len(df)} neighborhoods for clustering")

    all_features = NUMERIC_FEATURES + ENGINEERED_FEATURES
    X_cluster = df[all_features].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_cluster)

    # Scan k=3..12 to show the full picture
    k_range = range(3, 13)
    inertias = []
    silhouettes = []

    print("\nCluster analysis (20 features):")
    print(f"  {'k':>3s}  {'Inertia':>10s}  {'Silhouette':>10s}  {'MaxSize':>8s}  {'MinSize':>8s}")
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=RANDOM_SEED, n_init=20)
        labels = km.fit_predict(X_scaled)
        inertias.append(km.inertia_)
        sil = silhouette_score(X_scaled, labels)
        silhouettes.append(sil)
        sizes = pd.Series(labels).value_counts()
        print(f"  {k:>3d}  {km.inertia_:>10.1f}  {sil:>10.4f}  {sizes.max():>8d}  {sizes.min():>8d}")

    # k=7 balances granularity with interpretability.
    # - k=5 was too coarse (one 70-neighborhood catch-all)
    # - k=7 gives 7 distinct profiles with the smallest at 2 neighborhoods
    # - k=8+ starts producing single-neighborhood clusters (overfitting)
    best_k = 7
    best_sil_idx = list(k_range).index(best_k)
    print(f"\nSelected k={best_k} (silhouette: {silhouettes[best_sil_idx]:.4f})")

    final_km = KMeans(n_clusters=best_k, random_state=RANDOM_SEED, n_init=20)
    cluster_labels = final_km.fit_predict(X_scaled)

    centroid_df = pd.DataFrame(final_km.cluster_centers_, columns=all_features)
    cluster_names = label_clusters(centroid_df, best_k)

    print("\nCluster labels:")
    for cid, name in cluster_names.items():
        count = (cluster_labels == cid).sum()
        examples = df.loc[cluster_labels == cid, "AREA_NAME"].values[:4]
        print(f"  Cluster {cid}: {name} ({count} neighborhoods)")
        print(f"    e.g. {', '.join(examples)}")

    assignments = pd.DataFrame(
        {
            "AREA_NAME": df["AREA_NAME"],
            "cluster_id": cluster_labels,
            "cluster_label": [cluster_names[c] for c in cluster_labels],
        }
    )

    out_path = DATA_DIR / "cluster_assignments.csv"
    assignments.to_csv(out_path, index=False)
    print(f"\nExported cluster assignments to {out_path}")

    scaler_path = MODEL_DIR / "scaler.pkl"
    joblib.dump(scaler, scaler_path)
    print(f"Saved scaler to {scaler_path}")

    return assignments, final_km, scaler, best_k, inertias, silhouettes, centroid_df


def label_clusters(centroid_df, k):
    """Assign human-readable names to clusters based on their centroids.

    Each centroid is a vector of z-scores (standardized values). We look at
    the most extreme values to understand what makes each cluster distinctive:
    - Values > 0 mean above the city-wide average
    - Values < 0 mean below average
    - The further from 0, the more distinctive that feature is for the cluster

    These rules were written by inspecting the actual k=7 centroids.
    """
    names = {}
    for i in range(k):
        row = centroid_df.iloc[i]

        # Identify the dominant characteristics of this cluster
        has_extreme_transit = (
            row.get("transit_line_density", 0) > 3.0
            and row.get("total_stop_count", 0) > 3.0
        )
        has_high_crime = (
            row.get("ASSAULT_RATE", 0) > 2.0
            or row.get("total_crime_rate", 0) > 2.5
        )
        has_high_density = row.get("pop_density", 0) > 2.0
        has_high_frequency = row.get("avg_stop_frequency", 0) > 1.0
        has_high_connectivity = row.get("routes_per_stop", 0) > 0.8
        has_low_pop = row.get("POPULATION", 0) < -0.5
        has_low_transit = (
            row.get("distinct_route_count", 0) < -0.4
            and row.get("max_stop_frequency", 0) < -0.4
        )
        has_high_transit_infra = (
            row.get("transit_line_density", 0) > 1.0
            and row.get("total_stop_count", 0) > 1.0
        )
        has_parks_and_pop = (
            row.get("park_count", 0) > 0.3
            and row.get("POPULATION", 0) > 0.3
        )

        if has_extreme_transit:
            names[i] = "Major Transit Hub"
        elif has_high_crime:
            names[i] = "Downtown & Entertainment"
        elif has_high_density:
            names[i] = "High-Density Urban Core"
        elif has_high_frequency and has_high_connectivity:
            names[i] = "Frequent-Service Corridor"
        elif has_high_transit_infra:
            names[i] = "Transit-Rich Suburban"
        elif has_parks_and_pop:
            names[i] = "Connected Family Neighborhood"
        elif has_low_transit and has_low_pop:
            names[i] = "Quiet Low-Density Residential"
        elif has_low_transit:
            names[i] = "Quiet Residential"
        else:
            names[i] = f"Mixed Neighborhood {i+1}"

    # Deduplicate
    seen = {}
    for i in list(names.keys()):
        if names[i] in seen:
            names[i] = names[i] + f" ({i+1})"
        seen[names[i]] = True

    return names


# ===================================================================
# MAIN
# ===================================================================


def main():
    print("=" * 60)
    print("TIER CLASSIFIER + NEIGHBORHOOD CLUSTERING")
    print("  with cross-validated hyperparameter search")
    print("  and bootstrapped confidence intervals")
    print("=" * 60)

    # --- Part 1: Tier Classifier ---
    print("\n--- PART 1: TIER CLASSIFIER ---\n")

    X_train, y_train, X_test, y_test, le, train_df, test_df = load_and_prepare_data()

    # All models are trained on 0-indexed labels (0-3) so XGBoost, RF, and
    # GBM all use the same label space. Shift test labels to match.
    y_test_0 = y_test - 1

    # --- Hyperparameter search (3 model families x 2 CV strategies) ---
    best_model, best_meta, all_results, search_metadata = run_hyperparameter_search(
        X_train, y_train, train_df
    )

    search_metadata["n_train"] = len(X_train)
    search_metadata["n_test"] = len(X_test)
    search_metadata["n_features"] = X_train.shape[1]

    best_name = best_meta["model_type"]

    # --- Evaluate on held-out test set ---
    best_acc, best_f1, per_class_f1, best_pred, best_cm = evaluate_model(
        best_model, X_test, y_test_0, best_name
    )

    test_metrics = {
        "accuracy": float(best_acc),
        "macro_f1": float(best_f1),
        "per_class_f1": per_class_f1,
    }

    # --- Bootstrap confidence intervals ---
    ci_results = bootstrap_confidence_intervals(
        best_model, X_test, y_test_0, n_bootstrap=2000, ci=0.95
    )

    # --- Export experiment results (JSON + CSV) ---
    export_experiment_results(
        all_results, search_metadata, best_meta, test_metrics, ci_results, MODEL_DIR
    )

    # --- Save model bundle (backward-compatible with backend) ---
    print(f"\n{'='*60}")
    print(f"BEST MODEL: {best_name}")
    print(f"  Test Accuracy: {best_acc:.4f} ({best_acc*100:.1f}%)")
    print(f"  Test Macro F1: {best_f1:.4f}")
    ci_acc = ci_results["accuracy"]
    ci_f1 = ci_results["macro_f1"]
    print(f"  Accuracy 95% CI: [{ci_acc['ci_lower']:.4f}, {ci_acc['ci_upper']:.4f}]")
    print(f"  Macro F1 95% CI: [{ci_f1['ci_lower']:.4f}, {ci_f1['ci_upper']:.4f}]")
    print(f"  CV Strategy: {best_meta['cv_strategy']}")
    print(f"  CV F1: {best_meta['cv_mean_f1']:.4f} +/- {best_meta['cv_std_f1']:.4f}")
    print(f"{'='*60}")

    model_path = MODEL_DIR / "tier_classifier.pkl"
    le_path = MODEL_DIR / "label_encoder.pkl"

    model_bundle = {
        # --- Original keys (backward-compatible with backend) ---
        "model": best_model,
        "model_name": best_name,
        # All models are trained on 0-indexed labels (0-3). The backend uses
        # is_xgboost to decide whether to +1 predictions back to 1-4 tiers.
        # We set this True unconditionally so the backend always shifts.
        "is_xgboost": True,
        "accuracy": best_acc,
        "macro_f1": best_f1,
        "feature_columns": NUMERIC_FEATURES + ENGINEERED_FEATURES + [CATEGORICAL_FEATURE],
        "numeric_features": NUMERIC_FEATURES,
        "engineered_features": ENGINEERED_FEATURES,
        "categorical_feature": CATEGORICAL_FEATURE,
        "tier_labels": TIER_LABELS,
        # --- New keys from search + bootstrap ---
        "best_params": best_meta["best_params"],
        "cv_strategy": best_meta["cv_strategy"],
        "cv_mean_f1": best_meta["cv_mean_f1"],
        "cv_std_f1": best_meta["cv_std_f1"],
        "cv_fold_scores": best_meta["cv_fold_scores"],
        "confidence_intervals": ci_results,
        "search_metadata": search_metadata,
    }

    joblib.dump(model_bundle, model_path)
    joblib.dump(le, le_path)
    print(f"\nSaved model bundle to {model_path}")
    print(f"Saved label encoder to {le_path}")

    # --- Part 2: Clustering ---
    print("\n--- PART 2: NEIGHBORHOOD CLUSTERING ---\n")
    assignments, km_model, scaler, best_k, inertias, silhouettes, centroid_df = (
        run_clustering()
    )

    # --- Summary ---
    print(f"\n{'='*60}")
    print("TRAINING COMPLETE")
    print(f"{'='*60}")
    print(f"  Classifier: {best_name}")
    print(f"    Test accuracy: {best_acc*100:.1f}% "
          f"(95% CI: [{ci_acc['ci_lower']*100:.1f}%, {ci_acc['ci_upper']*100:.1f}%])")
    print(f"    Test macro F1: {best_f1:.4f} "
          f"(95% CI: [{ci_f1['ci_lower']:.4f}, {ci_f1['ci_upper']:.4f}])")
    print(f"    CV F1: {best_meta['cv_mean_f1']:.4f} +/- {best_meta['cv_std_f1']:.4f}")
    print(f"    Configs evaluated: {search_metadata['n_configs_evaluated']}")
    print(f"  Clustering: {best_k} clusters assigned to 158 neighborhoods")
    print(f"  Artifacts:")
    print(f"    models/tier_classifier.pkl")
    print(f"    models/label_encoder.pkl")
    print(f"    models/scaler.pkl")
    print(f"    models/experiment_results.json")
    print(f"    models/experiment_summary.csv")
    print(f"    data/processed_data/cluster_assignments.csv")


if __name__ == "__main__":
    main()
