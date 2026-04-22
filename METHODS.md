# Methods & Design — Toronto Rent Explorer

This document describes the **methods** (how we build and run the system) and **design** (why we made key choices) for the Toronto Rent Explorer project. It is written for both technical contributors and business or product stakeholders.

---

## 1. Business Context & Goals

### Problem

Students and young adults in Toronto face a difficult rental market. They need to:

- Understand **where they can afford to live** given their income
- Anticipate **how neighborhoods might change** in affordability over time
- Discover **similar but more affordable** neighborhoods when their preferred area is out of reach

### Solution

We built a **neighborhood-level exploration and prediction tool** that:

1. **Explores** 15 years of open data (2010–2024) across 158 Toronto neighborhoods: rent, crime, transit, green space, and demographics.
2. **Predicts** which **affordability tier** (Budget / Moderate / Expensive / Premium) a neighborhood will fall into **2 years from now**, using only its current characteristics (no current rent).
3. **Filters** neighborhoods by what a user can afford using the **30% income rule** (monthly rent ≤ 30% of gross monthly income).
4. **Clusters** neighborhoods by similarity so users can find alternatives (“I like the Annex but can’t afford it — what’s similar but cheaper?”).

### Value Proposition

- **Data as product:** 15 years of curated, neighborhood-level data is valuable for exploration and planning even without a perfect predictive model.
- **Actionable predictions:** Tier classification (not exact dollar amounts) avoids overconfidence and supports planning (“this area may stay Moderate or move to Expensive”).
- **Transparency:** We expose confidence scores and make the 30% rule and tier definitions explicit so users can interpret results.

---

## 2. Design Philosophy

### Pivot: From Regression to Classification

The original goal was to **predict exact rental dollar amounts** (e.g. “$2,400 in 5 years”) using XGBoost regression. After several training iterations we found:

- **Data leakage:** Current rent and lagged rent almost perfectly predict future rent. The model learned to “copy current rent and add a bit” and ignored neighborhood characteristics.
- **Static features:** Crime, transit, and parks were proxied from 2024 to all years, so they act as neighborhood identity, not as signals of change over time.
- **Ceiling effect:** Regression achieved high R² on training data but failed to generalize on held-out time periods.

**Design decision:** We **pivoted to classification**. We predict which **quartile-based tier** (1–4) a neighborhood will be in 2 years from now, using **no rent-related features**. This:

- Removes leakage (the model never sees current rent).
- Focuses the question on: “Do neighborhood characteristics (safety, transit, parks, density) predict affordability tier?”
- Uses a **2-year horizon** so we can use 2020–2022 as test data (we have labels at year+2), nearly doubling usable training data vs. a 5-year target.

### Principles

- **Reproducibility:** Critical data and model steps run as scripts (`rebuild_dataset.py`, `train_tier_classifier.py`), not only notebooks.
- **Temporal validity:** Train/test split is **time-based** (train on 2010–2019, test on 2020–2022) so we never train on the future.
- **Leak-free features:** Current rent (`avg_rent_1br`) is deliberately excluded from the tier classifier; it is used only for labeling, filtering affordable neighborhoods, and display.

---

## 3. Data Methods

### 3.1 Data Sources

| Source | Content | Use |
|--------|---------|-----|
| **TREB Rental Reports** | Average lease rates by area (1BR, 2BR, etc.) | Rent targets and tier labels |
| **Toronto Open Data** | Neighborhood boundaries (GeoJSON), parks, crime | Geometry, green space, safety |
| **TTC GTFS** | Stops, routes, frequencies | Transit accessibility |
| **Census / StatCan** | Population | Density and demographics |

### 3.2 Pipeline Overview

Data flows in three stages:

1. **Per-year ETL (`pipelines/`)**  
   For each year (2010–2024), a DuckDB-based pipeline (with spatial extensions) joins:
   - Neighborhood boundaries, crime, transit stops/routes, parks, and TREB-extracted rents  
   into one CSV per year (158 rows × many columns).  
   **Why DuckDB:** Spatial joins (point-in-polygon, etc.) without a separate PostGIS server; runs in notebooks or scripts.

