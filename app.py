import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
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
# 3) Neue, deutlich unterscheidbare transparente Farben pro Consultant
# -----------------------------
farbe_map = {
    "Dustin": "rgba(31,119,180,0.4)",      # kräftiges Blau, transparent
    "Patricia": "rgba(0,162,232,0.4)",     # helles Blau
    "Jonathan": "rgba(102,204,255,0.4)",   # hellstes Blau
    "Tobias": "rgba(255,127,14,0.4)",      # kräftiges Orange
    "Kathrin": "rgba(255,178,102,0.4)",    # helleres Orange
    "Sumak": "rgba(255,210,120,0.4)",      # sehr helles Orange
    "Vanessa": "rgba(214,39,40,0.4)",      # kräftiges Rot
    "Sebastian": "rgba(255,99,92,0.4)",    # helleres Rot
    "Philipp": "rgba(44,160,44,0.4)",      # Grün
    "Unassigned": "rgba(200,200,200,0.4)"  # Grau
}

# -----------------------------
# 4) Hover-Text
# -----------------------------
plz_gdf['hover_text'] = plz_gdf.apply(
    lambda row: f"PLZ: {row['plz2']}<br>Consultant: {row['consultant']}",
    axis=1
)

# -----------------------------
# 5) Karte: Scattermapbox pro PLZ-Gebiet
# -----------------------------
fig = go.Figure()

for consultant in plz_gdf['consultant'].unique():
    subset = plz_gdf[plz_gdf['consultant'] == consultant]
    if subset.empty:
        continue
    
    for geom, hover in zip(subset.geometry, subset.hover_text):
        polys = [geom] if geom.geom_type == "Polygon" else geom.geoms
        for poly in polys:
            lons, lats = zip(*poly.exterior.coords)
            fig.add_trace(go.Scattermapbox(
                lon=lons,
                lat=lats,
                mode='lines',
                fill='toself',
                fillcolor=farbe_map[consultant],
                line=dict(color='black', width=1),
                hoverinfo='text',
                text=[hover]*len(lons),
                name=consultant,       # Legende einmal pro Consultant
                legendgroup=consultant, 
                showlegend=True
            ))

# -----------------------------
# 6) Bundesländer Linien
# -----------------------------
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
for _, row in bl_gdf.iterrows():
    geom = row.geometry
    polys = [geom] if geom.geom_type=='Polygon' else geom.geoms
    for poly in polys:
        lons, lats = zip(*poly.exterior.coords)
        fig.add_trace(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            line=dict(color='black', width=2),
            hoverinfo='skip',
            showlegend=False
        ))

# -----------------------------
# 7) Layout
# -----------------------------
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat": 51.0, "lon": 10.0},
    height=1000,
    legend=dict(
        title="Consultants",
        yanchor="top",
        y=0.99,
        xanchor="right",
        x=0.99,
        bgcolor="white",
        bordercolor="black",
        borderwidth=1
    )
)

st.plotly_chart(fig, use_container_width=True)
