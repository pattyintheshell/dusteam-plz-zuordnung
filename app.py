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

# --------------------------
# Farben nach Consultant
# --------------------------
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
def load_data():
    gdfs = []
    for url in PLZ_URLS:
        gdf = gpd.read_file(url)
        # PLZ-Spalte finden
        plz_col = None
        for col in gdf.columns:
            if col.lower() in ["plz","postcode","postal_code","zip"]:
                plz_col = col
                break
        if plz_col is None:
            gdf["PLZ2"] = "unknown"
        else:
            gdf["PLZ2"] = gdf[plz_col].astype(str).str[:2]  # nur 2-stellig

        # Consultant zuweisen
        gdf["Consultant"] = gdf["PLZ2"].apply(
            lambda x: next((c for c, codes in consultants.items() if x in codes), "Unassigned")
        )

        # Farbe für PyDeck
        gdf["color"] = gdf["Consultant"].apply(lambda c: consultant_colors.get(c,[100,100,100,100]))
        gdfs.append(gdf)

    all_gdf = pd.concat(gdfs, ignore_index=True)
    return gpd.GeoDataFrame(all_gdf, crs=gdfs[0].crs)

with st.spinner("Lade PLZ-2er Gebiete …"):
    plz_gdf = load_data()

st.success("Daten erfolgreich geladen ✅")
st.write(f"**PLZ-2er Gebiete:** {len(plz_gdf)}")

# --------------------------
# PyDeck Polygon-Layer
# --------------------------
layer = pdk.Layer(
    "PolygonLayer",
    plz_gdf,
    get_polygon="geometry.coordinates",
    get_fill_color="color",
    get_line_color=[0,0,0,50],
    pickable=True,
    auto_highlight=True
)

view_state = pdk.ViewState(latitude=51.0, longitude=10.0, zoom=5)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{Consultant}\nPLZ-2er: {PLZ2}"}
    )
)
