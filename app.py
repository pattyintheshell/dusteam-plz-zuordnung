import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
import requests
from io import BytesIO
import numpy as np

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

# PLZ2 extrahieren
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
# Hover-Text pro PLZ (PLZ2 + Consultant)
plz_gdf['hover_text'] = plz_gdf.apply(
    lambda row: f"{row['plz2']} {row['consultant']}",
    axis=1
)

# -----------------------------
# Farben pro Consultant (RGBA, transparent)
farbe_map = {
    "Dustin": "rgba(255, 223, 0, 0.4)",       # Gelb
    "Patricia": "rgba(255, 0, 0, 0.4)",       # Rot
    "Jonathan": "rgba(255, 102, 0, 0.4)",     # Orange
    "Philipp": "rgba(0, 100, 255, 0.4)",      # Blau
    "Tobias": "rgba(0, 100, 0, 0.4)",         # Dunkleres Grün
    "Kathrin": "rgba(160, 80, 210, 0.4)",     # Lila minimal heller
    "Sumak": "rgba(0, 206, 209, 0.4)",        # Cyan/Türkis
    "Vanessa": "rgba(255, 102, 204, 0.4)",    # Helleres, rosa Pink
    "Sebastian": "rgba(110, 210, 110, 0.4)",  # Hellgrün minimal dunkler
    "Unassigned": "rgba(200, 200, 200, 0.4)"  # Grau
}

# -----------------------------
# Karte bauen: EIN Trace pro Consultant
fig = go.Figure()

# Flächen-Trace für PLZ-Gebiete (NumPy-Optimierung)
for consultant, color in farbe_map.items():
    subset = plz_gdf[plz_gdf['consultant'] == consultant]
    if subset.empty:
        continue

    lon_arrays, lat_arrays, text_arrays = [], [], []
    for geom, hover in zip(subset.geometry, subset['hover_text']):
        if geom.geom_type == "Polygon":
            polys = [geom]
        elif geom.geom_type == "MultiPolygon":
            polys = geom.geoms
        else:
            continue

        for poly in polys:
            lons, lats = zip(*poly.exterior.coords)
            lon_arrays.append(np.concatenate([np.array(lons), [np.nan]]))
            lat_arrays.append(np.concatenate([np.array(lats), [np.nan]]))
            text_arrays.append(np.concatenate([np.array([hover]*len(lons)), [np.nan]]))

    lon_list = np.concatenate(lon_arrays).tolist()
    lat_list = np.concatenate(lat_arrays).tolist()
    text_list = np.concatenate(text_arrays).tolist()

    fig.add_trace(go.Scattermapbox(
        lon=lon_list,
        lat=lat_list,
        mode='lines',
        fill='toself',
        fillcolor=color,
        line=dict(color='black', width=1),  # PLZ-Linien
        text=text_list,
        hoverinfo='text',
        name=consultant,
        showlegend=False
    ))

# Dummy-Traces für Legende (größere Marker)
for consultant, color in farbe_map.items():
    fig.add_trace(go.Scattermapbox(
        lon=[None], lat=[None],
        mode='markers',
        marker=dict(size=20, color=color),
        name=consultant,
        showlegend=True
    ))

# -----------------------------
# Bundesländer-Linien
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
for geom in bl_gdf.geometry:
    polys = [geom] if geom.geom_type=='Polygon' else geom.geoms
    for poly in polys:
        lons, lats = zip(*poly.exterior.coords)
        fig.add_trace(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            line=dict(color='black', width=2),  # Bundesländer-Linien
            hoverinfo='skip',
            showlegend=False
        ))

# -----------------------------
# Layout: alphabetische Legende, Unassigned am Ende
legend_order = sorted([c for c in farbe_map.keys() if c != "Unassigned"]) + ["Unassigned"]

fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat":51.0,"lon":10.0},
    height=800,
    width=800,
    legend=dict(
        title=dict(text="Consultants", font=dict(size=20, family="Arial, sans-serif", color="black")),
        font=dict(size=16),
        tracegroupgap=10,  # Abstand Titel -> erstes Element
        x=0.99,
        y=0.99,
        xanchor="right",
        yanchor="top",
        traceorder='normal'
    )
)

# Sortiere Dummy-Traces für die Legende
new_order = []
for name in legend_order:
    for trace in fig.data:
        if trace.name == name and trace.showlegend:
            new_order.append(trace)
fig.data = tuple([t for t in fig.data if not t.showlegend] + new_order)

# -----------------------------
st.plotly_chart(fig, use_container_width=False)