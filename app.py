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
# Farben pro Consultant (RGBA, transparent)
farbe_map = {
    "Dustin": "rgba(255, 223, 0, 0.4)",    # Kräftiges Gelb
    "Patricia": "rgba(255, 0, 0, 0.4)",     # Rot
    "Jonathan": "rgba(255, 102, 0, 0.4)",   # Dunkleres Orange
    "Philipp": "rgba(30, 144, 255, 0.4)",   # Blau
    "Tobias": "rgba(34, 139, 34, 0.4)",     # Dunkleres Grün
    "Kathrin": "rgba(186, 85, 211, 0.4)",   # Helleres Lila
    "Sumak": "rgba(0, 206, 209, 0.4)",      # Cyan/Türkis
    "Vanessa": "rgba(255, 20, 147, 0.4)",   # Kräftiges Pink
    "Sebastian": "rgba(102, 0, 204, 0.4)",  # Dunkleres Violett
    "Unassigned": "rgba(200, 200, 200, 0.4)"# Grau
}

# -----------------------------
# Karte bauen: EIN Trace pro Consultant
fig = go.Figure()

# Flächen-Trace
for consultant, color in farbe_map.items():
    subset = plz_gdf[plz_gdf['consultant'] == consultant]
    if subset.empty:
        continue

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
        showlegend=False
    ))

# Dummy-Traces für Legende (exakte Farbe)
for consultant, color in farbe_map.items():
    fig.add_trace(go.Scattermapbox(
        lon=[None], lat=[None],
        mode='markers',
        marker=dict(size=10, color=color),
        name=consultant,
        showlegend=True
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