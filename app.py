import streamlit as st
import geopandas as gpd
import plotly.express as px
import requests
import json

st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam")

# -----------------------------
# 1. Hilfsfunktion zum Laden von GeoJSON aus Release Assets
# -----------------------------
def load_geojson_from_release(url):
    r = requests.get(url)
    if r.status_code != 200:
        st.error(f"Fehler beim Download der Datei: {url}\nHTTP Status: {r.status_code}")
        st.stop()
    try:
        data = json.loads(r.content)
        gdf = gpd.GeoDataFrame.from_features(data["features"])
        return gdf
    except Exception as e:
        st.error(f"Fehler beim Parsen der GeoJSON: {e}")
        st.stop()

# -----------------------------
# 2. Bundesländer laden
# -----------------------------
bundeslaender_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-bundeslaender/bundeslaender_deutschland.txt"
bundeslaender = load_geojson_from_release(bundeslaender_url)

# -----------------------------
# 3. Große PLZ-Datei laden
# -----------------------------
plz_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_deutschland.txt"
plz = load_geojson_from_release(plz_url)

# -----------------------------
# 4. Automatisch 2er PLZ erstellen
# -----------------------------
# Prüfen, welche Spalte wie PLZ aussieht
plz_column = None
for col in plz.columns:
    sample = str(plz[col].dropna().iloc[0])
    if sample.isdigit() and len(sample) == 5:
        plz_column = col
        break

if plz_column is None:
    st.error("Keine gültige 5-stellige PLZ-Spalte gefunden!")
    st.stop()

# 2er PLZ extrahieren
plz['plz2'] = plz[plz_column].astype(str).str[:2]

# Alle Geometrien mit derselben 2er PLZ zusammenführen
plz_2er = plz.dissolve(by='plz2').reset_index()

# -----------------------------
# 5. Consultant-Zuordnung
# -----------------------------
plz_mapping = {
    '68': 'Anna',
    '69': 'Ben',
    '70': 'Clara',
    '71': 'David',
    # weitere 2er PLZ hier eintragen
}

plz_2er['consultant'] = plz_2er['plz2'].map(plz_mapping)

# -----------------------------
# 6. Karte plotten
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

# Bundesländer-Umriss drüberlegen
fig.update_traces(marker_line_width=1, marker_line_color="black")

st.plotly_chart(fig, use_container_width=True)
