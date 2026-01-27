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
# Daten laden
# --------------------------
@st.cache_data
def load_plz_data():
    gdfs = []
    for url in PLZ_URLS:
        gdf = gpd.read_file(url)
        plz_col = next((c for c in gdf.columns if c.lower() in ["plz","postcode","postal_code","zip"]), None)
        gdf["PLZ2"] = gdf[plz_col].astype(str).str[:2] if plz_col else "unknown"
        gdf["Consultant"] = gdf["PLZ2"].apply(
            lambda x: next((c for c, codes in consultants.items() if x in codes), "Unassigned")
        )
        gdf["color"] = gdf["Consultant"].apply(lambda c: consultant_colors.get(c,[100,100,100,100]))

        # Polygon → Liste für PyDeck
        def poly_to_coords(geom):
            if geom.geom_type == "Polygon":
                return [list(geom.exterior.coords)]
            elif geom.geom_type == "MultiPolygon":
                return [list(p.exterior.coords) for p in geom.geoms]
            else:
                return []
        gdf["polygon_coords"] = gdf["geometry"].apply(poly_to_coords)
        gdfs.append(gdf)
    return pd.concat(gdfs, ignore_index=True)

@st.cache_data
def load_bundeslaender():
    gdf = gpd.read_file(BUNDESLAENDER_FILE)
    # Polygon → Liste für PyDeck
    def poly_to_coords(geom):
        if geom.geom_type == "Polygon":
            return [list(geom.exterior.coords)]
        elif geom.geom_type == "MultiPolygon":
            return [list(p.exterior.coords) for p in geom.geoms]
        else:
            return []
    gdf["polygon_coords"] = gdf["geometry"].apply(poly_to_coords)
    return gdf

with st.spinner("Lade PLZ-2er Gebiete …"):
    plz_gdf = load_plz_data()
st.success(f"Daten geladen: {len(plz_gdf)} PLZ-2er Gebiete")

with st.spinner("Lade Bundesländer …"):
    bundes_gdf = load_bundeslaender()
st.success(f"Bundesländer geladen: {len(bundes_gdf)}")

# --------------------------
# PyDeck Layer
# --------------------------
plz_layer = pdk.Layer(
    "PolygonLayer",
    plz_gdf,
    get_polygon="polygon_coords",
    get_fill_color="color",
    get_line_color=[0,0,0,50],
    pickable=True,
    auto_highlight=True
)

bundes_layer = pdk.Layer(
    "PolygonLayer",
    bundes_gdf,
    get_polygon="polygon_coords",
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
