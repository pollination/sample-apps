"""Pollination outdoor comfort app."""
import pathlib

import streamlit as st

from ladybug.epw import EPW
from ladybug.analysisperiod import AnalysisPeriod
from ladybug_comfort.collection.utci import UTCI
from ladybug_comfort.parameter.utci import UTCIParameter


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
    with st.sidebar:
        # epw file
        epw_source = st.selectbox(
            'Select EPW data',
            ['Sample EPW data', 'Upload an EPW file']
        )

        if epw_source == 'Upload an EPW file':
            epw_data = st.file_uploader('Select an EPW file', type='epw')
            if not epw_data:
                return
            epw_file = pathlib.Path('./data/sample.epw')
            epw_file.parent.mkdir(parents=True, exist_ok=True)
            epw_file.write_bytes(epw_data.read())
        else:
            epw_file = './assets/sample.epw'

        epw = EPW(epw_file)

        # analysis period
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

        # conditional statement
        with st.expander('Apply conditional statement'):
            conditional_statement = st.text_input('')

        # analysis type
        anlysis_type = st.radio('Analysis type', options=[
            'utci', 'comfort', 'condition', 'category'])

        # scenarios
        wind_help = 'Select "Add wind" include the EPW wind speed in the calculation.'\
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

        scenario = st.radio('Scenarios', options=[
            'No wind & sun', 'Add wind', 'Add sun', 'Add wind & sun'],
            help=wind_help + '\n' + sun_help + '\n' + win_sun_help)

    with st.container():
        st.header('Outdoor Comfort')
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

        if anlysis_type == 'utci':
            for obj in comf_objs:
                utci = obj.universal_thermal_climate_index
                if analysis_period == 'Custom':
                    utci = utci.filter_by_analysis_period(lb_ap)
                if conditional_statement:
                    utci = utci.filter_by_conditional_statement(conditional_statement)
                figure = utci.heat_map(num_labels=10)
                st.plotly_chart(figure, use_container_width=True)

        elif anlysis_type == 'comfort':
            for obj in comf_objs:
                comfort = obj.is_comfortable
                if analysis_period == 'Custom':
                    comfort = comfort.filter_by_analysis_period(lb_ap)
                if conditional_statement:
                    comfort = comfort.filter_by_conditional_statement(
                        conditional_statement)
                figure = comfort.heat_map(num_labels=2, labels=[0, 1])
                st.plotly_chart(figure, use_container_width=True)

        elif anlysis_type == 'condition':
            for obj in comf_objs:
                condition = obj.thermal_condition
                if analysis_period == 'Custom':
                    condition = condition.filter_by_analysis_period(lb_ap)
                if conditional_statement:
                    condition = condition.filter_by_conditional_statement(
                        conditional_statement)
                figure = condition.heat_map(num_labels=3, labels=[-1, 0, 1])
                st.plotly_chart(figure, use_container_width=True)

        elif anlysis_type == 'category':
            for obj in comf_objs:
                category = obj.thermal_condition_eleven_point
                if analysis_period == 'Custom':
                    category = category.filter_by_analysis_period(lb_ap)
                if conditional_statement:
                    category = category.filter_by_conditional_statement(
                        conditional_statement)
                figure = category.heat_map(
                    min_range=-5, max_range=5, num_labels=11, labels=[-5, -4, -3, -2, -1,
                                                                      0, 1, 2, 3, 4, 5])
                st.plotly_chart(figure, use_container_width=True)


if __name__ == '__main__':
    main()
