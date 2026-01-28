import streamlit as st
import geopandas as gpd
import plotly.express as px
import requests
from io import BytesIO

# -----------------------------
# 0) Titel
# -----------------------------
st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung DE Perm Embedded Team")

# -----------------------------
# 1) GeoJSON laden
# -----------------------------
def load_geojson(url: str) -> gpd.GeoDataFrame:
    r = requests.get(url)
    if r.status_code != 200:
        st.error(f"Fehler beim Laden: {r.status_code}")
        st.stop()
    return gpd.read_file(BytesIO(r.content))

PLZ_URL = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_deutschland.geojson"
BL_URL  = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-bundeslaender/bundeslaender_deutschland.geojson"

plz_gdf = load_geojson(PLZ_URL)
bl_gdf  = load_geojson(BL_URL)
plz_gdf['plz2'] = plz_gdf['plz'].astype(str).str[:2]

# -----------------------------
# 2) Consultant Zuordnung
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
plz_gdf['consultant'] = plz_gdf['plz2'].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# 3) Farben pro Consultant
# -----------------------------
farbe_map = {
    "Dustin": "#1f77b4",
    "Patricia": "#4682b4",
    "Jonathan": "#6495ed",
    "Tobias": "#ff7f0e",
    "Kathrin": "#ffa500",
    "Sumak": "#ffc800",
    "Vanessa": "#d62728",
    "Sebastian": "#b22222",
    "Philipp": "#2ca02c",
    "Unassigned": "#c8c8c8"
}

# -----------------------------
# 4) Hover-Text vorbereiten
# -----------------------------
plz_gdf['hover_text'] = plz_gdf.apply(
    lambda row: f"PLZ: {row['plz2']}<br>Consultant: {row['consultant']}",
    axis=1
)

# -----------------------------
# 5) Choropleth-Karte mit Plotly Express
# -----------------------------
fig = px.choropleth_mapbox(
    plz_gdf,
    geojson=plz_gdf.geometry,
    locations=plz_gdf.index,
    color='consultant',
    hover_name='hover_text',
    color_discrete_map=farbe_map,
    mapbox_style="carto-positron",
    zoom=5,
    center={"lat": 51.0, "lon": 10.0},
)

fig.update_layout(
    margin={"r":0,"t":0,"l":0,"b":0},
    legend_title_text="Consultant",
    height=1000
)

st.plotly_chart(fig, use_container_width=True)
