"""The Pollination sunpath app."""


import pathlib
import csv
from numpy import row_stack

import streamlit as st
from streamlit_vtkjs import st_vtkjs

from typing import List, Tuple

from ladybug.color import Color
from ladybug.sunpath import Sunpath
from ladybug.epw import EPW, EPWFields
from ladybug.location import Location
from ladybug.datacollection import HourlyContinuousCollection

# make it look good by setting up the title, icon, etc.
st.set_page_config(
    page_title='Interactive Sunpath',
    page_icon='https://app.pollination.cloud/favicon.ico'
)
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba_pollination_brandmark-p-500.png',
    use_column_width=True
)

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

# need to raise this in a way that users can see
if any(selection) and not epw_data:
    st.error('You need to load an EPW file first.')


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
    """
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
                               data=data, sun_color=Color(235, 33, 38))
    else:
        sp_vtkjs = sp.to_vtkjs(folder.as_posix(), file_name=name,
                               data=data, sun_color=Color(235, 33, 38), make_2d=True)
    return sp_vtkjs, sp


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
write_csv = st.checkbox('Generate CSV', value=False)


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
    with open(csv_file_path, 'r') as f:
        st.download_button('Download CSV', f, file_name='sunpath.csv')
