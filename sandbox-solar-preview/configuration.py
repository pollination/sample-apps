import pathlib
from typing import Dict
import streamlit as st
import json
import pandas as pd

# from pollination_streamlit_viewer import viewer
from streamlit_vtkjs import st_vtkjs as viewer
import plotly.graph_objects as go
import plotly.express as px

from charts import get_graph
from sidebar import place_holder_controls
from economics import calculate_economics
from visualization import ground_visualization

def active_controls():
    inp_1, inp_2 = st.columns(2)
    cfg_options = [
        "Fixed South Facing", "Fixed South Facing Canopy", "North-South Tracking",
        "Bifacial Solar Fence", "Fixed East-West Peak Canopy"
    ]
    configuration = inp_1.selectbox(
        'Select panel configuration',
        options=cfg_options, index=4
    )

    transparency_values = [0, 20, 40, 60, 80, 100]
    transparency = inp_2.selectbox(
        'Select panel transparency', options=transparency_values, index=0
    )

    return [
        {'value': configuration, 'index': cfg_options.index(configuration)},
        {'value': transparency,
            'index': transparency_values.index(transparency)}
    ]


@st.cache
def convert_to_csv(average_values: Dict, index=False, columns=None):
    df = pd.DataFrame.from_dict(average_values)
    index_label = 'ID' if index else None
    if columns:
        return df.to_csv(index=index, columns=columns, index_label=index_label).encode('utf-8')
    else:
        return df.to_csv(index=index, index_label=index_label).encode('utf-8')


def draw_table(par_values):
    values = [
        ['High', 'Medium', 'Low'],  # 1st column
        [par_values['high'], par_values['medium'], par_values['low']],
        ['> 600', '300-600', '< 300'],
        [
            'Solanaceae (nightshade)<br>Cucurbitaceae (melon)',
            'Fabaceae (legume)<br>Apiaceae (carrot)<br>Asteraceae (lettuce)<br>Lamiaceae<br>Amaryllidaceae',
            'Brassicaceae (cruciferous)<br>Apiaceae (carrot)<br>Asteraceae (lettuce)<br>Chenopodiaceae'
        ]
    ]
    
    figure = go.Figure(data=[go.Table(
        columnorder=[1, 2, 3, 4],
        columnwidth=[80, 80, 80, 200],
        header=dict(
            values=[['<b>Light levels</b>'], ['<b>% Area</b>'], ['<b>PPFD</b>'], ['<b>Potential Crop Families</b>']],
            fill_color='white',
            line_color='black',
            font=dict(size=15)
        ),
        cells=dict(
            values=values,
            line_color='black',
            fill_color=[
                ['rgb(184,216,190)', 'rgb(210,231,214)','rgb(232,244,234)'],
                ['rgb(255,255,255)', 'rgb(255,255,255)','rgb(255,255,255)']
            ],
            font=dict(size=13),
            align=['center', 'center', 'center', 'left']
        )
        )
    ])
    figure.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=340
    )
    st.plotly_chart(figure, use_container_width=True)


def draw_pie_chart(par_values: Dict):

    colors = ['rgb(232,244,234)', 'rgb(210,231,214)', 'rgb(184,216,190)']
    values = [par_values['low'], par_values['medium'], par_values['high']]
    labels = ['Low PAR <3.13 MJ/m2.d',
              'Medium PAR 3.13~5.48 MJ/m2.d', 'High PAR >5.48 MJ/m2.d']
    figure = go.Figure(
        data=go.Pie(
            values=values,
            labels=labels,
            hole=0.75,
            title='Percentage Land Area',
            marker_colors=colors,
            showlegend=False
        )
    )
    figure.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=300
    )
    st.plotly_chart(figure, use_container_width=True)


def draw_cf_chart(data):
    data = data[1:]
    data = pd.DataFrame(
        zip(data, [f'year {d + 1}' for d in range(len(data))]),
        columns=['$', 'year']
    )

    fig = px.bar(
        data, x='year', y='$', title='Payback Cash Flow',
        color_discrete_sequence=['darkblue'] * 25
    )
    st.plotly_chart(fig, use_container_width=True)


