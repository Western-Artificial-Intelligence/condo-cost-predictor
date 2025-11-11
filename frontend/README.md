

how to run the backend and frontend together:

1. clone the repo
git clone https://github.com/Western-Artificial-Intelligence/condo-cost-predictor.git
cd condo-cost-predictor





2. run backend after downloading necessary packages below
cd backend
uvicorn app.main:app --reload --port 8000

make sure you have these files installed (pip install):
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-dotenv
requests
pandas
numpy






3. run frontend after downloading necessary packages below
open another terminal (command + T)
cd ../frontend
streamlit run app.py

make sure you have these files installed (pip install):
streamlit
requests
pandas
numpy





4. open browser to see the backend and frontend connected
http://localhost:8501

------------------------------------------------------
key features:
- shows live neighborhood data from backend
- displays demo line chart for condo price trends
- lets users enter details for price prediction
- includes loader and error handling
- ready for future machine learning updates

------------------------------------------------------
notes:
- backend must be running before the streamlit frontend
- frontend default port: 8501
- chart data is currently demo-only until ml predictions are added
- future updates will include affordability zones and real housing data
