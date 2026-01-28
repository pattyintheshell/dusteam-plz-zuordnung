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
farbe_map = {
    "Dustin": "rgba(31,119,180,0.4)",
    "Patricia": "rgba(0,162,232,0.4)",
    "Jonathan": "rgba(102,204,255,0.4)",
    "Tobias": "rgba(255,127,14,0.4)",
    "Kathrin": "rgba(255,178,102,0.4)",
    "Sumak": "rgba(255,210,120,0.4)",
    "Vanessa": "rgba(214,39,40,0.4)",
    "Sebastian": "rgba(255,99,92,0.4)",
    "Philipp": "rgba(44,160,44,0.4)",
    "Unassigned": "rgba(200,200,200,0.4)"
}

# -----------------------------
plz_gdf['hover_text'] = plz_gdf.apply(
    lambda row: f"PLZ: {row['plz2']}<br>Consultant: {row['consultant']}",
    axis=1
)

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
                showlegend=False  # KEINE automatische Legende mehr
            ))

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
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat": 51.0, "lon": 10.0},
    height=1000
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 8) Manuelle Legende oben rechts
st.markdown("""
<div style="position: absolute; top: 10px; right: 10px; background-color:white; padding:10px; border:1px solid black;">
<strong>Consultants</strong><br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(31,119,180,0.4);margin-right:5px;"></span>Dustin<br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(0,162,232,0.4);margin-right:5px;"></span>Patricia<br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(102,204,255,0.4);margin-right:5px;"></span>Jonathan<br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(255,127,14,0.4);margin-right:5px;"></span>Tobias<br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(255,178,102,0.4);margin-right:5px;"></span>Kathrin<br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(255,210,120,0.4);margin-right:5px;"></span>Sumak<br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(214,39,40,0.4);margin-right:5px;"></span>Vanessa<br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(255,99,92,0.4);margin-right:5px;"></span>Sebastian<br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(44,160,44,0.4);margin-right:5px;"></span>Philipp<br>
<span style="display:inline-block;width:20px;height:20px;background-color:rgba(200,200,200,0.4);margin-right:5px;"></span>Unassigned
</div>
""", unsafe_allow_html=True)
