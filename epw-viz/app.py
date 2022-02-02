import pathlib
import streamlit as st
import pandas as pd
import numpy as np

from ladybug.epw import EPW

from helper import colorsets, get_fields, get_image, get_hourly_data_figure, \
    get_bar_chart_figure, get_hourly_line_chart_figure, get_figure_config,\
    get_hourly_diurnal_average_chart_figure, get_daily_chart_figure, get_sunpath_figure,\
    get_degree_days_figure, get_windrose_figure, get_psy_chart_figure, \
    get_diurnal_average_chart_figure

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
        with st.expander('Upload EPW file'):
            epw_data = st.file_uploader('', type='epw')
            if epw_data:
                epw_file = pathlib.Path(f'./data/{epw_data.name}')
                epw_file.parent.mkdir(parents=True, exist_ok=True)
                epw_file.write_bytes(epw_data.read())
            else:
                epw_file = './assets/sample.epw'

            global_epw = EPW(epw_file)

        # Global Colorset ##############################################################
        with st.expander('Global colorset'):
            global_colorset = st.selectbox('', list(colorsets.keys()))

        st.markdown('---')

        # diurnal average chart #########################################################
        with st.expander('Diurnal average chart'):
            diurnal_average_chart_switch = st.checkbox(
                'Switch colors', value=False, key='diurnal_average_chart_switch',
                help='Reverse the colorset')

        # Hourly data ##################################################################
        with st.expander('Hourly data'):
            hourly_selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), key='hourly_data')
            hourly_data = global_epw._get_data_by_field(fields[hourly_selected])
            hourly_data_conditional_statement = st.text_input(
                'Apply conditional statement')
            hourly_data_min = st.text_input('Min')
            hourly_data_max = st.text_input('Max')

            hourly_data_st_month = st.number_input(
                'Start month', min_value=1, max_value=12, value=1, key='hourly_data_st_month')
            hourly_data_end_month = st.number_input(
                'End month', min_value=1, max_value=12, value=12, key='hourly_data_end_month')

            hourly_data_st_day = st.number_input(
                'Start day', min_value=1, max_value=31, value=1, key='hourly_data_st_day')
            hourly_data_end_day = st.number_input(
                'End day', min_value=1, max_value=31, value=31, key='hourly_data_end_day')

            hourly_data_st_hour = st.number_input(
                'Start hour', min_value=0, max_value=23, value=0, key='hourly_data_st_hour')
            hourly_data_end_hour = st.number_input(
                'End hour', min_value=0, max_value=23, value=23, key='hourly_data_end_hour')

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
                'Switch colors', value=False, key='bar_chart_switch',
                help='Reverse the colorset')
            bar_chart_stack = st.checkbox('Stack', value=False, key='bar_chart_stacked')

        # Hourly line chart ############################################################
        with st.expander('Hourly line chart'):

            hourly_line_chart_selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), index=2,
                key='line_chart')
            hourly_line_chart_data = global_epw._get_data_by_field(
                fields[hourly_line_chart_selected])

            hourly_line_chart_switch = st.checkbox('Switch colors', key='line_chart_switch',
                                                   help='Reverse the colorset')

        # Hourly diurnal chart ##########################################################
        with st.expander('Diurnal average chart from Hourly data'):

            diurnal_average_chart_hourly_selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), index=8,
                key='hourly_diurnal_average_chart')
            diurnal_average_chart_hourly_data = global_epw._get_data_by_field(
                fields[diurnal_average_chart_hourly_selected])

            diurnal_average_chart_hourly_switch = st.checkbox(
                'Switch colors', key='hourly_diurnal_average_chart_switch',
                help='Reverse the colorset')

        # Daily chart ###################################################################
        with st.expander('Daily chart'):

            daily_chart_selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), index=16,
                key='daily_chart')
            daily_chart_data = global_epw._get_data_by_field(
                fields[daily_chart_selected])

            daily_chart_switch = st.checkbox('Switch colors', key='daily_chart_switch',
                                             help='Reverse the colorset')

        # Sunpath #######################################################################
        with st.expander('Sunpath'):

            sunpath_radio = st.radio(
                '', ['from epw location', 'with epw data'],
                index=0, key=0
            )

            if sunpath_radio == 'from epw location':
                sunpath_switch = st.checkbox('Switch colors', key='sunpath_switch',
                                             help='Reverse the colorset')
                sunpath_data = None

            else:
                sunpath_selected = st.selectbox(
                    'Select an environmental variable', options=fields.keys(), key='sunpath')
                sunpath_data = global_epw._get_data_by_field(fields[sunpath_selected])
                sunpath_switch = None

        # Degree days ###################################################################
        with st.expander('Degree days'):

            degree_days_stack = st.checkbox('Stack')

            degree_days_heat_base = st.number_input('Base heating temperature',
                                                    value=18)

            degree_days_switch = st.checkbox('Switch colors', key='degree_switch',
                                             help='Reverse the colorset')

            degree_days_cool_base = st.number_input('Base cooling temperature',
                                                    value=23)

        # Windrose ######################################################################
        with st.expander('Windrose'):

            windrose_st_month = st.number_input(
                'Start month', min_value=1, max_value=12, value=1, key='windrose_st_month')
            windrose_end_month = st.number_input(
                'End month', min_value=1, max_value=12, value=12, key='windrose_end_month')

            windrose_st_day = st.number_input(
                'Start day', min_value=1, max_value=31, value=1, key='windrose_st_day')
            windrose_end_day = st.number_input(
                'End day', min_value=1, max_value=31, value=31, key='windrose_end_day')

            windrose_st_hour = st.number_input(
                'Start hour', min_value=0, max_value=23, value=0, key='windrose_st_hour')
            windrose_end_hour = st.number_input(
                'End hour', min_value=0, max_value=23, value=23, key='windrose_end_hour')

        # Psychrometric chart ############################################################
        with st.expander('Psychrometric chart'):

            psy_load_data = st.checkbox('Load data', key='psychrometric')
            if psy_load_data:
                psy_selected = st.selectbox('Select an environmental variable',
                                            options=fields.keys(), key='psychrometric')
                psy_data = global_epw._get_data_by_field(fields[psy_selected])
            else:
                psy_data = None

            psy_draw_polygons = st.checkbox('Draw comfort polygons', key='psychrometric')
            psy_strategy_options = ['Comfort', 'Evaporative Cooling',
                                    'Mass + Night Ventilation', ' Occupant use of fans',
                                    'Capture internal heat', 'Passive solar heating', 'All']
            psy_selected_strategy = st.selectbox(
                'Select a passive strategy', options=psy_strategy_options, key='psychrometric')

    ####################################################################################
    # Main page
    ####################################################################################
    with st.container():
        st.title('Weather Data Visualization App!')

        st.markdown('Welcome to the weather data visualization app! Browse to the downloaded'
                    ' EPW file on your system to visualize it. By default, the app loads EPW'
                    ' file for Boston, USA.')
        st.markdown('🖱️ Hover over every chart to see the values.')

        st.header(f'{global_epw.location.city}, {global_epw.location.country}')

        # image and map ################################################################
        col1, col2 = st.columns(2)

        with col1:
            st.text(
                f'Latitude: {global_epw.location.latitude}, Longitude: {global_epw.location.longitude},'
                f' Timezone: {global_epw.location.time_zone}, source: {global_epw.location.source}')

            with st.expander('Load imge from local drive'):
                local_image = st.file_uploader(
                    'Select an image', type=['png', 'jpg', 'jpeg'])

            get_image(global_epw.location.latitude, global_epw.location.longitude)

            if local_image:
                st.image(local_image)
            else:
                try:
                    st.image('./assets/image/000001.jpg')
                except FileNotFoundError:
                    pass

        with col2:
            location = pd.DataFrame(
                [np.array([global_epw.location.latitude,
                          global_epw.location.longitude], dtype=np.float64)],
                columns=['latitude', 'longitude']
            )
            st.map(location, use_container_width=True)

        # Diurnal average chart from hourly data ########################################
        with st.container():
            st.header('Diurnal average chart')
            st.markdown(
                'A chart showing how an average day looks like in this weather each month.')

            diurnal_average_chart_figure = get_diurnal_average_chart_figure(
                global_epw, global_colorset, diurnal_average_chart_switch)

            st.plotly_chart(diurnal_average_chart_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Diurnal chart_{global_epw.location.city}'))

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
                hourly_data_min, hourly_data_max, hourly_data_st_month, hourly_data_st_day,
                hourly_data_st_hour, hourly_data_end_month, hourly_data_end_day,
                hourly_data_end_hour)

            if isinstance(hourly_data_figure, str):
                st.error(hourly_data_figure)
            else:
                st.plotly_chart(hourly_data_figure, use_container_width=True,
                                config=get_figure_config(f'{hourly_data.header.data_type}'))

        # Bar Chart ####################################################################
        with st.container():
            st.header('Bar chart')
            st.markdown(
                'Select one or more environmental variable from the EPW weatherfile to'
                ' visualize side by side on a monthly or daily bar chart. By default, '
                ' "Dry bulb temperature" and "relative humidity" are selected.')

            bar_chart_figure = get_bar_chart_figure(
                fields, global_epw, bar_chart_selection, bar_chart_data_type,
                bar_chart_switch, bar_chart_stack, global_colorset)

            st.plotly_chart(bar_chart_figure, use_container_width=True,
                            config=get_figure_config(f'{bar_chart_data_type}'))

        # Hourly line chart ############################################################
        with st.container():
            st.header('Hourly line chart')
            st.markdown(
                'Select an environmental variable from the EPW weatherfile to visualize on a'
                ' line chart. By default, the hourly data is set to "relative humidity".')

            hourly_line_chart_figure = get_hourly_line_chart_figure(
                hourly_line_chart_data, hourly_line_chart_switch, global_colorset)

            st.plotly_chart(hourly_line_chart_figure, use_container_width=True,
                            config=get_figure_config(f'{hourly_line_chart_selected}'))

        # Diurnal average chart from hourly data ########################################
        with st.container():
            st.header('Diurnal average chart (hourly data)')
            st.markdown(
                'Select an environmental variable from the EPW weatherfile to visualize on a'
                ' diurnal average chart. By default, the hourly data is set to "Direct normal'
                ' radiation".')

            per_hour_line_chart_figure = get_hourly_diurnal_average_chart_figure(
                diurnal_average_chart_hourly_data, diurnal_average_chart_hourly_switch,
                global_colorset)

            st.plotly_chart(per_hour_line_chart_figure, use_container_width=True,
                            config=get_figure_config(
                                f'{diurnal_average_chart_hourly_data.header.data_type.name}'))

        # Daily chart ###################################################################
        with st.container():

            st.header('Daily chart')
            st.markdown(
                'Select an environmental variable from the EPW weatherfile to visualize on a'
                ' daily chart. This chart shows average daily values. By default, the hourly'
                ' data is set to "Total sky cover".')

            daily_chart_figure = get_daily_chart_figure(
                daily_chart_data, daily_chart_switch, global_colorset)

            st.plotly_chart(daily_chart_figure, use_container_width=True,
                            config=get_figure_config(
                                f'{daily_chart_data.header.data_type.name}'))

        # Sunpath #######################################################################
        with st.container():

            st.header('Sunpath')
            st.markdown('Generate a sunpath using EPW location. Additionally, you can'
                        ' also load one of the environmental variables from the EPW file'
                        ' on the sunpath.'
                        )

            sunpath_figure = get_sunpath_figure(
                sunpath_radio, global_colorset, global_epw, sunpath_switch, sunpath_data)

            st.plotly_chart(sunpath_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Sunpath_{global_epw.location.city}'))

        # Degree days ###################################################################
        with st.container():

            st.header('Degree Days')
            st.markdown('Calculates heating and cooling degree-days.'
                        ' Traditionally, degree-days are defined as the difference between'
                        ' a base temperature and the average ambient air temperature'
                        ' multiplied by the number of days that this difference exists.'
                        ' by default, the base heating temperature and base cooling'
                        ' degree temperatures are set to 18C and 23C respectively.'
                        ' Which means, it is assumed that below the heating base temperature'
                        ' heating will be deployed and above the cooling base temperature'
                        ' cooling will be deployed.')

            degree_days_figure, hourly_heat, hourly_cool = get_degree_days_figure(
                global_epw.dry_bulb_temperature, degree_days_heat_base,
                degree_days_cool_base, degree_days_stack, degree_days_switch,
                global_colorset)

            st.plotly_chart(degree_days_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Degree days_{global_epw.location.city}'))
            st.text(
                f'Total Cooling degree days are {round(hourly_cool.total)}'
                f' and total heating degree days {round(hourly_heat.total)}.')

        # Windrose ######################################################################
        with st.container():
            st.header('Windrose')
            st.markdown('Generate a windrose diagram')

            windrose_figure = get_windrose_figure(
                windrose_st_month, windrose_st_day, windrose_st_hour, windrose_end_month,
                windrose_end_day, windrose_end_hour, global_epw, global_colorset)

            st.plotly_chart(windrose_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Windrose_{global_epw.location.city}'))

        # Psychrometric chart ###########################################################
        with st.container():
            st.header('Psychrometric Chart')
            st.markdown(
                'Generate a psychrometric chart for the dry bulb temperature and relative'
                ' humidity of from the weather file. You can load one of the environmental'
                ' variables of EPW on the psychrometric chart. Additionally, you can also'
                ' add comfort polygons to the chart by selecting one of the passive strategies.'
                ' By default, the psychrometric shows the hours in year when a certain'
                ' dry bulb temperature and relative humidity occurs.')

            psy_chart_figure = get_psy_chart_figure(
                global_epw, global_colorset, psy_selected_strategy, psy_load_data,
                psy_draw_polygons, psy_data)

            st.plotly_chart(psy_chart_figure, use_container_width=True,
                            config=get_figure_config(
                                f'Psychrometric_chart_{global_epw.location.city}'))


if __name__ == '__main__':
    main()
