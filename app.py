import streamlit as st
import geopandas as gpd
import pydeck as pdk
import requests
from io import BytesIO
import json

# -----------------------------
# Streamlit Setup
# -----------------------------
st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam")

# -----------------------------
# Helper: GeoJSON aus GitHub Release laden
# -----------------------------
def load_geojson_from_github(url: str) -> gpd.GeoDataFrame:
    headers = {"User-Agent": "streamlit-app"}
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code != 200:
        st.error(f"GeoJSON konnte nicht geladen werden ({response.status_code})")
        st.stop()
    return gpd.read_file(BytesIO(response.content))

# -----------------------------
# 1) GeoJSON laden
# -----------------------------
PLZ_URL = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_deutschland.geojson"
BL_URL  = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-bundeslaender/bundeslaender_deutschland.geojson"

plz_gdf = load_geojson_from_github(PLZ_URL)
bl_gdf  = load_geojson_from_github(BL_URL)

plz_gdf["plz2"] = plz_gdf["plz"].astype(str).str[:2]

# -----------------------------
# 2) Consultant Mapping
# -----------------------------
plz_mapping = {
    "Dustin": ["77","78","79","88"],
    "Tobias": ["81","82","83","84"],
    "Philipp": ["32","33","40","41","42","43","44","45","46","47","48","50","51","52","53","56","57","58","59"],
    "Vanessa": ["10","11","12","13","20","21","22"],
    "Patricia": ["68","69","71","74","75","76"],
    "Kathrin": ["80","85","86","87"],
    "Sebastian": ["01","02","03","04","05","06","07","08","09","14","15","16","17","18","19"],
    "Sumak": ["90","91","92","93","94","95","96","97"],
    "Jonathan": ["70","72","73","89"]
}

plz2_to_consultant = {p: c for c, plz_list in plz_mapping.items() for p in plz_list}
plz_gdf["consultant"] = plz_gdf["plz2"].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# 3) Farben (RGB), Braun ersetzt durch Orange
# -----------------------------
color_map = {
    "Dustin": [31,119,180],
    "Tobias": [255,127,14],
    "Philipp": [44,160,44],
    "Vanessa": [214,39,40],
    "Patricia": [148,103,189],
    "Kathrin": [255,165,0],  # Braun ersetzt
    "Sebastian": [227,119,194],
    "Sumak": [23,190,207],
    "Jonathan": [188,189,34],
    "Unassigned": [200,200,200]
}
plz_gdf["fill_color"] = plz_gdf["consultant"].map(color_map)

# -----------------------------
# 4) Bundesland-Zuordnung für Tooltip
# -----------------------------
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)

# Spatial Join
plz_gdf_with_bl = gpd.sjoin(plz_gdf, bl_gdf[['name','geometry']], how='left', predicate='intersects')
plz_gdf_with_bl = plz_gdf_with_bl.reset_index(drop=True)  # ❌ Verhindert Index-Duplikate
plz_gdf = plz_gdf_with_bl.copy()

# Tooltip Spalte
plz_gdf['tooltip_text'] = (
    "PLZ: " + plz_gdf['plz2'] +
    "<br>Consultant: " + plz_gdf['consultant'] +
    "<br>Bundesland: " + plz_gdf['name'].fillna("Unbekannt")
)

# -----------------------------
# 5) Farben & Tooltip in GeoJSON
# -----------------------------
plz_geojson = json.loads(plz_gdf.to_json())
for i, feature in enumerate(plz_geojson["features"]):
    feature["properties"]["fill_color"] = plz_gdf.loc[i, "fill_color"]
    feature["properties"]["tooltip_text"] = plz_gdf.loc[i, "tooltip_text"]

# -----------------------------
# 6) Pydeck Layers
# -----------------------------
plz_layer = pdk.Layer(
    "GeoJsonLayer",
    data=plz_geojson,
    get_fill_color="properties.fill_color",
    get_line_color=[0,0,0],
    line_width_min_pixels=1,
    pickable=True,
    auto_highlight=True,
    tooltip={"html": "{tooltip_text}"}
)

bl_layer = pdk.Layer(
    "GeoJsonLayer",
    data=bl_gdf,
    get_fill_color=[0,0,0,0],
    get_line_color=[0,0,0],
    line_width_min_pixels=2,
    pickable=False
)

# -----------------------------
# 7) ViewState: Europa sichtbar
# -----------------------------
view_state = pdk.ViewState(
    latitude=51.0,
    longitude=10.0,
    zoom=4.5,
    min_zoom=3,
    max_zoom=8
)

deck = pdk.Deck(
    layers=[plz_layer, bl_layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v9"
)

st.pydeck_chart(deck, use_container_width=True)

# -----------------------------
# 8) Rechte, vertikale Legende über Karte
# -----------------------------
legend_html = "<div style='position:absolute; top:20px; right:20px; background:white; padding:10px; border:1px solid black; z-index:999;'>"
legend_html += "<b>Consultants</b><br><br>"
for name, rgb in color_map.items():
    legend_html += (
        f"<div style='display:flex; align-items:center; margin-bottom:4px;'>"
        f"<div style='width:15px; height:15px; background-color:rgb{tuple(rgb)}; margin-right:8px;'></div>"
        f"{name}</div>"
    )
legend_html += "</div>"

st.markdown(legend_html, unsafe_allow_html=True)
