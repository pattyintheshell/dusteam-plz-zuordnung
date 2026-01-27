import streamlit as st
import geopandas as gpd
import pandas as pd
import pydeck as pdk

st.set_page_config(page_title="🗺️ Dusteam Marktverteilung PLZ", layout="wide")
st.title("🗺️ Dusteam Marktverteilung PLZ")

# --------------------------
# GitHub Release Links
# --------------------------
GITHUB_USER = "pattyintheshell"
REPO = "dusteam-plz-zuordnung"

# PLZ-Dateien
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

# Bundesländer-Datei
BUNDESLAENDER_FILE = f"https://github.com/{GITHUB_USER}/{REPO}/releases/download/v1.0-bundeslaender/bundeslaender.geojson"

# --------------------------
# Consultant Zuordnung
# --------------------------
consultants = {
    "Dustin": ["77","78","79","88"],
    "Tobias": ["81","82","83","84"],
    "Philipp": ["32","33","40","41","42","43","44","45","46","47","48","50","51","52","53","56","57","58","59"],
    "Vanessa": ["10","11","12","13","20","21","22"],
    "Patricia": ["68","69","71","74","75","76"],
    "Kathrin": ["80","85","86","87"],
    "Sebastian": ["01","02","03","04","05","06","07","08","09","14","15","16","17","18","19"],
    "Sumak": ["90","91","92","93","94","95","96","97"],
    "Jonathan": ["70","72","73","89"]
}

# Farben für Consultant
consultant_colors = {
    "Dustin": [255,0,0,150],
    "Tobias": [0,255,0,150],
    "Philipp": [0,0,255,150],
    "Vanessa": [255,165,0,150],
    "Patricia": [128,0,128,150],
    "Kathrin": [0,255,255,150],
    "Sebastian": [255,192,203,150],
    "Sumak": [128,128,0,150],
    "Jonathan": [0,128,128,150],
    "Unassigned": [200,200,200,50]
}

# --------------------------
# GeoJSON laden
# --------------------------
@st.cache_data
def load_data():
    gdfs = []
    for url in PLZ_URLS:
        gdf = gpd.read_file(url)
        # PLZ-2er extrahieren
        plz_col = next((c for c in gdf.columns if c.lower() in ["plz","postcode","postal_code","zip"]), None)
        gdf["PLZ2"] = gdf[plz_col].astype(str).str[:2] if plz_col else "unknown"

        # Consultant zuweisen
        gdf["Consultant"] = gdf["PLZ2"].apply(
            lambda x: next((c for c, codes in consultants.items() if x in codes), "Unassigned")
        )

        # Farbe
        gdf["color"] = gdf["Consultant"].apply(lambda c: consultant_colors.get(c,[100,100,100,100]))

        # Polygon in Liste konvertieren für PyDeck
        def polygon_to_coords(geom):
            if geom.geom_type == 'Polygon':
                return [list(geom.exterior.coords)]
            elif geom.geom_type == 'MultiPolygon':
                return [list(p.exterior.coords) for p in geom.geoms]
            else:
                return []
        gdf["polygon_coords"] = gdf["geometry"].apply(polygon_to_coords)

        gdfs.append(gdf)

    all_gdf = pd.concat(gdfs, ignore_index=True)
    return gpd.GeoDataFrame(all_gdf, crs=gdfs[0].crs)

with st.spinner("Lade PLZ-2er Gebiete …"):
    plz_gdf = load_data()

st.success("Daten erfolgreich geladen ✅")
st.write(f"**PLZ-2er Gebiete:** {len(plz_gdf)}")

# --------------------------
# Bundesländer
# --------------------------
with st.spinner("Lade Bundesländer …"):
    bundeslaender_gdf = gpd.read_file(BUNDESLAENDER_FILE)

# Polygon-Layer für PLZ
plz_layer = pdk.Layer(
    "PolygonLayer",
    plz_gdf,
    get_polygon="polygon_coords",
    get_fill_color="color",
    get_line_color=[0,0,0,50],
    pickable=True,
    auto_highlight=True
)

# Linien-Layer für Bundesländer
bundes_layer = pdk.Layer(
    "PolygonLayer",
    bundeslaender_gdf,
    get_polygon=lambda d: [list(d.exterior.coords)] if d.geom_type=="Polygon" else [list(p.exterior.coords) for p in d.geoms],
    get_fill_color=[0,0,0,0],
    get_line_color=[50,50,50,150],
    stroked=True,
    pickable=False
)

view_state = pdk.ViewState(latitude=51.0, longitude=10.0, zoom=5)

st.pydeck_chart(
    pdk.Deck(
        layers=[plz_layer, bundes_layer],
        initial_view_state=view_state,
        tooltip={"text": "PLZ-2er: {PLZ2}\nConsultant: {Consultant}"}
    )
)
