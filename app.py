```python
import json
from io import BytesIO

import geopandas as gpd
import plotly.graph_objects as go
import requests
import streamlit as st


# -----------------------------
# Seiteneinstellungen
st.set_page_config(layout="wide")
st.title("Marktaufteilung DE Perm Embedded")


# -----------------------------
# GeoJSON laden
@st.cache_data
def load_geojson(url: str) -> gpd.GeoDataFrame:
    try:
        response = requests.get(url, timeout=60)
        response.raise_for_status()
    except requests.RequestException as error:
        st.error(f"Fehler beim Laden der GeoJSON-Datei: {error}")
        st.stop()

    return gpd.read_file(BytesIO(response.content))


PLZ_URL = (
    "https://github.com/pattyintheshell/dusteam-plz-zuordnung/"
    "releases/download/v1.0-plz/plz_deutschland.geojson"
)

BL_URL = (
    "https://github.com/pattyintheshell/dusteam-plz-zuordnung/"
    "releases/download/v1.0-bundeslaender/"
    "bundeslaender_deutschland.geojson"
)

plz_gdf = load_geojson(PLZ_URL)
bl_gdf = load_geojson(BL_URL)


# -----------------------------
# Koordinatensystem für Plotly
plz_gdf = plz_gdf.to_crs(epsg=4326)
bl_gdf = bl_gdf.to_crs(epsg=4326)


# -----------------------------
# PLZ2 korrekt aufbereiten
def extract_plz2(value) -> str:
    value = str(value).strip()

    # Mögliche Dezimalendung entfernen:
    # "77.0" -> "77"
    if value.endswith(".0"):
        value = value[:-2]

    # Das GeoJSON enthält bereits PLZ2-Werte
    # wie "01", "10" oder "77".
    if len(value) <= 2:
        return value.zfill(2)

    # Unterstützt zusätzlich vier- oder fünfstellige PLZ-Werte.
    return value.zfill(5)[:2]


plz_gdf["plz2"] = plz_gdf["plz"].apply(extract_plz2)


# -----------------------------
# Consultant-Zuordnung
plz_mapping = {
    "Dustin": ["77", "78", "79", "88"],
    "Jonathan": ["68", "69", "70", "71", "72", "73", "74", "75", "76", "89"],
    "Laith": ["26", "27", "28", "29", "30", "31", "34", "35", "36", "37", "38", "49", "54", "55", "60", "61", "62", "63", "64", "65", "66", "67"],
    "Philipp": ["32", "33", "40", "41", "42", "43", "44", "45", "46", "47", "48", "50", "51", "52", "53", "56", "57", "58", "59"],
    "Sebastian": ["01", "02", "03", "04", "05", "06", "07", "08", "09", "14", "15", "16", "17", "18", "19", "39", "98", "99"],
    "Sumak": ["81", "82", "83", "84", "90", "91", "92", "93", "94", "95", "96", "97"],
    "Vanessa": ["10", "11", "12", "13", "20", "21", "22"],
}


# PLZ2 -> Consultant
plz2_to_consultant = {
    plz2: consultant
    for consultant, plz2_list in plz_mapping.items()
    for plz2 in plz2_list
}

plz_gdf["consultant"] = (
    plz_gdf["plz2"]
    .map(plz2_to_consultant)
    .fillna("Unassigned")
)


# -----------------------------
# Hover-Text
plz_gdf["hover_text"] = (
    "PLZ-Gebiet: "
    + plz_gdf["plz2"]
    + "<br>Consultant: "
    + plz_gdf["consultant"]
)


# -----------------------------
# Farben
farbe_map = {
    "Dustin": "#FFDF00",
    "Jonathan": "#FF6600",
    "Laith": "#A050D2",
    "Philipp": "#0064FF",
    "Sebastian": "#6ED26E",
    "Sumak": "#00CED1",
    "Vanessa": "#FF66CC",
    "Unassigned": "#C8C8C8",
}


# -----------------------------
# Reihenfolge in der Legende
legend_order = [
    "Dustin",
    "Jonathan",
    "Laith",
    "Philipp",
    "Sebastian",
    "Sumak",
    "Vanessa",
    "Unassigned",
]


# -----------------------------
# Karte erstellen
fig = go.Figure()


# -----------------------------
# Farbige PLZ-Flächen
for consultant in legend_order:
    color = farbe_map[consultant]

    subset = plz_gdf[
        plz_gdf["consultant"] == consultant
    ].copy()

    if subset.empty:
        continue

    # Eindeutige ID für jedes GeoJSON-Feature
    subset["feature_id"] = subset.index.astype(str)

    # GeoDataFrame in GeoJSON umwandeln
    subset_geojson = json.loads(
        subset.set_index("feature_id").to_json()
    )

    fig.add_trace(
        go.Choroplethmap(
            geojson=subset_geojson,
            locations=subset["feature_id"].tolist(),
            featureidkey="id",
            z=[1] * len(subset),
            text=subset["hover_text"].tolist(),
            hovertemplate="%{text}<extra></extra>",
            colorscale=[
                [0, color],
                [1, color],
            ],
            zmin=0,
            zmax=1,
            showscale=False,
            marker=dict(
                opacity=0.55,
                line=dict(
                    color="black",
                    width=0.5,
                ),
            ),
            name=consultant,
            showlegend=False,
        )
    )


# -----------------------------
# Bundesländer-Grenzen
for geometry in bl_gdf.geometry:
    if geometry is None or geometry.is_empty:
        continue

    if geometry.geom_type == "Polygon":
        polygons = [geometry]
    elif geometry.geom_type == "MultiPolygon":
        polygons = list(geometry.geoms)
    else:
        continue

    for polygon in polygons:
        lons, lats = zip(*polygon.exterior.coords)

        fig.add_trace(
            go.Scattermap(
                lon=list(lons),
                lat=list(lats),
                mode="lines",
                line=dict(
                    color="black",
                    width=2,
                ),
                hoverinfo="skip",
                showlegend=False,
            )
        )


# -----------------------------
# PLZ2-Gebiete zusammenfassen
plz2_gdf = plz_gdf.dissolve(
    by="plz2",
    aggfunc="first",
)


# Punkt innerhalb jedes PLZ2-Gebiets
label_points = plz2_gdf.geometry.representative_point()


# -----------------------------
# PLZ2-Beschriftungen
fig.add_trace(
    go.Scattermap(
        lon=label_points.x.tolist(),
        lat=label_points.y.tolist(),
        mode="text",
        text=plz2_gdf.index.astype(str).tolist(),
        textposition="middle center",
        textfont=dict(
            size=10,
            color="black",
        ),
        hoverinfo="skip",
        showlegend=False,
    )
)


# -----------------------------
# Legendeneinträge
for consultant in legend_order:
    fig.add_trace(
        go.Scattermap(
            lon=[None],
            lat=[None],
            mode="markers",
            marker=dict(
                size=18,
                color=farbe_map[consultant],
                opacity=0.7,
            ),
            name=consultant,
            showlegend=True,
            hoverinfo="skip",
        )
    )


# -----------------------------
# Kartenlayout
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
    margin=dict(
        l=0,
        r=0,
        t=0,
        b=0,
    ),
    legend=dict(
        title=dict(
            text="Consultants",
            font=dict(
                size=20,
                family="Arial, sans-serif",
                color="black",
            ),
        ),
        font=dict(
            size=16,
            color="black",
        ),
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
# Karte anzeigen
st.plotly_chart(
    fig,
    use_container_width=False,
)
```
