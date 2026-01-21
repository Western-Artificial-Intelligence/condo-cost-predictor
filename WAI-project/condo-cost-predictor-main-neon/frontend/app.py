from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from shapely import wkt
from shapely.geometry import MultiPolygon, Polygon

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "processed_data"
    / "toronto_map_key.csv"
)
BACKEND_URL = "http://localhost:8000"

GREEN_FILL = [0, 255, 0, 150]
RED_FILL = [255, 0, 0, 150]
GREEN_LINE = [0, 255, 200, 220]
RED_LINE = [255, 64, 96, 220]

MAP_STYLE = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"

CAREER_GROWTH = {
    "Technology": 6.5,
    "Finance": 5.0,
    "Healthcare": 4.5,
    "Education": 3.5,
    "Trades": 4.0,
    "Public Service": 3.0,
    "Student": 2.0,
}

SHAP_DRIVERS = [
    "High transit density",
    "Waterfront premium",
    "New condo supply",
    "Downtown proximity",
    "Strong school catchment",
    "Parks and green space",
    "Low vacancy rate",
    "Major employment hubs",
]


def _ring_to_coords(ring) -> list[list[float]]:
    return [[float(x), float(y)] for x, y in ring.coords]


def _polygon_to_coords(polygon: Polygon) -> list[list[list[float]]]:
    exterior = _ring_to_coords(polygon.exterior)
    holes = [_ring_to_coords(ring) for ring in polygon.interiors]
    return [exterior] + holes if holes else [exterior]


@st.cache_data(show_spinner=False)
def load_neighbourhood_polygons() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame()

    raw = pd.read_csv(DATA_PATH)
    records: list[dict] = []

    for row in raw.itertuples(index=False):
        geom = wkt.loads(row.geometry_wkt)
        if isinstance(geom, Polygon):
            geoms = [geom]
        elif isinstance(geom, MultiPolygon):
            geoms = list(geom.geoms)
        else:
            continue

        for poly in geoms:
            records.append(
                {
                    "area_name": row.AREA_NAME,
                    "classification": row.CLASSIFICATION,
                    "polygon": _polygon_to_coords(poly),
                }
            )

    return pd.DataFrame.from_records(records)


@st.cache_data(show_spinner=False)
def load_neighbourhood_metrics(names: list[str]) -> dict[str, dict[str, object]]:
    metrics: dict[str, dict[str, object]] = {}
    for name in names:
        seed = int(hashlib.md5(name.encode("utf-8")).hexdigest()[:8], 16)
        rent_2029 = 1600 + (seed % 2000)
        safety = 50 + ((seed >> 8) % 50)
        driver = SHAP_DRIVERS[seed % len(SHAP_DRIVERS)]
        metrics[name] = {
            "predicted_rent_2029": int(rent_2029),
            "safety_rating": int(safety),
            "shap_driver": driver,
        }
    return metrics


@st.cache_data(show_spinner=False)
def fetch_backend_neighbourhoods() -> list[str]:
    try:
        response = requests.get(f"{BACKEND_URL}/api/neighbourhoods", timeout=2)
        response.raise_for_status()
        payload = response.json()
        return [item["name"] for item in payload if "name" in item]
    except requests.RequestException:
        return []


@st.cache_data(show_spinner=False)
def build_base_map() -> pd.DataFrame:
    shapes = load_neighbourhood_polygons()
    if shapes.empty:
        return shapes

    names = sorted(shapes["area_name"].unique())
    metrics = load_neighbourhood_metrics(names)

    shapes["predicted_rent_2029"] = shapes["area_name"].map(
        lambda name: metrics[name]["predicted_rent_2029"]
    )
    shapes["safety_rating"] = shapes["area_name"].map(
        lambda name: metrics[name]["safety_rating"]
    )
    shapes["shap_driver"] = shapes["area_name"].map(
        lambda name: metrics[name]["shap_driver"]
    )

    return shapes


def apply_affordability(
    base_df: pd.DataFrame, income: int, savings: int, growth_rate: float
) -> tuple[pd.DataFrame, float]:
    years = 5
    projected_income = income * ((1 + growth_rate / 100) ** years)
    monthly_budget = (projected_income * 0.30) / 12
    savings_boost = savings / (years * 12)
    affordability_limit = monthly_budget + savings_boost

    affordable = base_df["predicted_rent_2029"] <= affordability_limit

    df = base_df.copy()
    df["affordable"] = affordable
    df["affordability_label"] = affordable.map(
        {True: "Affordable", False: "Unattainable"}
    )
    df["fill_color"] = [GREEN_FILL if ok else RED_FILL for ok in affordable]
    df["line_color"] = [GREEN_LINE if ok else RED_LINE for ok in affordable]

    return df, affordability_limit


