import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import requests
import io

st.set_page_config(layout="wide")
st.title("🗺️ Dusteam Marktverteilung PLZ")

# -----------------------------
# 1️⃣ GitHub Repo & Release Infos
# -----------------------------
GITHUB_USER = "pattyintheshell"
REPO = "dusteam-plz-zuordnung"
BUNDESLAENDER_RELEASE_TAG = "v1.0-bundeslaender"
PLZ_RELEASE_TAG = "v1.0-plz"

# -----------------------------
# 2️⃣ Funktion: GeoJSON aus GitHub Release laden
# -----------------------------
def get_release_assets_urls(user, repo, tag):
    api_url = f"https://api.github.com/repos/{user}/{repo}/releases/tags/{tag}"
    r = requests.get(api_url)
    r.raise_for_status()
    release_data = r.json()
    urls = [asset['browser_download_url'] for asset in release_data['assets']]
    return urls

def read_geojson_from_github(url):
    r = requests.get(url)
    r.raise_for_status()
    return gpd.read_file(io.BytesIO(r.content))

# -----------------------------
# 3️⃣ Daten laden
# -----------------------------
# Bundesländer
bundeslaender_urls = get_release_assets_urls(GITHUB_USER, REPO, BUNDESLAENDER_RELEASE_TAG)
bundeslaender_gdf = read_geojson_from_github(bundeslaender_urls[0])  # nur eine Datei

# PLZ-Dateien
plz_urls = get_release_assets_urls(GITHUB_USER, REPO, PLZ_RELEASE_TAG)
plz_gdfs = [read_geojson_from_github(url) for url in plz_urls]
plz_gdf = gpd.GeoDataFrame(pd.concat(plz_gdfs, ignore_index=True), crs="EPSG:4326")

# -----------------------------
# 4️⃣ Consultants & Farben
# -----------------------------
CONSULTANTS = {
    "Dustin": ["77", "78", "79", "88"],
    "Tobias": ["81", "82", "83", "84"],
    "Philipp": ["32","33","40","41","42","43","44","45","46","47","48","50","51","52","53","56","57","58","59"],
    "Vanessa": ["10","11","12","13","20","21","22"],
    "Patricia": ["68","69","71","74","75","76"],
    "Kathrin": ["80","85","86","87"],
    "Sebastian": ["01","02","03","04","05","06","07","08","09","14","15","16","17","18","19"],
    "Sumak": ["90","91","92","93","94","95","96","97"],
    "Jonathan": ["70","72","73","89"]
}

COLORS = {
    "Dustin": "#1f77b4",
    "Tobias": "#ff7f0e",
    "Philipp": "#2ca02c",
    "Vanessa": "#d62728",
    "Patricia": "#9467bd",
    "Kathrin": "#8c564b",
    "Sebastian": "#e377c2",
    "Sumak": "#7f7f7f",
    "Jonathan": "#bcbd22"
}

plz_gdf['plz2'] = plz_gdf['plz'].str[:2]
def assign_consultant(plz2):
    for name, plzs in CONSULTANTS.items():
        if plz2 in plzs:
            return name
    return "Unassigned"
plz_gdf['consultant'] = plz_gdf['plz2'].apply(assign_consultant)

# -----------------------------
# 5️⃣ Karte erstellen
# -----------------------------
m = folium.Map(location=[51.2, 10.4], zoom_start=6, tiles="cartodbpositron")

for _, row in plz_gdf.iterrows():
    color = COLORS.get(row['consultant'], "#cccccc")
    folium.GeoJson(
        row['geometry'],
        style_function=lambda feature, col=color: {
            'fillColor': col,
            'color': 'black',
            'weight': 0.5,
            'fillOpacity': 0.6
        },
        tooltip=f"PLZ {row['plz']} – {row['consultant']}"
    ).add_to(m)

# -----------------------------
# 6️⃣ Legende
# -----------------------------
legend_html = "<div style='position: fixed; bottom: 50px; left: 50px; background: white; padding: 10px; border:1px solid black;'>"
legend_html += "<b>Consultants</b><br>"
for name, color in COLORS.items():
    legend_html += f"<i style='background:{color};width:12px;height:12px;display:inline-block;margin-right:5px;'></i>{name}<br>"
legend_html += "</div>"
m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=1200, height=800)
