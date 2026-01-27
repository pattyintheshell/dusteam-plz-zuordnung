import streamlit as st
import geopandas as gpd
import plotly.express as px
import requests
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam")

# -----------------------------
# 1) 2er-PLZ GeoJSON laden
# -----------------------------
geojson_url = "https://raw.githubusercontent.com/tdudek/de-plz-geojson/master/plz-2stellig.geojson"
r = requests.get(geojson_url)
if r.status_code != 200:
    st.error(f"Fehler beim Laden der GeoJSON: {r.status_code}")
    st.stop()

plz_gdf = gpd.read_file(BytesIO(r.content))

# -----------------------------
# 2) 2er-PLZ erstellen
# -----------------------------
if 'plz' not in plz_gdf.columns:
    st.error("Keine PLZ-Spalte in der GeoJSON gefunden!")
    st.stop()

plz_gdf['plz2'] = plz_gdf['plz'].astype(str).str[:2]

# -----------------------------
# 3) Consultant-Zuordnung
# -----------------------------
plz_mapping = {
    'Dustin': ['77', '78', '79', '88'],
    'Tobias': ['81', '82', '83', '84'],
    'Philipp': ['32', '33', '40', '41', '42', '43', '44', '45', '46', '47', '48', '50', '51', '52', '53', '56', '57', '58', '59'],
    'Vanessa': ['10', '11', '12', '13', '20', '21', '22'],
    'Patricia': ['68', '69', '71', '74', '75', '76'],
    'Kathrin': ['80', '85', '86', '87'],
    'Sebastian': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '14', '15', '16', '17', '18', '19'],
    'Sumak': ['90', '91', '92', '93', '94', '95', '96', '97'],
    'Jonathan': ['70', '72', '73', '89']
}

plz2_to_consultant = {}
for consultant, plz_list in plz_mapping.items():
    for p in plz_list:
        plz2_to_consultant[p] = consultant

plz_gdf['consultant'] = plz_gdf['plz2'].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# 4) Farben festlegen
# -----------------------------
color_map = {
    'Dustin': '#1f77b4',    # blau
    'Tobias': '#ff7f0e',    # orange
    'Philipp': '#2ca02c',   # grün
    'Vanessa': '#d62728',   # rot
    'Patricia': '#9467bd',  # lila
    'Kathrin': '#8c564b',   # braun
    'Sebastian': '#e377c2', # pink
    'Sumak': '#17becf',     # türkis
    'Jonathan': '#bcbd22',  # oliv
    'Unassigned': '#c0c0c0' # grau
}

# -----------------------------
# 5) Karte plotten
# -----------------------------
fig = px.choropleth_mapbox(
    plz_gdf,
    geojson=plz_gdf.geometry,
    locations=plz_gdf.index,
    color='consultant',
    color_discrete_map=color_map,
    mapbox_style="carto-positron",
    zoom=5,
    center={"lat": 51.0, "lon": 10.0},
    opacity=0.6,
    hover_data={'plz2': True, 'consultant': True},
    height=1000
)

# Hover nur Consultant + PLZ
fig.update_traces(
    hovertemplate="<b>Consultant:</b> %{customdata[1]}<br><b>PLZ:</b> %{customdata[0]}<extra></extra>"
)

# Umrisse
fig.update_traces(marker_line_width=1, marker_line_color="black")

st.plotly_chart(fig, use_container_width=True)
