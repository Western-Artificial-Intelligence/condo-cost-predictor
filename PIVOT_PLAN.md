# Toronto Rent Explorer + Tier Classifier — Sprint Plan

**Deadline:** February 24, 2026 (5 days from Feb 20)
**Approach:** Option C (Rent Explorer data product) as the base, with Option A (Tier Classifier) layered on top as the ML component.

---

## What We're Building

An interactive Toronto neighborhood rent intelligence tool that lets users explore 15 years of rental data across 158 neighborhoods, filter by affordability, discover similar neighborhoods, and see ML-predicted affordability tiers.

**The product:**
- Interactive map of Toronto, color-coded by rent tier or cluster
- Neighborhood detail panel: rent history, crime stats, transit stats, predicted tier
- Affordability filter: enter income, see which neighborhoods you can afford
- "Find similar neighborhoods" via clustering
- Tier classifier: predict which affordability tier a neighborhood will be in 2 years from now

**The presentation story:** "We collected and cleaned 15 years of Toronto neighborhood data, built an interactive exploration tool, and trained a model to predict which affordability tier neighborhoods will fall into."

---

## Why the Original Model Failed

Thomson's 5 training iterations proved the problem is data, not modeling:

1. `avg_rent_1br`, `rent_lag_1`, `rent_lag_2`, `rent_growth_rate` leak the target. Rent is highly autocorrelated — the model memorizes "future rent = current rent + delta" and learns nothing else.
2. Non-rent features (crime, transit, parks, population) are static proxies copied from 2024 to all prior years. They don't vary over time, so they can't explain changes in rent.
3. Confirmed across XGBoost, Random Forest, and Elastic Net. Not an algorithm problem.

The pivot reframes the task: instead of predicting exact dollar amounts (regression), classify neighborhoods into affordability tiers (classification) and make the data itself the product.

---

## Data Reference

### Available Datasets

| File | Rows | Columns | Description |
|------|------|---------|-------------|
| `data/processed_data/train_v2.csv` | 1,580 | 21 | Training set, 2010–2019 |
| `data/processed_data/test_v2.csv` | 474 | 21 | Test set, 2020–2022 |
| `data/processed_data/neighborhoods_2024.csv` | 158 | 21 | 2024 snapshot with geometry |
| `data/processed_data/toronto_master_2010_2024.csv` | 2,528 | 95 | Original master (for rent history charts) |
| `data/processed_data/toronto_map_key.csv` | 158 | 4 | Neighborhood geometry (WKT polygons) |

### Columns in train_v2 / test_v2

| Column | Type | Role |
|--------|------|------|
| `AREA_NAME` | string | Neighborhood identifier |
| `YEAR` | int | Year of observation |
| `CLASSIFICATION_CODE` | string (nullable) | Geographic group (e.g. "Toronto E07") |
| `area_sq_meters` | float | Neighborhood area |
| `perimeter_meters` | float | Neighborhood perimeter |
| `park_count` | float | Parks within boundary |
| `ASSAULT_RATE` | float | Assaults per 100k |
| `AUTOTHEFT_RATE` | float | Auto thefts per 100k |
| `ROBBERY_RATE` | float | Robberies per 100k |
| `THEFTOVER_RATE` | float | Thefts over $5k per 100k |
| `POPULATION` | float | Neighborhood population |
| `total_stop_count` | float | TTC stops in neighborhood |
| `avg_stop_frequency` | float | Average stop service frequency |
| `max_stop_frequency` | float | Max stop service frequency |
| `total_line_length_meters` | float | Total transit line length |
| `transit_line_density` | float | Transit lines per sq meter |
| `distinct_route_count` | float | Number of distinct TTC routes |
| `avg_rent_1br` | float | Current 1BR rent (for UI only, NOT a model feature) |
| `TARGET_RENT_2YR` | float | 1BR rent 2 years ahead (regression target) |
| `RENT_TIER` | int (1-4) | Current rent quartile |
| `TARGET_TIER_2YR` | int (1-4) | Rent quartile 2 years ahead (classification target) |

### Tier Definitions

| Tier | Label | Meaning |
|------|-------|---------|
| 1 | Budget | Bottom 25% of rents for that year |
| 2 | Moderate | 25th–50th percentile |
| 3 | Expensive | 50th–75th percentile |
| 4 | Premium | Top 25% of rents for that year |

### Model Features (14 numeric + 1 categorical)

For the tier classifier, use ONLY these as input features:

**Numeric (14):** `area_sq_meters`, `perimeter_meters`, `park_count`, `ASSAULT_RATE`, `AUTOTHEFT_RATE`, `ROBBERY_RATE`, `THEFTOVER_RATE`, `POPULATION`, `total_stop_count`, `avg_stop_frequency`, `max_stop_frequency`, `total_line_length_meters`, `transit_line_density`, `distinct_route_count`

**Categorical (1):** `CLASSIFICATION_CODE` (OHE or label-encode)

**DO NOT use `avg_rent_1br` as a feature — it leaks the target.**

---

## Execution Plan

### Day 1 (Feb 20): Data Rebuild -- DONE

**Owner:** lgomezvi
**Script:** `data/rebuild_dataset.py`

- [x] Rebuild master dataset with 2-year target (`TARGET_RENT_2YR`)
- [x] Include 2010–2022 rows (backfilled crime data for 2010–2013)
- [x] Compute rent tier labels per year (quartile-based)
- [x] Compute 2-year-ahead tier labels (`TARGET_TIER_2YR`)
- [x] Clean feature matrix: 21 columns, 0 NaN in numeric features
- [x] Export train/test splits + 2024 neighborhood snapshot with geometry
- [x] Fix population proxy (was all-zeros for 2010–2020)
- [x] Deduplicate 2017 (had 317 rows, now 158)

