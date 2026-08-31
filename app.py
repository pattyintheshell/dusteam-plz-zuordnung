import streamlit as st
import geopandas as gpd
import plotly.graph_objects as go
import requests
from io import BytesIO
import numpy as np


# -----------------------------
# Seiteneinstellungen
st.set_page_config(layout="wide")
st.title("Marktaufteilung DE Perm Embedded")


# -----------------------------
# GeoJSON laden
def load_geojson(url: str) -> gpd.GeoDataFrame:
    response = requests.get(url, timeout=60)

    if response.status_code != 200:
        st.error(f"Fehler beim Laden der Datei: {response.status_code}")
        st.stop()

    return gpd.read_file(BytesIO(response.content))


PLZ_URL = (
    "https://github.com/pattyintheshell/dusteam-plz-zuordnung/"
    "releases/download/v1.0-plz/plz_deutschland.geojson"
)

BL_URL = (
    "https://github.com/pattyintheshell/dusteam-plz-zuordnung/"
    "releases/download/v1.0-bundeslaender/bundeslaender_deutschland.geojson"
)

plz_gdf = load_geojson(PLZ_URL)
bl_gdf = load_geojson(BL_URL)


# -----------------------------
# Koordinatensystem für Längen- und Breitengrade
plz_gdf = plz_gdf.to_crs(epsg=4326)
bl_gdf = bl_gdf.to_crs(epsg=4326)


# -----------------------------
# PLZ2 extrahieren
plz_gdf["plz2"] = plz_gdf["plz"].astype(str).str.zfill(5).str[:2]


# -----------------------------
# Consultant-Mapping
plz_mapping = {
    "Dustin": ["77", "78", "79", "88"],
    "Jonathan": ["68", "69", "70", "71", "72", "73", "74", "75", "76", "89"],
    "Sumak": ["81", "82", "83", "84", "90", "91", "92", "93", "94", "95", "96", "97"],
    "Kathrin": ["80", "85", "86", "87"],
    "Philipp": [
        "32", "33", "40", "41", "42", "43", "44", "45", "46",
        "47", "48", "50", "51", "52", "53", "56", "57", "58", "59"
    ],
    "Vanessa": ["10", "11", "12", "13", "20", "21", "22"],
    "Sebastian": [
        "01", "02", "03", "04", "05", "06", "07", "08", "09",
        "14", "15", "16", "17", "18", "19"
    ],
}

plz2_to_consultant = {
    plz: consultant
    for consultant, plz_list in plz_mapping.items()
    for plz in plz_list
}

plz_gdf["consultant"] = (
    plz_gdf["plz2"]
    .map(plz2_to_consultant)
    .fillna("Unassigned")
)


# -----------------------------
# Hover-Text
plz_gdf["hover_text"] = plz_gdf.apply(
    lambda row: f"{row['plz2']} {row['consultant']}",
    axis=1
)


# -----------------------------
# Farben
farbe_map = {
    "Dustin": "rgba(255, 223, 0, 0.4)",
    "Jonathan": "rgba(255, 102, 0, 0.4)",
    "Sumak": "rgba(0, 206, 209, 0.4)",
    "Kathrin": "rgba(160, 80, 210, 0.4)",
    "Philipp": "rgba(0, 100, 255, 0.4)",
    "Vanessa": "rgba(255, 102, 204, 0.4)",
    "Sebastian": "rgba(110, 210, 110, 0.4)",
    "Unassigned": "rgba(200, 200, 200, 0.4)",
}


# -----------------------------
# Karte erstellen
fig = go.Figure()


