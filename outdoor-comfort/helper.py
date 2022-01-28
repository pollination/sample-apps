"""Helper functions for the outdoor-comfort package."""

import base64
import pathlib
import shutil
import streamlit as st

from fpdf import FPDF
from plotly.graph_objects import Figure

from typing import List, Tuple, Dict
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.color import Colorset, Color
from ladybug.epw import EPW
from ladybug_comfort.collection.utci import UTCI


def epw_hash_func(epw: EPW) -> str:
    """Function to help streamlit hash an EPW object."""
    return epw.location.city


def utci_hash_func(utci: UTCI) -> float:
    """Function to help streamlit hash a UTCI object."""
    return utci.percent_comfortable


def color_hash_func(color: Color) -> Tuple[float, float, float]:
    """Function to help streamlit hash a Color object."""
    return color.r, color.g, color.b


def analysis_period_hash_func(ap: AnalysisPeriod) -> Tuple[int, int, int, int, int, int]:
    """Function to help streamlit hash an AnalysisPeriod object."""
    return ap.st_month, ap.st_day, ap.st_hour, ap.end_month, ap.end_day, ap.end_hour


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


@st.cache(allow_output_mutation=True, hash_funcs={EPW: epw_hash_func})
def get_comfort_objs_and_title(scenario: str, epw: EPW) -> Tuple[List[UTCI], Dict[int, str]]:
    """Get Comfort objects and figure title for a given scenario.

    Args:
        scenario: Name of the scenario as a text.
        epw: Ladybug EPW object.

    Returns:
        A tuple of two elements

        -   A list of Ladybug UTCI objects.

        -   A dictionary with the figure texts.
    """

    if scenario == 'Add wind & sun':
        comf_objs = [
            UTCI.from_epw(epw, include_wind=False, include_sun=False),
            UTCI.from_epw(epw, include_wind=True, include_sun=False),
            UTCI.from_epw(epw, include_sun=True, include_wind=False),
            UTCI.from_epw(epw, include_wind=True, include_sun=True)
        ]
    elif scenario == 'Add wind':
        comf_objs = [
            UTCI.from_epw(epw, include_wind=False, include_sun=False),
            UTCI.from_epw(epw, include_wind=True, include_sun=False),
        ]
    elif scenario == 'Add sun':
        comf_objs = [
            UTCI.from_epw(epw, include_wind=False, include_sun=False),
            UTCI.from_epw(epw, include_sun=True, include_wind=False),
        ]
    else:
        comf_objs = [UTCI.from_epw(epw, include_wind=False, include_sun=False)]

    if scenario == 'Add sun':
        title_scenario = {
            0: ' without the effect of sun and wind',
            1: ' with the effect of sun ☀️'
        }
    else:
        title_scenario = {
            0: ' without the effect of sun and wind',
            1: ' with the effect of wind 💨',
            2: ' with the effect of sun ☀️',
            3: ' with the effect of sun ☀️ and wind 💨'
        }

    return comf_objs, title_scenario


