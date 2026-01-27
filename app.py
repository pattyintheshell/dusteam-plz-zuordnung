import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
import pandas as pd
import requests
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam")

# -----------------------------
# 1) PLZ GeoJSON direkt online laden
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
    'Dustin': ['77', '78', '79', '88'],
    'Tobias': ['81', '82', '83', '84'],
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
    'Dustin': '#1f77b4', 'Tobias': '#ff7f0e', 'Philipp': '#2ca02c',
    'Vanessa': '#d62728', 'Patricia': '#9467bd', 'Kathrin': '#8c564b',
    'Sebastian': '#e377c2', 'Sumak': '#17becf', 'Jonathan': '#bcbd22',
    'Unassigned': '#c0c0c0'
}

# -----------------------------
# 4) Karte vorbereiten
# -----------------------------
fig = go.Figure()

for consultant, color in color_map.items():
    subset = plz_gdf[plz_gdf['consultant'] == consultant]
    fig.add_trace(
        go.Choroplethmapbox(
            geojson=subset.geometry.__geo_interface__,
            locations=subset.index,
            z=[1]*len(subset),
            showscale=False,
            marker_opacity=0.6,
            marker_line_width=1,
            marker_line_color="black",
            name=consultant,
            hovertemplate="<b>Consultant:</b> %{customdata[1]}<br><b>PLZ:</b> %{customdata[0]}<extra></extra>",
            customdata=subset[['plz2','consultant']].values
        )
    )

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
        traceorder="normal",
        yanchor="top", y=0.99,
        xanchor="right", x=0.99
    )
)

st.plotly_chart(fig, use_container_width=True)