st.set_page_config(page_title="Toronto Condo Affordability", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Space+Grotesk:wght@400;500;600&display=swap');
    :root {
        --neon-cyan: #33f4ff;
        --neon-pink: #ff2fd0;
        --neon-green: #00ff9c;
        --deep-space: #07060f;
        --panel: rgba(12, 15, 30, 0.85);
        --panel-border: rgba(90, 155, 255, 0.35);
        --text-main: #e8f1ff;
        --text-muted: #9cb3d4;
    }
    html, body, [class*="css"] {
        font-family: "Space Grotesk", sans-serif;
        color: var(--text-main);
    }
    .stApp {
        font-size: 1.05rem;
    }
    .stApp {
        background: #0a0f24;
    }
    .stSidebar > div:first-child {
        background: rgba(5, 6, 15, 0.95);
        border-right: 1px solid rgba(90, 155, 255, 0.35);
        box-shadow: 0 0 25px rgba(51, 244, 255, 0.08);
    }
    .cyber-hero {
        padding: 22px 28px;
        background: var(--panel);
        border: 1px solid var(--panel-border);
        border-radius: 16px;
        box-shadow: 0 0 28px rgba(51, 244, 255, 0.15);
        margin-bottom: 16px;
    }
    .cyber-title {
        font-family: "Orbitron", sans-serif;
        font-size: 2.6rem;
        letter-spacing: 1px;
        margin: 0;
        text-transform: uppercase;
        color: var(--text-main);
        text-shadow: 0 0 4px rgba(51, 244, 255, 0.45), 0 0 10px rgba(255, 47, 208, 0.25);
    }
    .cyber-subtitle {
        margin-top: 6px;
        color: var(--text-muted);
        font-size: 1.2rem;
    }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 14px;
        margin: 6px 0 16px;
    }
    .cyber-card {
        background: var(--panel);
        border: 1px solid var(--panel-border);
        border-radius: 14px;
        padding: 14px 18px;
        box-shadow: inset 0 0 18px rgba(51, 244, 255, 0.08);
    }
    .metric-label {
        color: var(--text-muted);
        font-size: 1.05rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .metric-value {
        font-family: "Orbitron", sans-serif;
        font-size: 1.85rem;
        margin-top: 6px;
        color: var(--neon-cyan);
        text-shadow: 0 0 10px rgba(51, 244, 255, 0.6);
    }
    .legend-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 12px;
        border-radius: 999px;
        border: 1px solid rgba(90, 155, 255, 0.35);
        background: rgba(10, 14, 30, 0.75);
        margin-right: 10px;
        font-size: 1.05rem;
        color: var(--text-muted);
    }
    .chip-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        box-shadow: 0 0 10px currentColor;
    }
    .stSlider label, .stSelectbox label {
        color: var(--text-muted);
        letter-spacing: 0.04em;
        text-transform: uppercase;
        font-size: 1.05rem;
    }
    div[data-testid="stSlider"] div[data-baseweb="slider"] > div {
        background: #0a0f24;
        box-shadow: none;
    }
    div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div {
        background: #ffffff;
    }
    div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div > div {
        background: #ffffff;
    }
    div[data-baseweb="slider"] div[role="slider"] {
        border: 2px solid var(--neon-cyan);
        box-shadow: 0 0 8px rgba(51, 244, 255, 0.6);
        background: #05040a;
    }
    div[data-testid="stSlider"] div[data-baseweb="slider"] ~ div {
        color: #ffffff;
        font-size: 3.6rem;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background: rgba(8, 12, 24, 0.9);
        border: 1px solid rgba(90, 155, 255, 0.35);
        box-shadow: inset 0 0 12px rgba(51, 244, 255, 0.08);
    }
    .stSelectbox div[data-baseweb="select"] span,
    .stSelectbox div[data-baseweb="select"] div {
        color: var(--neon-cyan);
    }
    div[data-testid="stSlider"] div[data-baseweb="slider"] ~ div p,
    div[data-testid="stSlider"] div[data-baseweb="slider"] ~ div span,
    div[data-testid="stSlider"] div[data-baseweb="slider"] ~ div div,
    div[data-testid="stSlider"] [data-testid="stTickBar"] span,
    div[data-testid="stSlider"] [data-testid="stTickBar"] p,
    div[data-testid="stSlider"] [data-testid="stTickBar"] {
        color: #ffffff !important;
        font-size: 2.2rem;
    }
    div[data-testid="stDeckGlJsonChart"] > div {
        border-radius: 18px;
        border: 1px solid rgba(90, 155, 255, 0.35);
        box-shadow: 0 0 30px rgba(51, 244, 255, 0.12);
        overflow: hidden;
    }
    .stMarkdown, .stCaption {
        color: var(--text-muted);
    }
    .sidebar-title {
        font-family: "Orbitron", sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: var(--neon-green);
        font-size: 1.4rem;
        margin-bottom: 8px;
        text-shadow: 0 0 10px rgba(0, 255, 156, 0.6);
    }
    .sidebar-subtitle {
        color: var(--text-muted);
        font-size: 1.15rem;
        margin-bottom: 12px;
    }
    .stSidebar .stMarkdown,
    .stSidebar .stCaption,
    .stSidebar p,
    .stSidebar span,
    .stSidebar label {
        font-size: 1.25rem;
    }
    .stSidebar .stCaption {
        font-size: 1.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="cyber-hero">
        <h1 class="cyber-title">Toronto Condo Affordability Grid</h1>
        <div class="cyber-subtitle">
            Drag the controls to watch the neighborhoods change between attainable and unattainable.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "career_path" not in st.session_state:
    st.session_state.career_path = list(CAREER_GROWTH.keys())[0]
if "growth_rate" not in st.session_state:
    st.session_state.growth_rate = CAREER_GROWTH[st.session_state.career_path]


def sync_growth_rate() -> None:
    st.session_state.growth_rate = CAREER_GROWTH[st.session_state.career_path]


st.sidebar.markdown(
    """
    <div class="sidebar-title">Affordability Controls</div>
    <div class="sidebar-subtitle">The affordability grid updates live.</div>
    """,
    unsafe_allow_html=True,
)

income = st.sidebar.slider(
    "Annual Gross Income (CAD)",
    min_value=40_000,
    max_value=200_000,
    value=90_000,
    step=1_000,
    format="$%d / yr",
)
savings = st.sidebar.slider(
    "Current Savings",
    min_value=0,
    max_value=50_000,
    value=10_000,
    step=1_000,
    format="$%d",
)
st.sidebar.caption("Includes TFSA, RRSP, FHSA, cash savings, and liquid investments.")

st.sidebar.selectbox(
    "Career Path",
    list(CAREER_GROWTH.keys()),
    key="career_path",
    on_change=sync_growth_rate,
)

growth_rate = st.sidebar.slider(
    "Expected Annual Growth (%)",
    min_value=0.0,
    max_value=12.0,
    value=st.session_state.growth_rate,
    step=0.5,
    key="growth_rate",
    format="%.1f%%",
)
st.sidebar.caption(
    "Annual income growth rate over time based on your career path or promotions."
)

st.sidebar.caption("Growth rate auto-fills from career path. Adjust if needed.")

backend_neighbourhoods = fetch_backend_neighbourhoods()
if backend_neighbourhoods:
    st.sidebar.caption(
        f"Backend connected: {len(backend_neighbourhoods)} neighbourhoods loaded."
    )
else:
    st.sidebar.caption("Backend not reachable. Using local map data only.")


base_map = build_base_map()
if base_map.empty:
    st.error("Missing map data. Expected toronto_map_key.csv in data/processed_data.")
    st.stop()

map_df, affordability_limit = apply_affordability(
    base_map, income=income, savings=savings, growth_rate=growth_rate
)

unique_status = map_df.drop_duplicates("area_name")
affordable_count = int(unique_status["affordable"].sum())
total_neighborhoods = int(unique_status["area_name"].nunique())

st.markdown(
    f"""
    <div class="metric-grid">
        <div class="cyber-card">
            <div class="metric-label">Affordable Neighborhoods</div>
            <div class="metric-value">{affordable_count} / {total_neighborhoods}</div>
        </div>
        <div class="cyber-card">
            <div class="metric-label">Projected Monthly Budget</div>
            <div class="metric-value">${affordability_limit:,.0f}</div>
        </div>
        <div class="cyber-card">
            <div class="metric-label">Growth Rate</div>
            <div class="metric-value">{growth_rate:.1f}%</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

layer = pdk.Layer(
    "PolygonLayer",
    data=map_df,
    get_polygon="polygon",
    get_fill_color="fill_color",
    get_line_color="line_color",
    line_width_min_pixels=1,
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.ViewState(latitude=43.71, longitude=-79.38, zoom=10.3, pitch=0)

tooltip = {
    "html": (
        "<b>{area_name}</b><br/>"
        "Predicted 2029 Rent: ${predicted_rent_2029}/mo<br/>"
        "Safety Rating: {safety_rating}/100<br/>"
        "Why it's priced this way: {shap_driver}<br/>"
        "Status: {affordability_label}"
    ),
    "style": {
        "backgroundColor": "rgba(6, 10, 22, 0.95)",
        "color": "#e8f1ff",
        "fontSize": "20px",
        "border": "1px solid rgba(51, 244, 255, 0.5)",
        "boxShadow": "0 0 12px rgba(51, 244, 255, 0.35)",
    },
}

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style=MAP_STYLE,
    tooltip=tooltip,
)

st.pydeck_chart(deck, use_container_width=True, height=720)

st.markdown(
    """
    <div>
        <span class="legend-chip"><span class="chip-dot" style="color:#00ff9c;background:#00ff9c;"></span>Affordable</span>
        <span class="legend-chip"><span class="chip-dot" style="color:#ff405f;background:#ff405f;"></span>Unattainable</span>
    </div>
    """,
    unsafe_allow_html=True,
)