**Key improvements over old dataset:** 2x training data (1,580 vs 790), 3x test data (474 vs 316), no leaky features, 21 clean columns instead of 95.

---

### Day 2 (Feb 21): Model Training + Clustering -- DONE

**Owner:** Thomson / ore7117
**Notebook:** `notebooks/day2_model_and_clustering.ipynb`
**Script:** `models/train_tier_classifier.py`

**Tier Classifier:**
- [x] Train XGBoost or Random Forest multi-class classifier
  - Input: 14 numeric + 6 engineered ratio features + `CLASSIFICATION_CODE` (21 total)
  - Target: `TARGET_TIER_2YR` (values 1–4)
  - Data: `train_v2.csv` for training, `test_v2.csv` for evaluation
  - DO NOT use `avg_rent_1br` as a feature
- [x] Evaluate: accuracy, confusion matrix, per-class precision/recall
- [x] Run SHAP for feature importance
- [x] Save model to `models/tier_classifier.pkl`
- [x] Feature engineering iteration: added park_density, pop_density, transit_per_capita, total_crime_rate, compactness, routes_per_stop
- [x] Hyperparameter sweep across RF, XGBoost, and GBM configurations

**Neighborhood Clustering:**
- [x] K-means (k=7) on standardized 20 features (14 base + 6 engineered) from `neighborhoods_2024.csv`
- [x] Label clusters with human-readable names based on centroids
- [x] Export cluster assignments to `data/processed_data/cluster_assignments.csv`

**Deliverables:** `.pkl` model file, cluster CSV, documented accuracy/confusion matrix

**Results:**
- Randomized hyperparameter search: 3 model families x 2 CV strategies x 10 configs = 60 configurations, 300 total model fits
- Best model: **GradientBoosting** (CV F1 = 0.7400 +/- 0.0327 via StratifiedKFold)
- All three model families converge to similar CV F1 (0.73-0.74), confirming the ceiling is data-driven
- Test accuracy: **60.1% (95% CI: 55.7%-64.3%)**, macro F1: **0.604 (95% CI: 0.560-0.644)**
- Feature engineering added 6 ratio features (park_density, pop_density, etc.) — park_density alone has 0.47 correlation with target vs 0.01 for raw park_count
- Most errors are between adjacent tiers (Budget<->Moderate, Expensive<->Premium) — neighborhoods near tier boundaries could go either way
- Premium tier is easiest to predict (0.73 F1); Moderate is hardest (0.53 F1)
- CV-test gap (0.74 vs 0.60) quantifies the static-feature limitation and 2020-2022 distributional shift
- 7 clusters: Frequent-Service Corridor (22), Connected Family Neighborhood (45), Quiet Low-Density Residential (56), Downtown & Entertainment (5), Major Transit Hub (2), Transit-Rich Suburban (18), High-Density Urban Core (10)
- SHAP analysis shows park_density, pop_density, and transit features are the strongest predictors

**Artifacts:**

| File | Description |
|------|-------------|
| `models/tier_classifier.pkl` | GradientBoosting model bundle (model + metadata + CIs) |
| `models/label_encoder.pkl` | LabelEncoder for CLASSIFICATION_CODE |
| `models/scaler.pkl` | StandardScaler fitted on clustering features |
| `models/experiment_results.json` | Full search results (60 configs, per-fold scores, CIs) |
| `models/experiment_summary.csv` | Ranked leaderboard of all configurations |
| `models/experiment_summary.md` | Formatted experiment report |
| `data/processed_data/cluster_assignments.csv` | 158 neighborhoods with cluster IDs and labels |

---

### Day 3 (Feb 22): API + Backend Integration -- DONE

**Owner:** besma / Kevin

- [x] Update `PredictRequest` schema: take `neighbourhood` (required), return tier prediction + confidence
- [x] Load trained classifier in `backend/app/services/model.py`
- [x] `GET /api/neighbourhood/{name}` — full feature profile + cluster + predicted tier
- [x] `GET /api/clusters` — cluster definitions and member neighborhoods
- [x] `GET /api/affordable?income=X` — neighborhoods affordable at given income (30% of gross rule)
- [x] Test all endpoints manually

---

### Day 4 (Feb 23): Frontend — Map + Explorer -- DONE

**Owner:** Kevin / Streamlit person

- [x] Replace current Streamlit app with new layout:
  - **Map view** (Folium): neighborhoods colored by rent tier or cluster
  - **Neighborhood detail panel**: rent history chart (15 years), crime stats, transit stats, predicted tier
  - **Affordability filter**: income input, map highlights affordable neighborhoods
  - **"Find similar"**: select a neighborhood, show its cluster members
- [x] Wire up to backend API endpoints
- [x] Style and polish

**Backend additions:** `GET /api/map-data` (geometry + tier + cluster), `GET /api/neighbourhood/{name}/history` (15-year rent history)

---

### Day 5 (Feb 24): Polish + Presentation Prep

**Owner:** Everyone

- [ ] Fix bugs, handle edge cases
- [ ] Update README to reflect the actual product
- [ ] Prepare demo script: what to show, in what order
- [ ] Document the pivot story for presentation

---

## Team Message

The model isn't broken because anyone did bad work. Thomson's 5 iterations of systematic diagnosis is exactly what good ML engineering looks like. The dataset has a structural limitation: the features that vary over time (rent) leak the target, and the features that describe neighborhoods (crime, transit, parks) don't vary over time. No algorithm can fix that.

The pivot isn't a retreat — it's a reframing. The data you spent 2 months collecting is genuinely valuable. The 15-year longitudinal view of 158 Toronto neighborhoods with crime, transit, and rental data doesn't exist anywhere else in a clean, usable form. Make that the product, add a defensible ML layer on top, and you have something worth presenting.
