import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
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
# Farben pro Consultant (klar, transparent)
farbe_map = {
    "Dustin": "rgba(31,119,180,0.5)",     # Blau
    "Patricia": "rgba(255,127,14,0.5)",   # Orange
    "Jonathan": "rgba(44,160,44,0.5)",    # Grün
    "Tobias": "rgba(214,39,40,0.5)",      # Rot
    "Kathrin": "rgba(148,103,189,0.5)",   # Lila
    "Sumak": "rgba(255,152,150,0.5)",     # Pink
    "Vanessa": "rgba(255,187,120,0.5)",   # Hellorange
    "Sebastian": "rgba(23,190,207,0.5)",  # Cyan
    "Philipp": "rgba(127,127,0,0.5)",     # Gelb/Olive
    "Unassigned": "rgba(200,200,200,0.3)" # Grau
}

# -----------------------------
# Bundesländer join
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
plz_with_bl = gpd.sjoin(plz_gdf, bl_gdf[['name','geometry']], how='left', predicate='intersects')
plz_with_bl = plz_with_bl.reset_index(drop=True)

# Hover-Text pro PLZ
plz_with_bl['hover_text'] = plz_with_bl.apply(
    lambda row: f"{row['plz2']}\n{row['name'] if row['name'] else 'Unbekannt'}\n{row['consultant']}",
    axis=1
)

# -----------------------------
# Karte bauen
fig = go.Figure()

for consultant, group in plz_with_bl.groupby("consultant"):
    all_lons = []
    all_lats = []
    all_text = []

    # Jede 2er-PLZ einzeln, Linien, Farbe pro Consultant
    for geom, hover in zip(group.geometry, group['hover_text']):
        if geom.geom_type == "Polygon":
            polys = [geom]
        elif geom.geom_type == "MultiPolygon":
            polys = list(geom.geoms)
        else:
            continue

        for poly in polys:
            lons, lats = zip(*poly.exterior.coords)
            all_lons.extend(lons + (None,))
            all_lats.extend(lats + (None,))
            all_text.extend([hover]*len(lons) + [None])

    fig.add_trace(go.Scattermapbox(
        lon=all_lons,
        lat=all_lats,
        mode="lines",
        line=dict(color=farbe_map[consultant], width=2),
        hoverinfo="text",
        text=all_text,
        name=consultant,
        showlegend=True,
        legendgroup=consultant
    ))

# -----------------------------
# Bundesländer Linien (schwarz)
for geom in bl_gdf.geometry:
    if geom.geom_type == "Polygon":
        lons, lats = zip(*geom.exterior.coords)
        fig.add_trace(go.Scattermapbox(
            lon=list(lons), lat=list(lats),
            mode="lines",
            line=dict(color="black", width=2),
            hoverinfo="skip",
            showlegend=False
        ))
    elif geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            lons, lats = zip(*poly.exterior.coords)
            fig.add_trace(go.Scattermapbox(
                lon=list(lons), lat=list(lats),
                mode="lines",
                line=dict(color="black", width=2),
                hoverinfo="skip",
                showlegend=False
            ))

# -----------------------------
# Layout
fig.update_layout(
    mapbox_style="carto-positron",
    mapbox_zoom=5,
    mapbox_center={"lat":51,"lon":10},
    height=800,
    width=800,
    legend=dict(
        title="Consultants",
        title_font=dict(size=16),
        font=dict(size=14),
        x=0.99,
        y=0.99,
        xanchor="right",
        yanchor="top"
    )
)

st.plotly_chart(fig, use_container_width=False)
