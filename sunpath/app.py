"""The Pollination sunpath app."""


import pathlib
import csv

import streamlit as st
from streamlit_vtkjs import st_vtkjs

from typing import List, Tuple

from ladybug.compass import Compass
from ladybug.color import Color
from ladybug.sunpath import Sunpath
from ladybug.epw import EPW, EPWFields
from ladybug.location import Location
from ladybug.datacollection import HourlyContinuousCollection
from pollination_streamlit_io import inputs

# make it look good by setting up the title, icon, etc.
st.set_page_config(
    page_title='Sunpath',
    page_icon='https://app.pollination.cloud/favicon.ico'
)
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba_pollination_brandmark-p-500.png',
    use_column_width=True
)

# helper hash functions


def epw_hash_func(epw): return epw.location.city
def sunpath_hash_func(sp): return sp.latitude, sp.longitude, sp.north_angle
def hourly_data_hash_func(data): return data.header.data_type


# create the control panel
with st.sidebar:

    latitude = st.slider('Latitude', -90.0, 90.0, 0.0, 0.5)
    longitude = st.slider('Longitude', -90.0, 90.0, 0.0, 0.5)
    north = st.slider('North', -180, 180, 0, 1)
    projection = st.slider('Projection', 2, 3, value=3, help='Choose between 2D and 3D.')

    # load EPW
    with st.expander('Sunpath for EPW'):
        epw_data = st.file_uploader('Load EPW', type='epw')
        # if epw file is uploaded, load it
        if epw_data:
            epw_file = pathlib.Path('./data/sample.epw')
            epw_file.parent.mkdir(parents=True, exist_ok=True)
            epw_file.write_bytes(epw_data.read())
            epw = EPW(epw_file)
        else:
            epw = None

    # select data from EPW to mount on Sunpath
    fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}
    with st.expander('Load data on sunpath'):
        st.text('*Load EPW first*')
        selection = []
        for var in fields.keys():
            selection.append(st.checkbox(var, value=False))

        if any(selection) and not epw_data:
            load_data = False
        else:
            load_data = True

        if load_data:
            data = []
            for count, var in enumerate(selection):
                if var:
                    data.append(epw._get_data_by_field(
                        fields[list(fields.keys())[count]]))

    st.markdown('----')

    menu = st.checkbox('Show viewer controls', value=False)


def create_sunpath(latitude: float, longitude: float, north: int,
                   location: Location = None,
                   data: List[HourlyContinuousCollection] = None) -> Tuple[pathlib.Path,
                                                                           Sunpath]:
    """Create a sunpath and generate a vtkjs file for it.

    Args:
        latitude: The latitude of the location.
        longitude: The longitude of the location.
        north: The north angle of the sunpath.
        location: A ladybug location object. Defaults to None.
        data: A list of ladybug HourlyContinuousCollection objects. Defaults to None.

    Returns:
        A tuple of two elements

        -   A pathlib.Path object pointing to the vtkjs file.

        -   A ladybug Sunpath object.

        -   A ladybug Color object.

    """
    sun_color = Color(235, 33, 38)
    folder = pathlib.Path('./data')
    folder.mkdir(parents=True, exist_ok=True)
    name = f'{latitude}_{longitude}_{north}'

    if location:
        sp = Sunpath.from_location(epw.location, north_angle=north)
    else:
        sp = Sunpath(latitude, longitude, north_angle=north)

    # create a vtkjs file for sunpath
    if projection == 3:
        sp_vtkjs = sp.to_vtkjs(folder.as_posix(), file_name=name,
                               data=data, sun_color=sun_color)
    else:
        sp_vtkjs = sp.to_vtkjs(folder.as_posix(), file_name=name,
                               data=data, sun_color=sun_color, make_2d=True)
    return sp_vtkjs, sp, sun_color


# call the function to create the sunpath
if epw_data:
    if data:
        result = create_sunpath(latitude, longitude, north,
                                location=epw.location, data=data)
    else:
        result = create_sunpath(latitude, longitude, north,
                                location=epw.location)
    header_text = f'Sunpath for {epw.location.city} '
else:
    result = create_sunpath(latitude, longitude, north)
    header_text = f'Sunpath for latitude: {latitude} and longitude: {longitude}'


# add header
st.markdown(header_text)

# update the viewer
st_vtkjs(result[0].read_bytes(), menu=menu, key='viewer')

# generate a csv file
col2 = st.columns(3)[1]
with col2:
    write_csv = st.checkbox('Generate CSV', value=False)


