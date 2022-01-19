"""Pollination outdoor comfort app."""

import pathlib

import streamlit as st

from plotly.graph_objects import Figure
from typing import List

from ladybug.epw import EPW
from ladybug.color import Colorset
from ladybug.datacollection import HourlyContinuousCollection
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

        # page header
        st.header('Outdoor Comfort')

        # selecting scnearios to plot
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

        def plot_figure(hourly_data: HourlyContinuousCollection,
                        analysis_period: AnalysisPeriod = None,
                        conditional_statement: str = None,
                        min_range: float = None,
                        max_range: float = None,
                        num_labels: int = None,
                        labels: List[float] = None,
                        colors=colorset) -> None:
            """Plot figure."""

            # apply analysis period
            if analysis_period:
                hourly_data = hourly_data.filter_by_analysis_period(analysis_period)

            # apply conditional statement
            if conditional_statement:
                try:
                    hourly_data = hourly_data.filter_by_conditional_statement(
                        conditional_statement)
                except AssertionError:
                    st.error('No values found for that conditional statement.')
                    return

            # apply legend info
            figure = hourly_data.heat_map(colors=colors, min_range=min_range,
                                          max_range=max_range, num_labels=num_labels,
                                          labels=labels)

            # plot figure
            st.plotly_chart(figure, use_container_width=True)

        if anlysis_type == 'utci':
            # get min and max of first hourly data and apply it to all to keep
            # consistent legend for comparison
            min = comf_objs[0].universal_thermal_climate_index.min
            max = comf_objs[0].universal_thermal_climate_index.max
            # TODO add legend labels as per number of labels
            for obj in comf_objs:
                plot_figure(obj.universal_thermal_climate_index, analysis_period=lb_ap,
                            conditional_statement=conditional_statement,
                            min_range=min, max_range=max)

        elif anlysis_type == 'comfort':
            for obj in comf_objs:
                plot_figure(obj.is_comfortable, analysis_period=lb_ap,
                            conditional_statement=conditional_statement,
                            min_range=0, max_range=1,
                            num_labels=2, labels=[0, 1])

        elif anlysis_type == 'condition':
            for obj in comf_objs:
                plot_figure(obj.thermal_condition, analysis_period=lb_ap,
                            conditional_statement=conditional_statement,
                            min_range=-1, max_range=1,
                            num_labels=3, labels=[-1, 0, 1])

        elif anlysis_type == 'category':
            for obj in comf_objs:
                plot_figure(obj.thermal_condition_eleven_point, analysis_period=lb_ap,
                            conditional_statement=conditional_statement,
                            min_range=-5, max_range=5,
                            num_labels=11, labels=[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5])


if __name__ == '__main__':
    main()
