import streamlit as st
import geopandas as gpd
import plotly.express as px
import requests
import json

st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam")

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
# 2) PLZ laden
# -----------------------------
plz_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_deutschland.geojson"
plz = load_geojson_release_asset(plz_url)

# -----------------------------
# 3) 2er-PLZ automatisch aus geeigneter Spalte ableiten
# -----------------------------
# Wir nehmen die Spalte "AGS", wenn sie existiert
if 'AGS' in plz.columns:
    plz['plz2'] = plz['AGS'].astype(str).str[:2]
elif 'RS' in plz.columns:
    plz['plz2'] = plz['RS'].astype(str).str[:2]
else:
    st.error("Keine geeignete Spalte für 2er-PLZ gefunden! Bitte prüfen.")
    st.stop()

# Alle Geometrien mit derselben 2er-PLZ zusammenführen
plz_2er = plz.dissolve(by='plz2').reset_index()

# -----------------------------
# 4) Consultant-Zuordnung
# -----------------------------
plz_mapping = {
    '68': 'Anna',
    '69': 'Ben',
    '70': 'Clara',
    '71': 'David',
    # weitere 2er-PLZ hier ergänzen
}
plz_2er['consultant'] = plz_2er['plz2'].map(plz_mapping)

# -----------------------------
# 5) Karte plotten
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
    hover_data={'plz2': True, 'consultant': True}
)

# Bundesländer-Umriss drüber
fig.update_traces(marker_line_width=1, marker_line_color="black")

st.plotly_chart(fig, use_container_width=True)
