import streamlit as st
import requests
import geopandas as gpd
import pandas as pd
import io

# =========================
# KONFIG
# =========================
GITHUB_USER = "pattyintheshell"
REPO = "dusteam-plz-zuordnung"

BUNDESLAENDER_RELEASE_TAG = "v1.0-bundeslaender"
PLZ_RELEASE_TAG = "v1.0-plz"

# =========================
# HILFSFUNKTIONEN
# =========================

def get_release_assets_urls(user, repo, tag):
    url = f"https://api.github.com/repos/{user}/{repo}/releases/tags/{tag}"
    r = requests.get(url)
    r.raise_for_status()
    data = r.json()

    urls = {}
    for asset in data["assets"]:
        name = asset["name"]
        if name.endswith(".geojson"):
            urls[name] = asset["browser_download_url"]

    return urls


def read_geojson_from_github(url):
    r = requests.get(url)
    r.raise_for_status()
    return gpd.read_file(io.BytesIO(r.content))


def find_plz_column(gdf):
    for col in gdf.columns:
        if col.lower() in ["plz", "postcode", "postal_code", "zip"]:
            return col
    raise ValueError("Keine PLZ-Spalte gefunden.")


# =========================
# STREAMLIT UI
# =========================

st.set_page_config(layout="wide")
st.title("🗺️ Dusteam Marktverteilung PLZ")

st.write("Lade Geodaten aus GitHub Releases …")

# =========================
# DATEN LADEN
# =========================

try:
    bundeslaender_urls = get_release_assets_urls(
        GITHUB_USER, REPO, BUNDESLAENDER_RELEASE_TAG
    )
    plz_urls = get_release_assets_urls(
        GITHUB_USER, REPO, PLZ_RELEASE_TAG
    )

    bundeslaender_gdf = read_geojson_from_github(
        list(bundeslaender_urls.values())[0]
    )

    plz_gdfs = []
    for name, url in plz_urls.items():
        gdf = read_geojson_from_github(url)

        plz_col = find_plz_column(gdf)
        gdf["PLZ"] = gdf[plz_col].astype(str)

        plz_gdfs.append(gdf)

    plz_gdf = gpd.GeoDataFrame(
        pd.concat(plz_gdfs, ignore_index=True),
        crs=plz_gdfs[0].crs
    )

except Exception as e:
    st.error(f"Fehler beim Laden der Daten: {e}")
    st.stop()

# =========================
# MAP
# =========================

st.success("Daten erfolgreich geladen ✅")
st.map(plz_gdf)
