import pathlib
from typing import Dict
import streamlit as st
import json
import pandas as pd

from sidebar import branding, active_controls, place_holder_controls
from streamlit_vtkjs import st_vtkjs
from streamlit_elements import Elements

from charts import get_graph


st.set_page_config(
    page_title='Sandbox Solar',
    initial_sidebar_state='auto',
    page_icon='https://app.pollination.cloud/favicon.ico',

)

@st.cache
def convert_to_csv(average_values: Dict, index=False, columns=None):
    df = pd.DataFrame.from_dict(average_values)
    index_label = 'ID' if index else None
    if columns:
        return df.to_csv(index=index, columns=columns, index_label=index_label).encode('utf-8')
    else:
        return df.to_csv(index=index, index_label=index_label).encode('utf-8')


branding()
configuration, transparency, location = active_controls()
st.sidebar.markdown('---')

selection_index = f'{configuration["index"]}_{transparency["index"]}_{location["index"]}'
selection_name = f'{configuration["value"]}_{location["value"]}_{transparency["value"]}%'

here = pathlib.Path(__file__).parent
results_folder = here.joinpath('sim_data', f'{selection_index}')

viz = results_folder.joinpath('results.vtkjs')

# add button
mt = Elements()

mt.button(
    "Visit our website!", 
    target="_blank", 
    size="medium", 
    variant="contained", 
    start_icon=mt.icons.send, 
    onclick="none", 
    style={"color":"#FFFFFF", "background":"#4ba3ff"}, 
    href="https://sandboxsolar.com/agrivoltaics/"
)

col1, col2 = st.columns([3, 1])


col1.markdown('## Annual Average Irradiance')
with col2:
    mt.show(key = "840")
st.text(f"Location: {location['value']}; Transparency: {transparency['value']}%")
st_vtkjs(
    key='viewer',
    content=viz.read_bytes(),
    style={'height': '400px'},
    sidebar=False, subscribe=False
)
st.text('ℹ Hold down the Alt button to rotate around the cursor.')

# add a table for predictive outcome
with st.expander('Click here to learn more about the metrics'):
    st.markdown(
        'We provide two metrics that can help you to evaluate the performance of each '
        'configuration at your specific location:\n\n'
        '* **Average Irradiance** is the average solar power (W/m2) falling on the surface '
        'over the course of the year.\n\n'
        '* **Cumulative Radiation** is the total solar energy (kWh/m2) falling on the '
        'surface over the course of the year.'
    )

panel_file = results_folder.joinpath('Agrivoltaic_Panel.csv')
crops_file = results_folder.joinpath('Crops_Surface.csv')

st.sidebar.text("Download data in CSV format")

st.sidebar.download_button(
    label="Crops Annual Average Values",
    data=crops_file.read_text(),
    file_name=f'{selection_name}_crops_annual_average.csv',
    mime='text/csv'
)

st.sidebar.download_button(
    label="Panel Annual Average Values",
    data=panel_file.read_text(),
    file_name=f'{selection_name}_panel_annual_average.csv',
    mime='text/csv'
)

st.markdown('## Monthly Average Irradiance')
average_file = results_folder.joinpath('average_monthly.json')
average_values = json.loads(average_file.read_text())
average_values['month'] = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]
monthly_csv = convert_to_csv(
    average_values, index=False, columns=['month', 'crops', 'panel']
)

st.sidebar.download_button(
    label="Monthly Average Values",
    data=monthly_csv,
    file_name=f'{selection_name}_monthly_average.csv',
    mime='text/csv'
)

fig = get_graph(
    panel_data=average_values['panel'],
    crops_data=average_values['crops'],
)
st.plotly_chart(fig, use_container_width=True, height=300)

# add place holder controls
st.sidebar.markdown('---')
place_holder_controls()
