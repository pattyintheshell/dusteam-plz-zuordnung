import streamlit as st
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import BytesIO
import plotly.colors as pc

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
# Automatische Farbauswahl für beliebig viele Consultants
consultants = [c for c in plz_mapping.keys()]
num_consultants = len(consultants)
palette = px.colors.qualitative.Dark24  # max 24 unterschiedliche Farben
farbe_map = {}
for i, c in enumerate(consultants):
    base_color = palette[i % len(palette)]
    farbe_map[c] = base_color.replace("rgb", "rgba").replace(")", ",0.4)")
farbe_map["Unassigned"] = "rgba(200,200,200,0.4)"

# -----------------------------
# Bundesländer joinen
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
plz_with_bl = gpd.sjoin(plz_gdf, bl_gdf[['name','geometry']], how='left', predicate='intersects')
plz_with_bl = plz_with_bl.reset_index(drop=True)

# -----------------------------
# Hover-Text untereinander
plz_with_bl['hover_text'] = plz_with_bl.apply(
    lambda row: f"{row['plz2']}<br>{row['name'] if row['name'] else 'Unbekannt'}<br>{row['consultant']}",
    axis=1
)

# -----------------------------
# Spalten: Karte links, Legende rechts
col1, col2 = st.columns([3,1])

with col1:
    fig = go.Figure()

    # Wir gruppieren direkt nach Consultant und nutzen MultiPolygons
    for consultant, group in plz_with_bl.groupby("consultant"):
        fig.add_trace(go.Choroplethmapbox(
            geojson=group.__geo_interface__,
            locations=group.index,
            z=[1]*len(group),
            showscale=False,
            marker_opacity=0.4,
            marker_line_width=1,
            marker_line_color="black",
            hovertext=group['hover_text'],
            hoverinfo="text",
            colorscale=[[0, farbe_map[consultant]], [1, farbe_map[consultant]]],  # Einheitliche Farbe
            name=consultant
        ))

    # Bundesländer Linien
    for geom in bl_gdf.geometry:
        if geom.geom_type == "Polygon":
            lon, lat = geom.exterior.xy
            fig.add_trace(go.Scattermapbox(lon=lon, lat=lat, mode="lines", line=dict(color="black", width=2), hoverinfo="skip", showlegend=False))
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                lon, lat = poly.exterior.xy
                fig.add_trace(go.Scattermapbox(lon=lon, lat=lat, mode="lines", line=dict(color="black", width=2), hoverinfo="skip", showlegend=False))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=5,
        mapbox_center={"lat":51,"lon":10},
        height=800,
        width=800
    )

    st.plotly_chart(fig, use_container_width=False)

with col2:
    st.subheader("Consultants")
    for consultant, color in farbe_map.items():
        if consultant != "Unassigned":
            st.markdown(f"<span style='display:inline-block;width:20px;height:20px;background-color:{color};margin-right:5px;'></span>{consultant}", unsafe_allow_html=True)
