import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
import plotly.colors as pc
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
# Automatische Farbauswahl: maximal unterscheidbare Farben
consultants = [c for c in plz_mapping.keys()]
base_colors = pc.qualitative.Plotly  # 10 Farben Basis
# Wenn mehr Consultants als Basisfarben, wiederholen, aber leicht abgedunkelt
farbe_map = {}
for i, c in enumerate(consultants):
    color = base_colors[i % len(base_colors)]
    # Dunkler für Wiederholungen
    factor = 0.7 ** (i // len(base_colors))
    r, g, b = [int(int(x,16)*factor) if isinstance(x,str) else int(x*factor) for x in [color[1:3], color[3:5], color[5:7]]]
    farbe_map[c] = f"rgba({r},{g},{b},0.4)"
farbe_map["Unassigned"] = "rgba(200,200,200,0.4)"

# -----------------------------
# Bundesländer joinen
bl_gdf = bl_gdf.to_crs(plz_gdf.crs)
plz_with_bl = gpd.sjoin(plz_gdf, bl_gdf[['name','geometry']], how='left', predicate='intersects')
plz_with_bl = plz_with_bl.reset_index(drop=True)

# -----------------------------
# Polygonvereinfachung für Performance
plz_with_bl['geometry'] = plz_with_bl['geometry'].simplify(tolerance=0.05, preserve_topology=True)
bl_gdf['geometry'] = bl_gdf['geometry'].simplify(tolerance=0.05, preserve_topology=True)

# -----------------------------
# Hover-Text untereinander
plz_with_bl['hover_text'] = plz_with_bl.apply(
    lambda row: f"{row['plz2']}<br>{row['name'] if row['name'] else 'Unbekannt'}<br>{row['consultant']}",
    axis=1
)

# -----------------------------
# Layout: Streamlit Spalten
col1, col2 = st.columns([3,1])

with col1:
    fig = go.Figure()
    
    # 2er-PLZ Gebiete
    for consultant in plz_with_bl['consultant'].unique():
        subset = plz_with_bl[plz_with_bl['consultant'] == consultant]
        if subset.empty:
            continue
        for geom, hover in zip(subset.geometry, subset.hover_text):
            polys = [geom] if geom.geom_type=="Polygon" else geom.geoms
            for poly in polys:
                lons, lats = zip(*poly.exterior.coords)
                fig.add_trace(go.Scattermapbox(
                    lon=lons,
                    lat=lats,
                    mode='lines',
                    fill='toself',
                    fillcolor=farbe_map[consultant],
                    line=dict(color='black', width=1),
                    hoverinfo='text',
                    text=[hover]*len(lons),
                    showlegend=False
                ))

    # Bundesländer Linien
    for _, row in bl_gdf.iterrows():
        geom = row.geometry
        polys = [geom] if geom.geom_type=="Polygon" else geom.geoms
        for poly in polys:
            lons, lats = zip(*poly.exterior.coords)
            fig.add_trace(go.Scattermapbox(
                lon=lons,
                lat=lats,
                mode='lines',
                line=dict(color='black', width=2),
                hoverinfo='skip',
                showlegend=False
            ))

    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=5,
        mapbox_center={"lat": 51.0, "lon": 10.0},
        height=800,
        width=800
    )

    st.plotly_chart(fig, use_container_width=False)

with col2:
    st.subheader("Consultants")
    for consultant, color in farbe_map.items():
        if consultant != "Unassigned":
            st.markdown(
                f"<span style='display:inline-block;width:20px;height:20px;background-color:{color};margin-right:5px;'></span>{consultant}",
                unsafe_allow_html=True
            )
