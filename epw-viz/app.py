import pathlib

import streamlit as st
import pandas as pd
import numpy as np
from streamlit_vtkjs import st_vtkjs
from ladybug.epw import EPW, EPWFields
from ladybug.hourlyplot import HourlyPlot
from ladybug_pandas import DataFrame

from ladybug.sunpath import Sunpath

st.set_page_config(
    page_title='Weather data visualization', layout='wide',
    page_icon='https://app.pollination.cloud/favicon.ico'
)

st.title('Sample Weather Data Visualization App!')


def main():
    # split the first container into 2
    with st.container():
        col1, col2 = st.columns(2)

        with col1.expander('Click to read more'):
            """
            A sample app for visualizing weather data from an EPW file.

            This app is very simple and is mainly developed for demonestration purposes.
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
            # update the viewer
            st_vtkjs(sp_file.read_bytes(), menu=True, key='viewer')

    with st.container():
        # show weather data in 2D and 3D
        fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}
        selected = st.selectbox('Select data', options=fields.keys())
        data = epw._get_data_by_field(fields[selected])

    with st.container():
        col1, col2 = st.columns([2.5, 1.5])
        with col1:
            # keeping things very simple here
            # you can draw really advanced charts if desired
            st.header(selected)
            st.line_chart(DataFrame([data]))
            st.header('Average monthly')
            df = DataFrame([data.average_monthly()]).transpose()
            df.columns = [
                'Jan', 'Feb', 'Mar','Apr', 'May', 'Jun','Jul', 'Aug', 'Sep','Oct',
                'Nov', 'Dec'
            ]
            st.table(df)
        with col2:
            # show off 3D charts
            hp = HourlyPlot(data, z_dim=100)
            hp_file = hp.to_vtkjs(folder.as_posix(), file_name=selected)
            st_vtkjs(hp_file.read_bytes(), menu=True, key='hourly_plot')

if __name__ == '__main__':
    main()
