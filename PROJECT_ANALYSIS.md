# Toronto Condo Affordability Predictor — Project Analysis

**Date:** February 19, 2026
**Repository:** `Western-Artificial-Intelligence/condo-cost-predictor`
**Contributors:** 8 (Thomson Lam, laura, ore7117, Kevin Liu, lgomezvi, Guojia, besma, kayaba-attribution)
**Total Commits:** 156 across 32 feature branches
**Active Development Period:** December 2025 — February 2026 (~2 months)

---

## 1. Project Goal

Build a **spatio-temporal machine learning system** that predicts neighborhood-level condo **rental prices** across Toronto and helps users (students, young adults) plan affordability timelines. The system combines 15 years of open municipal data (2010–2024) with spatial, socio-economic, and macro-economic features to produce price forecasts with uncertainty estimates via quantile regression.

### Target Users
- Students and young adults in Toronto facing housing affordability challenges.

### Core Value Propositions
1. **Predict condo rent prices** across ~158 Toronto neighborhoods using XGBoost/LightGBM.
2. **Estimate affordability timelines** based on user income, savings rate, and target neighborhood.
3. **Visualize attainable neighborhoods** through an interactive map-based web application.

---

## 2. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                                  │
│  Toronto Open Data (GeoJSON) · TREB Rental Reports (PDF) · CMHC     │
│  TTC GTFS Transit Data · Census / StatCan · Crime Statistics         │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    ETL PIPELINE (DuckDB + Jupyter)                    │
│  pipelines/*.ipynb — Year-specific spatial joins, feature extraction │
│  DuckDB spatial extension for neighborhood/park/transit/crime joins  │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│               MASTER DATASET ASSEMBLY                                │
│  data/master_dataset_pipeline.ipynb                                  │
│  Output: toronto_master_2010_2024.csv (2,529 rows × 95 columns)     │
│  Includes: lag features, growth rates, 5-year forward rent targets   │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    MODEL TRAINING                                     │
│  training/cleaning.ipynb → train.csv / test.csv                      │
│  training/train_1.ipynb, train_2.ipynb, train_3.ipynb (XGBoost)     │
│  models/XGBoost_scaffold.py (quantile regression template)           │
│  3 trained model iterations (.pkl files)                             │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    BACKEND API (FastAPI)                              │
│  POST /api/predict — price prediction (currently mock model)         │
│  GET  /api/neighbourhoods — neighborhood list                        │
│  Optional PostgreSQL via SQLAlchemy (falls back to mock data)        │
└────────────────────────┬─────────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit)                               │
│  User inputs: income, savings rate, neighbourhood, bedrooms, sqft    │
│  Displays: predicted price, demo trend chart                         │
│  Neon-themed UI                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **ML / Training** | XGBoost, scikit-learn, SHAP | Model training, evaluation, explainability |
| **Data Processing** | Pandas, DuckDB, GeoPandas | ETL, spatial joins, feature engineering |
| **Backend API** | FastAPI, Uvicorn | REST API for predictions |
| **Frontend** | Streamlit | Interactive web interface |
| **Database** | PostgreSQL (SQLAlchemy, psycopg2) | Planned persistence layer |
| **Visualization** | Plotly, Folium, Matplotlib, Seaborn | Charts, maps, data exploration |
| **Data Versioning** | DVC (planned) | Dataset tracking |
| **Dev Tools** | Jupyter, pytest, black, flake8 | Notebooks, testing, formatting |

---

## 4. Data Pipeline

### 4.1 Raw Data Sources (15 years: 2010–2024)
- **15 CSV files** in `data/raw_data/` — one per year
- **158 Toronto neighborhoods** classified into regions: Central (C01–C15), East (E01–E11), West (W01–W10)
- **Sources:** Toronto Open Data (GeoJSON boundaries, parks, crime stats), TREB rental market reports (PDF → extracted tables), TTC GTFS transit feeds

### 4.2 Feature Categories (~95 columns in master dataset)

| Category | Features | Source |
|----------|----------|--------|
| **Spatial** | `AREA_NAME`, `geometry_wkt`, `area_sq_meters`, `perimeter_meters` | Toronto Open Data GeoJSON |
| **Crime** | `ASSAULT_RATE`, `ROBBERY_RATE`, `SHOOTING_RATE`, `BREAKENTER_RATE`, `THEFT_RATE` (per year) | Toronto Police |
| **Transit** | `total_stop_count`, `avg_stop_frequency`, `transit_line_density`, `distinct_route_count` | TTC GTFS |
| **Green Space** | `park_count` | Toronto Parks GeoJSON |
| **Demographics** | `POPULATION` (per year) | Census / StatCan |
| **Rental Targets** | `bachelor_avg_lease_rate`, `1_bed_room_avg_lease_rate`, `2_bedrooms_avg_lease_rate`, `3_bedrooms_avg_lease_rate` | TREB Reports |
| **Temporal** | Lag features (1yr, 2yr, 3yr), growth rates, `TARGET_RENT_5YR` (5-year forward) | Derived |

### 4.3 Known Data Quality Issues
- **2010–2013:** Missing crime rate data — backfilled using rate coefficients derived from later years
- **2010–2013:** Missing population data — backfilled with defined rates
- **Some neighborhoods:** Zero values in target rental variables (TREB data gaps)
- **Data sparsity:** Analyzed and documented in `training/data_sparsity_heatmap.png`

---

## 5. Model Training Status

### 5.1 Training Iterations

| Iteration | File | Description | Status |
|-----------|------|-------------|--------|
| **Model 1** | `training/train_1.ipynb` → `xgb_model_1.pkl` | Baseline XGBoost | Trained, high MAE |
| **Model 2** | `training/train_2.ipynb` → `xgb_model_2.pkl` | Fine-tuned features | Trained |
| **Model 3** | `training/train_3.ipynb` → `xgb_model_3.pkl` | Constrained XGBoost | Trained |

### 5.2 Model Architecture (from scaffold)
- **Algorithm:** XGBoost with quantile regression (τ = 0.1, 0.5, 0.9)
- **Planned features:** lat, lon, distance_to_ttc, median_income, population_density, housing_starts_3m_lag, price_index_yoy, unemployment_rate
- **Explainability:** SHAP values implemented
- **Grid search:** Code added for hyperparameter tuning

### 5.3 Gap: Model ↔ Backend Integration
The backend currently uses a **mock linear model** (`base + sqft*900 + bedrooms*75000 + bathrooms*50000`). The three trained `.pkl` models exist in `training/models/` but are **not loaded or served** by the FastAPI backend.

---

## 6. Component Status Summary

### Fully Implemented
| Component | Details |
|-----------|---------|
| Raw data collection | 15 years of CSVs (2010–2024) |
| ETL pipelines | DuckDB-based spatial joins per year |
| Master dataset | 2,529 rows × 95 columns |
| Data cleaning | Missing data analysis, imputation strategies |
| FastAPI backend | Endpoints, CORS, schemas, OpenAPI docs |
| Streamlit frontend | Input forms, prediction display, neon theme |
| XGBoost training | 3 model iterations with SHAP |
| Feature documentation | Spatial, socio-economic, supply, temporal categories |
| Contribution guidelines | Branch naming, PR workflow |

### Partially Implemented
| Component | What's Done | What's Missing |
|-----------|-------------|----------------|
| ML model | 3 trained .pkl files | Not integrated into backend API |
| Quantile regression | Scaffold code exists | Not trained or served |
| Database | SQLAlchemy models, config | PostgreSQL not set up, using mocks |
| Data backfilling | Crime/population rates for 2010–2013 | Validation of backfilled values |
| Frontend charts | Demo random data chart | Real ML prediction trends |

### Not Implemented
| Component | Priority |
|-----------|----------|
| Model serving (load .pkl in backend) | **Critical** |
| Quantile regression (uncertainty bands) | High |
| Interactive map (Folium) | High |
| Affordability timeline calculator | High |
| PostgreSQL database setup | Medium |
| Docker / containerization | Medium |
| CI/CD (GitHub Actions) | Medium |
| Automated tests | Medium |
| DVC data versioning | Low |
| User authentication | Low |

---

## 7. Development Timeline

```
Dec 2025    ████████░░░░  Data collection & pipeline creation
            - Raw CSVs for 2010-2024 assembled
            - DuckDB ETL pipelines per year
            - Neighborhood classification scripts

Jan 2026    ████████████  Master dataset + first training
 (early)    - Master dataset assembled (2,529 rows)
            - Data cleaning & missing data analysis
            - Imputation strategies planned
 (mid)      - First XGBoost training iteration (high MAE)
            - Training requirements & README
            - Frontend neon theme (Kevin)
 (late)     - Grid search code added
            - Feature fine-tuning

Feb 2026    ████████░░░░  Model refinement + data fixes
 (week 1)   - 3 XGBoost iterations trained
            - SHAP explainability added
            - Constrained XGBoost (iter 3)
            - Crime rate backfilling (2010-2013)
 (week 2-3) - Population rate backfilling
            - Backfilling applied to cleaning pipeline
```

---

## 8. Team & Contributions

| Contributor | Commits | Primary Role |
|-------------|---------|-------------|
| Thomson Lam | 40 | Model training, data cleaning, SHAP analysis |
| laura | 32 | Project management, merges, PR reviews |
| ore7117 | 29 | Training iterations, grid search, data backfilling |
| Kevin Liu | 24 | Frontend (Streamlit neon theme), README |
| lgomezvi | 15 | Data pipeline, master dataset, rate fixes |
| Guojia | 9 | Feature documentation, early pipeline work |
| besma | 4 | Backend (FastAPI) implementation |
| kayaba-attribution | 2 | Minor contributions |

---

## 9. Key Risks & Blockers

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Model not integrated into API** | App shows fake predictions | Load trained .pkl in `backend/app/services/model.py` |
| **High MAE in initial models** | Predictions unreliable | Constrained XGBoost (iter 3) may improve; needs evaluation metrics |
| **Data gaps (2010–2013)** | Backfilled data may introduce bias | Validate backfilling coefficients against known benchmarks |
| **No automated tests** | Regressions go undetected | Add pytest suite for API, model, and data pipeline |
| **No CI/CD** | Manual deployment, no quality gates | Set up GitHub Actions |
| **No Docker** | Environment inconsistency across team | Create Dockerfiles for backend + frontend |
| **README outdated** | Structure section doesn't match actual repo | Update to reflect current directory layout |

---

## 10. Recommendations (Prioritized)

### Phase 1 — Ship a Working Prediction (Critical Path)
1. **Integrate trained model into backend** — Load `xgb_model_3.pkl` in `model.py`, replace mock formula
2. **Evaluate model performance** — Document MAE, RMSE, R² on test set; decide if model quality is sufficient
3. **Connect frontend to real predictions** — Replace demo chart with actual model output
4. **Update README** — Reflect actual project structure and setup instructions

### Phase 2 — Production Readiness
5. **Implement quantile regression** — Train τ=0.1, 0.5, 0.9 models for uncertainty bands
6. **Add affordability timeline** — Core feature from project goals, not yet built
7. **Interactive Folium map** — Visualize attainable neighborhoods on a map
8. **Docker containerization** — Dockerfile for backend + frontend + docker-compose
9. **PostgreSQL setup** — Persist neighborhood data and prediction history

### Phase 3 — Quality & Operations
10. **Automated tests** — API endpoint tests, model inference tests, data validation
11. **CI/CD pipeline** — GitHub Actions for lint, test, build
12. **DVC for data versioning** — Track dataset changes alongside code
13. **Model versioning** — Track which model version is serving predictions
14. **Monitoring & logging** — Track prediction latency, error rates, data drift

---

## 11. File Inventory

### Source Code
| Path | Type | Lines | Purpose |
|------|------|-------|---------|
| `backend/app/main.py` | Python | ~30 | FastAPI app entry point |
| `backend/app/core/config.py` | Python | ~25 | Settings (Pydantic) |
| `backend/app/models/neighbourhood.py` | Python | ~15 | SQLAlchemy ORM |
| `backend/app/routers/predict.py` | Python | ~20 | Prediction endpoint |
| `backend/app/routers/neighbourhoods.py` | Python | ~30 | Neighbourhood endpoint |
| `backend/app/schemas/models.py` | Python | ~30 | Pydantic schemas |
| `backend/app/services/model.py` | Python | ~15 | Mock model (needs real ML) |
| `backend/app/services/db.py` | Python | ~25 | DB session management |
| `frontend/app.py` | Python | ~100 | Streamlit UI |
| `models/XGBoost_scaffold.py` | Python | ~80 | Quantile regression template |

### Notebooks (24 total)
| Path | Purpose |
|------|---------|
| `data/master_dataset_pipeline.ipynb` | Master dataset assembly |
| `training/cleaning.ipynb` | Data cleaning & imputation |
| `training/train_1.ipynb` | XGBoost iteration 1 |
| `training/train_2.ipynb` | XGBoost iteration 2 |
| `training/train_3.ipynb` | XGBoost iteration 3 (constrained) |
| `pipelines/data-pipeline.ipynb` | Base DuckDB ETL template |
| `pipelines/data-pipeline-2016.ipynb` — `2023.ipynb` | Year-specific ETL |
| `pipelines/extract_content.ipynb` | PDF table extraction (Tabula) |

### Data Files
| Path | Size | Rows | Purpose |
|------|------|------|---------|
| `data/processed_data/toronto_master_2010_2024.csv` | 6.1 MB | 2,529 | Training-ready master dataset |
| `data/processed_data/toronto_map_key.csv` | 1.6 MB | 159 | Neighborhood geometry mapping |
| `data/processed_data/mastersheet.csv` | 782 KB | — | Summary data |
| `training/train.csv` | — | — | Training split |
| `training/test.csv` | — | — | Test split |
| `training/models/xgb_model_1.pkl` | — | — | Trained XGBoost v1 |
| `training/models/xgb_model_2.pkl` | — | — | Trained XGBoost v2 |
| `training/models/xgb_model_3.pkl` | — | — | Trained XGBoost v3 (constrained) |

---

## 12. Conclusion

The Toronto Condo Affordability Predictor has a **solid foundation**: 15 years of curated open data, a working ETL pipeline, three trained XGBoost models, a FastAPI backend, and a Streamlit frontend. The project is the product of an 8-person team working actively over ~2 months.

The **critical gap** is the last mile: connecting the trained models to the API so the app produces real predictions instead of mock values. Once that bridge is built, the core MVP — "enter your details, see predicted rent by neighborhood" — is functional.

Beyond that, the planned features (quantile uncertainty bands, affordability timelines, interactive maps) would elevate the project from a demo to a genuinely useful tool for Toronto renters.
