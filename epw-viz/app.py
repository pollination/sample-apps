import pathlib
import streamlit as st
import pandas as pd
import numpy as np
import shutil

from icrawler.builtin import GoogleImageCrawler
from geopy.geocoders import Nominatim

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


@st.cache(suppress_st_warning=True)
def get_image(keyword):
    # nuke the images folder if exists
    path = pathlib.Path('./assets/image')
    if path.is_dir():
        shutil.rmtree(path)
    # create a new folder to download the image
    path.mkdir(parents=True, exist_ok=True)
    filters = dict(size='medium', type='photo',
                   license='commercial,modify')
    google_crawler = GoogleImageCrawler(storage={'root_dir': './assets/image'})
    google_crawler.crawl(keyword=keyword, max_num=1, filters=filters)


def city_name(latitude: float, longitude: float) -> str:
    """Get the city name from latitude and longitude"""
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(str(latitude)+","+str(longitude), language='en')
    address = location.raw['address']
    city = address.get('city', '')
    return city


st.set_page_config(
    page_title='Weather data visualization', layout='wide',
    page_icon='https://app.pollination.cloud/favicon.ico'
)


####################################################################################
# Introduction
####################################################################################
st.title('Weather Data Visualization App!')
st.markdown('Welcome to the weather data visualization app! Browse to the downloaded'
            ' EPW file on your system to visualize it. By default, the app loads EPW'
            ' file for Boston, USA.')
st.markdown('🖱️ Hover over every chart to see the values.')


