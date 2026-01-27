import streamlit as st
import geopandas as gpd
import plotly.express as px
import requests
import json

st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam")

# -----------------------------
# Funktion: GeoJSON von GitHub Release laden
# -----------------------------
def load_geojson_release_asset(url: str):
    r = requests.get(url, allow_redirects=True)
    if r.status_code != 200:
        st.error(f"Fehler beim Download der Datei:\n{url}\nStatuscode: {r.status_code}")
        st.stop()
    try:
        data = json.loads(r.content)
        gdf = gpd.GeoDataFrame.from_features(data["features"])
        return gdf
    except Exception as e:
        st.error(f"GeoJSON Parsing Fehler:\n{e}")
        st.stop()

# -----------------------------
# 1) Bundesländer laden
# -----------------------------
bundeslaender_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-bundeslaender/bundeslaender_deutschland.geojson"
bundeslaender = load_geojson_release_asset(bundeslaender_url)

# -----------------------------
# 2) PLZ-GeoJSON laden
# -----------------------------
plz_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_deutschland.geojson"
plz_2er = load_geojson_release_asset(plz_url)

# -----------------------------
# 3) Consultant-Zuordnung
# -----------------------------
# Jede Geometrie ist ein „2er-Gebiet“, hier manuell zuordnen
# Du musst die keys anpassen, z.B. nach einem Feld wie 'GEN' oder 'AGS'
plz_mapping = {
    # Beispiel: 'GEN' = Ortsname, oder Index als Key
    0: 'Anna',
    1: 'Ben',
    2: 'Clara',
    3: 'David',
    # weitere Geometrien hier ergänzen
}

plz_2er['consultant'] = plz_2er.index.map(plz_mapping)  # Index-basierte Zuordnung

# -----------------------------
# 4) Karte plotten
# -----------------------------
fig = px.choropleth_mapbox(
    plz_2er,
    geojson=plz_2er.geometry,
    locations=plz_2er.index,
    color='consultant',
    mapbox_style="carto-positron",
    zoom=5,
    center={"lat": 51.0, "lon": 10.0},
    opacity=0.5,
    hover_data={'consultant': True}
)

# Bundesländer-Umriss darüber
fig.update_traces(marker_line_width=1, marker_line_color="black")

st.plotly_chart(fig, use_container_width=True)
