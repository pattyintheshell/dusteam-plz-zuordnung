import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🗺️ Dusteam Marktverteilung PLZ")

# =====================
# CONSULTANTS
# =====================
CONSULTANTS = {
    "Dustin": ["77", "78", "79", "88"],
    "Tobias": ["81", "82", "83", "84"],
    "Philipp": ["32", "33", "40", "41", "42", "43", "44", "45", "46", "47", "48", "50", "51", "52", "53", "56", "57", "58", "59"],
    "Vanessa": ["10", "11", "12", "13", "20", "21", "22"],
    "Patricia": ["68", "69", "71", "74", "75", "76"],
    "Kathrin": ["80", "85", "86", "87"],
    "Sebastian": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "14", "15", "16", "17", "18", "19"],
    "Sumak": ["90", "91", "92", "93", "94", "95", "96", "97"],
    "Jonathan": ["70", "72", "73", "89"]
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

# =====================
# GITHUB RELEASE URLS
# =====================
BASE = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download"

BUNDESLAENDER_URL = f"{BASE}/v1.0-bundeslaender/bundeslaender.geojson"

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

PLZ_URLS = [f"{BASE}/v1.0-plz/{f}" for f in PLZ_FILES]

# =====================
# LOAD DATA
# =====================
bundeslaender_gdf = gpd.read_file(BUNDESLAENDER_URL)

plz_gdfs = [gpd.read_file(url) for url in PLZ_URLS]
plz_gdf = gpd.GeoDataFrame(pd.concat(plz_gdfs, ignore_index=True), crs="EPSG:4326")

# PLZ-Spalte robust finden
if "plz" in plz_gdf.columns:
    plz_col = "plz"
elif "postcode" in plz_gdf.columns:
    plz_col = "postcode"
else:
    st.error("Keine PLZ-Spalte gefunden.")
    st.stop()

plz_gdf["plz2"] = plz_gdf[plz_col].astype(str).str[:2]

def assign_consultant(plz2):
    for name, codes in CONSULTANTS.items():
        if plz2 in codes:
            return name
    return "Unassigned"

plz_gdf["consultant"] = plz_gdf["plz2"].apply(assign_consultant)

# =====================
# MAP
# =====================
m = folium.Map(location=[51.2, 10.4], zoom_start=6, tiles="cartodbpositron")

folium.GeoJson(
    bundeslaender_gdf,
    style_function=lambda x: {"fillOpacity": 0, "color": "black", "weight": 1},
).add_to(m)

for _, row in plz_gdf.iterrows():
    folium.GeoJson(
        row.geometry,
        style_function=lambda x, col=COLORS.get(row["consultant"], "#cccccc"): {
            "fillColor": col,
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.6,
        },
        tooltip=f"PLZ {row[plz_col]} – {row['consultant']}",
    ).add_to(m)

# =====================
# LEGEND
# =====================
legend_html = "<div style='position: fixed; bottom: 40px; left: 40px; background: white; padding: 10px; border:1px solid black; z-index:9999;'>"
legend_html += "<b>Consultants</b><br>"
for name, color in COLORS.items():
    legend_html += f"<i style='background:{color};width:12px;height:12px;display:inline-block;margin-right:5px;'></i>{name}<br>"
legend_html += "</div>"

m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=1200, height=800)
