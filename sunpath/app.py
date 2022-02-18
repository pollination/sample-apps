"""The Pollination sunpath app."""


import pathlib
import streamlit as st

from typing import List
from streamlit_vtkjs import st_vtkjs
from streamlit.uploaded_file_manager import UploadedFile
from ladybug.epw import EPW

from helper import get_sunpath_vtkjs, get_sunpath, write_csv_file, get_data, epw_fields
from rhino import add_rhino_controls


st.set_page_config(
    page_title='Sunpath',
    page_icon='https://app.pollination.cloud/favicon.ico',
    initial_sidebar_state='collapsed',
)  # type: ignore
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba'
    '_pollination_brandmark-p-500.png',
    use_column_width=True
)

def main(platform):
    st.title('Interactive Sunpath App!')
    epw = None
    with st.expander('Click here to create a Sunpath from an EPW file'):
        epw_data: UploadedFile = st.file_uploader('Load EPW', type='epw')
        if epw_data:
            epw_file = pathlib.Path('./data/sample.epw')
            epw_file.parent.mkdir(parents=True, exist_ok=True)
            epw_file.write_bytes(epw_data.read())
            epw = EPW(epw_file)

    selection: List[bool] = []
    if not epw:
        c1, c2 = st.columns(2)
        latitude = c1.slider('Latitude', -90.0, 90.0, 0.0, 0.5)
        longitude = c1.slider('Longitude', -180.0, 180.0, 0.0, 0.5)
    else:
        st.markdown(f'### Sunpath for {epw.location.city}')
        latitude = epw.location.latitude
        longitude = epw.location.longitude
        c1, c2 = st.columns(2)
        c1.write(f'Latitude: {latitude}')
        c1.write(f'Longitude: {longitude}')

        selection = st.multiselect(
            'Select data to plot on top of the Sunpath',
            epw_fields().keys()
        )

    north_angle = c2.slider('North', -180, 180, 0, 1)
    radius = c2.slider('Sun path radius', 0, 500, 100)

    sunpath = get_sunpath(latitude, longitude, north_angle=north_angle, epw=epw)

    # add download to sidebar
    st.sidebar.markdown('---')
    st.sidebar.write(
        'Use this checkbox to download the position of suns for all the sun up hours.'
    )
    write_csv = st.sidebar.checkbox('Download CSV', value=False)

    # add Rhino controls
    if platform == 'Rhino':
        add_rhino_controls(sunpath, radius, north_angle)

    # viewer
    hourly_data = get_data(selection, epw_fields(), epw)
    sunpath_vtkjs, sun_color = get_sunpath_vtkjs(sunpath, data=hourly_data)
    st_vtkjs(sunpath_vtkjs.read_bytes(), menu=True, key='viewer')

    if write_csv:
        csv_file_path = write_csv_file(sunpath, epw, [])
        with open(csv_file_path, 'r') as f:
            st.sidebar.download_button('Download CSV', f, file_name='sunpath.csv')


if __name__ == '__main__':
    # get the platform from the query uri
    query = st.experimental_get_query_params()
    platform = query['__platform__'][0] if '__platform__' in query else 'web'
    main(platform)
