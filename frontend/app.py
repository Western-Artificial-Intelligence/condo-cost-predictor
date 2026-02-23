import os
import re
from typing import Any
from urllib.parse import quote

import folium
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

try:
    from streamlit_folium import st_folium

    HAS_STREAMLIT_FOLIUM = True
except Exception:
    HAS_STREAMLIT_FOLIUM = False
    st_folium = None


st.set_page_config(page_title="Toronto Rent Explorer", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT_SECONDS = 20

TIER_COLORS = {
    1: "#1B9E77",
    2: "#66A61E",
    3: "#E6AB02",
    4: "#D95F02",
}

CLUSTER_COLORS = {
    0: "#264653",
    1: "#2A9D8F",
    2: "#E9C46A",
    3: "#F4A261",
    4: "#E76F51",
    5: "#457B9D",
    6: "#6A4C93",
}


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg-a: #f6f8fa;
                --bg-b: #e8eff7;
                --card: rgba(255, 255, 255, 0.92);
                --line: rgba(18, 38, 58, 0.18);
                --text: #12263a;
                --muted: #3f5368;
            }
            .stApp {
                background:
                    radial-gradient(circle at 8% 12%, rgba(42,157,143,0.14), transparent 42%),
                    radial-gradient(circle at 95% 20%, rgba(244,162,97,0.14), transparent 40%),
                    linear-gradient(150deg, var(--bg-a), var(--bg-b));
                color: var(--text);
            }
            [data-testid="stSidebar"] {
                background: #111827;
            }
            [data-testid="stSidebar"] * {
                color: #e8edf3 !important;
            }
            .hero {
                border: 1px solid var(--line);
                background: var(--card);
                border-radius: 16px;
                padding: 18px 20px;
                margin-bottom: 12px;
                box-shadow: 0 10px 26px rgba(18,38,58,0.10);
            }
            .hero h1 {
                margin: 0;
                color: var(--text);
                font-family: "Avenir Next", "Trebuchet MS", sans-serif;
                letter-spacing: 0.2px;
                font-size: 2rem;
            }
            .hero p {
                margin: 6px 0 0 0;
                color: var(--muted);
                font-size: 1rem;
            }
            .panel {
                border: 1px solid var(--line);
                background: var(--card);
                border-radius: 14px;
                padding: 12px 14px;
                box-shadow: 0 10px 24px rgba(18,38,58,0.08);
            }
            .panel h1, .panel h2, .panel h3, .panel p, .panel span, .panel strong, .panel label {
                color: var(--text) !important;
            }
            [data-testid="stMetricLabel"] {
                color: #2a3d52 !important;
                font-weight: 600;
            }
            [data-testid="stMetricValue"] {
                color: #12263a !important;
                font-weight: 700;
            }
            [data-testid="stCaptionContainer"] {
                color: #33495f !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _api_get(path: str, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(
        f"{BACKEND_URL}{path}",
        params=params,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


@st.cache_data(show_spinner=False, ttl=300)
def fetch_neighbourhoods() -> list[dict[str, Any]]:
    return _api_get("/api/neighbourhoods")


@st.cache_data(show_spinner=False, ttl=300)
def fetch_map_data() -> list[dict[str, Any]]:
    return _api_get("/api/map-data")


@st.cache_data(show_spinner=False, ttl=300)
def fetch_clusters() -> list[dict[str, Any]]:
    return _api_get("/api/clusters")


@st.cache_data(show_spinner=False, ttl=120)
def fetch_affordable(income: float) -> dict[str, Any]:
    return _api_get("/api/affordable", params={"income": income})


@st.cache_data(show_spinner=False, ttl=120)
def fetch_neighbourhood_detail(name: str) -> dict[str, Any]:
    return _api_get(f"/api/neighbourhood/{quote(name, safe='')}")


@st.cache_data(show_spinner=False, ttl=120)
def fetch_neighbourhood_history(name: str) -> dict[str, Any]:
    return _api_get(f"/api/neighbourhood/{quote(name, safe='')}/history")


def _safe_get_name_list(neighbourhoods: list[dict[str, Any]]) -> list[str]:
    return sorted((row["name"] for row in neighbourhoods), key=lambda value: value.lower())


def _legend_html(color_mode: str, clusters: list[dict[str, Any]]) -> str:
    if color_mode == "Predicted Tier":
        items = [
            ("Tier 1: Budget", TIER_COLORS[1]),
            ("Tier 2: Moderate", TIER_COLORS[2]),
            ("Tier 3: Expensive", TIER_COLORS[3]),
            ("Tier 4: Premium", TIER_COLORS[4]),
        ]
    else:
        items = [
            (
                f"C{cluster['cluster_id']} ({cluster['count']}): {cluster['cluster_label']}",
                CLUSTER_COLORS.get(cluster["cluster_id"], "#999999"),
            )
            for cluster in clusters
        ]

    entries = "".join(
        [
            (
                "<div style='display:flex;align-items:center;margin:2px 0;'>"
                f"<span style='display:inline-block;width:12px;height:12px;background:{color};"
                "border:1px solid rgba(0,0,0,0.35);margin-right:8px;'></span>"
                f"<span style='font-size:12px'>{label}</span></div>"
            )
            for label, color in items
        ]
    )
    return (
        "<div style='position:fixed;bottom:18px;left:18px;z-index:9999;"
        "background:rgba(255,255,255,0.94);padding:9px 11px;border-radius:9px;"
        "border:1px solid rgba(0,0,0,0.25);font-family:Arial,sans-serif;'>"
        f"<div style='font-size:12px;font-weight:700;margin-bottom:5px'>{color_mode}</div>"
        f"{entries}</div>"
    )


def build_map(
    rows: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    color_mode: str,
    selected_neighbourhood: str,
    affordable_names: set[str],
    highlight_affordable: bool,
) -> folium.Map:
    map_obj = folium.Map(
        location=[43.70, -79.38],
        zoom_start=10,
        tiles="CartoDB positron",
        control_scale=True,
    )

    def color_for_row(row: dict[str, Any]) -> str:
        if color_mode == "Predicted Tier":
            return TIER_COLORS.get(int(row["predicted_tier"]), "#999999")
        return CLUSTER_COLORS.get(int(row["cluster_id"]), "#999999")

    draw_rows = sorted(rows, key=lambda item: item["neighbourhood"] != selected_neighbourhood)
    for row in draw_rows:
        geometry = row.get("geometry")
        if not geometry:
            continue

        neighbourhood = row["neighbourhood"]
        is_selected = neighbourhood == selected_neighbourhood
        is_affordable = neighbourhood in affordable_names

        if highlight_affordable and not is_affordable:
            fill_opacity = 0.16
        else:
            fill_opacity = 0.78 if is_selected else 0.52

        style = {
            "fillColor": color_for_row(row),
            "fillOpacity": fill_opacity,
            "color": "#0f172a" if is_selected else "#ffffff",
            "weight": 3 if is_selected else 1.2,
            "opacity": 0.96,
        }
        highlight = {
            "weight": max(style["weight"] + 1, 3),
            "fillOpacity": min(fill_opacity + 0.12, 0.92),
        }

        tooltip = (
            f"<b>{neighbourhood}</b><br>"
            f"Current Avg 1BR: ${row['avg_rent_1br']:.0f}<br>"
            f"Predicted Tier (2yr): {row['tier_label']} ({row['confidence']:.2f})<br>"
            f"Cluster: {row['cluster_label']}"
        )
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {"neighbourhood": neighbourhood},
        }
        folium.GeoJson(
            data=feature,
            style_function=lambda _feature, s=style: s,
            highlight_function=lambda _feature, h=highlight: h,
            tooltip=folium.Tooltip(tooltip, sticky=True),
            popup=folium.Popup(neighbourhood, max_width=260),
        ).add_to(map_obj)

    map_obj.get_root().html.add_child(folium.Element(_legend_html(color_mode, clusters)))
    return map_obj


