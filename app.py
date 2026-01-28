import streamlit as st
import geopandas as gpd
import pydeck as pdk
import requests
from io import BytesIO

# -----------------------------
# Streamlit Setup
# -----------------------------
st.set_page_config(
    layout="wide",
    initial_sidebar_state="collapsed"
)
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
# 3) Farben (RGB)
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
    "Unassigned": [200,200,200]
}
plz_gdf["fill_color"] = plz_gdf["consultant"].map(color_map)

# -----------------------------
# 4) Pydeck Layers
# -----------------------------
plz_layer = pdk.Layer(
    "GeoJsonLayer",
    data=plz_gdf,
    get_fill_color="properties.fill_color",
    get_line_color=[0,0,0],
    line_width_min_pixels=1,
    pickable=True,
    auto_highlight=True
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
# 5) Pydeck ViewState
# -----------------------------
view_state = pdk.ViewState(
    latitude=51.0,
    longitude=10.0,
    zoom=5
)

# -----------------------------
# 6) Deck erstellen
# -----------------------------
deck = pdk.Deck(
    layers=[plz_layer, bl_layer],
    initial_view_state=view_state,
    map_style="mapbox://styles/mapbox/light-v9",
    tooltip={"text": "{consultant}"}
)

# -----------------------------
# 7) Anzeige in Streamlit
# -----------------------------
st.pydeck_chart(deck, use_container_width=True)

# -----------------------------
# 8) Legende selbst bauen
# -----------------------------
st.markdown("### Legende")
cols = st.columns(len(color_map))
for i, (name, rgb) in enumerate(color_map.items()):
    with cols[i % len(cols)]:
        st.markdown(
            f"<div style='display:flex; align-items:center;'>"
            f"<div style='width:15px; height:15px; background-color:rgb{tuple(rgb)}; margin-right:5px;'></div>"
            f"{name}</div>", unsafe_allow_html=True
        )
