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
# 3) Farben pro Consultant
# -----------------------------
farbe_map = {
    "Dustin": "rgba(31,119,180,0.5)",
    "Patricia": "rgba(70,130,180,0.5)",
    "Jonathan": "rgba(173,216,230,0.5)",
    "Tobias": "rgba(255,127,14,0.5)",
    "Kathrin": "rgba(255,165,0,0.5)",
    "Sumak": "rgba(255,200,0,0.5)",
    "Vanessa": "rgba(214,39,40,0.5)",
    "Sebastian": "rgba(178,34,34,0.5)",
    "Philipp": "rgba(44,160,44,0.5)",
    "Unassigned": "rgba(200,200,200,0.5)"
}

# -----------------------------
# 4) Bundesländer-Zuordnung + Hover
# -----------------------------
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
plz_mit_bl = gpd.sjoin(plz_gdf, bl_gdf[['name','geometry']], how='left', predicate='intersects')
plz_mit_bl = plz_mit_bl.reset_index(drop=True)
plz_mit_bl['hover_text'] = plz_mit_bl.apply(
    lambda row: f"{row['plz2']}\n{row['name'] if row['name'] else 'Unbekannt'}\n{row['consultant']}",
    axis=1
)

# -----------------------------
# 5) Karte bauen
# -----------------------------
fig = go.Figure()

for idx, row in plz_mit_bl.iterrows():
    geom = row.geometry
    polygons = [geom] if geom.geom_type=='Polygon' else geom.geoms
    for poly in polygons:
        lons, lats = zip(*poly.exterior.coords)
        fig.add_trace(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            fill='toself',
            fillcolor=farbe_map[row['consultant']],
            line=dict(color='black', width=1),
            hoverinfo='text',
            text=[row['hover_text']]*len(lons)
        ))

# Bundesländer als Linien
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
            hoverinfo='skip'
        ))

# Layout
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat":51.0,"lon":10.0},
    height=1000
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# 6) Legende manuell in Streamlit
# -----------------------------
st.markdown("### Consultants")
cols = st.columns(len(farbe_map))
for i, (consultant, farbe) in enumerate(farbe_map.items()):
    cols[i].markdown(f"<div style='background:{farbe};padding:10px;text-align:center;border-radius:5px'>{consultant}</div>", unsafe_allow_html=True)
