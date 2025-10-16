 🏙️ Toronto Condo Affordability Predictor

A spatio-temporal machine learning system that predicts neighborhood-level condo prices and helps users plan down payments based on income and savings

---

## 📘 Overview

Housing affordability is a major challenge for students and young adults in Toronto.  
This project uses open municipal and federal datasets to:

1. **Predict condo prices** across Toronto neighborhoods using machine learning (LightGBM/XGBoost).  
2. **Estimate affordability timelines** for users based on their income and savings rate.  
3. **Visualize attainable neighborhoods** through an interactive web application.

---

## 🧠 Core Features

- 🗺️ Spatio-temporal price forecasting  
- 💰 Personalized affordability and down-payment planner  
- 📊 Interactive map with attainable neighborhoods  
- 📦 Fully open-data pipeline using PostGIS, CMHC, and Census data  
- ⚙️ Quantile regression for uncertainty estimates  

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| **Backend / ML** | Python, scikit-learn, LightGBM, XGBoost |
| **Database** | PostgreSQL + PostGIS |
| **Frontend** | Streamlit |
| **API Layer** | FastAPI |
| **Visualization** | Plotly, Folium |
| **Version Control** | Git + GitHub |

---

## ⚙️ Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/Western-Artificial-Intelligence/condo-cost-predictor.git
cd condo-cost-predictor


STRCUTURE ONCE WE HAVE ALL SET UP 
condo-cost-predictor/
├── data/                   # Open datasets (CMHC, StatCan, City of Toronto)
├── notebooks/              # Exploratory and model development notebooks
├── src/
│   ├── data_pipeline/      # ETL scripts for data cleaning and joins
│   ├── models/             # Training, validation, and evaluation scripts
│   ├── api/                # FastAPI endpoints
│   └── app/                # Streamlit front-end
├── requirements.txt
├── README.md
└── LICENSE


MAKE SURE YOU DO THIS
- START AN ENV 
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

- DOWNLOAD DEPENDECIES
pip install -r requirements.txt

-after when we have it running we will use
streamlit run app.py



## 🏁 Sprint 1 Summary

**Sprint Duration:** 2 weeks  
**Sprint Goal:** Establish the foundational architecture of the Toronto Condo Affordability Predictor — including data ingestion, baseline modeling, backend setup, and a minimal frontend prototype — to enable end-to-end testing with sample data.

---

### 🎯 Objectives
1. Set up a unified project structure (data, backend, frontend, models, docs).
2. Ingest and clean the first open datasets for Toronto neighbourhoods.
3. Implement a baseline ML model (linear regression) to predict condo prices.
4. Deploy placeholder API endpoints in FastAPI.
5. Build a basic Streamlit interface connected to the API.
6. Document environment setup, data sources, and development workflow.

---

### 👥 Team Responsibilities

| Member | Role | Sprint 1 Focus |
|---------|------|----------------|
| **Thomson** | Data | Set up PostgreSQL + PostGIS, design database schema, ingest and clean datasets (Neighbourhood Profiles, CMHC, Toronto Boundaries), and run exploratory data analysis. |
| **Guojia** | ML  | Develop the baseline linear/ridge regression model on processed data, compute MAE, and save model artifacts. |
| **Ore** | ML E| Support feature preprocessing, explore LightGBM/XGBoost setup, and draft `features_documentation.md`. |
| **Besma** | Backend Developer | Scaffold FastAPI app, implement `/predict` and `/neighbourhoods` endpoints, connect to database, and return mock JSON for testing. |
| **Kevin** | Frontend Developer | Scaffold Streamlit app with user input sidebar, placeholder map view, and test connectivity to FastAPI endpoints. |

---

### 🧩 Deliverables
- ✅ **Database:** PostgreSQL + PostGIS instance with 2 datasets loaded  
- ✅ **ETL Scripts:** `etl_pipeline.ipynb` / `etl_scripts.py`  
- ✅ **Baseline Model:** `baseline_model.ipynb` with MAE results and saved artifact  
- ✅ **Backend:** FastAPI server running locally with sample routes  
- ✅ **Frontend:** Streamlit interface displaying API response  
- ✅ **Documentation:** Updated `README.md` and `/docs/feature_schema.md`

---

### 🧠 Next Steps for Sprint 2
- Expand dataset coverage (crime rates, transit GTFS, building permits).  
- Implement full LightGBM/XGBoost model with time-aware cross-validation.  
- Establish integration between API and trained model.  
- Add first visualization components (affordability map + neighbourhood filters).  



