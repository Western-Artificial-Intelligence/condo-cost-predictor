Here's a short setup guide for this project:

---

## Quick setup guide

### 1. Create and activate a virtual environment

```bash
cd /Users/juangomez/Documents/other\ SWE\ projecs/condo-cost-predictor

# Create venv (if you don't have one yet)
python3 -m venv env

# Activate it
source env/bin/activate   # macOS/Linux
# env\Scripts\activate   # Windows
```

You already have an `env` folder, so you can skip creation and just run `source env/bin/activate`.

---

### 2. Install requirements

**Backend (root requirements):**

```bash
pip install -r requirements.txt
```

**Frontend (optional, if you want a minimal install):**

```bash
pip install -r frontend/requirements.txt
```

The root `requirements.txt` already includes FastAPI, uvicorn, Streamlit, etc., so installing it once is enough for both backend and frontend.

---

### 3. Environment variables

```bash
cp .env.example .env
# Edit .env with your DB credentials and API settings
```

---

### 4. Run backend and frontend

**Terminal 1 – backend (FastAPI):**

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 – frontend (Streamlit):**

```bash
cd frontend
streamlit run app.py
```

---

### 5. URLs

| Service  | URL                    |
|----------|------------------------|
| Backend  | http://127.0.0.1:8000  |
| Frontend | http://localhost:8501   |

---

**Summary:** One venv, one `pip install -r requirements.txt`, then run backend and frontend in separate terminals. Start the backend before the frontend.