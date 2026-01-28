import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
import requests
from io import BytesIO
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon

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
    "Dustin": "rgba(31,119,180,0.6)",
    "Patricia": "rgba(70,130,180,0.6)",
    "Jonathan": "rgba(100,149,237,0.6)",
    "Tobias": "rgba(255,127,14,0.6)",
    "Kathrin": "rgba(255,165,0,0.6)",
    "Sumak": "rgba(255,200,0,0.6)",
    "Vanessa": "rgba(214,39,40,0.6)",
    "Sebastian": "rgba(178,34,34,0.6)",
    "Philipp": "rgba(44,160,44,0.6)",
    "Unassigned": "rgba(200,200,200,0.6)"
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
# 5) Alle Polygone pro Consultant zusammenfassen
# -----------------------------
traces = []
for consultant in plz_mit_bl['consultant'].unique():
    subset = plz_mit_bl[plz_mit_bl['consultant']==consultant]
    if subset.empty:
        continue

    # Alle Geometrien zusammenfassen
    merged = unary_union(subset.geometry)

    # Stelle sicher, dass wir immer eine Liste von Polygonen haben
    polys = [merged] if merged.geom_type=="Polygon" else list(merged.geoms)

    for poly in polys:
        lons, lats = zip(*poly.exterior.coords)
        traces.append(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            fill='toself',
            fillcolor=farbe_map[consultant],
            line=dict(color='black', width=1),
            hoverinfo='text',
            text=[f"{consultant}"]*len(lons),
            showlegend=False  # absolut keine automatische Legende
        ))

# -----------------------------
# 6) Bundesländer Linien
# -----------------------------
for _, row in bl_gdf.iterrows():
    geom = row.geometry
    polys = [geom] if geom.geom_type=='Polygon' else geom.geoms
    for poly in polys:
        lons, lats = zip(*poly.exterior.coords)
        traces.append(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            line=dict(color='black', width=2),
            hoverinfo='skip',
            showlegend=False
        ))

# -----------------------------
# 7) Karte
# -----------------------------
fig = go.Figure(data=traces)
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat":51.0,"lon":10.0},
    height=1000,
    showlegend=False  # Sicherheit: keine Legende
)

st.plotly_chart(fig, use_container_width=True)
st.markdown("**Automatische Legende entfernt. Jede Farbe zeigt einen Consultant.**")
