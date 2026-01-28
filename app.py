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
plz2_to_consultant = {p: c for c, plz_list in plz_mapping.items() for p in plz_list}
plz_gdf['consultant'] = plz_gdf['plz2'].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# Hover-Text pro PLZ (untereinander)
plz_gdf['hover_text'] = plz_gdf.apply(
    lambda row: f"{row['plz2']}\n{row['name'] if 'name' in row else 'Unbekannt'}\n{row['consultant']}",
    axis=1
)

# -----------------------------
# Farben pro Consultant (nur #RRGGBB, Transparenz über opacity)
farbe_map = {
    "Dustin": "#1f77b4",     
    "Patricia": "#ff7f14",   
    "Jonathan": "#2ca03c",   
    "Tobias": "#d62740",     
    "Kathrin": "#9467bd",    
    "Sumak": "#ff9896",      
    "Vanessa": "#ffbb78",    
    "Sebastian": "#17becf",  
    "Philipp": "#7f7f00",    
    "Unassigned": "#c8c8c8"
}

# -----------------------------
# Karte bauen: EIN Trace pro Consultant
fig = go.Figure()

for consultant, color in farbe_map.items():
    subset = plz_gdf[plz_gdf['consultant'] == consultant]
    if subset.empty:
        continue

    # Alle Polygone sammeln
    lon_list, lat_list, text_list = [], [], []
    for geom, hover in zip(subset.geometry, subset['hover_text']):
        if geom.geom_type == "Polygon":
            polys = [geom]
        elif geom.geom_type == "MultiPolygon":
            polys = geom.geoms
        else:
            continue
        for poly in polys:
            lons, lats = zip(*poly.exterior.coords)
            lon_list.extend(lons + (None,))
            lat_list.extend(lats + (None,))
            text_list.extend([hover]*len(lons) + [None])

    # Trace pro Consultant
    fig.add_trace(go.Scattermapbox(
        lon=lon_list,
        lat=lat_list,
        mode='lines',
        fill='toself',
        fillcolor=color,
        line=dict(color='black', width=1),
        text=text_list,
        hoverinfo='text',
        name=consultant,
        showlegend=True,
        legendgroup=consultant,
        opacity=0.5
    ))

# -----------------------------
# Bundesländer Umrisse
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
for geom in bl_gdf.geometry:
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
# Layout
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat":51.0,"lon":10.0},
    height=800,
    width=800,
    legend=dict(
        title="Consultants",
        x=0.99,
        y=0.99,
        xanchor="right",
        yanchor="top"
    )
)

st.plotly_chart(fig, use_container_width=False)
