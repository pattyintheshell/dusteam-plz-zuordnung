import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
import os

st.set_page_config(layout="wide")
st.title("Dusteam PLZ Zuordnung")

# 1️⃣ Bundesländer hochladen
bundeslaender_file = st.file_uploader("Bundesländer GeoJSON", type="geojson")
if bundeslaender_file is not None:
    bundeslaender_gdf = gpd.read_file(bundeslaender_file)

# 2️⃣ PLZ-Dateien hochladen (mehrere)
plz_files = st.file_uploader("PLZ GeoJSONs (mehrere auswählen)", type="geojson", accept_multiple_files=True)
if plz_files:
    plz_gdfs = [gpd.read_file(f) for f in plz_files]
    plz_gdf = gpd.GeoDataFrame(pd.concat(plz_gdfs, ignore_index=True), crs="EPSG:4326")

    # 3️⃣ Consultant-Zuweisung
    CONSULTANTS = {
        "Dustin": ["77", "78", "79", "88"],
        "Tobias": ["81", "82", "83", "84"],
        "Philipp": ["32", "33", "40", "41", "42", "43", "44", "45", "46", "47", "48", "50", "51", "52", "53", "56", "57", "58", "59"],
        "Vanessa": ["10", "11", "12", "13", "20", "21", "22"],
        "Patricia": ["68", "69", "71", "74", "75", "76"],
        "Kathrin": ["80", "85", "86", "87"],
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

    # 4️⃣ Map erstellen
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

    # 5️⃣ Legende
    legend_html = "<div style='position: fixed; bottom: 50px; left: 50px; background: white; padding: 10px; border:1px solid black;'>"
    legend_html += "<b>Consultants</b><br>"
    for name, color in COLORS.items():
        legend_html += f"<i style='background:{color};width:12px;height:12px;display:inline-block;margin-right:5px;'></i>{name}<br>"
    legend_html += "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width=1200, height=800)
