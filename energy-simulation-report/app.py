import zipfile
from typing import Tuple

import streamlit as st
from requests.exceptions import HTTPError
from streamlit.components.v1 import html
from pollination_streamlit.selectors import run_selector

from report import copy_static_assets, replace_links_in_report

# https://app.pollination.cloud/projects/riennnnn-1000/demo/jobs/eb1f3afd-3c22-4003-aa1e-d41420ab7279/runs/a81a9fac-14d5-5ef2-84ca-d89ed80e2a23

# Use this URL for testing
# https://app.pollination.cloud/projects/chriswmackey/demo/jobs/67a49e35-38da-414c-ac24-6a739da46a87/runs/3243570c-850b-591e-aa11-09a0c8b69283?path=&tab=run

st.set_page_config(
    page_title='Visualize energy simulation results', layout='wide',
    page_icon='https://app.pollination.cloud/favicon.ico'
)

copy_static_assets()


def get_info(visualization_type) -> Tuple:
    if visualization_type == '2D':
        output_name = 'result-report'
        file_name = 'results.html'
    elif visualization_type == '3D':
        output_name = 'visual-report'
        file_name = 'visual.html'
    else:
        raise ValueError(
            f'Visualization type should either be 2D or 3D not {visualization_type}'
        )
    return output_name, file_name


st.cache(suppress_st_warning=True)


def download_results(run, viz_type) -> str:
    output_name, file_name = get_info(viz_type)
    report_zip = run.download_zipped_output(output_name)
    zip = zipfile.ZipFile(report_zip)
    html_report = zip.read(file_name).decode('utf-8').strip()
    return replace_links_in_report(html_report)


st.cache(suppress_st_warning=True)


def try_get_results(run, viz_type):
    try:
        html_report = download_results(run, viz_type)
    except HTTPError as e:
        if viz_type == '2D':
            raise HTTPError(e)
        viz_type = '2D'
        html_report = download_results(run, viz_type)
    return html_report, viz_type


# Import script tags for html report
html("""
  <script type="text/javascript" src="http://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>
  <script type="text/javascript" src="http://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/js/bootstrap.min.js"></script>
  <script type="text/javascript" src="http://cdnjs.cloudflare.com/ajax/libs/d3/3.4.8/d3.min.js"></script>
  <script type="text/javascript" src="http://dimplejs.org/dist/dimple.v2.1.2.min.js"></script>
""")

st.header(
    'Visualize energy simulation results'
)

run = run_selector(
    default='https://app.pollination.cloud/projects/chriswmackey/demo/jobs/67a49e35-38da-414c-ac24-6a739da46a87/runs/3243570c-850b-591e-aa11-09a0c8b69283',
    help='This application visualizes the results of any run that is using '
    '`ladybug-tools/annual-energy-use:0.3.6` recipe. Copy the URL to the run and press '
    'Enter.'
)

viz_type = st.sidebar.selectbox(
    'Visualization style',
    options=['2D', '3D', 'Combo']
)

if run is not None:
    # TODO: Find a way to check the version of the recipe for this run
    # this visualization will not work with older versions of the recipe
    if viz_type != 'Combo':

        html_report, out_viz_type = try_get_results(run, viz_type)
        if viz_type == '3D' and out_viz_type == '2D':
            st.warning('No 3D results available. Switching to 2D.')

        # TODO: figure out how to make the viewer full screen
        html(html_report, scrolling=True, height=720)
    else:
        html_report_3d, out_viz_type = try_get_results(run, '3D')
        if out_viz_type == '2D':
            st.warning(
                'No 3D results available to create a combo view. Switching to 2D.'
            )
            html(html_report_3d, scrolling=True, height=720)
        else:
            html_report_2d, out_viz_type = try_get_results(run, '2D')
            # create 2 columns and show 2D and 3D side by side
            col1, col2 = st.columns(2)
            with col1:
                html(html_report_2d, scrolling=True, height=720)
            with col2:
                html(html_report_3d, scrolling=True, height=720)