def get_figure_and_percentage(
        hourly_data: HourlyContinuousCollection, scenario: str,
        percent_comfortable: float, analysis_period: AnalysisPeriod = None,
        conditional_statement: str = None, min_range: float = None,
        max_range: float = None, num_labels: int = None, labels: List[float] = None,
        colors: Colorset = None) -> Tuple[Figure, str]:
    """Plot figure and percentage of hours that are comfortable.

    Args:
        hourly_data: HourlyContinuousCollection to be plotted.
        scenario: Name of the scenario.
        percent_comfortable: Percentage of hours that are comfortable.
        analysis_period: Ladybug analysis period object. Default is None.
        conditional_statement: Conditional statement to filter data. Default is None.
        min_range: Minimum value of data range. Default is None.
        max_range: Maximum value of data range. Default is None.
        num_labels: Number of labels to be used on the legend bar. Default is None.
        labels: Labels to be used on the legend bar. Default is None.
        colors: Ladybug Colorset to be used to color the figure. Default is None.

    Returns:
        A tuple of two elements

        -   A plotly figure object.

        -   A text string with the percentage of hours that are comfortable.

    """
    # prepare figure
    title = f'{scenario}'

    if analysis_period:
        hourly_data = hourly_data.filter_by_analysis_period(analysis_period)

    if conditional_statement:
        try:
            hourly_data = hourly_data.filter_by_conditional_statement(
                conditional_statement)
        except AssertionError:
            return 'No values found for that conditional statement.'

    figure = hourly_data.heat_map(title=title, show_title=True,
                                  colors=colors, min_range=min_range,
                                  max_range=max_range, num_labels=num_labels,
                                  labels=labels)

    # prepare result to show on the side
    num_hours = len(hourly_data.values)
    percent_comfortable = round(percent_comfortable, 2)

    percentage_html = ("<div><br>" +
                       "<br>" +
                       "<br>" +
                       "<br>" +
                       "<br>" +
                       "<br>" +
                       " <h3 style ='text-align: center; padding-bottom:0px;" +
                       f" color: gray;'>{percent_comfortable} %</h3>" +
                       "<p style ='text-align: center;" +
                       f" color: gray;'>comfortable in {num_hours} hours</div>")

    result_txt = f'{percent_comfortable}% comfortable in {num_hours} hours'

    return figure, percentage_html, result_txt


@st.cache(allow_output_mutation=True)
def get_legend_info(analysis_type: str) -> str:
    """Get legend info for a given analysis type.

    Args:
        analysis_type: Analysis type as a text.

    Returns:
        A text string with the legend info.
    """

    if analysis_type == 'UTCI':
        legend_info = 'UTCI in Celsius'

    elif analysis_type == 'Comfortable or not':
        legend_info = (
            """
            Comfortable or not

            -   0 = Uncomfortable (thermal stress)
            -   1 = Comfortable (no thermal stress)
            """
        )

    elif analysis_type == 'Comfort conditions':
        legend_info = (
            """
            Comfort conditions

            -   -1 = Cold
            -    0 = Neutral
            -   +1 = Hot
            """
        )

    elif analysis_type == 'Comfort categories':
        legend_info = (
            """
            Comfort categories

            -   -5 = Extreme Cold Stress       (UTCI < -40)
            -   -4 = Very Strong Cold Stress   (-40 <= UTCI < -27)
            -   -3 = Strong Cold Stress        (-27 <= UTCI < -13)
            -   -2 = Moderate Cold Stress      (-12 <= UTCI < 0)
            -   -1 = Slight Cold Stress        (0 <= UTCI < 9)
            -    0 = No Thermal Stress         (9 <= UTCI < 26)
            -   +1 = Slight Heat Stress        (26 <= UTCI < 28)
            -   +2 = Moderate Heat Stress      (28 <= UTCI < 32)
            -   +3 = Strong Heat Stress        (32 <= UTCI < 38)
            -   +4 = Very Strong Heat Stress   (38 <= UTCI < 46)
            -   +5 = Extreme Heat Stress       (46 < UTCI)
            """
        )

    return legend_info


@ st.cache(
    allow_output_mutation=True, hash_funcs={UTCI: utci_hash_func, Color: color_hash_func,
                                            AnalysisPeriod: analysis_period_hash_func})
