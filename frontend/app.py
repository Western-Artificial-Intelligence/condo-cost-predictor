#set up scaffolding for the Streamlit frontend, will connect with FastAPI backend eventually
import streamlit as st

st.title("Condo Cost Predictor")

st.sidebar.header("User Inputs")
income = st.sidebar.number_input("Annual Income ($ CAD)", min_value=0, step=1000)
savings_rate = st.sidebar.slider("Savings Rate (%)", 0, 100, 20)

st.subheader("Condo Affordability Map")
st.write("🗺️ Map placeholder will be here")

st.subheader("Affordability Prediction Results")
st.write("📊 Prediction results will be displayed here")
