import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam")

# -----------------------------
# 1) PLZ GeoJSON laden
# -----------------------------
PLZ_URL = "https://raw.githubusercontent.com/tdudek/de-plz-geojson/master/plz-2stellig.geojson"
r = requests.get(PLZ_URL)
if r.status_code != 200:
    st.error(f"Fehler beim Laden der PLZ GeoJSON: {r.status_code}")
    st.stop()

plz_gdf = gpd.read_file(BytesIO(r.content))
plz_gdf['plz2'] = plz_gdf['plz'].astype(str).str[:2]

# -----------------------------
# 2) Consultant-Zuordnung
# -----------------------------
plz_mapping = {
    'Dustin': ['77','78','79','88'],
    'Tobias': ['81','82','83','84'],
    'Philipp': ['32','33','40','41','42','43','44','45','46','47','48','50','51','52','53','56','57','58','59'],
    'Vanessa': ['10','11','12','13','20','21','22'],
    'Patricia': ['68','69','71','74','75','76'],
    'Kathrin': ['80','85','86','87'],
    'Sebastian': ['01','02','03','04','05','06','07','08','09','14','15','16','17','18','19'],
    'Sumak': ['90','91','92','93','94','95','96','97'],
    'Jonathan': ['70','72','73','89']
}
plz2_to_consultant = {p: c for c, plz_list in plz_mapping.items() for p in plz_list}
plz_gdf['consultant'] = plz_gdf['plz2'].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# 3) Farben
# -----------------------------
color_map = {
    'Dustin': '#1f77b4','Tobias': '#ff7f0e','Philipp': '#2ca02c','Vanessa': '#d62728',
    'Patricia': '#9467bd','Kathrin': '#8c564b','Sebastian': '#e377c2','Sumak': '#17becf',
    'Jonathan': '#bcbd22','Unassigned': '#c0c0c0'
}

# -----------------------------
# 4) Legende-Reihenfolge
# -----------------------------
categories = ['Dustin','Tobias','Philipp','Vanessa','Patricia','Kathrin',
              'Sebastian','Sumak','Jonathan','Unassigned']

# -----------------------------
# 5) Karte bauen
# -----------------------------
fig = go.Figure()

for consultant in categories:
    subset = plz_gdf[plz_gdf['consultant']==consultant]
    for _, row in subset.iterrows():
        if row.geometry.type == "Polygon":
            coords = row.geometry.exterior.coords
        else:  # MultiPolygon
            coords = []
            for poly in row.geometry.geoms:
                coords += list(poly.exterior.coords)
        lons, lats = zip(*coords)
        fig.add_trace(go.Scattermapbox(
            lon=lons,
            lat=lats,
            mode='lines',
            fill='toself',
            fillcolor=color_map[consultant],
            line=dict(color='black', width=1),
            name=consultant,
            hoverinfo='text',
            text=f"PLZ: {row['plz2']}<br>Consultant: {consultant}",
            showlegend=False if consultant=="Unassigned" else True
        ))

# Dummy-Traces nur für die Legende, exakt 1 Eintrag pro Consultant
for consultant in categories:
    fig.add_trace(go.Scattermapbox(
        lon=[None], lat=[None],
        mode='markers',
        marker=dict(size=10, color=color_map[consultant]),
        name=consultant,
        showlegend=True
    ))

# -----------------------------
# 6) Layout
# -----------------------------
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat":51.0,"lon":10.0},
    height=1000,
    legend=dict(
        title="Consultants",
        title_font=dict(color="black", size=20, family="Arial Black"),
        font=dict(color="black", size=16),
        bgcolor="rgba(255,255,255,0.9)",
        yanchor="top", y=0.99,
        xanchor="right", x=0.99,
        traceorder="normal"
    )
)

st.plotly_chart(fig, use_container_width=True)