import streamlit as st
import geopandas as gpd
import pydeck as pdk

st.set_page_config(page_title="🗺️ Dusteam Marktverteilung PLZ", layout="wide")
st.title("🗺️ Dusteam Marktverteilung PLZ")

# --------------------------
# Pfad zur neuen PLZ-2er Datei
# --------------------------
PLZ_2ER_FILE = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_2er.geojson"

# --------------------------
# Lade Daten
# --------------------------
@st.cache_data
def load_plz_2er():
    gdf = gpd.read_file(PLZ_2ER_FILE)
    gdf["polygon_coords"] = gdf["geometry"].apply(lambda geom: [list(p.exterior.coords) for p in geom.geoms] 
                                                  if geom.geom_type=="MultiPolygon" else [list(geom.exterior.coords)])
    return gdf

with st.spinner("Lade PLZ-2er Daten…"):
    plz_gdf = load_plz_2er()

st.success(f"PLZ-2er Gebiete geladen: {len(plz_gdf)}")

# --------------------------
# PyDeck Karte
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

view_state = pdk.ViewState(latitude=51.0, longitude=10.0, zoom=5)

st.pydeck_chart(
    pdk.Deck(
        layers=[plz_layer],
        initial_view_state=view_state,
        tooltip={"text": "PLZ-2er: {PLZ2}\nConsultant: {Consultant}"}
    )
)
