import streamlit as st
import geopandas as gpd
import plotly.express as px
import requests
import json

st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung Dusteam")

# -----------------------------
# 1. Bundesländer laden
# -----------------------------
bundeslaender_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-bundeslaender/bundeslaender_deutschland.txt"
r = requests.get(bundeslaender_url)
data = json.loads(r.content)
bundeslaender = gpd.GeoDataFrame.from_features(data["features"])

# -----------------------------
# 2. Große PLZ-Datei laden
# -----------------------------
plz_url = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_deutschland.txt"
r = requests.get(plz_url)
data = json.loads(r.content)
plz = gpd.GeoDataFrame.from_features(data["features"])

# -----------------------------
# 3. Automatisch 2er PLZ erstellen
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
# 4. Consultant-Zuordnung
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
# 5. Karte plotten
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
