import streamlit as st
import geopandas as gpd
import pandas as pd

st.set_page_config(page_title="🗺️ Dusteam Marktverteilung PLZ", layout="wide")
st.title("🗺️ Dusteam Marktverteilung PLZ")

GITHUB_USER = "pattyintheshell"
REPO = "dusteam-plz-zuordnung"

# ---------- Direkt-Links (KEINE API) ----------

BUNDESLAENDER_URL = (
    "https://github.com/pattyintheshell/dusteam-plz-zuordnung/"
    "releases/download/v1.0-bundeslaender/bundeslaender.geojson"
)

PLZ_FILES = [
    "badenwuerttemberg.geojson",
    "bayern.geojson",
    "berlin.geojson",
    "brandenburg.geojson",
    "bremen.geojson",
    "hamburg.geojson",
    "hessen.geojson",
    "mecklenburgvorpommern.geojson",
    "niedersachsen.geojson",
    "nordrheinwestfalen.geojson",
    "rheinlandpfalz.geojson",
    "saarland.geojson",
    "sachsen.geojson",
    "sachsenanhalt.geojson",
    "schleswigholstein.geojson",
    "thueringen.geojson",
]

PLZ_URLS = [
    f"https://github.com/{GITHUB_USER}/{REPO}/releases/download/v1.0-plz/{name}"
    for name in PLZ_FILES
]

# ---------- Laden ----------

@st.cache_data
def load_data():
    bundeslaender = gpd.read_file(BUNDESLAENDER_URL)

    plz_gdfs = []
    for url in PLZ_URLS:
        gdf = gpd.read_file(url)
        plz_gdfs.append(gdf)

    plz = pd.concat(plz_gdfs, ignore_index=True)
    return bundeslaender, plz


with st.spinner("Lade Geodaten …"):
    bundeslaender_gdf, plz_gdf = load_data()

st.success("Daten erfolgreich geladen ✅")

st.write("**Bundesländer:**", len(bundeslaender_gdf))
st.write("**PLZ-Flächen:**", len(plz_gdf))

import pydeck as pdk

geojson_data = plz_gdf.__geo_interface__

layer = pdk.Layer(
    "GeoJsonLayer",
    geojson_data,
    pickable=True,
    stroked=True,
    filled=True,
    get_fill_color="[200, 30, 0, 80]",
    get_line_color="[0, 0, 0, 200]",
    line_width_min_pixels=0.5,
)

view_state = pdk.ViewState(
    latitude=51.0,
    longitude=10.0,
    zoom=5,
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "PLZ: {plz}"},
    )
)
