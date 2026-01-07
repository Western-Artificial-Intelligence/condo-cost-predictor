 🏙️ Toronto Condo Affordability Predictor

A spatio-temporal machine learning system that predicts neighborhood-level condo prices and helps users plan down savings and rent affordability 

---

## 📘 Overview

Housing affordability is a major challenge for students and young adults in Toronto.  
This project uses open municipal and federal datasets to:

1. **Predict condo rent prices** across Toronto neighborhoods using machine learning (LightGBM/XGBoost).  
2. **Estimate affordability timelines** for users based on their income and other metrics.  
3. **Visualize attainable neighborhoods** through an interactive web application.

---

## 🧠 Core Features

- 🗺️ Spatio-temporal price forecasting  
- 💰 Personalized affordability 
- 📊 Interactive map with attainable neighborhoods  
- 📦 Fully open-data pipeline using CMHC, and Census data  
- ⚙️ Quantile regression for uncertainty estimates  

---

## 🧰 Tech Stack

| Component | Technology |
|------------|-------------|
| **Backend / ML** | Python, scikit-learn, XGBoost |
| **Database** | DuckBD, dvc |
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



