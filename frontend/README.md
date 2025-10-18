Steps to set up Streamlit frontend:

# 1. Clone the repo in your desktop
git clone https://github.com/Western-Artificial-Intelligence/condo-cost-predictor.git
cd condo-cost-predictor

# 2. Navigate to the frontend folder
cd frontend

# 3. Create a virtual environment
python3 -m venv venv

source venv/bin/activate    (for Mac)

venv\Scripts\activate       (for Windows)

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the Streamlit website
streamlit run app.py
