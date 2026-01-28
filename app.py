import streamlit as st
import geopandas as gpd
import plotly.express as px
import requests
from io import BytesIO

# -----------------------------
st.set_page_config(layout="wide")
st.title("🗺️ Marktaufteilung DE Perm Embedded Team")

# -----------------------------
def load_geojson(url: str) -> gpd.GeoDataFrame:
    r = requests.get(url)
    if r.status_code != 200:
        st.error(f"Fehler beim Laden: {r.status_code}")
        st.stop()
    return gpd.read_file(BytesIO(r.content))

PLZ_URL = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-plz/plz_deutschland.geojson"
BL_URL  = "https://github.com/pattyintheshell/dusteam-plz-zuordnung/releases/download/v1.0-bundeslaender/bundeslaender_deutschland.geojson"

plz_gdf = load_geojson(PLZ_URL)
bl_gdf  = load_geojson(BL_URL)
plz_gdf['plz2'] = plz_gdf['plz'].astype(str).str[:2]

# -----------------------------
# Consultant Mapping
plz_mapping = {
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
plz2_to_consultant = {p: c for c, plz_list in plz_mapping.items() for p in plz_list}
plz_gdf['consultant'] = plz_gdf['plz2'].map(plz2_to_consultant).fillna("Unassigned")

# -----------------------------
# Hover-Text pro PLZ (untereinander)
plz_gdf['hover_text'] = plz_gdf.apply(
    lambda row: f"{row['plz2']}\n{row['name'] if 'name' in row else 'Unbekannt'}\n{row['consultant']}",
    axis=1
)

# -----------------------------
# Farben pro Consultant (einheitlich)
farbe_map = {
    "Dustin": "#7f7f0080",      # Gelb/Olive transparent
    "Patricia": "#d6274080",    # Rot transparent
    "Jonathan": "#ff7f1480",    # Orange transparent
    "Tobias": "#2ca03c80",      # Grün transparent
    "Kathrin": "#9467bd80",     # Lila transparent
    "Sumak": "#17becf80",       # Cyan transparent
    "Vanessa": "#ff989680",     # Pink transparent
    "Sebastian": "#ffbb7880",   # Hellorange transparent
    "Philipp": "#1f77b480",     # Blau transparent
    "Unassigned": "#c8c8c830"  # Grau
}
ffbb7880
# Farbe als neue Spalte
plz_gdf['color'] = plz_gdf['consultant'].map(farbe_map)

# -----------------------------
# Karte mit choroplethmapbox
fig = px.choropleth_mapbox(
    plz_gdf,
    geojson=plz_gdf.geometry,
    locations=plz_gdf.index,
    color='consultant',             # Farbe pro Consultant
    hover_name='hover_text',
    color_discrete_map=farbe_map,
    mapbox_style="carto-positron",
    center={"lat":51,"lon":10},
    zoom=5,
    opacity=0.5
)

# Linien der Bundesländer
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
for geom in bl_gdf.geometry:
    if geom.geom_type == "Polygon":
        lons, lats = zip(*geom.exterior.coords)
        fig.add_trace(px.line_mapbox(
            x=lons, y=lats
        ).data[0])
    elif geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            lons, lats = zip(*poly.exterior.coords)
            fig.add_trace(px.line_mapbox(
                x=lons, y=lats
            ).data[0])

fig.update_layout(
    height=800,
    width=800,
    legend=dict(
        title="Consultants",
        x=0.99, y=0.99,
        xanchor="right",
        yanchor="top"
    )
)

st.plotly_chart(fig, use_container_width=False)
