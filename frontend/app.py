import streamlit as st
import requests
import pandas as pd
import numpy as np

#page setup and layout
st.set_page_config(page_title="Condo Cost Predictor", layout="wide")
st.title("toronto condo cost predictor")

#backend server address
BACKEND_URL = "http://localhost:8000"

#helper functions
@st.cache_data
def fetch_neighbourhoods():
    #tries to get list of neighborhoods from the backend
    try:
        response = requests.get(f"{BACKEND_URL}/api/neighbourhoods")
        response.raise_for_status()
        return response.json()
    #shows error if the backend request fails
    except requests.RequestException as e:
        st.error(f"error fetching neighborhoods: {e}")
        return []

#sends condo info to backend to get price prediction
def predict_price(data):
    try:
        response = requests.post(f"{BACKEND_URL}/api/predict", json=data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        st.error(f"error fetching prediction: {e}")
        return None

#sidebar user inputs
st.sidebar.header("user inputs")

income = st.sidebar.number_input("annual income ($ cad)", min_value=0, step=1000)
savings_rate = st.sidebar.slider("savings rate (%)", 0, 100, 20)

#fetch neighborhoods from backend and show loading spinner
with st.spinner("loading neighborhoods..."):
    neighborhoods = fetch_neighbourhoods()

#if neighborhoods are available, show them in dropdown
if neighborhoods:
    neighborhood_names = [n["name"] for n in neighborhoods]
    selected_neighborhood = st.sidebar.selectbox("select neighborhood", neighborhood_names)
else:
    st.warning("no neighborhoods available.")
    selected_neighborhood = ""

#basic condo info for prediction
bedrooms = st.sidebar.number_input("bedrooms", min_value=0, step=1)
bathrooms = st.sidebar.number_input("bathrooms", min_value=0, step=1)
sqft = st.sidebar.number_input("square footage", min_value=0, step=50)
year = st.sidebar.number_input("year built", min_value=1900, step=1, value=2025)

#predicted price section
st.subheader("predicted condo price")
if st.button("predict price"):
    if selected_neighborhood:
        #shows spinner while waiting for prediction
        with st.spinner("calculating prediction..."):
            data = {
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "sqft": sqft,
                "neighbourhood": selected_neighborhood,
                "year": year
            }
            result = predict_price(data)
            if result:
                price = result.get("predicted_price", 0)
                currency = result.get("currency", "CAD")
                model = result.get("model", "baseline")
                st.success(f"predicted price: {currency} {price:,.0f} (model: {model})")
    else:
        st.warning("please select a neighborhood.")

#demo chart to show fake condo price trends
st.subheader("average condo price trends (demo)")
if selected_neighborhood:
    #makes random monthly price data for one year
    dates = pd.date_range(start="2023-01-01", periods=12, freq="M")
    prices = np.linspace(700_000, 850_000, 12) + np.random.randint(-10_000, 10_000, size=12)
    trend_df = pd.DataFrame({"date": dates, "price": prices})
    trend_df.set_index("date", inplace=True)
    st.line_chart(trend_df)
else:
    st.info("select a neighborhood to view price trends.")

#placeholder for future ai prediction features
st.subheader("future features")
st.info("ml predictions and live price trends will appear here once backend supports them.")

#shows back all the inputs user entered
st.subheader("your inputs")
st.write(f"annual income: ${income:,}")
st.write(f"savings rate: {savings_rate}%")
st.write(f"bedrooms: {bedrooms}, bathrooms: {bathrooms}, sqft: {sqft}, year: {year}")
st.write(f"neighborhood: {selected_neighborhood}")