def main():
    # create the data folder if it is not created already
    folder = pathlib.Path('./data')
    folder.mkdir(parents=True, exist_ok=True)

    ####################################################################################
    # Select weather file
    ####################################################################################
    with st.container():
        # # Create a dropdown to upload a file or use a sample file
        epw_source = st.selectbox(
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
        epw_loc = epw.location
        location = pd.DataFrame(
            [np.array([epw_loc.latitude, epw_loc.longitude], dtype=np.float64)],
            columns=['latitude', 'longitude']
        )

    ####################################################################################
    # Image and Map
    ####################################################################################
    with st.container():
        st.header(f'{epw_loc.city}, {epw_loc.country}')

        col1, col2 = st.columns(2)

        with col1:
            # write location info
            st.text(
                f'Latitude: {epw_loc.latitude}, Longitude: {epw_loc.longitude},'
                f' Timezone: {epw_loc.time_zone}, source: {epw_loc.source}')

            # load image
            # local image
            with st.expander('Load imge from local drive'):
                local_image = st.file_uploader(
                    'Select an image', type=['png', 'jpg', 'jpeg'])

            # get the image from the internet
            # get the city name from latitude and longitude
            keyword = city_name(epw_loc.latitude, epw_loc.longitude) + ' city image'
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
            st.map(location, use_container_width=True)

    ####################################################################################
    # Global colorset
    ####################################################################################
    with st.container():
        colorsets = {
            'original': Colorset.original(),
            'nuanced': Colorset.nuanced(),
            'annual_comfort': Colorset.annual_comfort(),
            'benefit': Colorset.benefit(),
            'benefit_harm': Colorset.benefit_harm(),
            'black_to_white': Colorset.black_to_white(),
            'blue_green_red': Colorset.blue_green_red(),
            'cloud_cover': Colorset.cloud_cover(),
            'cold_sensation': Colorset.cold_sensation(),
            'ecotect': Colorset.ecotect(),
            'energy_balance': Colorset.energy_balance(),
            'energy_balance_storage': Colorset.energy_balance_storage(),
            'glare_study': Colorset.glare_study(),
            'harm': Colorset.harm(),
            'heat_sensation': Colorset.heat_sensation(),
            'multi_colored': Colorset.multi_colored(),
            'multicolored_2': Colorset.multicolored_2(),
            'multicolored_3': Colorset.multicolored_3(),
            'openstudio_palette': Colorset.openstudio_palette(),
            'peak_load_balance': Colorset.peak_load_balance(),
            'shade_benefit': Colorset.shade_benefit(),
            'shade_benefit_harm': Colorset.shade_benefit_harm(),
            'shade_harm': Colorset.shade_harm(),
            'shadow_study': Colorset.shadow_study(),
            'therm': Colorset.therm(),
            'thermal_comfort': Colorset.thermal_comfort(),
            'view_study': Colorset.view_study()
        }
        st.header('Colorset')
        st.markdown(
            'Select a Ladybug colorset to apply consistent color scheme to all the charts'
            ' in this app. By default, the colorset is set to "original".')

        selected_colorset = st.selectbox('', list(colorsets.keys()))
        colorset = colorsets[selected_colorset]

    ####################################################################################
    # Hourly data
    ####################################################################################
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

        col1, col2, col3, col4 = st.columns([5, 3, 1, 1])

        with col1:
            # select the data to visualize
            fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}
            selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), key='hourly_data')
            data = epw._get_data_by_field(fields[selected])

        with col2:
            # apply conditional statement to the selected data
            conditional_statement = st.text_input('Apply conditional statement')
            if conditional_statement:
                try:
                    data = data.filter_by_conditional_statement(
                        conditional_statement)
                except AssertionError:
                    st.error('No values found for that conditional statement')
                    data = data
                except ValueError:
                    st.error('Invalid conditional statement')
                    data = data

        with col3:
            # minimum value of legend
            min = st.text_input('Min')
            if min:
                try:
                    min = float(min)
                except ValueError:
                    st.error('Invalid minimum value')
                    min = None

        with col4:
            # maximum value of legend
            max = st.text_input('Max')
            if max:
                try:
                    max = float(max)
                except ValueError:
                    st.error('Invalid maximum value')
                    max = None

    # plot hourly data
    with st.container():
        lb_lp = LegendParameters(colors=colorset)
        if min:
            lb_lp.min = min
        if max:
            lb_lp.max = max
        hourly_plot = HourlyPlot(data, legend_parameters=lb_lp)

        figure = hourly_plot.plot()
        st.plotly_chart(figure, use_container_width=True)

    ####################################################################################
    # Bar chart
    ####################################################################################
    with st.container():

        st.header('Bar chart')
        st.markdown(
            'Select one or more environmental variable from the EPW weatherfile to'
            ' visualize side by side on a monthly or daily bar chart. By default, '
            ' "Dry bulb temperature" and "relative humidity" are selected.')

        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

        with col1:
            # select the data to visualize
            fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}

            with st.expander('Select variables'):
                selection = []
                for var in fields.keys():
                    if var == 'Dry Bulb Temperature' or var == 'Relative Humidity':
                        selection.append(st.checkbox(var, value=True))
                    else:
                        selection.append(st.checkbox(var, value=False))

        with col2:
            with st.expander('Select data type'):
                data_type = st.selectbox('', ('Monthly average', 'Monthly total', 'Daily average',
                                              'Daily total'), key=0)

        with col3:
            st.text('')
            switch = st.checkbox('Switch colors', value=False, key='bar_chart_switch')

        with col4:
            st.text('')
            stack = st.checkbox('Stack', value=False, key='bar_chart_stacked')

        if switch:
            colors = list(colorset)
            colors.reverse()
        else:
            colors = colorset

        data = []
        for count, item in enumerate(selection):
            if item:
                var = epw._get_data_by_field(fields[list(fields.keys())[count]])
                if data_type == 'Monthly average':
                    data.append(var.average_monthly())
                elif data_type == 'Monthly total':
                    data.append(var.total_monthly())
                elif data_type == 'Daily average':
                    data.append(var.average_daily())
                elif data_type == 'Daily total':
                    data.append(var.total_daily())

        lb_lp = LegendParameters(colors=colors)
        monthly_chart = MonthlyChart(data, legend_parameters=lb_lp)
        figure = monthly_chart.plot(stack=stack, title=data_type, show_title=True)
        st.plotly_chart(figure, use_container_width=True)

    ####################################################################################
    # Hourly line chart
    ####################################################################################
    with st.container():

        st.header('Hourly line chart')
        st.markdown(
            'Select an environmental variable from the EPW weatherfile to visualize on a'
            ' line chart. By default, the hourly data is set to "relative humidity".')

        col1, col2 = st.columns(2)

        with col1:
            # select the data to visualize
            fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}

            selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), index=2,
                key='line_chart')
            data = epw._get_data_by_field(fields[selected])

        with col2:
            st.text("")
            st.text("")
            st.text("")
            switch = st.checkbox('Switch colors', key='line_chart_switch',
                                 help='Reverse the colorset')

        if switch:
            colors = list(colorset)
            colors.reverse()
        else:
            colors = colorset

        fig = data.line_chart(color=colors[-1])
        st.plotly_chart(fig, use_container_width=True)

    ####################################################################################
    # Per hour line chart
    ####################################################################################
    with st.container():

        st.header('Per hour line chart')
        st.markdown(
            'Select an environmental variable from the EPW weatherfile to visualize on a'
            ' per hour line chart. By default, the hourly data is set to "Direct normal'
            ' radiation".')

        col1, col2 = st.columns(2)

        with col1:
            # select the data to visualize
            fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}

            selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), index=8,
                key='per_hour_chart')
            data = epw._get_data_by_field(fields[selected])

        with col2:
            st.text("")
            st.text("")
            st.text("")
            switch = st.checkbox('Switch colors', key='per_hour_chart_switch',
                                 help='Reverse the colorset')

        if switch:
            colors = list(colorset)
            colors.reverse()
        else:
            colors = colorset

        fig = data.per_hour_line_chart(title=data.header.unit, show_title=True,
                                       color=colors[-1])
        st.plotly_chart(fig, use_container_width=True)

    ####################################################################################
    # Daily chart
    ####################################################################################
    with st.container():

        st.header('Daily chart')
        st.markdown(
            'Select an environmental variable from the EPW weatherfile to visualize on a'
            ' daily chart. This chart shows average daily values. By default, the hourly'
            ' data is set to "Total sky cover".')

        col1, col2 = st.columns(2)

        with col1:
            # select the data to visualize
            fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}

            selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), index=16,
                key='daily_chart')
            data = epw._get_data_by_field(fields[selected])

        with col2:
            st.text("")
            st.text("")
            st.text("")
            switch = st.checkbox('Switch colors', key='daily_chart_switch',
                                 help='Reverse the colorset')

        if switch:
            colors = list(colorset)
            colors.reverse()
        else:
            colors = colorset

        data = data.average_daily()
        fig = data.bar_chart(color=colors[-1])
        st.plotly_chart(fig, use_container_width=True)

    ####################################################################################
    # SUNPATH
    ####################################################################################
    with st.container():

        st.header('Sunpath')
        st.markdown('Generate a sunpath based on the latitude and longitude of a'
                    ' location. Additionally, you can also load one of the environmental'
                    ' variables from the EPW file on the sunpath. By default, the'
                    ' sunpath is plotted for the location mentioned in the EPW file.'
                    )

        col1, col2 = st.columns(2)

        with col1:
            load_data = st.checkbox('Load data')
            # select the data to visualize
            fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}
            selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), key='sunpath')
            data = epw._get_data_by_field(fields[selected])

        with col2:
            switch = st.checkbox('Switch colors', key='sunpath_switch',
                                 help='Reverse the colorset')
            # set latitude and longitude
            lat_lon = st.text_input('Latitude and Longitude separated by a comma')
            if lat_lon:
                lat, lon = lat_lon.split(',')
                if lat:
                    try:
                        lat = float(lat)
                    except ValueError:
                        st.error('Invalid value for latitude')
                        lat = None
                if lon:
                    try:
                        lon = float(lon)
                    except ValueError:
                        st.error('Invalid value for longitude')
                        lon = None

        if lat_lon:
            lb_sunpath = Sunpath(lat, lon)
        else:
            lb_sunpath = Sunpath.from_location(epw.location)

        if switch:
            colors = list(colorset)
            colors.reverse()
        else:
            colors = colorset

        if load_data:
            fig = lb_sunpath.plot(colorset=colors, data=data)
        else:
            fig = lb_sunpath.plot(colorset=colors)

        st.plotly_chart(fig, use_container_width=True)

    ####################################################################################
    # Heating degree days and Cooling degree days
    ####################################################################################
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

        dbt = epw.dry_bulb_temperature

        col1, col2 = st.columns(2)
        with col1:
            stack = st.checkbox('Stack')
            _heat_base_ = st.number_input('Base heating temperature', value=18)
        with col2:
            switch = st.checkbox('Switch colors', key='degree_switch',
                                 help='Reverse the colorset')
            _cool_base_ = st.number_input('Base cooling temperature', value=23)

        hourly_heat = HourlyContinuousCollection.compute_function_aligned(
            heating_degree_time, [dbt, _heat_base_],
            HeatingDegreeTime(), 'degC-hours')
        hourly_heat.convert_to_unit('degC-days')

        hourly_cool = HourlyContinuousCollection.compute_function_aligned(
            cooling_degree_time, [dbt, _cool_base_],
            CoolingDegreeTime(), 'degC-hours')
        hourly_cool.convert_to_unit('degC-days')

        if switch:
            colors = list(colorset)
            colors.reverse()
        else:
            colors = colorset

        lb_lp = LegendParameters(colors=colors)
        monthly_chart = MonthlyChart([hourly_cool.total_monthly(),
                                      hourly_heat.total_monthly()], legend_parameters=lb_lp)
        figure = monthly_chart.plot(stack=stack)
        st.plotly_chart(figure, use_container_width=True)
        st.text(
            f'Total Cooling degree days are {round(hourly_cool.total)}'
            f' and total heating degree days {round(hourly_heat.total)}.')

    ####################################################################################
    # windrose
    ####################################################################################
    with st.container():
        st.header('Windrose')
        st.markdown('Generate a windrose diagram')

        col1, col2, col3 = st.columns(3)

        with col1:
            st_month = st.number_input('Start month', min_value=1, max_value=12, value=1)
            end_month = st.number_input('End month', min_value=1, max_value=12, value=12)
        with col2:
            st_day = st.number_input('Start day', min_value=1, max_value=31, value=1)
            end_day = st.number_input('End day', min_value=1, max_value=31, value=31)
        with col3:
            st_hour = st.number_input('Start hour', min_value=0, max_value=23, value=0)
            end_hour = st.number_input('End hour', min_value=0, max_value=23, value=23)

        lb_ap = AnalysisPeriod(st_month, st_day, st_hour, end_month, end_day, end_hour)
        wind_dir = epw.wind_direction.filter_by_analysis_period(lb_ap)
        wind_spd = epw.wind_speed.filter_by_analysis_period(lb_ap)

        lb_lp = LegendParameters(colors=colorset)
        lb_wind_rose = WindRose(wind_dir, wind_spd)
        lb_wind_rose.legend_parameters = lb_lp
        fig = lb_wind_rose.plot()

        st.plotly_chart(fig, use_container_width=True)

    ####################################################################################
    # Psychrometric chart
    ####################################################################################
    with st.container():
        st.header('Psychrometric Chart')
        st.markdown(
            'Generate a psychrometric chart for the dry bulb temperature and relative'
            ' humidity of from the weather file. You can load one of the environmental'
            ' variables of EPW on the psychrometric chart. Additionally, you can also'
            ' add comfort polygons to the chart by selecting one of the passive strategies.'
            ' By default, the psychrometric shows the hours in year when a certain'
            ' dry bulb temperature and relative humidity occurs.')

        col1, col2 = st.columns(2)

        with col1:
            # select the data to visualize
            load_data = st.checkbox('Load data', key='psychrometric')
            fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}
            selected = st.selectbox(
                'Select an environmental variable', options=fields.keys(), key='psychrometric')
            data = epw._get_data_by_field(fields[selected])

        with col2:
            draw_polygons = st.checkbox('Draw comfort polygons', key='psychrometric')
            strategy_options = ['Comfort', 'Evaporative Cooling',
                                'Mass + Night Ventilation', ' Occupant use of fans',
                                'Capture internal heat', 'Passive solar heating', 'All']
            selected_strategy = st.selectbox(
                'Select a passive strategy', options=strategy_options, key='psychrometric')

        lb_lp = LegendParameters(colors=colorset)
        lb_psy = PsychrometricChart(epw.dry_bulb_temperature,
                                    epw.relative_humidity, legend_parameters=lb_lp)

        if selected_strategy == 'All':
            strategies = [Strategy.comfort, Strategy.evaporative_cooling,
                          Strategy.mas_night_ventilation, Strategy.occupant_use_of_fans,
                          Strategy.capture_internal_heat, Strategy.passive_solar_heating]
        elif selected_strategy == 'Comfort':
            strategies = [Strategy.comfort]
        elif selected_strategy == 'Evaporative Cooling':
            strategies = [Strategy.evaporative_cooling]
        elif selected_strategy == 'Mass + Night Ventilation':
            strategies = [Strategy.mas_night_ventilation]
        elif selected_strategy == 'Occupant use of fans':
            strategies = [Strategy.occupant_use_of_fans]
        elif selected_strategy == 'Capture internal heat':
            strategies = [Strategy.capture_internal_heat]
        elif selected_strategy == 'Passive solar heating':
            strategies = [Strategy.passive_solar_heating]

        pmv = PolygonPMV(lb_psy)

        if load_data:
            if draw_polygons:
                fig = lb_psy.plot(data=data, polygon_pmv=pmv,
                                  strategies=strategies,
                                  solar_data=epw.direct_normal_radiation,)
            else:
                fig = lb_psy.plot(data=data)
        else:
            if draw_polygons:
                fig = lb_psy.plot(polygon_pmv=pmv, strategies=strategies,
                                  solar_data=epw.direct_normal_radiation)
            else:
                fig = lb_psy.plot()

        st.plotly_chart(fig, use_container_width=True)


if __name__ == '__main__':
    main()
