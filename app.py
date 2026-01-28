import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
import requests
from io import BytesIO
from shapely.geometry import Polygon, MultiPolygon

st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam")

# -----------------------------
# 1) PLZ GeoJSON laden aus eigenem GitHub Release
# -----------------------------
PLZ_URL = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/PLZ%20GeoJSON/plz_deutschland.geojson"

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

categories = ['Dustin','Tobias','Philipp','Vanessa','Patricia','Kathrin',
              'Sebastian','Sumak','Jonathan','Unassigned']

# -----------------------------
# 4) Karte bauen: 1 Trace pro Consultant (PLZ 2-stellig)
# -----------------------------
fig = go.Figure()

for consultant in categories:
    subset = plz_gdf[plz_gdf['consultant'] == consultant]
    lons_all, lats_all, texts_all = [], [], []

    for _, row in subset.iterrows():
        geom = row.geometry
        polys = [geom] if isinstance(geom, Polygon) else geom.geoms
        for poly in polys:
            lons, lats = zip(*poly.exterior.coords)
            lons_all.extend(lons + (None,))
            lats_all.extend(lats + (None,))
            texts_all.extend([f"PLZ: {row['plz2']}<br>Consultant: {consultant}"]*len(lons) + [None])

    fig.add_trace(go.Scattermapbox(
        lon=lons_all,
        lat=lats_all,
        mode='lines',
        fill='toself',
        fillcolor=color_map[consultant],
        line=dict(color='black', width=1),
        hoverinfo='text',
        text=texts_all,
        name=consultant,
        showlegend=True,
        legendgroup=consultant
    ))

# -----------------------------
# 5) Bundesländer GeoJSON laden
# -----------------------------
BL_URL = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/Bundesländer%20GeoJSON/bundeslaender_deutschland.geojson"

r_bl = requests.get(BL_URL)
if r_bl.status_code != 200:
    st.error(f"Fehler beim Laden der Bundesländer GeoJSON: {r_bl.status_code}")
    st.stop()

bl_gdf = gpd.read_file(BytesIO(r_bl.content))

# -----------------------------
# 6) Bundesländer als Umrisse hinzufügen
# -----------------------------
for _, row in bl_gdf.iterrows():
    geom = row.geometry
    polys = [geom] if isinstance(geom, Polygon) else geom.geoms
    for poly in polys:
        lons, lats = zip(*poly.exterior.coords)
        fig.add_trace(go.Scattermapbox(
            lon=lons + (None,),
            lat=lats + (None,),
            mode='lines',
            line=dict(color='black', width=2),
            fill=None,
            hoverinfo='skip',
            showlegend=False
        ))

# -----------------------------
# 7) Layout: schwebende, mobilfreundliche Legende
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