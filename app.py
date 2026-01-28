import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
import requests
from io import BytesIO

# -----------------------------
st.set_page_config(layout="wide")
st.title("Marktaufteilung DE Perm Embedded")

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

# -----------------------------
# PLZ2 extrahieren
plz_gdf["plz2"] = plz_gdf["plz"].astype(str).str[:2]

# -----------------------------
# Consultant Mapping
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

plz2_to_consultant = {p: c for c, v in plz_mapping.items() for p in v}
plz_gdf["consultant"] = plz_gdf["plz2"].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# Farben für Consultants
farbe_map = {
    "Dustin": "rgba(255, 223, 0, 0.4)",
    "Patricia": "rgba(255, 0, 0, 0.4)",
    "Jonathan": "rgba(255, 102, 0, 0.4)",
    "Philipp": "rgba(0, 100, 255, 0.4)",
    "Tobias": "rgba(0, 100, 0, 0.4)",
    "Kathrin": "rgba(160, 80, 210, 0.4)",
    "Sumak": "rgba(0, 206, 209, 0.4)",
    "Vanessa": "rgba(255, 102, 204, 0.4)",
    "Sebastian": "rgba(110, 210, 110, 0.4)",
    "Unassigned": "rgba(200, 200, 200, 0.4)"
}

# -----------------------------
# Numerische IDs für Choroplethmapbox
consultants = list(farbe_map.keys())
consultant_id = {c: i for i, c in enumerate(consultants)}
plz_gdf["consultant_id"] = plz_gdf["consultant"].map(consultant_id)

# -----------------------------
# Choropleth-Karte
fig = go.Figure(go.Choroplethmapbox(
    geojson=plz_gdf.__geo_interface__,
    locations=plz_gdf.index,
    z=plz_gdf["consultant_id"],
    colorscale=[  # Farben gemäß farbe_map
        [0.0, farbe_map["Dustin"]],
        [0.1, farbe_map["Patricia"]],
        [0.2, farbe_map["Jonathan"]],
        [0.3, farbe_map["Philipp"]],
        [0.4, farbe_map["Tobias"]],
        [0.5, farbe_map["Kathrin"]],
        [0.6, farbe_map["Sumak"]],
        [0.7, farbe_map["Vanessa"]],
        [0.8, farbe_map["Sebastian"]],
        [0.9, farbe_map["Unassigned"]],
        [1.0, farbe_map["Unassigned"]]
    ],
    marker_line_width=0.5,
    hovertext=plz_gdf["plz2"] + " " + plz_gdf["consultant"],
    hoverinfo="text",
    showscale=False
))

# -----------------------------
# Bundesländer-Grenzen hinzufügen
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
for geom in bl_gdf.geometry:
    polys = [geom] if geom.geom_type=="Polygon" else geom.geoms
    for poly in polys:
        lons, lats = zip(*poly.exterior.coords)
        fig.add_trace(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode="lines",
            line=dict(color="black", width=2),
            hoverinfo="skip",
            showlegend=False
        ))

# -----------------------------
# Layout und