def get_data(analysis_type: str, comf_objs: List[UTCI],
             title_scenario: Dict[int, str], lb_ap,
             conditional_statement: str,
             colorset: Colorset) -> Tuple[List[Figure], List[str], List[str]]:
    """Generate figures and result info for the app and the PDF.

    Args:
        analysis_type: Analysis type as a text.
        comf_objs: List of comfort objects.
        title_scenario: Dictionary with the title of each scenario.
        lb_ap: Ladybug analysis period object.
        conditional_statement: Conditional statement to filter data. Default is None.
        colorset: Ladybug Colorset to be used to color the figure.

    Returns:
        A tuple of three elements

        -   A list of Plotly figures.

        -   A list of HTML objects to be used to show results on the side.

        -   A list of text strings to be used in PDF.
    """

    figures, percentage_html_objs, result_txts = [], [], []

    if analysis_type == 'UTCI':
        # get min and max of first hourly data and apply it to all to keep
        # consistent legend for comparison
        min = comf_objs[0].universal_thermal_climate_index.min
        max = comf_objs[0].universal_thermal_climate_index.max
        # TODO add legend labels as per number of labels
        for count, obj in enumerate(comf_objs):
            output = get_figure_and_percentage(
                obj.universal_thermal_climate_index, 'UTCI ' + title_scenario[count],
                obj.percent_comfortable, analysis_period=lb_ap,
                conditional_statement=conditional_statement, min_range=min,
                max_range=max, colors=colorset)

            if isinstance(output, str):
                return output
            figure, percentage_html, result_txt = output
            figures.append(figure)
            percentage_html_objs.append(percentage_html)
            result_txts.append(result_txt)

    elif analysis_type == 'Comfortable or not':
        for count, obj in enumerate(comf_objs):
            output = get_figure_and_percentage(
                obj.is_comfortable, 'Comfortable or not ' + title_scenario[count],
                obj.percent_comfortable, analysis_period=lb_ap,
                conditional_statement=conditional_statement, min_range=0, max_range=1,
                num_labels=2, labels=[0, 1], colors=colorset)

            if isinstance(output, str):
                return output
            figure, percentage_html, result_txt = output
            figures.append(figure)
            percentage_html_objs.append(percentage_html)
            result_txts.append(result_txt)

    elif analysis_type == 'Comfort conditions':
        for count, obj in enumerate(comf_objs):
            output = get_figure_and_percentage(
                obj.thermal_condition, 'Comfort conditions' + title_scenario[count],
                obj.percent_comfortable, analysis_period=lb_ap,
                conditional_statement=conditional_statement, min_range=-1, max_range=1,
                num_labels=3, labels=[-1, 0, 1], colors=colorset)

            if isinstance(output, str):
                return output
            figure, percentage_html, result_txt = output
            figures.append(figure)
            percentage_html_objs.append(percentage_html)
            result_txts.append(result_txt)

    elif analysis_type == 'Comfort categories':
        for count, obj in enumerate(comf_objs):
            output = get_figure_and_percentage(
                obj.thermal_condition_eleven_point, 'Comfort categories ' +
                title_scenario[count], obj.percent_comfortable, analysis_period=lb_ap,
                conditional_statement=conditional_statement, min_range=-5, max_range=5,
                num_labels=11, labels=[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5],
                colors=colorset)

            if isinstance(output, str):
                return output
            figure, percentage_html, result_txt = output
            figures.append(figure)
            percentage_html_objs.append(percentage_html)
            result_txts.append(result_txt)

    return figures, percentage_html_objs, result_txts


def create_download_link(val, filename: str) -> str:
    """Create download link for the pdf.

    Args:
        val: Bytearray
        filename: String

    Returns
        A download link
    """

    b64 = base64.b64encode(val)  # val looks like b'...'
    return '<a style="display:block; text-align: left" '\
        f' href="data:application/octet-stream;base64,{b64.decode()}" '\
        f' download="{filename}.pdf">Download PDF</a>'


