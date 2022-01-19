"""Pollination outdoor comfort app."""
import pathlib

import streamlit as st

from ladybug.epw import EPW
from ladybug_comfort.utci import universal_thermal_climate_index


# make it look good by setting up the title, icon, etc.
st.set_page_config(
    page_title='Outdoor Comfort',
    page_icon='https://app.pollination.cloud/favicon.ico'
)
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba_pollination_brandmark-p-500.png',
    use_column_width=True
)


def main():
    with st.sidebar:
        # Create a dropdown to upload a file or use a sample file
        epw_source = st.selectbox(
            '',
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

    st.header('Outdoor Comfort')
    utci = universal_thermal_climate_index(epw.dry_bulb_temperature)


if __name__ == '__main__':
    main()
