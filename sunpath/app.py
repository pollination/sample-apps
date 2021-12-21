# an interactive app for drawing sunpath
import pathlib

import streamlit as st
from streamlit_vtkjs import st_vtkjs

from ladybug.sunpath import Sunpath

# make it look good by setting up the title, icon, etc.
st.set_page_config(
    page_title='Interactive Sunpath',
    page_icon='https://app.pollination.cloud/favicon.ico'
)
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba_pollination_brandmark-p-500.png',
    use_column_width=True
)

# create the control panel
latitude = st.sidebar.slider('Latitude', -90.0, 90.0, 0.0, 0.5)
longitude = st.sidebar.slider('Longitude', -90.0, 90.0, 0.0, 0.5)
north = st.sidebar.slider('North', -180, 180, 0, 1)
menu = st.sidebar.checkbox('Show viewer controls', value=False)

@st.cache(suppress_st_warning=True)
def create_sunpath(latitude, longitude, north):
    """Create the sunpath geometry."""
    folder = pathlib.Path('./data')
    folder.mkdir(parents=True, exist_ok=True)
    name = f'{latitude}_{longitude}_{north}'
    sp = Sunpath(latitude, longitude, north_angle=north)
    # create a vtkjs file for sunpath
    sp_file = sp.to_vtkjs(folder.as_posix(), file_name=name)
    return sp_file

# call the function to create the sunpath
sp_file = create_sunpath(latitude, longitude, north)

# update the viewer
st_vtkjs(sp_file.read_bytes(), menu=menu, key='viewer')
