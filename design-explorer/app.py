import json
import pathlib
import zipfile
from requests.exceptions import HTTPError
from typing import Dict, List

import hiplot
import numpy as np
import pandas as pd
import streamlit as st
from honeybee_vtk.actor import Actor
from honeybee_vtk.camera import Camera
from honeybee_vtk.config import load_config
from honeybee_vtk.model import HBModel, Model
from honeybee_vtk.scene import Scene
from honeybee_vtk.vtkjs.schema import DisplayMode, SensorGridOptions
from pollination_streamlit.interactors import Job, Run
from pollination_streamlit.selectors import job_selector
from streamlit_vtkjs import st_vtkjs

pd.set_option("display.precision", 3)


st.set_page_config(
    page_title='Parametric job visualization', layout='wide',
    page_icon='https://app.pollination.cloud/favicon.ico'
)


# branding, api-key and url
# we should wrap this up as part of the pollination-streamlit library
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba_pollination_brandmark-p-500.png',
    use_column_width=True
)

api_key = st.sidebar.text_input(
    'Enter Pollination APIKEY', type='password',
    help=':bulb: You only need an API Key to access private projects. '
    'If you do not have a key already go to the settings tab under your profile to '
    'generate one.'
) or None

query_params = st.experimental_get_query_params()
defult_url = query_params['url'][0] if 'url' in query_params else \
    'https://app.pollination.cloud/projects/ladybug-tools/demo/jobs/89c01325-b2dd-4423-8d54-a6fae296c79a'


job = job_selector(api_key=api_key, default=defult_url)


@st.cache
def get_hiplot(df: pd.DataFrame):
    """Get hiplot only once on load.

    See: https://facebookresearch.github.io/hiplot/tuto_streamlit.html
    """
    plt = hiplot.Experiment.from_dataframe(df)
    # EXPERIMENTAL: Reduces bandwidth at first load
    plt._compress = True
    # ... convert it to streamlit and cache that (`@st.cache` decorator)
    return job.runs_dataframe.dataframe, plt.to_streamlit(ret="selected_uids", key="hiplot")


@st.cache
def download_model(dataframe: pd.DataFrame, run_number: str) -> pathlib.Path:
    run_row = dataframe.iloc[int(run_number)]
    run_id = dataframe.index.to_series().iloc[int(run_number)]
    model_path = run_row.model
    model_dict = json.load(job.download_artifact(model_path))
    hb_model = HBModel.from_dict(model_dict)
    vtk_model = Model(hb_model, SensorGridOptions.Sensors)
    vtk_model.update_display_mode(DisplayMode.Wireframe)

    data_folder = pathlib.Path('data', job.id, run_id)
    config_file = data_folder.joinpath('config.json')
    if config_file.is_file():
        scene = Scene()
        actors = Actor.from_model(vtk_model)
        bounds = Actor.get_bounds(actors)
        centroid = Actor.get_centroid(actors)
        cameras = Camera.aerial_cameras(bounds=bounds, centroid=centroid)
        scene.add_actors(actors)
        scene.add_cameras(cameras)
        vtk_model = load_config(config_file.as_posix(), vtk_model, scene)

    # create a folder based on job id and resuse the geometry
    vtk_file = data_folder.joinpath('model.vtkjs')
    data_folder.mkdir(parents=True, exist_ok=True)
    vtk_model.to_vtkjs(data_folder.as_posix(), 'model')

    return vtk_file


@st.cache
def download_results(runs: List[Run], output: str) -> pathlib.Path:
    for run in runs:
        res_zip = run.download_zipped_output(output)

        if output == 'results':
            res_folder = pathlib.Path('data', run.job_id, run.id, output)
        else:
            res_folder = pathlib.Path('data', run.job_id, run.id)

        with zipfile.ZipFile(res_zip) as zip_folder:
            zip_folder.extractall(res_folder.as_posix())
        if output == 'results':
            config_file = res_folder.parent.joinpath('config.json')
            config_file.write_text(json.dumps({
                "data": [
                    {
                        "identifier": "Daylight-Factor...ecotect",
                        "object_type": "grid",
                        "unit": "Percentage",
                        "path": res_folder.absolute().as_posix(),
                        "hide": False,
                        "legend_parameters": {
                            "hide_legend": False,
                            "min": 0,
                            "max": 5,
                            "color_set": "ecotect",
                            "label_parameters": {
                                "color": [34, 247, 10],
                                "size": 0,
                                "bold": True
                            }
                        }
                    }
                ]
            }))


