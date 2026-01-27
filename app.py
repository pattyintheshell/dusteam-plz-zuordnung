import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="🗺️ Dusteam Marktverteilung PLZ", layout="wide")
st.title("🗺️ Dusteam Marktverteilung PLZ")

# --------------------------
# GitHub Release-Links
# --------------------------
GITHUB_USER = "pattyintheshell"
REPO = "dusteam-plz-zuordnung"

BUNDESLAENDER_URL = f"https://github.com/{GITHUB_USER}/{REPO}/releases/download/v1.0-bundeslaender/bundeslaender.geojson"

PLZ_FILES = [
    "badenwuerttemberg.geojson","bayern.geojson","berlin.geojson","brandenburg.geojson",
    "bremen.geojson","hamburg.geojson","hessen.geojson","mecklenburgvorpommern.geojson",
    "niedersachsen.geojson","nordrheinwestfalen.geojson","rheinlandpfalz.geojson","saarland.geojson",
    "sachsen.geojson","sachsenanhalt.geojson","schleswigholstein.geojson","thueringen.geojson"
]

PLZ_URLS = [
    f"https://github.com/{GITHUB_USER}/{REPO}/releases/download/v1.0-plz/{name}"
    for name in PLZ_FILES
]

# --------------------------
# Daten laden
# --------------------------
@st.cache_data
def load_data():
    # Bundesländer
    bundeslaender = gpd.read_file(BUNDESLAENDER_URL)

    # PLZ
    plz_list = []
    for url in PLZ_URLS:
        gdf = gpd.read_file(url)
        # PLZ-Spalte finden
        plz_col = None
        for col in gdf.columns:
            if col.lower() in ["plz","postcode","postal_code","zip"]:
                plz_col = col
                break
        if plz_col is None:
            gdf["PLZ"] = "unknown"
        else:
            gdf["PLZ"] = gdf[plz_col].astype(str)
        # Zentroiden extrahieren
        gdf["lon"] = gdf.geometry.centroid.x
        gdf["lat"] = gdf.geometry.centroid.y
        plz_list.append(gdf[["PLZ","lat","lon"]])

    plz_df = pd.concat(plz_list, ignore_index=True)
    return bundeslaender, plz_df

with st.spinner("Lade Geodaten …"):
    bundeslaender_gdf, plz_df = load_data()

st.success("Daten erfolgreich geladen ✅")
st.write(f"**Bundesländer:** {len(bundeslaender_gdf)}")
st.write(f"**PLZ-Punkte:** {len(plz_df)}")

# --------------------------
# PyDeck Scatterplot
# --------------------------
layer = pdk.Layer(
    "ScatterplotLayer",
    plz_df,
    get_position='[lon, lat]',
    get_fill_color='[200, 30, 0, 180]',
    get_line_color='[0,0,0,200]',
    get_radius=3000,
    pickable=True
)

view_state = pdk.ViewState(latitude=51.0, longitude=10.0, zoom=5)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "PLZ: {PLZ}"}
    )
)
