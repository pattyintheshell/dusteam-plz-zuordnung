import streamlit as st
import geopandas as gpd
import plotly.express as px
import requests
from io import BytesIO

st.set_page_config(layout="wide")
st.title("Vertriebsgebiete Deutschland")

# -----------------------------
# 1. Bundesländer laden
# -----------------------------
bundeslaender_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-bundeslaender/bundeslaender_deutschland.geojson"
bundeslaender_bytes = BytesIO(requests.get(bundeslaender_url).content)
bundeslaender = gpd.read_file(bundeslaender_bytes)

# -----------------------------
# 2. PLZ laden
# -----------------------------
plz_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_deutschland.geojson"
plz_bytes = BytesIO(requests.get(plz_url).content)
plz = gpd.read_file(plz_bytes)

# -----------------------------
# 3. 2er PLZ zusammenführen
# -----------------------------
plz['plz2'] = plz['plz'].str[:2]
plz_2er = plz.dissolve(by='plz2').reset_index()

# -----------------------------
# 4. Consultant-Zuordnung
# -----------------------------
# Hier einfach eure Vertriebszuordnung eintragen
plz_mapping = {
    '68': 'Anna',
    '69': 'Ben',
    '70': 'Clara',
    '71': 'David',
    # weitere 2er PLZ hier hinzufügen
}

plz_2er['consultant'] = plz_2er['plz2'].map(plz_mapping)

# -----------------------------
# 5. Plot mit Plotly
# -----------------------------
fig = px.choropleth_mapbox(
    plz_2er,
    geojson=plz_2er.geometry,
    locations=plz_2er.index,
    color='consultant',
    mapbox_style="carto-positron",
    zoom=5,
    center={"lat": 51.0, "lon": 10.0},
    opacity=0.5,
    hover_data={'plz2':True, 'consultant':True}
)

# Bundesländer-Umriss drüberlegen
fig.update_traces(marker_line_width=1, marker_line_color="black")

st.plotly_chart(fig, use_container_width=True)