@st.cache(allow_output_mutation=True, hash_funcs={Sunpath: sunpath_hash_func, EPW: epw_hash_func,
                                                  HourlyContinuousCollection: hourly_data_hash_func})
def write_csv_file(sunpath: Sunpath, epw: EPW = None,
                   data: List[HourlyContinuousCollection] = None) -> str:
    filename = './data/sunpath.csv'
    header = ['Month', 'Day', 'Hour', 'Altitude', 'Azimuth']
    # writing to csv files
    with open(filename, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        if epw:
            csv_writer.writerow(['City', epw.location.city])
        csv_writer.writerow(['Latitude', str(sunpath.latitude)])
        csv_writer.writerow(['Longitude', str(sunpath.longitude)])

        if data:
            data_headers = [dt.header.data_type for dt in data]
            header.extend(data_headers)
            csv_writer.writerow(header)
        else:
            csv_writer.writerow(header)

        # write values for all hours of the year
        for hr in range(8760):
            sun = sunpath.calculate_sun_from_hoy(hr)
            date_time = sun.datetime

            if data:
                csv_writer.writerow([date_time.month, date_time.day,
                                     date_time.hour, sun.altitude, sun.azimuth] +
                                    [dt.values[hr] for dt in data])
            else:
                csv_writer.writerow([date_time.month, date_time.day,
                                     date_time.hour, sun.altitude, sun.azimuth])

    return filename


# write csv and serve a button if csv is requested
if write_csv:
    if epw_data:
        if data:
            csv_file_path = write_csv_file(result[1], epw, data)
        else:
            csv_file_path = write_csv_file(result[1], epw)
    else:
        csv_file_path = write_csv_file(result[1])
    with col2:
        with open(csv_file_path, 'r') as f:
            st.download_button('Download CSV', f, file_name='sunpath.csv')

# rhino integration

# get the platform from the query uri
query = st.experimental_get_query_params()
platform = query['__platform__'][0] if '__platform__' in query else 'web'

if platform == 'Rhino':
    def get_colored_geometry_json_strings(geometries, hex_color):
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        geometry_dicts = [g.to_dict() for g in geometries]
        for d in geometry_dicts:
            d['color'] = Color(*rgb).to_dict()
        return geometry_dicts

    # layout
    col1, col2, col3 = st.columns(3)

    # get results from vtk
    sun_file, sun_path, sun_color = result

    # values here
    radius = st.slider('Sun path radius', 0, 500, 100)

    # create the compass
    co = Compass(radius=radius,
                 north_angle=north,
                 spacing_factor=0.15)

    with col1:
        # analemma
        col = st.color_picker('Analemma Color', '#000000',
                              key='poly-col').lstrip('#')
        polylines = sun_path.hourly_analemma_polyline3d(radius=radius)
        polylines_dicts = get_colored_geometry_json_strings(polylines, col)

        # arcs
        col = st.color_picker('Arcs Color', '#bcbec0',
                              key='arc-col').lstrip('#')
        arcs = sun_path.monthly_day_arc3d(radius=radius)
        arcs_dicts = get_colored_geometry_json_strings(arcs, col)

    with col2:
        # circles
        col = st.color_picker('Circles Color', '#eb2126',
                              key='circl-col').lstrip('#')
        circles = co.all_boundary_circles
        circles_dicts = get_colored_geometry_json_strings(circles, col)

        # ticks
        col = st.color_picker('Ticks Color', '#2ea8e0',
                              key='tick-col').lstrip('#')
        major_ticks = co.major_azimuth_ticks
        minor_ticks = co.minor_azimuth_ticks
        ticks = major_ticks + minor_ticks
        ticks_dicts = get_colored_geometry_json_strings(ticks, col)

    with col3:
        # altitude circles
        col = st.color_picker('Circle Color', '#05a64f',
                              key='tick-col').lstrip('#')
        altitude_circ = co.stereographic_altitude_circles
        altitude_circ_dicts = get_colored_geometry_json_strings(altitude_circ, col)

        # suns
        points = []
        col = st.color_picker('Sun Color', '#f2b24d',
                              key='sun-col').lstrip('#')
        hourly_suns = sun_path.hourly_analemma_suns()
        for suns in hourly_suns:
            for sun in suns:
                if sun.is_during_day:
                    pt = sun.position_3d(radius=radius)
                    points.append(pt)
        suns_dicts = get_colored_geometry_json_strings(points, col)

    # group them
    geometries = polylines_dicts + arcs_dicts + circles_dicts + \
        ticks_dicts + altitude_circ_dicts + suns_dicts

    inputs.send(geometries, 'my-secret-key', key='goo')
