import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🗺️ Vertriebsregionen Deutschland")

# Daten laden
plz_gdf = gpd.read_file("plz-2stellig.geojson")
bundeslaender = gpd.read_file("bundeslaender.geojson")

# Consultant zuordnen
plz_gdf["consultant"] = plz_gdf["plz"].apply(get_consultant)
plz_gdf["color"] = plz_gdf["consultant"].map(COLORS)

# Karte
m = folium.Map(location=[51.1, 10.4], zoom_start=6, tiles="cartodbpositron")

# PLZ Flächen
folium.GeoJson(
    plz_gdf,
    style_function=lambda x: {
        "fillColor": x["properties"]["color"],
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.6,
    },
    tooltip=folium.GeoJsonTooltip(fields=["plz", "consultant"])
).add_to(m)

# Bundesländer-Grenzen
folium.GeoJson(
    bundeslaender,
    style_function=lambda x: {
        "fillOpacity": 0,
        "color": "black",
        "weight": 1.2
    }
).add_to(m)

# Legende
legend_html = "<div style='position: fixed; bottom: 50px; left: 50px; background: white; padding: 10px; border:1px solid black;'>"
legend_html += "<b>Consultants</b><br>"
for name, color in COLORS.items():
    legend_html += f"<i style='background:{color};width:12px;height:12px;display:inline-block;'></i> {name}<br>"
legend_html += "</div>"
m.get_root().html.add_child(folium.Element(legend_html))

# Anzeigen
st_folium(m, width=1200, height=800)
