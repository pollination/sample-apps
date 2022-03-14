import json
import pathlib
import zipfile

import pandas as pd
import streamlit as st
from pollination_streamlit.selectors import job_selector
from streamlit_vtkjs import st_vtkjs

from honeybee_vtk.model import HBModel, Model, SensorGridOptions, DisplayMode
from vtk_config import daylight_factor_config

st.set_page_config(
    page_title='Compare daylight factor studies', layout='wide',
    page_icon='https://app.pollination.cloud/favicon.ico'
)

st.header(
    'Compare the results of a parametric daylight-factor job'
)

column_count = st.sidebar.slider(
    label='Number of columns', min_value=2, max_value=3
)

df_threshold = st.sidebar.slider(
    label='Threshold value for daylight factor', min_value=1.0, max_value=20.0,
    value=2.0
)

job = job_selector(
    default='https://app.pollination.cloud/projects/ladybug-tools/demo/jobs/fcd52e87-510c-447e-acdd-9f89fd696408',
    help='This application visualizes the results of any parametric job that is using '
    '`ladybug-tools/daylight-factor` recipe. Copy the URL to the run and press Enter.'
)


@st.cache(suppress_st_warning=True)
def download_artifacts(job):
    """Download artifacts on load and cache results"""
    df = job.runs_dataframe.dataframe
    row_count = len(df.index)
    runs = job.runs
    st.markdown('### Total runs: %d' % row_count)
    job_id = job.id
    progress_bar = st.progress(0)
    for count, (index, row) in enumerate(df.iterrows()):
        progress_bar.progress((count + 1) / row_count)
        # download results
        output_folder = pathlib.Path('data', job_id).joinpath(index)
        results_folder = output_folder.joinpath('results')
        info_file = results_folder.joinpath('grids_info.json')
        if not info_file.is_file():
            results_folder.mkdir(parents=True, exist_ok=True)
            # couldn't find a better way to download folder data from job api
            # directly and had to use run. Most likely I'm missing something
            run = runs[count]
            results_zip = run.download_zipped_output('results')
            with zipfile.ZipFile(results_zip) as zip_folder:
                zip_folder.extractall(results_folder.as_posix())
        # write config information to folder
        viz_file = output_folder.joinpath('model.vtkjs')
        if not viz_file.is_file():
            results_path = output_folder.joinpath('results').as_posix()
            cfg_file = daylight_factor_config(results_path, output_folder)
            # load model and results and save them as a vtkjs file
            model_dict = json.load(job.download_artifact(row.model))
            hb_model = HBModel.from_dict(model_dict)
            model = Model(hb_model, SensorGridOptions.Sensors)
            model.to_vtkjs(folder=viz_file.parent, config=cfg_file,
                           model_display_mode=DisplayMode.Wireframe)

    progress_bar.empty()


def add_viewer(job_id, run_id, count):
    return st_vtkjs(
        content=pathlib.Path('data', job_id, run_id, 'model.vtkjs').read_bytes(),
        key=str(count) + run_id, subscribe=False
    )


@st.cache(suppress_st_warning=True)
def additional_metrics(job_id, run_id, identifier, threshold):
    results_file = pathlib.Path(
        'data', job_id, run_id, 'results', identifier + '.res'
    )
    with results_file.open() as inf:
        results = [float(i) for i in inf.readlines()]

    average = sum(results) / len(results)
    percentage = sum(1 for i in results if i >= threshold) * 100 / len(results)

    return average, percentage


@st.cache(suppress_st_warning=True)
def get_table_df(job_id, run_id, df_threshold):
    grids_info = pathlib.Path(
        'data', job_id, run_id, 'results', 'grids_info.json'
    )
    grids_info = json.loads(grids_info.read_text())
    table_data = {}
    for grid in grids_info:
        average, percentage = additional_metrics(
            job_id, run_id, grid['full_id'], df_threshold
        )
        table_data[grid['name']] = [average, percentage]

    pdf = pd.DataFrame.from_dict(
        table_data, orient='index',
        columns=['Average daylight factor', '% larger than threshold']
    )
    return pdf


if job is not None:
    # downlad artifacts first time
    download_artifacts(job)
    df = job.runs_dataframe.dataframe
    job_id = job.id
    try:
        names = df['name'].values
    except:
        # fall back on model in case there is no name input
        names = df['model'].values

    # I'm sure there is a better way for doing this
    names_mapper = {name: id_ for name, id_ in zip(names, df.index)}
    column_select_tracker = {}

    # load a job with runs
    for count, column in enumerate(st.columns(column_count)):
        with column:
            names_select = st.selectbox(
                'Select run', names, index=count, key=count)
            column_select_tracker[count] = names_select
            run_id = names_mapper[column_select_tracker[count]]
            # calculate average daylight factor
            st.table(get_table_df(job_id, run_id, df_threshold))
            add_viewer(job_id, run_id, count)