@st.cache(allow_output_mutation=True, hash_funcs={EPW: epw_hash_func})
def write_pdf(
        epw: EPW, intro_1: str, intro_2: str, lb_ap: AnalysisPeriod,
        conditional_statement: str, analysis_type: str, scenario: str,
        figures: List[Figure], result_txts: List[str]) -> str:
    """Generate a PDF.

    Args:
        epw: EPW object.
        intro_1: String.
        intro_2: String.
        lb_ap: Ladybug analysis period object.
        conditional_statement: Conditional statement to filter data.
        analysis_type: Analysis type as a text.
        scenario: Scenario as a text.
        figures: List of Plotly figures.
        result_txts: List of text strings to be used in PDF.

    Returns:
        A download link
    """
    # Create a folder to write images
    path = pathlib.Path('./assets/images/figures')

    # nuke the images folder if exists
    if path.is_dir():
        shutil.rmtree(path)

    # create a new folder to download the image
    path.mkdir(parents=True, exist_ok=True)

    class PDF(FPDF):
        def header(self):
            # Logo
            self.image('./assets/images/pollination_brandmark.png', 130, 8, 33)

        # Page footer
        def footer(self):
            # Position at 1.5 cm from bottom
            self.set_y(-15)
            # Arial italic 8
            self.set_font('Arial', 'I', 8)
            # Page number
            self.cell(0, 10, 'Page ' + str(self.page_no()), 0, 0, 'C')

        def chater_title(self, label):
            self.set_font('Arial', 'B', 14)
            # Title
            self.cell(0, 6, f'{label}', 0, 1, 'L', 0)
            # Line break
            self.ln(4)

        def chapter_body(self, text):
            self.set_font('Arial', '', 14)
            # Output justified text
            self.multi_cell(0, 5, text)
            # Line break
            self.ln()

    # instantiate the report
    pdf = PDF(orientation='L', unit='mm', format='A4')
    # pdf.set_margins(right=50, top=50, left=50)
    # pdf.set_auto_page_break(True, margin=50)

    # image type
    image_format = 'jpg'

    # container width & height
    # A little less than the width of A4 paper in mm
    container_width = 280
    container_height = container_width / 1.414

    # add front page
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(container_width, 170,
             f'Outdoor Comfort Report | {epw.location.city}', align='C')

    # add summary page
    pdf.add_page()
    pdf.chater_title('Introduction')
    pdf.chapter_body(intro_1 + '\n' + intro_2)

    # add parameters page
    pdf.add_page()
    pdf.chater_title('Parameters')

    # collect all the parameters
    location_par = f'EPW: country: {epw.location.country}, state: {epw.location.state},'\
        f' city: {epw.location.city}, time zone: {epw.location.time_zone} \n'

    ap = lb_ap if lb_ap else AnalysisPeriod()
    analysis_period_par = f'Analysis period: start month{ap.st_month}, start day: {ap.st_day}, '\
        f'start hour: {ap.st_hour}, end month: {ap.end_month}, end day: {ap.end_day},'\
        f' end hour: {ap.end_hour} \n '
    conditional_par = f'Conditional statement: '\
        f' {conditional_statement if conditional_statement else "Not set"} \n'
    analysis_type_par = f'Analysis type: {analysis_type} \n'
    scenario_par = f'Scenario: {scenario} \n'
    # write parameters
    pdf.chapter_body(location_par + '\n' + analysis_period_par + '\n' +
                     conditional_par + '\n' + analysis_type_par + '\n' + scenario_par)

    # add other charts
    for count, figure in enumerate(figures):
        pdf.add_page()
        pdf.set_font('Arial', '', 14)
        image_path = path.joinpath(str(count) + '.' + image_format)
        # set black font color for the text on the image since fpdf does not
        # support setting text color
        figure.update_layout(
            font=dict(color='#000000', size=7),
            title=dict(font=dict(color='#000000', size=7), pad=dict(b=0))
        )

        figure.write_image(image_path, format=image_format,
                           width=500, height=250, scale=3)

        pdf.image(image_path.as_posix(), x=(297/2 - container_width/2),
                  y=60, w=container_width, h=container_width/2)

        pdf.cell(w=container_width, h=50,
                 txt=result_txts[count], align='C')

    download_link = create_download_link(
        pdf.output(), f'Outdoor comfort_{epw.location.city}')

    return download_link
