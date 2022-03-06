import pathlib
from typing import Dict
import streamlit as st
import json
import pandas as pd

from sidebar import branding, active_controls, place_holder_controls
from streamlit_vtkjs import st_vtkjs

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

st.markdown('## Annual Average Irradiance')
st.text(f"Location: {location['value']}; Transparency: {transparency['value']}%")
st_vtkjs(
    key='viewer',
    content=viz.read_bytes(),
    style={'height': '400px'},
    sidebar=False, subscribe=False
)

# TODO: Move to a separate module
panel_file = results_folder.joinpath('Agrivoltaic_Panel.res')
crops_file = results_folder.joinpath('Crops_Surface.res')

panel_values = panel_file.read_text().splitlines()
crops_values = crops_file.read_text().splitlines()

length_diff = len(panel_values) - len(crops_values)
target_list = crops_values if length_diff > 0 else panel_values
for _ in range(abs(length_diff)):
    target_list.append(None)

annual_values = {'crops': crops_values, 'panel': panel_values}
annual_csv = convert_to_csv(annual_values, index=True)
st.sidebar.download_button(
    label="Download Annual Average Values",
    data=annual_csv,
    file_name=f'{selection_name}_annual_average.csv',
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
    label="Download Monthly Average Values",
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
