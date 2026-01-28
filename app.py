import streamlit as st
import geopandas as gpd
import pydeck as pdk
import requests
from io import BytesIO

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(layout="wide")

st.title("🗺️ Marktaufteilung Dusteam")

# -----------------------------
# PLZ GeoJSON laden
# -----------------------------
PLZ_URL = (
    "https://github.com/pattyintheshell/dusteam-plz-zuordnung/"
    "releases/download/PLZ%20GeoJSON/plz_deutschland.geojson"
)

plz_gdf = gpd.read_file(BytesIO(requests.get(PLZ_URL).content))
plz_gdf["plz2"] = plz_gdf["plz"].astype(str).str[:2]

# -----------------------------
# Consultant Mapping
# -----------------------------
plz_mapping = {
    "Dustin": ["77", "78", "79", "88"],
    "Tobias": ["81", "82", "83", "84"],
    "Philipp": ["32","33","40","41","42","43","44","45","46","47","48","50","51","52","53","56","57","58","59"],
    "Vanessa": ["10","11","12","13","20","21","22"],
    "Patricia": ["68","69","71","74","75","76"],
    "Kathrin": ["80","85","86","87"],
    "Sebastian": ["01","02","03","04","05","06","07","08","09","14","15","16","17","18","19"],
    "Sumak": ["90","91","92","93","94","95","96","97"],
    "Jonathan": ["70","72","73","89"],
}

plz2_to_consultant = {
    plz: consultant
    for consultant, plzs in plz_mapping.items()
    for plz in plzs
}

plz_gdf["consultant"] = plz_gdf["plz2"].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# Farben (RGB!)
# -----------------------------
color_map = {
    "Dustin": [31,119,180],
    "Tobias": [255,127,14],
    "Philipp": [44,160,44],
    "Vanessa": [214,39,40],
    "Patricia": [148,103,189],
    "Kathrin": [140,86,75],
    "Sebastian": [227,119,194],
    "Sumak": [23,190,207],
    "Jonathan": [188,189,34],
    "Unassigned": [200,200,200],
}

plz_gdf["fill_color"] = plz_gdf["consultant"].map(color_map)

# -----------------------------
# Bundesländer laden
# -----------------------------
BL_URL = (
    "https://github.com/pattyintheshell/dusteam-plz-zuordnung/"
    "releases/download/Bundesländer%20GeoJSON/bundeslaender_deutschland.geojson"
)

bl_gdf = gpd.read_file(BytesIO(requests.get(BL_URL).content))

# -----------------------------
# Pydeck Layers
# -----------------------------
plz_layer = pdk.Layer(
    "GeoJsonLayer",
    data=plz_gdf,
    get_fill_color="properties.fill_color",
    get_line_color=[0, 0, 0],
    line_width_min_pixels=1,
    pickable=True,
)

bl_layer = pdk.Layer(
    "GeoJsonLayer",
    data=bl_gdf,
    get_line_color=[0, 0, 0],
    get_fill_color=[0, 0, 0, 0],
    line_width_min_pixels=2,
    pickable=False,
)

# -----------------------------
# View
# -----------------------------
view_state = pdk.ViewState(
    latitude=51.0,
    longitude=10.0,
    zoom=5,
)

deck = pdk.Deck(
    layers=[plz_layer, bl_layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v9",
)

st.pydeck_chart(deck, use_container_width=True)
