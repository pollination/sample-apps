"""Add additional elements for loading sunpath in Rhino."""
import streamlit as st

from ladybug.color import Color
from ladybug.compass import Compass
from ladybug.sunpath import Sunpath

from pollination_streamlit_io import inputs, button


def _add_color(geometries, hex_color):
    """Set the color for input geometry"""
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    geometry_dicts = [g.to_dict() for g in geometries]
    for d in geometry_dicts:
        d['color'] = Color(*rgb).to_dict()
    return geometry_dicts


def add_rhino_controls(sunpath: Sunpath, radius: int, north_angle: float):
    """Add Sunpath controls in Rhino."""
    # layout
    st.sidebar.markdown('### Rhino controls')

    col1, col2, col3 = st.sidebar.columns(3)

    # create the compass
    co = Compass(radius=radius, north_angle=north_angle, spacing_factor=0.15)

    with col1:
        # analemma
        col = st.color_picker('Analemma', '#000000',
                              key='poly-col').lstrip('#')
        polylines = sunpath.hourly_analemma_polyline3d(radius=radius)
        polylines_dicts = _add_color(polylines, col)

        # arcs
        col = st.color_picker('Arcs', '#000000',
                              key='arc-col').lstrip('#')
        arcs = sunpath.monthly_day_arc3d(radius=radius)
        arcs_dicts = _add_color(arcs, col)

    with col2:
        # circles
        col = st.color_picker('Circles', '#000000',
                              key='circl-col').lstrip('#')
        circles = co.all_boundary_circles
        circles_dicts = _add_color(circles, col)

        # ticks
        col = st.color_picker('Ticks', '#000000',
                              key='tick-col').lstrip('#')
        major_ticks = co.major_azimuth_ticks
        minor_ticks = co.minor_azimuth_ticks
        ticks = major_ticks + minor_ticks
        ticks_dicts = _add_color(ticks, col)

    with col3:
        # altitude circles
        col = st.color_picker('Circle', '#000000',
                              key='tick-col').lstrip('#')
        altitude_circ = co.stereographic_altitude_circles
        altitude_circ_dicts = _add_color(altitude_circ, col)

        # suns
        points = []
        col = st.color_picker('Sun Color', '#f2b24d',
                              key='sun-col').lstrip('#')
        hourly_suns = sunpath.hourly_analemma_suns()
        for suns in hourly_suns:
            for sun in suns:
                if sun.is_during_day:
                    pt = sun.position_3d(radius=radius)
                    points.append(pt)
        suns_dicts = _add_color(points, col)

    # group them
    geometries = polylines_dicts + arcs_dicts + circles_dicts + \
        ticks_dicts + altitude_circ_dicts + suns_dicts

    inputs.send(
        geometries, 'my-secret-key', key='goo', label='Preview',
        defaultChecked=True
    )

    with st.sidebar:
        # add bake button to side bar
        button.send('BakeGeometry',
            geometries, 'my-secret-key-2', 
            options={
                "layer":"Sunpath",
                "units": "Meters"},
            key='my-secret-key'
        )
