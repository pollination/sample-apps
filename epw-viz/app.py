import pathlib
import streamlit as st
import pandas as pd
import numpy as np
import copy

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

from helper import colorsets, get_fields, get_image, get_hourly_data_figure, \
    get_bar_chart_figure

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

    ####################################################################################
    # Control panel
    ####################################################################################
    with st.sidebar:

        # A dictionary of EPW variable name to its corresponding field number
        fields = get_fields()

        # epw file #####################################################################
        with st.expander('Upload an EPW file'):
            epw_data = st.file_uploader('', type='epw')
            if epw_data:
                epw_file = pathlib.Path('./data/sample.epw')
                epw_file.parent.mkdir(parents=True, exist_ok=True)
                epw_file.write_bytes(epw_data.read())
            else:
                epw_file = './assets/sample.epw'

            epw = EPW(epw_file)

        # analysis period ##############################################################
        with st.expander('Apply analysis period'):

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

        # Global Colorset ##############################################################
        with st.expander('Apply global colorset'):
            global_colorset = st.selectbox('', list(colorsets.keys()))

        # Hourly data ##################################################################
        with st.expander('Hourly data'):
            selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), key='hourly_data')
            hourly_data = epw._get_data_by_field(fields[selected])
            hourly_data_conditional_statement = st.text_input(
                'Apply conditional statement')
            hourly_data_min = st.text_input('Min')
            hourly_data_max = st.text_input('Max')

        # Bar Chart ####################################################################
        with st.expander('Bar Chart'):

            bar_chart_selection = []
            for var in fields.keys():
                if var == 'Dry Bulb Temperature' or var == 'Relative Humidity':
                    bar_chart_selection.append(st.checkbox(var, value=True))
                else:
                    bar_chart_selection.append(st.checkbox(var, value=False))

            bar_chart_data_type = st.selectbox('', ('Monthly average', 'Monthly total',
                                                    'Daily average',
                                                    'Daily total'), key=0)
            bar_chart_switch = st.checkbox(
                'Switch colors', value=False, key='bar_chart_switch')
            bar_chart_stack = st.checkbox('Stack', value=False, key='bar_chart_stacked')

    ####################################################################################
    # Main page
    ####################################################################################
    with st.container():
        st.title('Weather Data Visualization App!')

        st.markdown('Welcome to the weather data visualization app! Browse to the downloaded'
                    ' EPW file on your system to visualize it. By default, the app loads EPW'
                    ' file for Boston, USA.')
        st.markdown('🖱️ Hover over every chart to see the values.')

        st.header(f'{epw.location.city}, {epw.location.country}')

        # image and map ################################################################
        col1, col2 = st.columns(2)

        with col1:
            st.text(
                f'Latitude: {epw.location.latitude}, Longitude: {epw.location.longitude},'
                f' Timezone: {epw.location.time_zone}, source: {epw.location.source}')

            with st.expander('Load imge from local drive'):
                local_image = st.file_uploader(
                    'Select an image', type=['png', 'jpg', 'jpeg'])

            get_image(epw.location.latitude, epw.location.longitude)

            if local_image:
                st.image(local_image)
            else:
                try:
                    st.image('./assets/image/000001.jpg')
                except FileNotFoundError:
                    pass

        with col2:
            location = pd.DataFrame(
                [np.array([epw.location.latitude, epw.location.longitude], dtype=np.float64)],
                columns=['latitude', 'longitude']
            )
            st.map(location, use_container_width=True)

        # Hourly data ##################################################################
        with st.container():
            st.header('visualize hourly data')
            st.markdown(
                'Select an environmental variable from the EPW weatherfile to visualize.'
                ' By default, the hourly data is set to "dry bulb temperature".'
                ' You can use the conditional statement to filter the data.'
                ' For example, to see the dry bulb temperature above 10, you'
                ' can use the conditional statement, "a>10" without quotes.'
                ' To see dry bulb temperature between -5 and 10 you can use the '
                ' conditional statement, "a>-5 and a<10" without quotes.'
                ' You can also use the min and max inputs to customize the bounds of the'
                ' data you are visualizing and the legend. By default, the chart uses the'
                ' minimum and maximum values of the data to set the bounds.')

            hourly_data_figure = get_hourly_data_figure(
                hourly_data, global_colorset, hourly_data_conditional_statement,
                hourly_data_min, hourly_data_max)

            if isinstance(hourly_data_figure, str):
                st.error(hourly_data_figure)
            else:
                st.plotly_chart(hourly_data_figure, use_container_width=True)

        # Bar Chart ####################################################################
        with st.container():
            st.header('Bar chart')
            st.markdown(
                'Select one or more environmental variable from the EPW weatherfile to'
                ' visualize side by side on a monthly or daily bar chart. By default, '
                ' "Dry bulb temperature" and "relative humidity" are selected.')

            bar_chart_figure = get_bar_chart_figure(
                fields, epw, bar_chart_selection, bar_chart_data_type,
                bar_chart_switch, bar_chart_stack, global_colorset)

            st.plotly_chart(bar_chart_figure, use_container_width=True)


if __name__ == '__main__':
    main()
