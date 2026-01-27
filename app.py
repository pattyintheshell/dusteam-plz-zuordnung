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
# 3) 2er-PLZ aus einer existierenden Spalte ableiten
# -----------------------------
# Wir nehmen 'GEN', falls vorhanden, sonst Index als Key
if 'GEN' in plz_2er.columns:
    plz_2er['plz2'] = plz_2er['GEN'].astype(str).str[:2]
else:
    plz_2er['plz2'] = plz_2er.index.astype(str)

# -----------------------------
# 4) Consultant-Zuordnung
# -----------------------------
plz_mapping = {
    'Dustin': ['77', '78', '79', '88'],
    'Tobias': ['81', '82', '83', '84'],
    'Philipp': ['32', '33', '40', '41', '42', '43', '44', '45', '46', '47', '48', '50', '51', '52', '53', '56', '57', '58', '59'],
    'Vanessa': ['10', '11', '12', '13', '20', '21', '22'],
    'Patricia': ['68', '69', '71', '74', '75', '76'],
    'Kathrin': ['80', '85', '86', '87'],
    'Sebastian': ['01', '02', '03', '04', '05', '06', '07', '08', '09', '14', '15', '16', '17', '18', '19'],
    'Sumak': ['90', '91', '92', '93', '94', '95', '96', '97'],
    'Jonathan': ['70', '72', '73', '89']
}

plz2_to_consultant = {}
for consultant, plz_list in plz_mapping.items():
    for p in plz_list:
        plz2_to_consultant[p] = consultant

plz_2er['consultant'] = plz_2er['plz2'].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# 5) Dropdown: Consultant auswählen
# -----------------------------
all_consultants = ['All'] + sorted(plz_2er['consultant'].unique())
selected = st.selectbox("Consultant auswählen:", all_consultants)

if selected != 'All':
    plz_plot = plz_2er[plz_2er['consultant'] == selected]
else:
    plz_plot = plz_2er

# -----------------------------
# 6) Karte plotten
# -----------------------------
fig = px.choropleth_mapbox(
    plz_plot,
    geojson=plz_plot.geometry,
    locations=plz_plot.index,
    color='consultant',
    mapbox_style="carto-positron",
    zoom=5,
    center={"lat": 51.0, "lon": 10.0},
    opacity=0.5,
    hover_data={'plz2': True, 'consultant': True},
    height=800  # höhere Karte für bessere Sichtbarkeit
)

# Bundesländer-Umriss darüber
fig.update_traces(marker_line_width=1, marker_line_color="black")

st.plotly_chart(fig, use_container_width=True)