2. **Master dataset assembly (`data/master_dataset_pipeline.ipynb`)**  
   - Stacks all year-CSVs into a single longitudinal dataset.  
   - Standardizes column names (e.g. strips year suffixes).  
   - Engineers rent features (e.g. averages where quarterly data exists).  
   - Proxies static features (transit, parks, area) from 2024 backward where needed.  
   - Adds temporal features (lags, growth rates).  
   - Output: `toronto_master_2010_2024.csv` (≈2,528 rows × 95 columns).

3. **ML-ready rebuild (`data/rebuild_dataset.py`)**  
   - **Deduplication:** Removes duplicate (AREA_NAME, YEAR) rows (e.g. 2017 had 317 rows).  
   - **Population:** Proxies missing/zero population with 2024 values where needed.  
   - **Targets:** Computes `TARGET_RENT_2YR` (rent at year+2) and quartile-based `RENT_TIER` (current) and `TARGET_TIER_2YR` (tier at year+2).  
   - **Column selection:** Keeps 21 columns; drops leaky, redundant, or unused columns.  
   - **Imputation:** Replaces zeros in crime rates with NaN, then fills with **training-set median only** (no test-set leakage).  
   - **Split:** Time-based train (2010–2019 → `train_v2.csv`) and test (2020–2022 → `test_v2.csv`).  
   - **Snapshot:** Exports `neighborhoods_2024.csv` (158 rows + geometry) for the explorer and map.

### 3.3 Feature Definitions (Tier Model)

**Base numeric (14):**  
Geography: `area_sq_meters`, `perimeter_meters`.  
Crime: `ASSAULT_RATE`, `AUTOTHEFT_RATE`, `ROBBERY_RATE`, `THEFTOVER_RATE`.  
Transit: `total_stop_count`, `avg_stop_frequency`, `max_stop_frequency`, `total_line_length_meters`, `transit_line_density`, `distinct_route_count`.  
Green: `park_count`.  
Demographics: `POPULATION`.

**Engineered (6):**  
- `park_density` = park_count / area_sq_meters  
- `pop_density` = POPULATION / area_sq_meters  
- `transit_per_capita` = total_stop_count / POPULATION  
- `total_crime_rate` = sum of the four crime rates  
- `compactness` = perimeter² / area_sq_meters  
- `routes_per_stop` = distinct_route_count / total_stop_count  

**Categorical (1):** `CLASSIFICATION_CODE` (e.g. Central/East/West region), label-encoded.

**Excluded by design:** `avg_rent_1br` (current rent). Including it would leak the target.

### 3.4 Target Definition

- **Tiers** are **quartile-based within each year:** bottom 25% of 1BR rent = Budget (1), next 25% = Moderate (2), then Expensive (3), top 25% = Premium (4).  
  This keeps tiers comparable across years despite inflation.  
- **Label:** `TARGET_TIER_2YR` = tier of that neighborhood at (current year + 2).  
- Rows without a valid 2-year-ahead rent (e.g. 2023–2024) are dropped from train/test.

---

## 4. Machine Learning Methods

### 4.1 Tier Classifier

**Task:** Multi-class classification with 4 classes (Budget / Moderate / Expensive / Premium).  
**Input:** 21 features (14 base + 6 engineered + 1 categorical).  
**Output:** Predicted tier 1–4 and, for the API, a confidence (class probability).

**Training:**

- **Algorithms:** XGBoost and Random Forest both trained with fixed seeds; best model selected by **macro F1** on the test set (2020–2022).
- **XGBoost:** `multi:softprob`, 4 classes, depth 4, 500 estimators, learning rate 0.03, L1/L2 regularization, label set 0–3 (internally).
- **Random Forest:** 500 trees, max depth 10, min_samples_leaf 5, `class_weight='balanced'` to handle tier imbalance.

**Evaluation:**

- **Primary metrics:** Accuracy and macro F1 (each tier weighted equally).
- **Artifacts:** Confusion matrix, per-tier precision/recall.  
  In practice, **Random Forest** was selected (e.g. ~64.8% accuracy, ~0.65 macro F1); most errors are between adjacent tiers.

**Inference:**

- The same 6 engineered features are computed at prediction time (in `backend/app/services/model.py`) so that the API and training pipeline stay aligned.
- Model bundle and label encoder are loaded once and cached; predictions for all 158 neighborhoods are precomputed and served from a lookup for speed.

### 4.2 Neighborhood Clustering

**Goal:** Group the 158 neighborhoods (2024 snapshot) into interpretable clusters for “find similar neighborhoods.”

