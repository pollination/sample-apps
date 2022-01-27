"""Functions to support the epw-viz app."""

import pathlib
import shutil
import streamlit as st

from typing import List, Tuple
from icrawler.builtin import GoogleImageCrawler
from geopy.geocoders import Nominatim
from plotly.graph_objects import Figure
from ladybug.datacollection import HourlyContinuousCollection

from ladybug.epw import EPW, EPWFields
from ladybug.color import Colorset, Color
from ladybug.legend import LegendParameters
from ladybug.hourlyplot import HourlyPlot
from ladybug.monthlychart import MonthlyChart

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
def get_hourly_data_figure(data: HourlyContinuousCollection, global_colorset: str,
                           conditional_statement: str, min: float, max: float) -> Figure:
    """Create heatmap from hourly data.

    Args:
        data: HourlyContinuousCollection object.
        global_colorset: A string representing the name of a Colorset.
        conditional_statement: A string representing a conditional statement.
        min: A string representing the lower bound of the data range.
        max: A string representing the upper bound of the data range.

    Returns:
        A plotly figure.
    """

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
    if switch:
        colors = list(colorsets[global_colorset])
        colors.reverse()
    else:
        colors = colorsets[global_colorset]

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
    if switch:
        colors = list(colorsets[global_colorset])
        colors.reverse()
    else:
        colors = colorsets[global_colorset]

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
    if switch:
        colors = list(colorsets[global_colorset])
        colors.reverse()
    else:
        colors = colorsets[global_colorset]

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
    if switch:
        colors = list(colorsets[global_colorset])
        colors.reverse()
    else:
        colors = colorsets[global_colorset]

    data = data.average_daily()

    return data.bar_chart(color=colors[-1], title=data.header.data_type.name,
                          show_title=True)
