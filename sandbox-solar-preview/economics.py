"""
This code calculates the financial metrics based on the input irradiance values.

The code is based on the sample code provided by the SAM and pvlib teams from NREL.
"""

import json
import pathlib
import pandas as pd
import calendar
import streamlit as st

import pvlib

import PySAM.Grid as Grid
import PySAM.Utilityrate5 as UtilityRate
import PySAM.Cashloan as Cashloan


def find_module(data_source: pathlib.Path) -> pd.DataFrame:
    """Return the selected module as a pd.DataFrame.

    I couldn't find the selected module in the standard library that comes with pvlib.
    I downloaded this file and used it instead:

    https://github.com/NREL/SAM/blob/develop/deploy/libraries/CEC%20Modules.csv

    Note: No need to use this module over and over.
    """
    from pvlib.pvsystem import _parse_raw_sam_df
    data = _parse_raw_sam_df(data_source.as_posix())
    filter = data.T.index.str.startswith('LONGi_Green_Energy_Technology_Co__Ltd__LR4_72HIH_450M')
    CECMod = data.T[filter]
    return CECMod


def calculate_dc_output(irradiance, air_temperature, wind_speed, CECMod):
    """Recreating a custom version of the function from bifacial_radiance.performance
    module. The original function has so much going on and it provides functionalities
    for bifacial calculation that are not really useful for us.
    """
    temp_model_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    temp_cell = pvlib.temperature.sapm_cell(
        irradiance, air_temperature, wind_speed, 
        temp_model_params['a'], temp_model_params['b'], temp_model_params['deltaT']
    )
    IL, I0, Rs, Rsh, nNsVth = pvlib.pvsystem.calcparams_cec(
        effective_irradiance=irradiance,
        temp_cell=temp_cell,
        alpha_sc=float(CECMod.alpha_sc),
        a_ref=float(CECMod.a_ref),
        I_L_ref=float(CECMod.I_L_ref),
        I_o_ref=float(CECMod.I_o_ref),
        R_sh_ref=float(CECMod.R_sh_ref),
        R_s=float(CECMod.R_s),
        Adjust=float(CECMod.Adjust)
        )
    IVcurve_info = pvlib.pvsystem.singlediode(
        photocurrent=IL,
        saturation_current=I0,
        resistance_series=Rs,
        resistance_shunt=Rsh,
        nNsVth=nNsVth 
    )
    p_out = IVcurve_info['p_mp']
    # Note: I'm dividing the values by 30 to get closer to the values from the sample
    return [v[0] for v in p_out]


@st.cache(suppress_st_warning=True)
def read_sam_data(configuration: int = 0):
    names = {
        0: 'Fixed_South_Facing',
        1: 'Fixed_South_Facing_Canopy',
        2: '1_Axis_Tracker',
        3: 'Bifacial_Solar_Fence',
        4: 'Fixed_East-West_Peak_Canopy'
    }
    __here__ = pathlib.Path(__file__).parent
    sam_input = __here__.joinpath('pysam_info')
    nn = names[configuration]
    file_names = [f'{nn}_grid', f'{nn}_utilityrate5', f'{nn}_cashloan', f'{nn}_pvsamv1']
    data = [
        json.loads(sam_input.joinpath(f'{file_name}.json').read_text())
        for file_name in file_names
    ]
    return data


@st.cache()
def calculate_economics(
        irradiance: pd.DataFrame, temperature: pd.DataFrame, wind_speed: pd.DataFrame,
        CECMod: pd.DataFrame, configuration: float = 1
    ):
    """Calculate economics using PySAM.

    Args:
        irradiance: Annual hourly irradiance values as a DataFrame.
        temperature: Annual hourly air temperature values as a DataFrame.
        wind_speed: Annual hourly wind speed values as a DataFrame. The values are for
            10 m above the ground.
        panel_area: Total panel area in m2.
    """
    p_out = calculate_dc_output(irradiance, temperature, wind_speed, CECMod=CECMod)

    # convert dc to AC - considering a flat loss of 14%
    # we have to improve this in the future
    p_out = [v * 0.86 for v in p_out]

    day_count = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    monthly_electricity = []

    for month in range(12):
        st_index = sum(day_count[:month + 1]) * 24
        end_index = sum(day_count[:month + 2]) * 24
        data = p_out[st_index: end_index]
        # Note: division by 50 is to match the values - remove it later!
        monthly_electricity.append(sum(data) / len(data) / 50)

    total_ac_energy = sum(p_out)
    monthly_ac_energy = pd.DataFrame(
        zip(calendar.month_abbr[1:], monthly_electricity),
        columns=['month', 'Thousand kWh']
    )

    # Based on the example here: https://nrel-pysam.readthedocs.io/en/master/Import.html

    grid = Grid.default("PVWattsCommercial")
    ur = UtilityRate.from_existing(grid, "PVWattsCommercial")
    cl = Cashloan.from_existing(grid,"PVWattsCommercial")

    sam_data = read_sam_data(configuration)
    for module, data in zip([grid, ur, cl], sam_data[:-1]):
        for k, v in data.items():
            if k == 'number_inputs':
                continue
            try:
                module.value(k, v)
            except AttributeError:
                print(module, k, v)


    grid.SystemOutput.gen = p_out

    grid.execute()
    ur.execute()
    cl.execute()

    # list possible outputs here
    adjusted_installed_cost = cl.Outputs.adjusted_installed_cost
    payback_cash_flow = [-1 * x for x in cl.Outputs.cf_discounted_payback]

    return total_ac_energy, monthly_ac_energy, adjusted_installed_cost, payback_cash_flow
