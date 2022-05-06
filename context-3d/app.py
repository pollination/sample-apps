import json
import pathlib
import math
import pydeck as pdk
import requests
import streamlit as st
from dragonfly_parser import get_json_array

from pollination_streamlit_io import (button, 
    inputs, special)
from ladybug.color import Color

def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

query = st.experimental_get_query_params()
platform = special.get_host()


@st.cache(suppress_st_warning=True)
def load_context(lat, lon, zoom):
    x, y = deg2num(lat, lon, zoom)
    DATA_URL = f"https://data.osmbuildings.org/0.2/anonymous/tile/{zoom}/{x}/{y}.json"

    text_content, lbt_text_content = None, None
    out_city = f"./data/{lat}_{lon}_{zoom}.json"
    out_lbt_city = f"./data/lbt_{lat}_{lon}_{zoom}.json"
    pathlib.Path('./data').mkdir(parents=True, exist_ok=True)
    try:
        req = requests.get(DATA_URL)
        with open(out_city, "w") as f:
            text_content = json.dumps(req.json())
    except requests.exceptions.RequestException as e:
        st.error(f"{e}")
    except Exception as e:
        st.error("Geojson not found.")

    json_out = None
    try:
        json_out = get_json_array(req.json(), lat, lon)
        with open(out_lbt_city, "w") as f:
            lbt_text_content = json_out
    except Exception as e:
        st.error("Convert to LBT failed.")
    return DATA_URL, text_content, lbt_text_content, out_city, out_lbt_city, json_out


cities = {
    'New York': [40.7495292, -73.9928448],
    'Boston': [42.361145, -71.057083],
    'Sydney': [-33.865143, 151.209900],
    'Rio De Janeiro': [-22.9094545, -43.1823189],
    'London': [51.5072, -0.1276]
}

option = st.selectbox("Samples",  cities.keys())
st.write(f"Lat: {cities[option][0]} ",
         f"Lon: {cities[option][1]}")

lat = st.number_input(
    "Latitude (deg)",
    min_value=-90.0,
    max_value=90.0,
    value=cities[option][0], step=0.1,
    format="%f")
lon = st.number_input(
    "Longitude (deg)",
    min_value=-180.0,
    max_value=180.0,
    value=cities[option][1],
    step=0.1,
    format="%f")
zoom = st.number_input(
    "Zoom (15 or 16)",
    min_value=15,
    max_value=16,
    value=15,
    step=1)

DATA_URL, text_content, lbt_text_content, out_city, out_lbt_city, json_out = load_context(lat, lon, zoom)

if text_content:
    st.download_button(
        label='Download Geojson',
        data=text_content,
        file_name=out_city)

if lbt_text_content:
    st.download_button(
        label='Download Ladybug Json',
        data=lbt_text_content,
        file_name=out_lbt_city)

# rhino integration here!
if platform == 'rhino' and json_out:
    # user color
    def get_colored_geometry_json_strings(geometries: dict, 
        hex_color: str) -> dict:
        """
        Add colors to dict. So rhino will know what color 
        to use with solids.
        """
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        geometry_dicts = [g for g in geometries]
        for d in geometry_dicts:
            d['color'] = Color(*rgb).to_dict()
            d['transparency'] = 0.6
        return geometry_dicts
    
    # color picker
    color = st.color_picker('Context Color', '#eb2126', 
            key='context-color').lstrip('#')

    # add your favourite color
    geometries_to_send = json.loads(json_out)
    colored_geometries = get_colored_geometry_json_strings(geometries_to_send,
        color)

    # pollination bake button
    # options: Layer to use for baking 
    #          source units
    button.send('BakeGeometry',
        colored_geometries, 'my-secret-key', 
        options={"layer":"StreamlitLayer",
            "units": "Meters"},
        key='my-secret-key')

    # display pollination checkbox
    inputs.send(colored_geometries, 
        'my-super-secret-key', 
        options={"layer":"StreamlitLayer", 
            "units": "Meters"}, 
        key='my-super-secret-key')

st.pydeck_chart(pdk.Deck(map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(latitude=lat,
        longitude=lon,
        zoom=zoom,
        max_zoom=18,
        pitch=45,
        bearing=0),
    layers=[pdk.Layer('GeoJsonLayer',
            DATA_URL,
            opacity=0.5,
            stroked=False,
            filled=True,
            extruded=True,
            wireframe=True,
            get_elevation='properties.height',
            get_fill_color='[255, 0, 0]',
            get_line_color=[255, 255, 255],
            pickable=True),]))
