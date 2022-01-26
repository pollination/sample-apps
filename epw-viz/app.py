import pathlib
import streamlit as st
import pandas as pd
import numpy as np


from ladybug.epw import EPW, EPWFields
from ladybug.hourlyplot import HourlyPlot
from ladybug.legend import LegendParameters
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.datatype.temperaturetime import HeatingDegreeTime, CoolingDegreeTime
from ladybug.sunpath import Sunpath
from ladybug.windrose import WindRose
from ladybug.psychchart import PsychrometricChart
from ladybug.color import Color, Colorset
from ladybug.monthlychart import MonthlyChart
from ladybug.analysisperiod import AnalysisPeriod

from ladybug_comfort.chart.polygonpmv import PolygonPMV
from ladybug_comfort.degreetime import heating_degree_time, cooling_degree_time

from ladybug_charts.utils import Strategy

from helper import get_image, city_name

st.set_page_config(
    page_title='Weather data visualization', layout='wide',
    page_icon='https://app.pollination.cloud/favicon.ico'
)

st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba'
    '_pollination_brandmark-p-500.png',
    use_column_width=True
)


def main():

    with st.sidebar:
        # epw file
        with st.expander('Upload an EPW file'):
            epw_data = st.file_uploader('', type='epw')
            if epw_data:
                epw_file = pathlib.Path('./data/sample.epw')
                epw_file.parent.mkdir(parents=True, exist_ok=True)
                epw_file.write_bytes(epw_data.read())
            else:
                epw_file = './assets/sample.epw'

            epw = EPW(epw_file)

        # analysis period
        with st.expander('Apply analysis period'):

            # switch between 'default' and 'custom'
            analysis_period = st.radio('Select default analysis period',
                                       options=['Default', 'Custom'])
            if analysis_period == 'Custom':
                st_month = st.number_input(
                    'Start month', min_value=1, max_value=12, value=1)
                end_month = st.number_input(
                    'End month', min_value=1, max_value=12, value=12)

                st_day = st.number_input('Start day', min_value=1, max_value=31, value=1)
                end_day = st.number_input('End day', min_value=1, max_value=31, value=31)

                st_hour = st.number_input(
                    'Start hour', min_value=0, max_value=23, value=0)
                end_hour = st.number_input(
                    'End hour', min_value=0, max_value=23, value=23)

                lb_ap = AnalysisPeriod(st_month, st_day, st_hour,
                                       end_month, end_day, end_hour)
            else:
                lb_ap = None

    with st.container():
        st.title('Weather Data Visualization App!')

        st.markdown('Welcome to the weather data visualization app! Browse to the downloaded'
                    ' EPW file on your system to visualize it. By default, the app loads EPW'
                    ' file for Boston, USA.')
        st.markdown('🖱️ Hover over every chart to see the values.')

        st.header(f'{epw.location.city}, {epw.location.country}')

        col1, col2 = st.columns(2)

        with col1:
            # write location info
            st.text(
                f'Latitude: {epw.location.latitude}, Longitude: {epw.location.longitude},'
                f' Timezone: {epw.location.time_zone}, source: {epw.location.source}')

            # load image
            # local image
            with st.expander('Load imge from local drive'):
                local_image = st.file_uploader(
                    'Select an image', type=['png', 'jpg', 'jpeg'])

            # get the image from the internet
            # get the city name from latitude and longitude
            keyword = city_name(epw.location.latitude,
                                epw.location.longitude) + ' city image'
            get_image(keyword)

            # If someone loads an image from local drive, use it else use the image from
            # the internet
            if local_image:
                st.image(local_image)
            else:
                try:
                    st.image('./assets/image/000001.jpg')
                except FileNotFoundError:
                    pass

        # add a map
        with col2:
            location = pd.DataFrame(
                [np.array([epw.location.latitude, epw.location.longitude], dtype=np.float64)],
                columns=['latitude', 'longitude']
            )
            st.map(location, use_container_width=True)


if __name__ == '__main__':
    main()