# -----------------------------
# PLZ-Flächen
for consultant, color in farbe_map.items():
    subset = plz_gdf[plz_gdf["consultant"] == consultant]

    if subset.empty:
        continue

    lon_arrays = []
    lat_arrays = []
    text_arrays = []

    for geom, hover in zip(subset.geometry, subset["hover_text"]):
        if geom is None or geom.is_empty:
            continue

        if geom.geom_type == "Polygon":
            polygons = [geom]
        elif geom.geom_type == "MultiPolygon":
            polygons = list(geom.geoms)
        else:
            continue

        for polygon in polygons:
            lons, lats = zip(*polygon.exterior.coords)

            lon_arrays.append(
                np.concatenate([np.asarray(lons), [np.nan]])
            )
            lat_arrays.append(
                np.concatenate([np.asarray(lats), [np.nan]])
            )
            text_arrays.append(
                np.asarray([hover] * len(lons) + [None], dtype=object)
            )

    if not lon_arrays:
        continue

    fig.add_trace(
        go.Scattermap(
            lon=np.concatenate(lon_arrays).tolist(),
            lat=np.concatenate(lat_arrays).tolist(),
            mode="lines",
            fill="toself",
            fillcolor=color,
            line=dict(color="black", width=1),
            text=np.concatenate(text_arrays).tolist(),
            hoverinfo="text",
            name=consultant,
            showlegend=False,
        )
    )


# -----------------------------
# Dummy-Traces für die Legende
for consultant, color in farbe_map.items():
    fig.add_trace(
        go.Scattermap(
            lon=[None],
            lat=[None],
            mode="markers",
            marker=dict(
                size=20,
                color=color,
            ),
            name=consultant,
            showlegend=True,
        )
    )


# -----------------------------
# Bundesländer-Grenzen
for geom in bl_gdf.geometry:
    if geom is None or geom.is_empty:
        continue

    if geom.geom_type == "Polygon":
        polygons = [geom]
    elif geom.geom_type == "MultiPolygon":
        polygons = list(geom.geoms)
    else:
        continue

    for polygon in polygons:
        lons, lats = zip(*polygon.exterior.coords)

        fig.add_trace(
            go.Scattermap(
                lon=list(lons),
                lat=list(lats),
                mode="lines",
                line=dict(color="black", width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )


# -----------------------------
# PLZ2-Beschriftungen
plz2_gdf = plz_gdf.dissolve(by="plz2")

# representative_point liegt im jeweiligen Gebiet und eignet sich
# deshalb besser für Beschriftungen als ein einfacher Mittelpunkt.
label_points = plz2_gdf.geometry.representative_point()

fig.add_trace(
    go.Scattermap(
        lon=label_points.x.tolist(),
        lat=label_points.y.tolist(),
        mode="text",
        text=plz2_gdf.index.astype(str).tolist(),
        textposition="middle center",
        textfont=dict(size=10, color="black"),
        hoverinfo="skip",
        showlegend=False,
    )
)


# -----------------------------
# Legenden-Reihenfolge
legend_order = sorted(
    consultant
    for consultant in farbe_map
    if consultant != "Unassigned"
) + ["Unassigned"]


# -----------------------------
# Layout
fig.update_layout(
    map=dict(
        style="carto-positron",
        zoom=5,
        center={
            "lat": 51.0,
            "lon": 10.0,
        },
    ),
    height=800,
    width=800,
    margin=dict(l=0, r=0, t=0, b=0),
    legend=dict(
        title=dict(
            text="Consultants",
            font=dict(
                size=20,
                family="Arial, sans-serif",
                color="black",
            ),
        ),
        font=dict(size=16, color="black"),
        bgcolor="rgba(255, 255, 255, 0.85)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
        tracegroupgap=10,
        x=0.99,
        y=0.99,
        xanchor="right",
        yanchor="top",
        traceorder="normal",
    ),
)


# -----------------------------
# Legendeneinträge sortieren
sorted_legend_traces = []

for name in legend_order:
    for trace in fig.data:
        if trace.name == name and trace.showlegend:
            sorted_legend_traces.append(trace)

fig.data = tuple(
    [trace for trace in fig.data if not trace.showlegend]
    + sorted_legend_traces
)


# -----------------------------
# Karte anzeigen
st.plotly_chart(
    fig,
    use_container_width=False,
)