**Method:**

- **Features:** 20 variables (14 base + 6 engineered ratios), same as above except no categorical (K-Means is numeric).
- **Preprocessing:** StandardScaler (z-score) fitted on the 2024 snapshot.
- **Algorithm:** K-Means with k=7, n_init=20, fixed seed.  
  k was chosen by scanning k=3..12 and balancing silhouette score and cluster sizes (avoid single-neighborhood clusters and one huge catch-all).
- **Labels:** Centroids are interpreted (e.g. high transit + high connectivity → “Frequent-Service Corridor”) and human-readable cluster names are stored.
- **Outputs:** `cluster_assignments.csv` (AREA_NAME, cluster_id, cluster_label), `scaler.pkl` for clustering features.

---

## 5. Application Design

### 5.1 Backend (FastAPI)

- **Role:** REST API that serves neighborhoods, predictions, affordability, history, and map data. No database required for core flows; data is read from CSVs and model artifacts.
- **Endpoints:**
  - `GET /api/neighbourhoods` — list of 158 neighborhoods.
  - `GET /api/neighbourhood/{name}` — profile, cluster, and tier prediction for one neighborhood.
  - `GET /api/neighbourhood/{name}/history` — historical 1BR rent by year.
  - `POST /api/predict` — tier prediction for a given neighborhood name (uses same precomputed lookup).
  - `GET /api/clusters` — cluster definitions and member neighborhoods.
  - `GET /api/map-data` — neighborhoods with geometry, rent, cluster, and prediction for the map.
  - `GET /api/affordable?income=<float>` — neighborhoods where current `avg_rent_1br` ≤ 30% of annual income / 12.

**Affordability rule:** 30% of gross annual income per month as maximum rent; comparison is against current 1BR average rent.

### 5.2 Frontend (Streamlit)

- **Role:** Single-page explorer: map (Folium), filters, neighborhood detail, affordability by income, and similar neighborhoods via clusters.
- **Data flow:** Frontend calls backend over HTTP; backend uses `model.py` (and CSVs) to compute or look up all responses.
- **UX:** User can enter income, select a neighborhood, see predicted tier and confidence, view history and cluster, and get a list of affordable neighborhoods and map data.

### 5.3 Integration

- Backend loads the tier classifier and label encoder at startup (or first use) and keeps them in memory.
- Predictions for all 158 neighborhoods are built once and served from an in-memory lookup for low latency.
- Same feature engineering (including the 6 ratios) is applied in both training (`train_tier_classifier.py`) and serving (`model.py`) so inputs are consistent.

---

## 6. Key Design Decisions (Summary)

| Decision | Rationale |
|----------|-----------|
| **Predict tier, not dollar amount** | Avoids leakage from current/lagged rent; answers “do characteristics predict affordability?” |
| **2-year horizon** | Enables use of 2020–2022 as test data; more training and test samples than 5-year. |
| **Quartile tiers per year** | Handles inflation; no fixed dollar thresholds to maintain. |
| **Exclude current rent from features** | Prevents “current tier ≈ future tier” shortcut; forces use of neighborhood traits. |
| **Time-based train/test split** | Respects temporal order; no future information in training. |
| **Train-set-only imputation** | Median for crime (and any other imputation) from train only to avoid test leakage. |
| **Proxy static features from 2024** | Pragmatic; historical transit/parks not available in clean form; they act as identity. |
| **Scripts for rebuild and training** | Reproducible, versionable runs independent of notebook order. |
| **Precomputed predictions** | Fast API responses; 158 neighborhoods small enough to hold in memory. |

---

## 7. Artifacts & Reproducibility

- **Data:** `data/processed_data/train_v2.csv`, `test_v2.csv`, `neighborhoods_2024.csv`, `cluster_assignments.csv`, `toronto_master_2010_2024.csv`.
- **Models:** `models/tier_classifier.pkl`, `models/label_encoder.pkl`, `models/scaler.pkl`.
- **Regeneration:**  
  - Clean datasets: `python3 data/rebuild_dataset.py` (from project root).  
  - Tier classifier + clustering: `python3 models/train_tier_classifier.py` (from project root).

For more on code layout and data flow, see **ARCHITECTURE.md**. For environment and run instructions, see **README.md** and **PYTHON.md**.
