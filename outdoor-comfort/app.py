"""Pollination outdoor comfort app."""

import pathlib
import streamlit as st
import shutil
import base64

from fpdf import FPDF
from plotly.graph_objects import Figure
from typing import List

from ladybug.epw import EPW
from ladybug.color import Colorset
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.analysisperiod import AnalysisPeriod
from ladybug_comfort.collection.utci import UTCI


# make it look good by setting up the title, icon, etc.
st.set_page_config(
    page_title='Outdoor Comfort',
    page_icon='https://app.pollination.cloud/favicon.ico',
    layout='wide'
)
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba_pollination_brandmark-p-500.png',
    use_column_width=True
)


def main():

    ####################################################################################
    # sidebar
    ####################################################################################
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

        # conditional statement
        with st.expander('Apply conditional statement'):
            conditional_statement = st.text_input('')

        # choose colorset
        with st.expander('Apply colorset'):
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

            selected_colorset = st.selectbox('', list(colorsets.keys()))
            colorset = colorsets[selected_colorset]

        # analysis type
        anlysis_type = st.radio('Analysis type', options=[
            'UTCI', 'Comfortable or not', 'Comfort conditions', 'Comfort categories'])

        # scenarios
        wind_help = 'Select "Add wind" to include the EPW wind speed in the calculation.'\
            ' Not selecting this will assume a condition that is shielded from wind'\
            ' where the human subject experiences a low wind speed of 0.5 m/s, which'\
            ' is the lowest input speed that is recommended for the UTCI model. \n'\


        sun_help = 'Select "Add sun" to include the mean radiant temperature (MRT)'\
            ' delta from both shortwave solar falling directly on people and long wave'\
            ' radiant exchange with the sky. Not checking this will assume a shaded'\
            ' condition with MRT being equal to the EPW dry bulb temperature.'\
            ' When checked, this calculation will assume no surrounding shade context,'\
            ' standing human geometry, and a solar horizontal angle relative to front'\
            ' of person (SHARP) of 135 degrees. A SHARP of 135 essentially assumes that'\
            ' a person typically faces their side or back to the sun to avoid glare. \n'

        win_sun_help = 'Select "Add wind & sun" to include both.'

        scenario = st.radio('Scenarios', options=['No wind & sun', 'Add wind', 'Add sun',
                                                  'Add wind & sun'],
                            help=wind_help + '\n' + sun_help + '\n' + win_sun_help)

    ####################################################################################
    # helper functions and info
    ####################################################################################
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

    # plotting figures with titles
    def plot_figure_with_title(hourly_data: HourlyContinuousCollection,
                               scenario: str,
                               percent_comfortable: float,
                               analysis_period: AnalysisPeriod = None,
                               conditional_statement: str = None,
                               min_range: float = None,
                               max_range: float = None,
                               num_labels: int = None,
                               labels: List[float] = None,
                               colors=colorset) -> Figure:
        """Plot figure."""
        col1, col2 = st.columns([5, 1])

        with col1:
            # figure title
            title = f'{scenario}'
            if analysis_period:
                hourly_data = hourly_data.filter_by_analysis_period(analysis_period)

            if conditional_statement:
                try:
                    hourly_data = hourly_data.filter_by_conditional_statement(
                        conditional_statement)
                except AssertionError:
                    st.error('No values found for that conditional statement.')
                    return

            figure = hourly_data.heat_map(title=title, show_title=True,
                                          colors=colors, min_range=min_range,
                                          max_range=max_range, num_labels=num_labels,
                                          labels=labels)

            config = {
                'toImageButtonOptions': {
                    'format': 'svg',  # one of png, svg, jpeg, webp
                    'filename': title,
                    'height': 350,
                    'width': 700,
                    'scale': 1  # Multiply title/legend/axis/canvas sizes by this factor
                }
            }

            st.plotly_chart(figure, use_container_width=True, config=config)
            figures.append(figure)

        with col2:
            num_hours = len(hourly_data.values)
            percent_comfortable = round(percent_comfortable, 2)

            title = ("<div><br>" +
                     "<br>" +
                     "<br>" +
                     "<br>" +
                     "<br>" +
                     "<br>" +
                     " <h3 style ='text-align: center; padding-bottom:0px;" +
                     f" color: gray;'>{percent_comfortable} %</h3>" +
                     "<p style ='text-align: center;" +
                     f" color: gray;'>comfortable in {num_hours} hours</div>")

            st.markdown(title, unsafe_allow_html=True)

            percentages.append(
                f'{percent_comfortable}% comfortable in {num_hours} hours')

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

    figures, percentages = [], []

    ####################################################################################
    # Main page
    ####################################################################################
    with st.container():

        # Creating face columns to display button at the center
        col1 = st.columns(3)[1]
        with col1:
            st.subheader(epw.location.city)

        intro_1 = 'Calculate the Universal Thermal Climate Index (UTCI)'\
            ' for a set of input climate conditions. Perhaps the most familiar'\
            ' application of Universal Thermal Climate Index(UTCI) is the'\
            ' temperature given by TV weathermen and women when they say that,'\
            ' "even though the dry bulb temperature outside is a certain value,'\
            ' the temperature actually "feels like" something higher or lower. \n'

        intro_2 = 'UTCI is this temperature of what the weather "feels like" and it'\
            ' takes into account the radiant temperature(sometimes including'\
            ' solar radiation) , relative humidity, and wind speed.'\
            ' UTCI uses these variables in a human energy balance model to'\
            ' give a temperature value that is indicative of the heat stress'\
            ' or cold stress felt by a human body outdoors.'

        # page header
        st.markdown(intro_1)
        st.markdown(intro_2)

        if anlysis_type == 'UTCI':
            st.markdown('UTCI in Celsius')
            # get min and max of first hourly data and apply it to all to keep
            # consistent legend for comparison
            min = comf_objs[0].universal_thermal_climate_index.min
            max = comf_objs[0].universal_thermal_climate_index.max
            # TODO add legend labels as per number of labels
            for count, obj in enumerate(comf_objs):
                plot_figure_with_title(obj.universal_thermal_climate_index,
                                       'UTCI ' + title_scenario[count],
                                       obj.percent_comfortable,
                                       analysis_period=lb_ap,
                                       conditional_statement=conditional_statement,
                                       min_range=min, max_range=max, colors=colorset)

        elif anlysis_type == 'Comfortable or not':
            st.markdown(
                """
                Comfortable or not

                -   0 = Uncomfortable (thermal stress)
                -   1 = Comfortable (no thermal stress)
                """)
            for count, obj in enumerate(comf_objs):
                plot_figure_with_title(obj.is_comfortable,
                                       'Comfortable or not ' + title_scenario[count],
                                       obj.percent_comfortable,
                                       analysis_period=lb_ap,
                                       conditional_statement=conditional_statement,
                                       min_range=0, max_range=1,
                                       num_labels=2, labels=[0, 1], colors=colorset)

        elif anlysis_type == 'Comfort conditions':
            st.markdown(
                """
                Comfort conditions

                -   -1 = Cold
                -    0 = Neutral
                -   +1 = Hot
                """)
            for count, obj in enumerate(comf_objs):
                plot_figure_with_title(obj.thermal_condition,
                                       'Comfort conditions' + title_scenario[count],
                                       obj.percent_comfortable,
                                       analysis_period=lb_ap,
                                       conditional_statement=conditional_statement,
                                       min_range=-1, max_range=1,
                                       num_labels=3, labels=[-1, 0, 1], colors=colorset)

        elif anlysis_type == 'Comfort categories':
            st.markdown(
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
                """)
            for count, obj in enumerate(comf_objs):
                plot_figure_with_title(obj.thermal_condition_eleven_point,
                                       'Comfort categories ' + title_scenario[count],
                                       obj.percent_comfortable,
                                       analysis_period=lb_ap,
                                       conditional_statement=conditional_statement,
                                       min_range=-5, max_range=5,
                                       num_labels=11,
                                       labels=[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5],
                                       colors=colorset)

    ####################################################################################
    # PDF export
    ####################################################################################

    def create_download_link(val, filename):
        """Create download link for the pdf.

        Args:
            val: Bytes
            filename: String

        Returns
            A download link
        """

        b64 = base64.b64encode(val)  # val looks like b'...'
        return '<a style="display:block; text-align: left" '\
            f' href="data:application/octet-stream;base64,{b64.decode()}" '\
            f' download="{filename}.pdf">Download PDF</a>'

    def write_pdf(col: st.columns):
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
        analysis_type_par = f'Analysis type: {anlysis_type} \n'
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
                     txt=percentages[count], align='C')

        html = create_download_link(pdf.output(), f'Outdoor comfort_{epw.location.city}')
        with col:
            st.markdown(html, unsafe_allow_html=True)

    col2 = st.columns(3)[1]
    with col2:
        export_as_pdf = st.button("Export Report")
    if export_as_pdf:
        write_pdf(col2)


if __name__ == '__main__':
    main()
