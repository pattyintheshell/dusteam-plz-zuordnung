import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🗺️ Vertriebsregionen Deutschland (mit echten PLZ-Gebieten)")

# ------------------------
# 1️⃣ Consultant + PLZ-Zuweisung
# ------------------------
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

# ------------------------
# 2️⃣ PLZ-Flächen laden
# ------------------------
plz_url = "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_plz/2_plz.geojson"
plz_gdf = gpd.read_file(plz_url)

# Prüfen, wie die PLZ-Spalte heißt
if "plz" in plz_gdf.columns:
    plz_col = "plz"
elif "PLZ" in plz_gdf.columns:
    plz_col = "PLZ"
else:
    st.error("Keine PLZ-Spalte gefunden im GeoJSON!")
    st.stop()

plz_gdf[plz_col] = plz_gdf[plz_col].astype(str).str.zfill(5)
plz_gdf['plz2'] = plz_gdf[plz_col].str[:2]

# Consultant zuweisen
def assign_consultant(plz2):
    for name, prefixes in CONSULTANTS.items():
        if plz2 in prefixes:
            return name
    return "Unassigned"

plz_gdf['consultant'] = plz_gdf['plz2'].apply(assign_consultant)

# ------------------------
# 3️⃣ Bundesländer laden
# ------------------------
bl_url = "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/1_bundeslaender/bundeslaender.geojson"
bl_gdf = gpd.read_file(bl_url)

# ------------------------
# 4️⃣ Map erstellen
# ------------------------
m = folium.Map(location=[51.2, 10.4], zoom_start=6, tiles="cartodbpositron")

# PLZ-Flächen einfärben (nur relevante PLZ)
for _, row in plz_gdf.iterrows():
    if row['consultant'] != "Unassigned":  # optional: nur Consultant-PLZ anzeigen
        color = COLORS.get(row['consultant'], "#cccccc")
        folium.GeoJson(
            row['geometry'],
            style_function=lambda feature, col=color: {
                'fillColor': col,
                'color': 'black',
                'weight': 0.3,
                'fillOpacity': 0.6
            },
            tooltip=f"PLZ {row[plz_col]} – {row['consultant']}"
        ).add_to(m)

# Bundesländer-Grenzen drüber legen
folium.GeoJson(
    bl_gdf,
    style_function=lambda feature: {
        'color': 'black',
        'weight': 2,
        'fillOpacity': 0
    },
    tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Bundesland"])
).add_to(m)

# ------------------------
# 5️⃣ Legende
# ------------------------
legend_html = "<div style='position: fixed; bottom: 50px; left: 50px; background: white; padding: 10px; border:1px solid black;'>"
legend_html += "<b>Consultants</b><br>"
for name, color in COLORS.items():
    legend_html += f"<i style='background:{color};width:12px;height:12px;display:inline-block;margin-right:5px;'></i>{name}<br>"
legend_html += "</div>"
m.get_root().html.add_child(folium.Element(legend_html))

# ------------------------
# 6️⃣ Streamlit-Anzeige
# ------------------------
st_folium(m, width=1200, height=800)
