"""
rebuild_dataset.py — Day 1 pivot data rebuild

Reads the existing toronto_master_2010_2024.csv, fixes structural problems
(deduplication, junk columns, leaky features), creates 2-year rent targets
and tier labels, and exports clean train/test splits + a 2024 neighborhood
snapshot for the explorer frontend.

Run from the data/ directory:
    python rebuild_dataset.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROCESSED = SCRIPT_DIR / "processed_data"
MAP_KEY_PATH = PROCESSED / "toronto_map_key.csv"
MASTER_PATH = PROCESSED / "toronto_master_2010_2024.csv"

KEEP_COLUMNS = [
    "AREA_NAME",
    "YEAR",
    "CLASSIFICATION_CODE",
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
    "avg_rent_1br",
]

CATEGORICAL_COLUMNS = ["CLASSIFICATION_CODE"]

FEATURE_COLUMNS = [
    c for c in KEEP_COLUMNS
    if c not in ("AREA_NAME", "YEAR", "avg_rent_1br") and c not in CATEGORICAL_COLUMNS
]

CRIME_RATE_COLS = ["ASSAULT_RATE", "AUTOTHEFT_RATE", "ROBBERY_RATE", "THEFTOVER_RATE"]

TIER_LABELS = {1: "Budget", 2: "Moderate", 3: "Expensive", 4: "Premium"}

TRAIN_YEARS = range(2010, 2020)  # 2010-2019
TEST_YEARS = range(2020, 2023)   # 2020-2022


def load_and_deduplicate(path: Path) -> pd.DataFrame:
    """Step 1: Load master CSV, deduplicate, and fix population proxy."""
    df = pd.read_csv(path, low_memory=False)
    before = len(df)
    df = df.drop_duplicates(subset=["AREA_NAME", "YEAR"], keep="first")
    df = df.sort_values(["AREA_NAME", "YEAR"]).reset_index(drop=True)
    after = len(df)

    pop_2024 = df.loc[df["YEAR"] == 2024, ["AREA_NAME", "POPULATION"]].dropna()
    pop_lookup = pop_2024.set_index("AREA_NAME")["POPULATION"].to_dict()
    filled = 0
    for idx, row in df.iterrows():
        if pd.isna(row["POPULATION"]) or row["POPULATION"] == 0:
            pop_val = pop_lookup.get(row["AREA_NAME"])
            if pop_val is not None:
                df.at[idx, "POPULATION"] = pop_val
                filled += 1

    print(f"Step 1 — Load & deduplicate")
    print(f"  Loaded {before} rows, deduplicated to {after}")
    print(f"  Neighborhoods: {df['AREA_NAME'].nunique()}, Years: {sorted(df['YEAR'].unique())}")
    print(f"  Population: proxied 2024 values to {filled} rows")
    return df


def compute_targets_and_tiers(df: pd.DataFrame) -> pd.DataFrame:
    """Steps 2-3: Compute 2-year rent target and tier labels.

    Tiers are computed on the FULL dataset (including 2023-2024) so that
    rows for 2021-2022 can look up their target tier at year+2. Then rows
    without a usable target (2023-2024) are dropped.
    """
    rent_lookup = df.set_index(["AREA_NAME", "YEAR"])["avg_rent_1br"].to_dict()

    df["TARGET_RENT_2YR"] = df.apply(
        lambda r: rent_lookup.get((r["AREA_NAME"], r["YEAR"] + 2), np.nan), axis=1
    )
    has_target = df["TARGET_RENT_2YR"].notna().sum()
    missing_target = df["TARGET_RENT_2YR"].isna().sum()
    print(f"\nStep 2 — 2-year rent target")
    print(f"  TARGET_RENT_2YR: {has_target} non-null, {missing_target} null")

    df["RENT_TIER"] = df.groupby("YEAR")["avg_rent_1br"].transform(assign_tier)

    tier_at_target_year = {}
    for year in df["YEAR"].unique():
        target_year = year + 2
        subset = df[df["YEAR"] == target_year]
        if len(subset) == 0:
            continue
        tiers = assign_tier(subset["avg_rent_1br"])
        for area, tier in zip(subset["AREA_NAME"], tiers):
            tier_at_target_year[(area, year)] = tier

    df["TARGET_TIER_2YR"] = df.apply(
        lambda r: tier_at_target_year.get((r["AREA_NAME"], r["YEAR"]), np.nan), axis=1
    )

    both_targets = df["TARGET_RENT_2YR"].notna() & df["TARGET_TIER_2YR"].notna()
    df = df[both_targets].copy()
    df["RENT_TIER"] = df["RENT_TIER"].astype(int)
    df["TARGET_TIER_2YR"] = df["TARGET_TIER_2YR"].astype(int)

    print(f"  Dropping rows without both targets (2023-2024)...")
    print(f"  Remaining: {len(df)} rows, years {df['YEAR'].min()}-{df['YEAR'].max()}")

    print(f"\nStep 3 — Rent tier labels")
    print(f"  RENT_TIER distribution:\n{df['RENT_TIER'].value_counts().sort_index().to_string()}")
    print(f"  TARGET_TIER_2YR distribution:\n{df['TARGET_TIER_2YR'].value_counts().sort_index().to_string()}")
    return df


def assign_tier(series: pd.Series) -> pd.Series:
    """Assign quartile-based tier labels (1-4) to a rent series."""
    return pd.qcut(series, q=4, labels=[1, 2, 3, 4], duplicates="drop").astype(int)


def select_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Step 4: Keep only the columns we need, drop everything else."""
    target_cols = ["TARGET_RENT_2YR", "RENT_TIER", "TARGET_TIER_2YR"]
    cols = KEEP_COLUMNS + target_cols
    missing_cols = [c for c in cols if c not in df.columns]
    if missing_cols:
        print(f"  WARNING: Missing columns: {missing_cols}")

    available = [c for c in cols if c in df.columns]
    df = df[available].copy()
    print(f"\nStep 4 — Column selection")
    print(f"  Kept {len(available)} columns: {available}")
    return df


