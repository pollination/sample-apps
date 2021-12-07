import pathlib

import streamlit as st
import pandas as pd
import numpy as np
from streamlit_vtkjs import st_vtkjs
from ladybug.epw import EPW
from ladybug_pandas import DataFrame

from ladybug.sunpath import Sunpath

st.set_page_config(
    page_title='Weather data visualization', layout='wide',
    page_icon='https://app.pollination.cloud/favicon.ico'
)

st.title('Sample Weather Data Visualization App!')


def main():
    # split the first container into 2
    col1, col2 = st.columns(2)

    with col1.expander('Click to read more'):
        """
        A sample app for visualizing weather data from an EPW file.

        The main goal of developing this app is to showcase how one can use ladybug's
        libraries in combination with Streamlit to quickly build meaningful apps.
        """

    # Create a dropdown to upload a file or use a sample file
    epw_source = col1.selectbox(
        '',
        ['Sample EPW data', 'Upload an EPW file']
    )

    if epw_source == 'Upload an EPW file':
        epw_data = st.file_uploader('Select an EPW file', type='epw')
        if not epw_data:
            return
        # this is a hack since EPW doesn't have any methods to read the data as a
        # single string/bytestream
        epw_file = pathlib.Path('./data/sample.epw')
        epw_file.parent.mkdir(parents=True, exist_ok=True)
        epw_file.write_bytes(epw_data.read())
    else:
        epw_file = './assets/sample.epw'

    epw = EPW(epw_file)

    # add a map with location
    epw_loc = epw.location
    location = pd.DataFrame(
        [np.array([epw_loc.latitude, epw_loc.longitude], dtype=np.float64)],
        columns=['latitude', 'longitude']
    )
    with col1:
        st.header('Location')
        st.markdown(f'### {epw_loc.city}, {epw_loc.country}')
        st.text(
            f'Latitude: {epw_loc.latitude}, Longitude: {epw_loc.longitude}, '
            f'Time zone: {epw_loc.time_zone}, Elevation: {epw_loc.elevation}, '
            f'Source: {epw_loc.source}'
        )
        # add a map
        st.map(location)

    with col2:
        # add sunpath
        folder = pathlib.Path('./data')
        folder.mkdir(parents=True, exist_ok=True)
        sp = Sunpath.from_location(epw_loc)
        sp_file = sp.to_vtkjs(folder.as_posix(),
                              data=[epw.diffuse_horizontal_radiation,
                              epw.direct_normal_radiation, epw.dry_bulb_temperature])
        menu = st.sidebar.checkbox('Show viewer controls', value=False)
        # update the viewer
        st_vtkjs(sp_file.read_bytes(), menu=menu, key='viewer')

    # add average monthly data
    st.header('Temperature')
    df = DataFrame(
        [
            epw.dry_bulb_temperature.average_monthly(),
            epw.dew_point_temperature.average_monthly()
        ]
    )

    # keeping things very simple here
    # you can draw really advanced charts if desired
    st.line_chart(df)

    # add radiation for fun
    st.header('Radiation')
    rad_df = DataFrame(
        [
            epw.direct_normal_radiation.average_monthly(),
            epw.diffuse_horizontal_radiation.average_monthly()
        ]
    )
    st.area_chart(rad_df)


if __name__ == '__main__':
    main()
