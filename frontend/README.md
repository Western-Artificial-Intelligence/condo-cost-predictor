

# Sprint 2
# How to run the backend and frontend together:

## 1. clone the repo
git clone https://github.com/Western-Artificial-Intelligence/condo-cost-predictor.git
cd condo-cost-predictor





## 2. run backend after downloading necessary packages below
cd backend
uvicorn app.main:app --reload --port 8000

make sure you have these files installed (pip install):

fastapi

uvicorn

pydantic

pydantic-settings

python-dotenv

requests

pandas

numpy






## 3. run frontend after downloading necessary packages below
open another terminal (command + T)
cd ../frontend
streamlit run app.py

make sure you have these files installed (pip install):

streamlit

requests

pandas

numpy





## 4. open browser to see the backend and frontend connected
http://localhost:8501

### This updated frontend folder fulfills these tasks from sprint2:
<img width="647" height="470" alt="Screen Shot 2025-11-11 at 5 31 51 PM" src="https://github.com/user-attachments/assets/c24583fb-d5b4-4213-9c9c-90146247dceb" />


### notes:
- backend must be running before the streamlit frontend runs
- frontend default port: 8501
- line chart shows the demo data of the predicted condo prices for the current year from Jan to Dec, since the census is only conducted every 5 years (2021, 2016, 2011...), and real ML predicted data will be added later

- Figma mockup using Figma AI:
- https://melon-speak-50866905.figma.site/


### screenshot of what you see after running backend + frontend:
<img width="1122" height="613" alt="Screen Shot 2025-11-11 at 5 27 43 PM" src="https://github.com/user-attachments/assets/14b06a38-26c8-4b68-895e-8e9f6c17f944" />

