import streamlit as st
import geopandas as gpd
import pydeck as pdk
import requests
import io

st.set_page_config(layout="wide")
st.title("🗺️ Dusteam Marktverteilung PLZ")

# -------------------------------
# GitHub Release URL für PLZ-GeoJSON
# -------------------------------
PLZ_URL = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.1-plz2/plz_2er.geojson.geojson"

# -------------------------------
# PLZ-Zuordnung zu Beratern
# -------------------------------
berater_mapping = {
    "Dustin": ["77","78","79","88"],
    "Tobias": ["81","82","83","84"],
    "Philipp": ["32","33","40","41","42","43","44","45","46","47","48","50","51","52","53","56","57","58","59"],
    "Vanessa": ["10","11","12","13","20","21","22"],
    "Patricia": ["68","69","71","74","75","76"],
    "Kathrin": ["80","85","86","87"],
    "Sebastian": ["01","02","03","04","05","06","07","08","09","14","15","16","17","18","19"],
    "Sumak": ["90","91","92","93","94","95","96","97"],
    "Jonathan": ["70","72","73","89"],
}

# Farben pro Berater (RGBA)
farben = {
    "Dustin":[255,0,0,120],
    "Tobias":[0,255,0,120],
    "Philipp":[0,0,255,120],
    "Vanessa":[255,165,0,120],
    "Patricia":[255,192,203,120],
    "Kathrin":[128,0,128,120],
    "Sebastian":[0,255,255,120],
    "Sumak":[255,255,0,120],
    "Jonathan":[128,128,128,120],
}

# -------------------------------
# Funktion: GeoJSON von GitHub laden
# -------------------------------
@st.cache_data
def load_geojson(url):
    try:
        r = requests.get(url)
        r.raise_for_status()
        gdf = gpd.read_file(io.BytesIO(r.content))
        return gdf
    except Exception as e:
        st.error(f"Fehler beim Laden der GeoJSON: {e}")
        return None

plz_gdf = load_geojson(PLZ_URL)

# -------------------------------
# Berater-Spalte hinzufügen
# -------------------------------
if plz_gdf is not None:
    # Extrahiere 2-stellige PLZ als String
    plz_gdf["plz_2er"] = plz_gdf["PLZ"].astype(str).str[:2]

    def get_berater(plz2):
        for name, plz_list in berater_mapping.items():
            if plz2 in plz_list:
                return name
        return "Unassigned"

    plz_gdf["Berater"] = plz_gdf["plz_2er"].apply(get_berater)

    # Farbe zuweisen
    plz_gdf["color"] = plz_gdf["Berater"].apply(lambda x: farben.get(x,[200,200,200,100]))

    st.success(f"Daten erfolgreich geladen ✅\nPLZ-2er Gebiete: {len(plz_gdf)}")

    # -------------------------------
    # PyDeck Polygon Layer
    # -------------------------------
    plz_gdf["coordinates"] = plz_gdf["geometry"].apply(
        lambda poly: [list(poly.exterior.coords)] if poly.geom_type=="Polygon" else [list(p.exterior.coords) for p in poly.geoms]
    )

    layer = pdk.Layer(
        "PolygonLayer",
        plz_gdf,
        get_polygon="coordinates",
        get_fill_color="color",
        get_line_color=[0,0,0,200],
        pickable=True,
        auto_highlight=True,
    )

    view_state = pdk.ViewState(
        longitude=10.5,
        latitude=51.2,
        zoom=5,
        min_zoom=4,
        max_zoom=10,
        pitch=0,
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{Berater}\nPLZ-2er: {plz_2er}"}
    )

    st.pydeck_chart(r)
else:
    st.error("Keine Daten zum Anzeigen.")
