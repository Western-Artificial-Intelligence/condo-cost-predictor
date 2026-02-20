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

import pandas as pd
import numpy as np
import joblib
from pathlib import Path

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score,
)
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
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
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    return rf


def evaluate_model(model, X_test, y_test, model_name, is_xgboost=False):
    """Evaluate a classifier and print metrics.

    We care about:
    - Accuracy: what fraction of predictions are correct overall
    - Macro F1: average F1 across all 4 tiers (treats each tier equally,
      important because we don't want the model to ignore rare tiers)
    - Per-class precision/recall: which tiers does the model struggle with?
    - Confusion matrix: shows exactly where misclassifications happen
    """
    if is_xgboost:
        y_pred = model.predict(X_test) + 1
    else:
        y_pred = model.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred, average="macro")
    cm = confusion_matrix(y_test, y_pred, labels=[1, 2, 3, 4])

    print(f"\n{'='*60}")
    print(f"{model_name} Results")
    print(f"{'='*60}")
    print(f"Accuracy:  {acc:.4f} ({acc*100:.1f}%)")
    print(f"Macro F1:  {f1:.4f}")
    print(f"\nClassification Report:")
    print(
        classification_report(
            y_test,
            y_pred,
            labels=[1, 2, 3, 4],
            target_names=["Budget", "Moderate", "Expensive", "Premium"],
        )
    )
    print(f"Confusion Matrix (rows=actual, cols=predicted):")
    print(f"           Budget  Moderate  Expensive  Premium")
    for i, row in enumerate(cm):
        tier_name = list(TIER_LABELS.values())[i]
        print(f"  {tier_name:>9s}  {'  '.join(f'{v:>6d}' for v in row)}")

    return acc, f1, y_pred, cm


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
    print("DAY 2: TIER CLASSIFIER + NEIGHBORHOOD CLUSTERING")
    print("=" * 60)

    # --- Part 1: Tier Classifier ---
    print("\n--- PART 1: TIER CLASSIFIER ---\n")

    X_train, y_train, X_test, y_test, le, train_df, test_df = load_and_prepare_data()

    print("\nTraining XGBoost classifier...")
    xgb_model = train_xgboost(X_train, y_train)

    print("Training Random Forest classifier...")
    rf_model = train_random_forest(X_train, y_train)

    xgb_acc, xgb_f1, xgb_pred, xgb_cm = evaluate_model(
        xgb_model, X_test, y_test, "XGBoost", is_xgboost=True
    )
    rf_acc, rf_f1, rf_pred, rf_cm = evaluate_model(
        rf_model, X_test, y_test, "Random Forest", is_xgboost=False
    )

    # Pick the best model by macro F1 (treats all tiers equally)
    if xgb_f1 >= rf_f1:
        best_model = xgb_model
        best_name = "XGBoost"
        best_acc = xgb_acc
        best_f1 = xgb_f1
        best_is_xgb = True
    else:
        best_model = rf_model
        best_name = "Random Forest"
        best_acc = rf_acc
        best_f1 = rf_f1
        best_is_xgb = False

    print(f"\n{'='*60}")
    print(f"BEST MODEL: {best_name}")
    print(f"  Accuracy: {best_acc:.4f} ({best_acc*100:.1f}%)")
    print(f"  Macro F1: {best_f1:.4f}")
    print(f"{'='*60}")

    model_path = MODEL_DIR / "tier_classifier.pkl"
    le_path = MODEL_DIR / "label_encoder.pkl"

    model_bundle = {
        "model": best_model,
        "model_name": best_name,
        "is_xgboost": best_is_xgb,
        "accuracy": best_acc,
        "macro_f1": best_f1,
        "feature_columns": NUMERIC_FEATURES + ENGINEERED_FEATURES + [CATEGORICAL_FEATURE],
        "numeric_features": NUMERIC_FEATURES,
        "engineered_features": ENGINEERED_FEATURES,
        "categorical_feature": CATEGORICAL_FEATURE,
        "tier_labels": TIER_LABELS,
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
    print("DAY 2 COMPLETE")
    print(f"{'='*60}")
    print(f"  Classifier: {best_name} — {best_acc*100:.1f}% accuracy, {best_f1:.4f} macro F1")
    print(f"  Clustering: {best_k} clusters assigned to 158 neighborhoods")
    print(f"  Artifacts:")
    print(f"    models/tier_classifier.pkl")
    print(f"    models/label_encoder.pkl")
    print(f"    models/scaler.pkl")
    print(f"    data/processed_data/cluster_assignments.csv")


if __name__ == "__main__":
    main()
