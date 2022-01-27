"""Functions to support the epw-viz app."""

import pathlib
import shutil
import streamlit as st

from typing import List, Tuple
from icrawler.builtin import GoogleImageCrawler
from geopy.geocoders import Nominatim
from plotly.graph_objects import Figure
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.datatype.temperaturetime import HeatingDegreeTime, CoolingDegreeTime
from ladybug_comfort.degreetime import heating_degree_time, cooling_degree_time

from ladybug.epw import EPW, EPWFields
from ladybug.color import Colorset, Color
from ladybug.legend import LegendParameters
from ladybug.hourlyplot import HourlyPlot
from ladybug.monthlychart import MonthlyChart
from ladybug.sunpath import Sunpath

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


def epw_hash_func(epw: EPW) -> str:
    """Function to help streamlit hash an EPW object."""
    return epw.location.city


def hourly_data_hash_func(hourly_data: HourlyContinuousCollection) -> str:
    """Function to help streamlit hash an HourlyContinuousCollection object."""
    return hourly_data.header.data_type


def color_hash_func(color: Color) -> Tuple[float, float, float]:
    """Function to help streamlit hash a Color object."""
    return color.r, color.g, color.b


def get_figure_config(title: str) -> dict:
    """Set figure config so that a figure can be downloaded as SVG."""

    return {
        'toImageButtonOptions': {
            'format': 'svg',  # one of png, svg, jpeg, webp
            'filename': title,
            'height': 350,
            'width': 700,
            'scale': 1  # Multiply title/legend/axis/canvas sizes by this factor
        }
    }


def get_colors(switch: bool, global_colorset: str) -> List[Color]:
    """Get switched colorset if requested.

    Args:
        switch: Boolean to switch colorset.
        global_colorset: Global colorset to use.

    Returns:
        List of colors.
    """

    if switch:
        colors = list(colorsets[global_colorset])
        colors.reverse()
    else:
        colors = colorsets[global_colorset]
    return colors


@st.cache()
def get_fields() -> dict:
    # A dictionary of EPW variable name to its corresponding field number
    return {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}


@st.cache()
def get_image(latitude: float, longitude: float) -> None:
    # find city name and create a keyword for search
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(str(latitude)+","+str(longitude), language='en')
    address = location.raw['address']
    city = address.get('city', '')
    keyword = city + ' city image'

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


@st.cache(hash_funcs={HourlyContinuousCollection: hourly_data_hash_func,
                      Color: color_hash_func}, allow_output_mutation=True)
def get_hourly_data_figure(
        data: HourlyContinuousCollection, global_colorset: str, conditional_statement: str,
        min: float, max: float, st_month: int, st_day: int, st_hour: int, end_month: int,
        end_day: int, end_hour: int) -> Figure:
    """Create heatmap from hourly data.

    Args:
        data: HourlyContinuousCollection object.
        global_colorset: A string representing the name of a Colorset.
        conditional_statement: A string representing a conditional statement.
        min: A string representing the lower bound of the data range.
        max: A string representing the upper bound of the data range.
        st_month: start month.
        st_day: start day.
        st_hour: start hour.
        end_month: end month.
        end_day: end day.
        end_hour: end hour.

    Returns:
        A plotly figure.
    """
    lb_ap = AnalysisPeriod(st_month, st_day, st_hour, end_month, end_day, end_hour)
    data = data.filter_by_analysis_period(lb_ap)

    if conditional_statement:
        try:
            data = data.filter_by_conditional_statement(
                conditional_statement)
        except AssertionError:
            return 'No values found for that conditional statement'
        except ValueError:
            return 'Invalid conditional statement'

    if min:
        try:
            min = float(min)
        except ValueError:
            return 'Invalid minimum value'

    if max:
        try:
            max = float(max)
        except ValueError:
            return 'Invalid maximum value'

    lb_lp = LegendParameters(colors=colorsets[global_colorset])

    if min:
        lb_lp.min = min
    if max:
        lb_lp.max = max

    hourly_plot = HourlyPlot(data, legend_parameters=lb_lp)

    return hourly_plot.plot(title=str(data.header.data_type), show_title=True)


@st.cache(hash_funcs={EPW: epw_hash_func, Color: color_hash_func})
def get_bar_chart_figure(fields: dict, epw: EPW, selection: List[str], data_type: str,
                         switch: bool, stack: bool, global_colorset: str) -> Figure:
    """Create bar chart figure.

    Args:
        fields: A dictionary of EPW variable name to its corresponding field number.
        epw: An EPW object.
        selection: A list of strings representing the names of the fields to be plotted.
        data_type: A string representing the data type of the data to be plotted.
        switch: A boolean to indicate whether to reverse the colorset.
        stack: A boolean to indicate whether to stack the bars.
        global_colorset: A string representing the name of a Colorset.

    Returns:
        A plotly figure.
    """
    colors = get_colors(switch, global_colorset)

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
    return monthly_chart.plot(stack=stack, title=data_type, show_title=True)


@st.cache(hash_funcs={HourlyContinuousCollection: hourly_data_hash_func,
                      Color: color_hash_func}, allow_output_mutation=True)