def impute_missing(df: pd.DataFrame, train_mask: pd.Series) -> pd.DataFrame:
    """Step 5: Impute missing values using train-set statistics only."""
    print(f"\nStep 5 — Imputation")

    for col in CRIME_RATE_COLS:
        zeros = (df[col] == 0).sum()
        if zeros > 0:
            df[col] = df[col].replace(0, np.nan)
            print(f"  {col}: replaced {zeros} zeros with NaN")

    train_medians = df.loc[train_mask, FEATURE_COLUMNS].median()

    for col in FEATURE_COLUMNS:
        nans_before = df[col].isna().sum()
        if nans_before > 0:
            df[col] = df[col].fillna(train_medians[col])
            print(f"  {col}: filled {nans_before} NaN with train median ({train_medians[col]:.2f})")

    remaining_nans = df[FEATURE_COLUMNS].isna().sum().sum()
    print(f"  Remaining NaN in features: {remaining_nans}")
    return df


def split_and_export(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Step 6: Time-based train/test split and export."""
    train = df[df["YEAR"].isin(TRAIN_YEARS)].copy()
    test = df[df["YEAR"].isin(TEST_YEARS)].copy()

    train_path = PROCESSED / "train_v2.csv"
    test_path = PROCESSED / "test_v2.csv"
    train.to_csv(train_path, index=False)
    test.to_csv(test_path, index=False)

    print(f"\nStep 6 — Train/test split")
    print(f"  Train: {len(train)} rows, years {sorted(train['YEAR'].unique())}")
    print(f"  Test:  {len(test)} rows, years {sorted(test['YEAR'].unique())}")
    print(f"  Exported: {train_path}, {test_path}")
    return train, test


def export_2024_snapshot(master_path: Path, map_key_path: Path):
    """Step 7: Export 2024 neighborhood snapshot with geometry for the explorer."""
    master = pd.read_csv(master_path, low_memory=False)
    master = master.drop_duplicates(subset=["AREA_NAME", "YEAR"], keep="first")
    snapshot = master[master["YEAR"] == 2024].copy()

    snapshot_cols = ["AREA_NAME"] + [c for c in KEEP_COLUMNS if c != "AREA_NAME"]
    available = [c for c in snapshot_cols if c in snapshot.columns]
    snapshot = snapshot[available].copy()

    map_key = pd.read_csv(map_key_path)
    snapshot = snapshot.merge(map_key, on="AREA_NAME", how="left")

    out_path = PROCESSED / "neighborhoods_2024.csv"
    snapshot.to_csv(out_path, index=False)

    print(f"\nStep 7 — 2024 neighborhood snapshot")
    print(f"  Rows: {len(snapshot)}, Columns: {list(snapshot.columns)}")
    print(f"  Has geometry: {snapshot['geometry_wkt'].notna().sum()}/{len(snapshot)}")
    print(f"  Exported: {out_path}")
    return snapshot


def print_summary(df: pd.DataFrame, train: pd.DataFrame, test: pd.DataFrame):
    """Step 8: Print summary statistics."""
    print(f"\n{'='*60}")
    print(f"REBUILD SUMMARY")
    print(f"{'='*60}")
    print(f"  Total rows:    {len(df)}")
    print(f"  Total columns: {len(df.columns)}")
    print(f"  Columns:       {list(df.columns)}")
    print(f"  Year range:    {df['YEAR'].min()}-{df['YEAR'].max()}")
    print(f"  Neighborhoods: {df['AREA_NAME'].nunique()}")
    print(f"\n  Train: {len(train)} rows ({sorted(train['YEAR'].unique())})")
    print(f"  Test:  {len(test)} rows ({sorted(test['YEAR'].unique())})")

    print(f"\n  Tier distribution per year:")
    tier_pivot = df.pivot_table(
        index="YEAR", columns="RENT_TIER", values="AREA_NAME", aggfunc="count", fill_value=0
    )
    tier_pivot.columns = [TIER_LABELS.get(c, c) for c in tier_pivot.columns]
    print(tier_pivot.to_string())

    print(f"\n  Missing values:")
    missing = df.isnull().sum()
    if missing.sum() == 0:
        print("    None")
    else:
        print(missing[missing > 0].to_string())

    print(f"\n  Feature statistics:")
    print(df[FEATURE_COLUMNS].describe().round(2).to_string())
    print()


def main():
    print("=" * 60)
    print("PIVOT DATA REBUILD")
    print("=" * 60)

    df = load_and_deduplicate(MASTER_PATH)
    df = compute_targets_and_tiers(df)
    df = select_columns(df)

    train_mask = df["YEAR"].isin(TRAIN_YEARS)
    df = impute_missing(df, train_mask)

    train, test = split_and_export(df)
    snapshot = export_2024_snapshot(MASTER_PATH, MAP_KEY_PATH)
    print_summary(df, train, test)

    print("Done.")


if __name__ == "__main__":
    main()
