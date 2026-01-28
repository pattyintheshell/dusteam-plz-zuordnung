import streamlit as st
import geopandas as gpd
import plotly.express as px
import requests
from io import BytesIO

# -----------------------------
# 0) Titel
# -----------------------------
st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung DE Perm Embedded")

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
plz_gdf['consultant'] = plz_gdf['plz2'].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# 3) Farben pro Consultant
# -----------------------------
color_map = {
    "Dustin": "#1f77b4",
    "Patricia": "#4682b4",
    "Jonathan": "#add8e6",
    "Tobias": "#ff7f0e",
    "Kathrin": "#ffa500",
    "Sumak": "#ffc800",
    "Vanessa": "#d62728",
    "Sebastian": "#b22222",
    "Philipp": "#2ca03c",
    "Unassigned": "#c8c8c8"
}

# -----------------------------
# 4) Bundesländer-Zuordnung + Hover-Text
# -----------------------------
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
plz_with_bl = gpd.sjoin(plz_gdf, bl_gdf[['name','geometry']], how='left', predicate='intersects')
plz_with_bl = plz_with_bl.reset_index(drop=True)

plz_with_bl['hover_text'] = plz_with_bl.apply(
    lambda row: f"{row['plz2']}\n{row['name'] if row['name'] else 'Unbekannt'}\n{row['consultant']}",
    axis=1
)

# -----------------------------
# 5) Choroplethmapbox Plot
# -----------------------------
# Wir brauchen für px.choropleth_mapbox ein GeoJSON-Feature
plz_with_bl_json = plz_with_bl.__geo_interface__

fig = px.choropleth_mapbox(
    plz_with_bl,
    geojson=plz_with_bl_json,
    locations=plz_with_bl.index,
    color='consultant',
    hover_name='hover_text',
    color_discrete_map=color_map,
    center={"lat":51.0,"lon":10.0},
    zoom=5,
    opacity=0.5
)

# -----------------------------
# 6) Bundesländer als Linien (optional)
# -----------------------------
for _, row in bl_gdf.iterrows():
    geom = row.geometry
    polygons = [geom] if geom.geom_type=='Polygon' else geom.geoms
    for poly in polygons:
        lons, lats = zip(*poly.exterior.coords)
        fig.add_scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            line=dict(color='black', width=2),
            hoverinfo='skip',
            showlegend=False
        )

# -----------------------------
# 7) Layout
# -----------------------------
fig.update_layout(
    mapbox_style="carto-positron",
    height=1000,
    legend=dict(
        title="Consultants",
        title_font=dict(color="black", size=20, family="Arial Black"),
        font=dict(color="black", size=16),
        bgcolor="white",
        bordercolor="black",
        borderwidth=2,
        x=0.99,
        y=0.99,
        xanchor="right",
        yanchor="top",
        traceorder="normal",
        orientation="v"
    )
)

st.plotly_chart(fig, use_container_width=True)
