import streamlit as st
import geopandas as gpd
import pydeck as pdk

# -------------------------------
# Titel der App
# -------------------------------
st.title("🗺️ Dusteam Marktverteilung PLZ")

# -------------------------------
# GeoJSON-Datei laden
# -------------------------------
PLZ_FILE = "plz_2er.geojson"

@st.cache_data
def load_geojson(file_path):
    try:
        gdf = gpd.read_file(file_path)
        return gdf
    except Exception as e:
        st.error(f"Fehler beim Laden der Datei: {e}")
        return None

plz_gdf = load_geojson(PLZ_FILE)

if plz_gdf is not None:
    st.success(f"Daten erfolgreich geladen ✅\nPLZ-2er Gebiete: {len(plz_gdf)}")

    # -------------------------------
    # PyDeck-Karte
    # -------------------------------
    # Wir nutzen die Centroid-Koordinaten der Flächen für die Deck-Visualisierung
    plz_gdf["centroid_lon"] = plz_gdf.geometry.centroid.x
    plz_gdf["centroid_lat"] = plz_gdf.geometry.centroid.y

    # PyDeck Layer
    layer = pdk.Layer(
        "PolygonLayer",
        plz_gdf,
        pickable=True,
        stroked=True,
        filled=True,
        get_polygon="coordinates",
        get_fill_color=[200, 30, 0, 100],
        get_line_color=[0, 0, 0, 200],
        auto_highlight=True,
    )

    # Deck-Objekt
    view_state = pdk.ViewState(
        longitude=10.5,  # ungefähr Mitte Deutschland
        latitude=51.2,
        zoom=5,
        min_zoom=4,
        max_zoom=10,
        pitch=0,
    )

    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{PLZ}"})

    st.pydeck_chart(r)
else:
    st.error("Keine Daten zum Anzeigen.")
