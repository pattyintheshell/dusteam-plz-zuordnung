import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
import requests
from io import BytesIO

# -----------------------------
st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung DE Perm Embedded Team")

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
# Farben deutlich unterscheidbar, dunkler Ton innerhalb Familie, transparent
farbe_map = {
    # Blau-Familie
    "Dustin": "rgba(31,119,180,0.4)",        # mittelblau
    "Patricia": "rgba(0,102,204,0.4)",       # dunkler
    "Jonathan": "rgba(102,178,255,0.4)",     # heller
    
    # Grün-Familie (war Orange)
    "Tobias": "rgba(44,160,44,0.4)",         # mittelgrün
    "Kathrin": "rgba(0,128,0,0.4)",          # dunkler
    "Sumak": "rgba(144,238,144,0.4)",        # heller
    
    # Lila/Pink-Familie (Vanessa Pink, Sebastian Lila)
    "Vanessa": "rgba(255,20,147,0.4)",       # Pink
    "Sebastian": "rgba(148,0,211,0.4)",      # Lila
    
    # Orange-Familie (war Grün)
    "Philipp": "rgba(255,127,14,0.4)",       # Orange
    
    "Unassigned": "rgba(200,200,200,0.4)"
}

# -----------------------------
# Bundesländer joinen
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
plz_with_bl = gpd.sjoin(plz_gdf, bl_gdf[['name','geometry']], how='left', predicate='intersects')
plz_with_bl = plz_with_bl.reset_index(drop=True)

# -----------------------------
# Performance-Optimierung: Polygone vereinfachen
plz_with_bl['geometry'] = plz_with_bl['geometry'].simplify(tolerance=0.01, preserve_topology=True)
bl_gdf['geometry'] = bl_gdf['geometry'].simplify(tolerance=0.01, preserve_topology=True)

# -----------------------------
# Hover-Text untereinander: PLZ, Bundesland, Consultant
plz_with_bl['hover_text'] = plz_with_bl.apply(
    lambda row: f"{row['plz2']}<br>{row['name'] if row['name'] else 'Unbekannt'}<br>{row['consultant']}",
    axis=1
)

# -----------------------------
fig = go.Figure()

# 2er-PLZ Gebiete
for consultant in plz_with_bl['consultant'].unique():
    subset = plz_with_bl[plz_with_bl['consultant'] == consultant]
    if subset.empty:
        continue
    
    for geom, hover in zip(subset.geometry, subset.hover_text):
        polys = [geom] if geom.geom_type=="Polygon" else geom.geoms
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
                showlegend=False
            ))

# -----------------------------
# Unsichtbare Traces nur für Legende
for consultant, color in farbe_map.items():
    fig.add_trace(go.Scattermapbox(
        lon=[None], lat=[None],
        mode='markers',
        marker=dict(size=10, color=color),
        name=consultant,
        showlegend=True
    ))

# -----------------------------
# Bundesländer Linien
for _, row in bl_gdf.iterrows():
    geom = row.geometry
    polys = [geom] if geom.geom_type=="Polygon" else geom.geoms
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