def get_hourly_line_chart_figure(data: HourlyContinuousCollection,
                                 switch: bool, global_colorset: str) -> Figure:
    """Create hourly line chart figure.

    Args:
        data: An HourlyContinuousCollection object.
        switch: A boolean to indicate whether to reverse the colorset.
        global_colorset: A string representing the name of a Colorset.

    Returns:
        A plotly figure.
    """
    colors = get_colors(switch, global_colorset)
    return data.line_chart(color=colors[-1])


@st.cache(hash_funcs={HourlyContinuousCollection: hourly_data_hash_func,
                      Color: color_hash_func}, allow_output_mutation=True)
def get_per_hour_line_chart_figure(data: HourlyContinuousCollection,
                                   switch: bool, global_colorset: str) -> Figure:
    """Create per hour line chart figure.

    Args:
        data: An HourlyContinuousCollection object.
        switch: A boolean to indicate whether to reverse the colorset.
        global_colorset: A string representing the name of a Colorset.

    Returns:
        A plotly figure.
    """
    colors = get_colors(switch, global_colorset)
    return data.per_hour_line_chart(title=data.header.unit, show_title=True,
                                    color=colors[-1])


@st.cache(hash_funcs={HourlyContinuousCollection: hourly_data_hash_func,
                      Color: color_hash_func}, allow_output_mutation=True)
def get_daily_chart_figure(data: HourlyContinuousCollection, switch: bool,
                           global_colorset: str) -> Figure:
    """Create daily chart figure.

    Args:
        data: An HourlyContinuousCollection object.
        switch: A boolean to indicate whether to reverse the colorset.
        global_colorset: A string representing the name of a Colorset.

    Returns:
        A plotly figure.
    """
    colors = get_colors(switch, global_colorset)
    data = data.average_daily()

    return data.bar_chart(color=colors[-1], title=data.header.data_type.name,
                          show_title=True)


@st.cache(hash_funcs={HourlyContinuousCollection: hourly_data_hash_func,
                      Color: color_hash_func, EPW: epw_hash_func}, allow_output_mutation=True)
def get_sunpath_figure(sunpath_type: str, global_colorset: str, epw: EPW = None,
                       switch: bool = False, lat_lon: str = '0.0,0.0',
                       data: HourlyContinuousCollection = None, ) -> Figure:
    """Create sunpath figure.

    Args:
        sunpath_type: A string representing the type of sunpath to be plotted.
        lat_lon: A string representing the latitude and longitude of the location.
        switch: A boolean to indicate whether to reverse the colorset.
        epw: An EPW object.
        load_data: A boolean to indicate whether to load the data.
        data: Hourly data to load on sunpath.
        global_colorset: A string representing the name of a Colorset.

    Returns:
        A plotly figure.
    """
    if sunpath_type == 'using lat-lon':
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

        lb_sunpath = Sunpath(lat, lon)
        colors = get_colors(switch, global_colorset)
        return lb_sunpath.plot(colorset=colors)

    elif sunpath_type == 'from epw location':
        lb_sunpath = Sunpath.from_location(epw.location)
        colors = get_colors(switch, global_colorset)
        return lb_sunpath.plot(colorset=colors)
    else:
        lb_sunpath = Sunpath.from_location(epw.location)
        colors = colorsets[global_colorset]
        return lb_sunpath.plot(colorset=colors, data=data)


@st.cache(hash_funcs={HourlyContinuousCollection: hourly_data_hash_func,
                      Color: color_hash_func}, allow_output_mutation=True)
def get_degree_days_figure(
    dbt: HourlyContinuousCollection, _heat_base_: int, _cool_base_: int,
    stack: bool, switch: bool, global_colorset: str) -> Tuple[Figure,
                                                              HourlyContinuousCollection,
                                                              HourlyContinuousCollection]:
    """Create HDD and CDD figure.

    Args:
        dbt: A HourlyContinuousCollection object.
        _heat_base_: A number representing the heat base temperature.
        _cool_base_: A number representing the cool base temperature.
        stack: A boolean to indicate whether to stack the data.
        switch: A boolean to indicate whether to reverse the colorset.
        global_colorset: A string representing the name of a Colorset.

    Returns:
        A tuple of three items:

        -   A plotly figure.

        -   Heating degree days as a HourlyContinuousCollection.

        -   Cooling degree days as a HourlyContinuousCollection.
    """

    hourly_heat = HourlyContinuousCollection.compute_function_aligned(
        heating_degree_time, [dbt, _heat_base_],
        HeatingDegreeTime(), 'degC-hours')
    hourly_heat.convert_to_unit('degC-days')

    hourly_cool = HourlyContinuousCollection.compute_function_aligned(
        cooling_degree_time, [dbt, _cool_base_],
        CoolingDegreeTime(), 'degC-hours')
    hourly_cool.convert_to_unit('degC-days')

    colors = get_colors(switch, global_colorset)

    lb_lp = LegendParameters(colors=colors)
    monthly_chart = MonthlyChart([hourly_cool.total_monthly(),
                                  hourly_heat.total_monthly()], legend_parameters=lb_lp)

    return monthly_chart.plot(stack=stack), hourly_heat, hourly_cool
