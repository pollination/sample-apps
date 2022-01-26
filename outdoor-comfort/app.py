"""Pollination outdoor comfort app."""

import pathlib
import streamlit as st

from ladybug.epw import EPW
from ladybug.color import Colorset
from ladybug.analysisperiod import AnalysisPeriod

from helper import get_comfort_objs_and_title, get_legend_info, get_data, \
    get_figure_config, write_pdf

# make it look good by setting up the title, icon, etc.
st.set_page_config(
    page_title='Outdoor Comfort',
    page_icon='https://app.pollination.cloud/favicon.ico',
    layout='wide'
)
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba'
    '_pollination_brandmark-p-500.png',
    use_column_width=True
)


def main():

    with st.sidebar:

        with st.form('Parameters'):
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
                # analysis_period = st.radio('Select default analysis period',
                #                            options=['Default', 'Custom'])
                # if analysis_period == 'Custom':
                st_month = st.number_input(
                    'Start month', min_value=1, max_value=12, value=1)
                end_month = st.number_input(
                    'End month', min_value=1, max_value=12, value=12)

                st_day = st.number_input(
                    'Start day', min_value=1, max_value=31, value=1)
                end_day = st.number_input(
                    'End day', min_value=1, max_value=31, value=31)

                st_hour = st.number_input(
                    'Start hour', min_value=0, max_value=23, value=0)
                end_hour = st.number_input(
                    'End hour', min_value=0, max_value=23, value=23)

                lb_ap = AnalysisPeriod(st_month, st_day, st_hour,
                                       end_month, end_day, end_hour)
                # else:
                #     lb_ap = None

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
            analysis_type = st.radio('Analysis type', options=[
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

            st.markdown('---')
            st.form_submit_button('Run')

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

        # add legend info
        st.markdown(get_legend_info(analysis_type))

        # get comfort objects and title to create the figures
        comf_objs, title_scenario = get_comfort_objs_and_title(scenario, epw)

        # generate figures, text to show on the side and the result texts to go into report
        figures, percentage_html_objs, result_txts = get_data(
            analysis_type, comf_objs, title_scenario, lb_ap, conditional_statement,
            colorset)

        # add figures and text on the side
        for count, figure in enumerate(figures):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.plotly_chart(figure, use_container_width=True,
                                config=get_figure_config(f'{scenario}'))
            with col2:
                st.markdown(percentage_html_objs[count], unsafe_allow_html=True)

        # export PDF
        col2 = st.columns(3)[1]
        with col2:
            export_as_pdf = st.button("Export Report")
            if export_as_pdf:
                html = write_pdf(epw, intro_1, intro_2, lb_ap, conditional_statement,
                                 analysis_type, scenario, figures, result_txts)
                st.markdown(html, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