def calculate_averag_daylight_factors(job_id) -> pd.DataFrame:
    data = []
    job_folder = pathlib.Path('data', job_id)
    job_folder.mkdir(parents=True, exist_ok=True)
    for run_folder in job_folder.iterdir():
        if run_folder.is_file():
            continue
        res_dict = {'run-id': run_folder.stem}
        res_folder = run_folder.joinpath('results')
        for p in res_folder.iterdir():
            if p.is_file() and p.suffix == '.res':
                grid_name = f'avg_df_{p.stem}'
                grid_mean_df = pd.read_csv(p, header=None).mean()[0]
                res_dict[grid_name] = grid_mean_df
        data.append(res_dict)
    df = pd.DataFrame(data)
    df['avg_df_total'] = df.set_index('run-id')\
        .select_dtypes(include=np.number).mean(axis=1).reset_index(inplace=False)[0]
    return df


def post_process_annual_metrics(job_id) -> pd.DataFrame:
    data = []
    job_folder = pathlib.Path('data', job_id)
    job_folder.mkdir(parents=True, exist_ok=True)
    for run_folder in job_folder.iterdir():
        if run_folder.is_file():
            continue
        res_dict = {'run-id': run_folder.stem}
        # iterate through metrics
        metrics_folder = run_folder.joinpath('udi')
        for p in metrics_folder.iterdir():
            if p.is_file() and p.suffix == '.udi':
                grid_name = f'avg_udi_{p.stem}'
                grid_mean_df = pd.read_csv(p, header=None).mean()[0]
                res_dict[grid_name] = grid_mean_df
        data.append(res_dict)
    df = pd.DataFrame(data)
    df['avg_udi_total'] = df.set_index('run-id')\
        .select_dtypes(include=np.number).mean(axis=1).reset_index(inplace=False)[0]
    return df


def check_recipe(recipe: Dict) -> List[str]:
    name = recipe.name
    if name == 'daylight-factor':
        output = 'results'
    elif name == 'annual-daylight':
        output = 'metrics'
    else:
        st.exception(
            'This app currently only supports annual daylight and daylight fatcor '
            'studies.'
        )
        st.stop()

    return name, output

# TODO: Figure out why the interactive design didn't work
# show_pc = st.sidebar.checkbox('Show parallel coordinates chart', value=True)
show_3d = st.sidebar.checkbox('Show 3D model grid')
if show_3d:
    # column_count = st.sidebar.slider(
    #     'Number of columns', min_value=1, max_value=3, value=3
    # )
    column_count = 2

if job is not None:
    try:
        recipe_name, output = check_recipe(job.recipe)
    except HTTPError as e:
        st.error(
            'The app cannot access this job on Pollination. Ensure the url is '
            'correct. In case the job is from a private project you will need to '
            'provide an API key to the app.\n\n :point_left: See the sidebar for '
            'more information.'
        )
        st.stop()
    
    with st.spinner('Downloading file...'):
            download_results(job.runs, output)

    if recipe_name == 'daylight-factor':
        res_df = calculate_averag_daylight_factors(job.id)
    else:
        # annual daylight
        res_df = post_process_annual_metrics(job.id)

    hiplot_df = pd.merge(job.runs_dataframe.parameters,
                         res_df, left_index=True, right_on='run-id')
    dataframe, plt = get_hiplot(hiplot_df)

    if show_3d:
        column_dist = [column_count]
        column_dist.extend([1] * column_count)
        chart, *viz_columns = st.columns(column_dist)
        # viz_columns = viz_1, viz_2, viz_3

        with chart:
            uuids = plt.display()
        # TODO: add a check to only show the first 12 if so many data is being filtered

        for count, run_number in enumerate(uuids):
            vtk_file = download_model(dataframe, run_number)
            with viz_columns[count % column_count]:
                st_vtkjs(vtk_file.read_bytes(), menu=True, key=str(run_number))
    else:
        plt.display()
