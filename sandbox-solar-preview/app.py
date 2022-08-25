from typing import Dict
import streamlit as st
import pandas as pd
from streamlit_elements import Elements

from location import add_map
from configuration import add_pv_config
from explorer import add_parallel_coordinates


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


mt = Elements()
mt.button(
    "Visit our website!", 
    target="_blank", 
    size="large", 
    variant="contained", 
    start_icon=mt.icons.send, 
    onclick="none", 
    style={"color":"#FFFFFF", "background":"#4ba3ff", "width": "100%"}, 
    href="https://sandboxsolar.com/agrivoltaics/"
)

col1, _, col2 = st.columns([1.5, 1.5, 1], gap='small')
col1.image('spade_logo.png', use_column_width=True)
with col2:
    mt.show(key="840")

# add introduction here
st.write(
    'Welcome to Sandbox Solar\'s SPADE application - your platform for agrivoltaic '
    'design & modeling. To begin, select your geographic location. You can then plot '
    'your panel configuration and optimize the system to meet your needs.'
    '\n\nNote: Note: Although the data on this app are calculated based on validated '
    'methods, you should consider them for demonstration purposes only. Contact us for '
    'an in-depth assessment of your particular project.'
)
# add the tabs to the app
# loc_tab, config_tab, explorer_tab = st.tabs(["Location", "Panel Configuration", "Optimization"])
# loc_tab, config_tab = st.tabs(["Location", "Panel Configuration"])


st.header('1. Location')
city = st.text_input(
    "Type in the city and the state separated by a comma. Currently, only locations in the United States are supported.",
    "Denver, CO"
)
location = add_map(city=city)

# start configuration section
st.header('2. Panel Configuration')
add_pv_config(location=location)

st.header('5. Dual Optimization')
st.write(
    'Use this parallel coordinates chart to quickly filter the best option that maximizes '
    'electricity and crops generation. Click on the top right type arrow to maximize the chart.'
)

fig = add_parallel_coordinates(0)
# fig = add_parallel_coordinates(location['index'])
st.plotly_chart(fig, use_container_width=True)

_, _, logo, _, _ = st.columns(5)
logo.image('AMC-solarPrize-logo-color_edited.webp')