def draw_monthly_electricity_chart(data):
    fig = px.bar(
        data, x='month', y='Thousand kWh', title='Electricity from System Year 1',
        color_discrete_sequence=['darkblue'] * 12
    )
    st.plotly_chart(fig, use_container_width=True)


def add_pv_config(location):
    here = pathlib.Path(__file__).parent

    st.write(f"Select panel configuration and transparency for {location['value']}.")
    configuration, transparency = active_controls()
    selection_index = f'{configuration["index"]}_{transparency["index"]}_{location["index"]}'
    # name is only for download buttons - don't use it!
    selection_name = f'{configuration["value"]}_{location["value"]}_{transparency["value"]}%'

    # add additional inputs here
    with st.expander('Click here for additional inputs (coming soon)'):
        # add place holder controls
        place_holder_controls()

    model_viz = here.joinpath('models_viz', f'{configuration["index"]}.vtkjs')

    viewer(
        key='model-viewer',
        content=model_viz.read_bytes(),
        style={'height': '400px'},
        sidebar=False, subscribe=False, toolbar=False
    )

    if configuration["index"] == 2:
        st.warning('Data for north-south tracking panels is not currently available.')
        st.stop()

    results_folder = here.joinpath('sim_data', f'{selection_index}')
    weather_folder = here.joinpath('weather_data')

    # show the outcome here
    st.header('3. PV Economic Modeling')
    st.info(
        'All pre-configured systems are based on a 12kW-dc PV System. '
        'Cost estimates are industry average. Please reach out to our team if you '
        'would like a more detailed techno-economic analysis and design.\n\n'
        'The PV Economic Modeling is powered by [NREL Advisor Model (SAM)](https://sam.nrel.gov/).'
    )
    with st.expander('Click here for additional inputs (coming soon)'):
        st.markdown(
            'We are currently working on adding control for additional parameters including:\n\n'
            '* Financial Ownership Model\n\n'
            '  * Commercial Net Metering [current option]\n\n'
            '  * Third-Party Owner\n\n'
            '  * Power Purchase Agreement - Single Owner\n\n'
            '  * Power Purchase Agreement - Partnership Flip with Debt\n\n'
            '* Modules\n\n'
            '* Inverter\n\n'
            '* Number of Panels or Area? As it relates to system size\n\n'
            '* Install Costs\n\n'
            '* Financial Parameters & Incentives\n\n'
            '* Utility Rate\n\n'
            '* Energy Usage'
        )
    # calculate economics for this location and configuration
    # Read the SAM module from the JSON file
    CECMod = pd.DataFrame.from_dict(json.loads(
        here.joinpath('cec_mod.json').read_text()))
    # Solution - parse the csv file and create the item from the csv file directly.
    irr_file = results_folder.joinpath(f'Agrivoltaic_Panel.ill')
    irradiance = pd.read_csv(irr_file.as_posix(), header=None)
    temperature = pd.read_csv(
        weather_folder.joinpath(f'{location["index"]}_temperature.txt').as_posix(),
        header=None
    )
    wind_speed = pd.read_csv(
        weather_folder.joinpath(f'{location["index"]}_wind_speed.txt').as_posix(),
        header=None
    )

    total_electricity, monthly_electricity, adjusted_installed_cost, payback_cash_flow = \
        calculate_economics(irradiance, temperature,
                            wind_speed, CECMod, configuration["index"])

    ec_clo1, ec_col2 = st.columns(2)
    with ec_clo1:
        # NOTE: I'm dividing this value by 30 to match SAM's output
        total_electricity = '{:,}'.format(int(total_electricity / 30))
        st.write(f'**Net AC electricity to grid: {total_electricity} kWh**')
    with ec_col2:
        adjusted_installed_cost = '{:,}'.format(int(adjusted_installed_cost))
        st.markdown(
            f'**Adjusted Installed Cost: ${adjusted_installed_cost}**'
        )

    draw_monthly_electricity_chart(monthly_electricity)
    draw_cf_chart(payback_cash_flow)

    months = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct',
        'Nov', 'Dec'
    ]
    st.header('4. Crop Potential')
    st.markdown(
        'This section provides the basic information to make estimators for yield '
        'success of your desired crop. If you\'d like to run some financial scenarios, '
        'please use these reference guides '
        '([1](https://abm.extension.colostate.edu/enterprise-budgets-small-farm-specialty-crops/), '
        '[2](https://www.extension.iastate.edu/agdm/crops/html/a1-17.html)) for your farm. '
        'Our team would be happy to assist further.\n\n'
    )
    st_month, end_month = st.select_slider(
        'Select the start and the end of the growing season', options=months,
        value=('Apr', 'Oct')
    )
    st.markdown('#### Average Photosynthetic Photon Flux Density (PPFD)')
    st.write('*PPFD measures the light wavelengths within the PAR range (400-700 nm) that reach the crop growth surface.')
    st_index = months.index(st_month)
    end_index = months.index(end_month)
    par_df = pd.read_csv(results_folder.joinpath('Crops_Surface.ill'))
    # Note: the results of the new method are about 1.5 times more than the original
    # hourly runs. I'm diving the values by 1.5 to adjust for that until I get a chance
    # to review the workflow. It is most likely an adjustment in the sky that I hacked
    # together from several skies.
    average_values = par_df[months[st_index: end_index + 1]].mean(axis=1) / 1.2

    vtkjs_index = f'{selection_index}_{st_index}_{end_index}'
    ppfd_values, ppfd_viz = ground_visualization(average_values.values.tolist(), vtkjs_index)

    col1, col2 = st.columns([1, 2])
    with col1:
        draw_pie_chart(par_values=ppfd_values)
    with col2:
        draw_table(par_values=ppfd_values)

    viewer(
        key='par-viewer',
        content=ppfd_viz.read_bytes(),
        style={'height': '600px'},
        sidebar=False, subscribe=False
    )

    st.text('ℹ Hold down the Alt button to rotate around the cursor.')

    # add a table for predictive outcome
    with st.expander('Click here to learn more about the metrics'):
        st.markdown(
            'We provide two metrics that can help you to evaluate the performance '
            'of each configuration at your specific location:\n\n'
            '* **Photosynthetic Photon Flux Density (PPFD)** measures the light wavelengths '
            'within the PAR range (400-700 nm) that reach the crop growth surface.\n\n'
            '* **Average Irradiance** is the average solar power (W/m2) falling on the surface '
            'over the course of the year.'
        )

    panel_file = results_folder.joinpath('Agrivoltaic_Panel.csv')
    crops_file = results_folder.joinpath('Crops_Surface.csv')

    average_file = results_folder.joinpath('average_monthly.json')
    average_values = json.loads(average_file.read_text())
    average_values['month'] = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]
    monthly_csv = convert_to_csv(
        average_values, index=False, columns=['month', 'crops', 'panel']
    )

    with st.expander("Click here to download data in CSV format"):
        c1, c2, c3 = st.columns(3)
        c1.download_button(
            label="Crops Annual Average Values",
            data=crops_file.read_text(),
            file_name=f'{selection_name}_crops_annual_average.csv',
            mime='text/csv'
        )

        c2.download_button(
            label="Panel Annual Average Values",
            data=panel_file.read_text(),
            file_name=f'{selection_name}_panel_annual_average.csv',
            mime='text/csv'
        )

        c3.download_button(
            label="Monthly Average Irradiance Values",
            data=monthly_csv,
            file_name=f'{selection_name}_monthly_average.csv',
            mime='text/csv'
        )

    with st.expander("Click here to see the monthly average irradiance chart"):

        fig = get_graph(
            panel_data=average_values['panel'],
            crops_data=average_values['crops'],
        )

        st.plotly_chart(fig, use_container_width=True, height=200)
