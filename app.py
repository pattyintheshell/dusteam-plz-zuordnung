import streamlit as st
import geopandas as gpd
import requests
from io import BytesIO

st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam - PLZ Check")

# ---- PLZ laden ----
plz_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_deutschland.geojson"
plz_bytes = BytesIO(requests.get(plz_url).content)
plz = gpd.read_file(plz_bytes)

# ---- Spalten anzeigen ----
st.write("PLZ GeoJSON Spalten:", plz.columns)

# ---- Erste Zeilen anzeigen ----
st.write(plz.head())
