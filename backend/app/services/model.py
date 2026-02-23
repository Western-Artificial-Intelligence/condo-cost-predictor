from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODELS_DIR = PROJECT_ROOT / "models"
DATA_DIR = PROJECT_ROOT / "data" / "processed_data"

MODEL_PATH = MODELS_DIR / "tier_classifier.pkl"
LABEL_ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"
NEIGHBORHOODS_PATH = DATA_DIR / "neighborhoods_2024.csv"
CLUSTERS_PATH = DATA_DIR / "cluster_assignments.csv"

BASE_NUMERIC_FEATURES = [
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

ENGINEERED_FEATURES = [
    "park_density",
    "pop_density",
    "transit_per_capita",
    "total_crime_rate",
    "compactness",
    "routes_per_stop",
]

TIER_FALLBACK = {1: "Budget", 2: "Moderate", 3: "Expensive", 4: "Premium"}


class NeighbourhoodNotFoundError(ValueError):
    pass


def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["park_density"] = df["park_count"] / df["area_sq_meters"].clip(lower=1e-10)
    df["pop_density"] = df["POPULATION"] / df["area_sq_meters"].clip(lower=1e-10)
    df["transit_per_capita"] = df["total_stop_count"] / df["POPULATION"].clip(lower=1)
    df["total_crime_rate"] = df[
        ["ASSAULT_RATE", "AUTOTHEFT_RATE", "ROBBERY_RATE", "THEFTOVER_RATE"]
    ].sum(axis=1)
    df["compactness"] = (df["perimeter_meters"] ** 2) / df["area_sq_meters"].clip(
        lower=1e-10
    )
    df["routes_per_stop"] = df["distinct_route_count"] / df["total_stop_count"].clip(
        lower=1
    )
    return df


def _to_native(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    return value.item() if hasattr(value, "item") else value


@lru_cache(maxsize=1)
def _load_model_bundle() -> dict[str, Any]:
    return joblib.load(MODEL_PATH)


@lru_cache(maxsize=1)
def _load_label_encoder() -> Any:
    return joblib.load(LABEL_ENCODER_PATH)


@lru_cache(maxsize=1)
def _load_data() -> dict[str, Any]:
    neighborhoods = pd.read_csv(NEIGHBORHOODS_PATH)
    clusters = pd.read_csv(CLUSTERS_PATH)

    model_bundle = _load_model_bundle()
    label_encoder = _load_label_encoder()

    canonical_by_key: dict[str, str] = {}
    for name in neighborhoods["AREA_NAME"].tolist():
        canonical_by_key[name.strip().lower()] = name

    neighborhoods_for_model = _engineer_features(neighborhoods)
    neighborhoods_for_model["CLASSIFICATION_CODE"] = label_encoder.transform(
        neighborhoods_for_model["CLASSIFICATION_CODE"].fillna("UNKNOWN")
    )

    clusters_by_name = {
        row.AREA_NAME: {"cluster_id": int(row.cluster_id), "cluster_label": row.cluster_label}
        for row in clusters.itertuples(index=False)
    }

    cluster_groups = (
        clusters.sort_values(["cluster_id", "AREA_NAME"])
        .groupby(["cluster_id", "cluster_label"])["AREA_NAME"]
        .apply(list)
        .reset_index()
    )

    return {
        "neighborhoods_raw": neighborhoods,
        "neighborhoods_model": neighborhoods_for_model,
        "clusters_by_name": clusters_by_name,
        "cluster_groups": cluster_groups,
        "canonical_by_key": canonical_by_key,
        "feature_columns": model_bundle["feature_columns"],
    }


def _resolve_neighbourhood_name(name: str) -> str:
    canonical = _load_data()["canonical_by_key"].get(name.strip().lower())
    if canonical is None:
        raise NeighbourhoodNotFoundError(f"Unknown neighbourhood: {name}")
    return canonical


def _predict_from_row(canonical_name: str) -> dict[str, Any]:
    bundle = _load_model_bundle()
    data = _load_data()
    model = bundle["model"]
    feature_columns = data["feature_columns"]

    row = data["neighborhoods_model"].loc[
        data["neighborhoods_model"]["AREA_NAME"] == canonical_name
    ]
    if row.empty:
        raise NeighbourhoodNotFoundError(f"Unknown neighbourhood: {canonical_name}")

    X = row.iloc[[0]][feature_columns]

    raw_pred = model.predict(X)[0]
    predicted_tier = int(raw_pred) + 1 if bundle.get("is_xgboost") else int(raw_pred)

    probs = model.predict_proba(X)[0]
    class_labels = list(model.classes_)
    probs_by_tier: dict[int, float] = {}
    for cls, prob in zip(class_labels, probs):
        tier = int(cls) + 1 if bundle.get("is_xgboost") else int(cls)
        probs_by_tier[tier] = float(prob)

    tier_labels_raw = bundle.get("tier_labels", TIER_FALLBACK)
    tier_labels = {int(k): v for k, v in tier_labels_raw.items()}

    return {
        "predicted_tier": predicted_tier,
        "tier_label": tier_labels.get(predicted_tier, str(predicted_tier)),
        "confidence": probs_by_tier.get(predicted_tier, max(probs_by_tier.values())),
        "model": bundle.get("model_name", "unknown"),
    }


def list_neighbourhoods() -> list[dict[str, Any]]:
    names = sorted(_load_data()["neighborhoods_raw"]["AREA_NAME"].tolist())
    return [{"id": i + 1, "name": name} for i, name in enumerate(names)]


def predict_neighbourhood(name: str) -> dict[str, Any]:
    canonical_name = _resolve_neighbourhood_name(name)
    prediction = _predict_from_row(canonical_name)
    return {"neighbourhood": canonical_name, **prediction}


def neighbourhood_detail(name: str) -> dict[str, Any]:
    canonical_name = _resolve_neighbourhood_name(name)
    data = _load_data()

    raw_row = data["neighborhoods_raw"].loc[
        data["neighborhoods_raw"]["AREA_NAME"] == canonical_name
    ].iloc[0]
    profile = {k: _to_native(v) for k, v in raw_row.to_dict().items()}

    cluster = data["clusters_by_name"].get(
        canonical_name, {"cluster_id": -1, "cluster_label": "Unknown"}
    )
    prediction = _predict_from_row(canonical_name)

    return {
        "neighbourhood": canonical_name,
        "profile": profile,
        "cluster_id": cluster["cluster_id"],
        "cluster_label": cluster["cluster_label"],
        "prediction": prediction,
    }


def clusters() -> list[dict[str, Any]]:
    groups = _load_data()["cluster_groups"]
    return [
        {
            "cluster_id": int(row.cluster_id),
            "cluster_label": row.cluster_label,
            "count": len(row.AREA_NAME),
            "neighbourhoods": row.AREA_NAME,
        }
        for row in groups.itertuples(index=False)
    ]


def affordable_neighbourhoods(annual_income: float) -> dict[str, Any]:
    data = _load_data()
    monthly_budget = float(annual_income) * 0.30 / 12.0

    affordable = data["neighborhoods_raw"].loc[
        data["neighborhoods_raw"]["avg_rent_1br"] <= monthly_budget
    ].copy()
    affordable = affordable.sort_values(["avg_rent_1br", "AREA_NAME"])

    results: list[dict[str, Any]] = []
    for row in affordable.itertuples(index=False):
        name = row.AREA_NAME
        prediction = _predict_from_row(name)
        cluster = data["clusters_by_name"].get(name, {"cluster_id": -1, "cluster_label": "Unknown"})
        results.append(
            {
                "neighbourhood": name,
                "avg_rent_1br": float(row.avg_rent_1br),
                "cluster_id": cluster["cluster_id"],
                "cluster_label": cluster["cluster_label"],
                "predicted_tier": prediction["predicted_tier"],
                "tier_label": prediction["tier_label"],
                "confidence": prediction["confidence"],
            }
        )

    return {
        "annual_income": float(annual_income),
        "monthly_budget": monthly_budget,
        "neighbourhoods": results,
    }
