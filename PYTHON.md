# Running Python in This Project


# its probably alr activated examples:

source "/Users/juangomez/Documents/other SWE projecs/condo-cost-predictor/.venv/bin/activate" && python3 -c

source "/Users/juangomez/Documents/other SWE projecs/condo-cost-predictor/.venv/bin/activate" && python3 "/Users/juangomez/Documents/other SWE projecs/condo-cost-predictor/data/rebuild_dataset.py"

## Virtual Environment

Create and activate a venv from the project root:

```bash
# Create venv
python3 -m venv .venv

# Activate (macOS/Linux)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate
```

**Note:** The `env/` folder has broken symlinks (points to another dev's pyenv). Use a fresh `.venv` instead.

## Install Dependencies

```bash
pip install -r requirements.txt
```

If you hit SSL certificate errors:

```bash
pip install -r requirements.txt --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org
```

## Run Scripts

From the project root:

```bash
# Data rebuild (outputs train_v2.csv, test_v2.csv, neighborhoods_2024.csv)
python3 data/rebuild_dataset.py

# Backend API (from project root)
uvicorn backend.app.main:app --reload

# Frontend
cd frontend && streamlit run app.py
```

## Minimal Setup (Data Pipeline Only)

For just the data rebuild script (pandas + numpy):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy
python3 data/rebuild_dataset.py
```
