import pathlib
from typing import Dict
import json
import plotly.graph_objects as go

import pandas as pd
import streamlit as st

from economics import calculate_economics
from par import calc_ppfd_clf


def get_input_values(folder) -> Dict:
    """Get input values based on the folder name.

    e.g. parametric_data\0\Fixed_South_Facing_1.5_2_15\0
    """
    data, transparency = pathlib.Path(folder).parts[-2:]
    transparency = int(transparency) * 25

    if data.startswith('Fixed_South_Facing'):
        configuration = 'Fixed South Facing Table'
        height, panel_count, angle = data.split('_')[-3:]
    elif data.startswith('Peak'):
        configuration = 'Fixed East-West Peak Canopy'
        height, panel_count, angle = data.split('_')[-3:]
    else:
        # vertical
        configuration = 'Bifacial Solar Fence'
        panel_count = data.split('_')[-1]
        height = 1
        angle = 90

    input_data = {
        'Configuration': configuration,
        'Transparency': transparency,
        'Height from Ground': height,
        'Panel Count': 10 * int(panel_count),
        'Angle': angle
    }

    return input_data


def _calculate_economic_outputs(folder: pathlib.Path):
    here = pathlib.Path(__file__).parent
    results_folder = folder
    weather_folder = here.joinpath('weather_data')
    location = pathlib.Path(folder).parts[-3]
    data = pathlib.Path(folder).parts[-2]
    if data.startswith('Fixed_South_Facing'):
        design_config = 0
    elif data.startswith('Peak'):
        design_config = 4
    else:
        design_config = 3

    # calculate economics for this location and configuration
    # Read the SAM module from the JSON file
    CECMod = pd.DataFrame.from_dict(json.loads(
        here.joinpath('cec_mod.json').read_text()))
    # Solution - parse the csv file and create the item from the csv file directly.
    irr_file = results_folder.joinpath(f'Agrivoltaic_Panel.ill')
    irradiance = pd.read_csv(irr_file.as_posix(), header=None)
    temperature = pd.read_csv(
        weather_folder.joinpath(f'{location}_temperature.txt').as_posix(),
        header=None
    )
    wind_speed = pd.read_csv(
        weather_folder.joinpath(f'{location}_wind_speed.txt').as_posix(),
        header=None
    )

    total_electricity, monthly_electricity, adjusted_installed_cost, payback_cash_flow = \
        calculate_economics(irradiance, temperature,
                            wind_speed, CECMod, design_config)
    return total_electricity, adjusted_installed_cost


def _calculate_ppdf_values(results_folder):
    par_df = pd.read_csv(results_folder.joinpath('Crops_Surface.ill'))
    # Note: the results of the new method are about 1.5 times more than the original
    # hourly runs. I'm diving the values by 1.5 to adjust for that until I get a chance
    # to review the workflow. It is most likely an adjustment in the sky that I hacked
    # together from several skies.
    average_values = par_df.mean(axis=1) / 1.2
    _, ppfd_classification = calc_ppfd_clf(average_values)
    return ppfd_classification


def get_output_values(folder: pathlib.Path) -> Dict:
    """Return output values for an iteration.

    The values are:
        * initial cost  - should be normalized based on the number of panels
        * annual electricity
        * % low, medium and high PPFD
    """

    total_electricity, adjusted_installed_cost = _calculate_economic_outputs(
        folder)

    classification = _calculate_ppdf_values(folder)

    outputs = {
        'Initial cost': adjusted_installed_cost,
        'Low light area (%)': classification['low'],
        'Medium light area (%)': classification['medium'],
        'High light area (%)': classification['high'],
        'Net AC electricity': total_electricity
    }

    return outputs


def calculate_values(fp: pathlib.Path):
    """Calculate both input and output values."""
    inputs = get_input_values(fp)
    outputs = get_output_values(fp)
    # adjust cost based on panel count
    ratio = inputs['Panel Count'] / 20
    values = {
        'Configuration': inputs['Configuration'],
        'Transparency': inputs['Transparency'],
        'Height from Ground': inputs['Height from Ground'],
        'Panel Count': inputs['Panel Count'],
        'Angle (Degrees)': inputs['Angle'],
        'Initial cost ($)': int(outputs['Initial cost'] * ratio),
        'Low light area (%)': outputs['Low light area (%)'],
        'Medium light area (%)': outputs['Medium light area (%)'],
        'High light area (%)': outputs['High light area (%)'],
        'Net AC electricity': int(outputs['Net AC electricity'] * ratio / 30)
    }

    return values


def collect_data(folder):
    """Collect data for a folder for a specific location."""
    folder = pathlib.Path(folder)
    cases = []
    for case_folder in folder.iterdir():
        print(f'start collecting data for location {case_folder.name}')
        for tr_folder in case_folder.iterdir():
            case = calculate_values(tr_folder)
            cases.append(case)
    
    df = pd.DataFrame(cases)
    print(folder.parent.joinpath(f'{folder.stem}.csv'))
    df.to_csv(folder.parent.joinpath(f'{folder.stem}.csv'), index=False)


@st.cache(suppress_st_warning=True)
def add_parallel_coordinates(location_index):
    here = pathlib.Path(__file__).parent
    data = here.joinpath('parametric_data', f'{location_index}.csv')
    df = pd.read_csv(data)

    df['Configuration'] = df['Configuration'].str.replace('Fixed South Facing Table', '-1').replace('Fixed East-West Peak Canopy', '0').replace('Bifacial Solar Fence', '1')

    fig = go.Figure(
        data= go.Parcoords(
            line = dict(
                color = df['Net AC electricity'],
                colorscale = 'viridis',
                # showscale = True,
                cmin=0,
                cmax=50000
            ),
            dimensions=list([
                dict(
                    tickvals = [-1, 0, 1],
                    label='Configuration',
                    ticktext = [
                        'Fixed South Facing Table',
                        'Fixed East-West Peak Canopy',
                        'Bifacial Solar Fence'
                    ],
                    values=df['Configuration']
                ),
                dict(
                    tickvals = [0, 25, 50],
                    range=[0, 50],
                    label='Transparency',
                    values=df['Transparency']
                ),
                dict(
                    label='Height',
                    values=df['Height from Ground']
                ),
                dict(
                    label='Angle',
                    values=df['Angle (Degrees)']
                ),
                dict(
                    tickvals = [10, 20, 30, 40],
                    label='Panel Count',
                    values=df['Panel Count']
                ),
                dict(
                    range = [20000, 105000],
                    label='Initial cost ($)',
                    values=df['Initial cost ($)']
                ),
                # dict(
                #     range=[0, 100],
                #     label='Low light (%)',
                #     values=df['Low light area (%)']
                # ),
                dict(
                    range=[0, 100],
                    label='Medium light (%)',
                    values=df['Medium light area (%)']
                ),
                dict(
                    range=[0, 100],
                    label='High light (%)',
                    values=df['High light area (%)']
                ),
                dict(
                    range=[0, 50000],
                    label='Net AC electricity',
                    values=df['Net AC electricity']
                )
            ]),
            unselected = dict(line = dict(color = 'gray', opacity = 0.01))
        )
    )

    return fig