def _strip_html(raw: str) -> str:
    return re.sub(r"<[^>]+>", "", raw).strip()


def _extract_clicked_neighbourhood(map_event: dict[str, Any] | None) -> str | None:
    if not map_event:
        return None

    popup = map_event.get("last_object_clicked_popup")
    if isinstance(popup, str) and popup.strip():
        text = _strip_html(popup)
        if text:
            return text

    drawing = map_event.get("last_active_drawing")
    if isinstance(drawing, dict):
        props = drawing.get("properties", {})
        if isinstance(props, dict):
            for key in ("neighbourhood", "name", "AREA_NAME"):
                value = props.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

    tooltip = map_event.get("last_object_clicked_tooltip")
    if isinstance(tooltip, str) and tooltip.strip():
        match = re.search(r"<b>(.*?)</b>", tooltip)
        if match:
            return _strip_html(match.group(1))
    return None


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Toronto Rent Explorer</h1>
            <p>Explore 158 neighborhoods by cluster, predicted affordability tier, and 15-year rent history.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_detail_panel(
    selected_neighbourhood: str,
    detail: dict[str, Any],
    history: dict[str, Any],
    map_lookup: dict[str, dict[str, Any]],
    cluster_lookup: dict[int, dict[str, Any]],
    affordable_names: set[str],
) -> None:
    profile = detail["profile"]
    prediction = detail["prediction"]
    cluster_id = detail["cluster_id"]
    cluster_label = detail["cluster_label"]

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.subheader(selected_neighbourhood)
    st.caption(
        f"Cluster {cluster_id}: {cluster_label} | Predicted Tier (2yr): "
        f"{prediction['tier_label']} (confidence {prediction['confidence']:.2f})"
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("Current Avg 1BR Rent", f"${profile['avg_rent_1br']:.0f}")
    c2.metric("Population", f"{int(profile['POPULATION']):,}")
    c3.metric("Parks", f"{int(profile['park_count'])}")

    c4, c5, c6 = st.columns(3)
    c4.metric("Assault Rate", f"{profile['ASSAULT_RATE']:.1f}")
    c5.metric("Transit Stops", f"{int(profile['total_stop_count'])}")
    c6.metric("Distinct Routes", f"{int(profile['distinct_route_count'])}")
    st.markdown("</div>", unsafe_allow_html=True)

    history_df = pd.DataFrame(history["history"])
    if not history_df.empty:
        history_df = history_df.sort_values("year").rename(
            columns={"year": "Year", "avg_rent_1br": "Average 1BR Rent"}
        )
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("**Rent History (2010-2024)**")
        st.line_chart(history_df.set_index("Year"), height=210)
        st.markdown("</div>", unsafe_allow_html=True)

    cluster_data = cluster_lookup.get(cluster_id)
    peers = []
    if cluster_data:
        peers = [n for n in cluster_data["neighbourhoods"] if n != selected_neighbourhood]

    peer_rows: list[dict[str, Any]] = []
    selected_rent = float(profile["avg_rent_1br"])
    for name in peers:
        row = map_lookup.get(name)
        if not row:
            continue
        peer_rows.append(
            {
                "Neighbourhood": name,
                "Current Avg 1BR Rent": float(row["avg_rent_1br"]),
                "Rent Gap vs Selected": float(row["avg_rent_1br"]) - selected_rent,
                "Predicted Tier (2yr)": row["tier_label"],
                "Tier Confidence": round(float(row["confidence"]), 2),
                "Affordable (Current Rule)": name in affordable_names,
            }
        )

    if peer_rows:
        peer_df = pd.DataFrame(peer_rows).sort_values("Current Avg 1BR Rent")
        cheaper_df = peer_df.loc[peer_df["Current Avg 1BR Rent"] < selected_rent].head(8)
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown("**Find Similar Neighborhoods**")
        st.caption(
            "Tier is a 2-year prediction from neighborhood features. "
            "Equal current rents can still have different predicted tiers."
        )
        if not cheaper_df.empty:
            st.caption("Cheaper options in the same cluster")
            st.dataframe(cheaper_df, width="stretch", hide_index=True, height=220)
        else:
            st.caption("No cheaper options found; showing nearest cluster peers by current rent")
            closest = peer_df.iloc[
                (peer_df["Current Avg 1BR Rent"] - selected_rent).abs().argsort()
            ].head(8)
            st.dataframe(closest, width="stretch", hide_index=True, height=220)
        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    _inject_styles()
    _render_header()

    with st.spinner("Loading explorer data..."):
        try:
            neighborhoods = fetch_neighbourhoods()
            map_rows = fetch_map_data()
            clusters = fetch_clusters()
        except requests.RequestException as exc:
            st.error(f"Unable to reach backend at {BACKEND_URL}: {exc}")
            st.stop()

    neighbourhood_names = _safe_get_name_list(neighborhoods)
    if not neighbourhood_names:
        st.error("No neighborhoods returned by the backend.")
        st.stop()

    if "selected_neighbourhood" not in st.session_state:
        st.session_state["selected_neighbourhood"] = neighbourhood_names[0]
    if "last_processed_map_click" not in st.session_state:
        st.session_state["last_processed_map_click"] = None
    if st.session_state["selected_neighbourhood"] not in neighbourhood_names:
        st.session_state["selected_neighbourhood"] = neighbourhood_names[0]

    st.sidebar.header("Explorer Controls")
    color_mode = st.sidebar.radio("Map color mode", ["Predicted Tier", "Cluster"])
    income = st.sidebar.number_input(
        "Annual gross income (CAD)", min_value=1000, value=100000, step=5000
    )
    highlight_affordable = st.sidebar.checkbox(
        "Highlight affordable neighborhoods", value=True
    )
    show_only_affordable = st.sidebar.checkbox("Show only affordable on map", value=False)

    st.sidebar.caption("Select from dropdown or click a neighborhood on the map.")
    selected_from_dropdown = st.sidebar.selectbox(
        "Selected neighborhood",
        neighbourhood_names,
        index=neighbourhood_names.index(st.session_state["selected_neighbourhood"]),
    )
    st.session_state["selected_neighbourhood"] = selected_from_dropdown
    selected_neighbourhood = st.session_state["selected_neighbourhood"]

    try:
        affordable = fetch_affordable(float(income))
    except requests.RequestException as exc:
        st.error(f"Could not load affordability data: {exc}")
        st.stop()

    affordable_names = {
        row["neighbourhood"] for row in affordable.get("neighbourhoods", [])
    }
    monthly_gross_income = float(income) / 12.0
    monthly_budget = float(affordable["monthly_budget"])
    monthly_budget_35 = float(income) * 0.35 / 12.0
    min_rent = min(float(row["avg_rent_1br"]) for row in map_rows)
    max_rent = max(float(row["avg_rent_1br"]) for row in map_rows)
    affordable_count_35 = sum(
        1 for row in map_rows if float(row["avg_rent_1br"]) <= monthly_budget_35
    )

    st.sidebar.markdown("### Affordability Rule")
    st.sidebar.caption(
        f"Gross monthly income = ${monthly_gross_income:,.0f}. "
        f"Max rent = 30% x gross monthly = ${monthly_budget:,.0f}."
    )
    st.sidebar.caption(
        f"Dataset current 1BR range: ${min_rent:,.0f} to ${max_rent:,.0f}. "
        f"Affordable now: {len(affordable_names)} neighborhoods."
    )
    st.sidebar.caption(
        f"If using a 35% gross rule instead: {affordable_count_35} neighborhoods."
    )

    if show_only_affordable:
        map_rows_to_render = [
            row for row in map_rows if row["neighbourhood"] in affordable_names
        ]
    else:
        map_rows_to_render = map_rows

    map_lookup = {row["neighbourhood"]: row for row in map_rows}
    cluster_lookup = {row["cluster_id"]: row for row in clusters}

    left_col, right_col = st.columns([1.65, 1.15], gap="large")

    with left_col:
        st.markdown("<div class='panel'>", unsafe_allow_html=True)
        st.markdown(
            f"**Map View** - {len(map_rows_to_render)} neighborhoods "
            f"({len(affordable_names)} affordable at ${income:,.0f}/year)"
        )
        map_obj = build_map(
            rows=map_rows_to_render,
            clusters=clusters,
            color_mode=color_mode,
            selected_neighbourhood=selected_neighbourhood,
            affordable_names=affordable_names,
            highlight_affordable=highlight_affordable,
        )

        map_event: dict[str, Any] | None = None
        if HAS_STREAMLIT_FOLIUM and st_folium is not None:
            map_event = st_folium(
                map_obj,
                height=680,
                width=None,
                key="toronto_map",
                returned_objects=[
                    "last_object_clicked_popup",
                    "last_active_drawing",
                    "last_object_clicked_tooltip",
                ],
            )
            clicked_name = _extract_clicked_neighbourhood(map_event)
            if clicked_name and clicked_name in map_lookup:
                if clicked_name != st.session_state["last_processed_map_click"]:
                    st.session_state["last_processed_map_click"] = clicked_name
                if clicked_name != st.session_state["selected_neighbourhood"]:
                    st.session_state["selected_neighbourhood"] = clicked_name
                    st.rerun()
        else:
            st.info(
                "Install `streamlit-folium` for click-to-select map interaction. "
                "Using static map fallback."
            )
            components.html(map_obj.get_root().render(), height=680, scrolling=False)

        st.caption(
            f"Affordability formula: 0.30 x (${income:,.0f}/12) = ${monthly_budget:,.2f}/month."
        )
        st.markdown("</div>", unsafe_allow_html=True)

    selected_neighbourhood = st.session_state["selected_neighbourhood"]
    try:
        detail = fetch_neighbourhood_detail(selected_neighbourhood)
        history = fetch_neighbourhood_history(selected_neighbourhood)
    except requests.RequestException as exc:
        st.error(f"Could not load neighborhood details for {selected_neighbourhood}: {exc}")
        st.stop()

    with right_col:
        _render_detail_panel(
            selected_neighbourhood=selected_neighbourhood,
            detail=detail,
            history=history,
            map_lookup=map_lookup,
            cluster_lookup=cluster_lookup,
            affordable_names=affordable_names,
        )


if __name__ == "__main__":
    main()
