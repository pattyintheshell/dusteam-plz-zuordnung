import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk

# =========================
# STREAMLIT CONFIG
# =========================
st.set_page_config(page_title="🗺️ Dusteam Marktverteilung PLZ", layout="wide")
st.title("🗺️ Dusteam Marktverteilung PLZ")

# =========================
# GITHUB RELEASES - DIREKTLINKS
# =========================
GITHUB_USER = "pattyintheshell"
REPO = "dusteam-plz-zuordnung"

BUNDESLAENDER_URL = (
    f"https://github.com/{GITHUB_USER}/{REPO}/releases/download/v1.0-bundeslaender/bundeslaender.geojson"
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

# =========================
# DATEN LADEN
# =========================
@st.cache_data
def load_data():
    # Bundesländer
    bundeslaender = gpd.read_file(BUNDESLAENDER_URL)

    # PLZ
    plz_gdfs = []
    for url in PLZ_URLS:
        gdf = gpd.read_file(url)
        # Spalte für PLZ sicherstellen
        plz_col = None
        for col in gdf.columns:
            if col.lower() in ["plz", "postcode", "postal_code", "zip"]:
                plz_col = col
                break
        if plz_col is None:
            gdf["PLZ"] = "unknown"
        else:
            gdf["PLZ"] = gdf[plz_col].astype(str)

        plz_gdfs.append(gdf)

    plz_gdf = pd.concat(plz_gdfs, ignore_index=True)
    plz_gdf = gpd.GeoDataFrame(plz_gdf, crs=plz_gdfs[0].crs)
    return bundeslaender, plz_gdf

with st.spinner("Lade Geodaten …"):
    bundeslaender_gdf, plz_gdf = load_data()

st.success("Daten erfolgreich geladen ✅")
st.write(f"**Bundesländer:** {len(bundeslaender_gdf)}")
st.write(f"**PLZ-Flächen:** {len(plz_gdf)}")

# =========================
# PYDECK MAP (Zentroiden)
# =========================
plz_points = plz_gdf.copy()
plz_points["geometry"] = plz_points["geometry"].centroid

layer = pdk.Layer(
    "ScatterplotLayer",
    plz_points,
    get_position="[geometry.x, geometry.y]",
    get_fill_color="[200, 30, 0, 180]",
    get_line_color="[0, 0, 0, 200]",
    get_radius=3000,
    pickable=True,
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
        tooltip={"text": "PLZ: {PLZ}"},
    )
)
