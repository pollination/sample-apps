import zipfile
import pathlib
import json

import streamlit as st
import pandas as pd

from requests.exceptions import HTTPError
from pollination_streamlit.selectors import run_selector

from streamlit_vtkjs import st_vtkjs

from honeybee_vtk.model import HBModel, Model, SensorGridOptions, DisplayMode
from vtk_config import leed_config


st.set_page_config(
    page_title='LEED Option II', layout='wide',
    page_icon='https://app.pollination.cloud/favicon.ico'
)

# branding, api-key and url
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
    'https://app.pollination.cloud/projects/chriswmackey/demo/jobs/0cd8f29b-71e1-44be-9ce2-7d4c6e4e5d13/runs/ec6bbd7e-1579-550c-9e89-2ba424cd2d04'


@st.cache(show_spinner=False)
def download_folder(run, output_name, folder):
    results_zip = run.download_zipped_output(output_name)
    with zipfile.ZipFile(results_zip) as zip_folder:
        zip_folder.extractall(folder.as_posix())


@st.cache(show_spinner=False)
def download_files(run):

    job = run.job
    results_folder = pathlib.Path('data', job.id, run.id)
    df = job.runs_dataframe.dataframe
    _, info = next(df.iterrows())
    metrics = [
        'illuminance-9am', 'illuminance-3pm', 'pass-fail-9am', 'pass-fail-3pm',
        'pass-fail-combined', 'credit-summary', 'space-summary'
    ]

    for metric in metrics:
        download_folder(run, metric, results_folder.joinpath(metric))

    credits = results_folder.joinpath('credit-summary', 'credit_summary.json')

    space_summary = results_folder.joinpath('space-summary', 'space_summary.csv')

    # write configs to load the results
    viz_file = results_folder.joinpath('model.vtkjs')
    cfg_file = leed_config(results_folder)
    model_dict = json.load(job.download_artifact(info.model))
    hb_model = HBModel.from_dict(model_dict)
    model = Model(hb_model, SensorGridOptions.Sensors)
    model.to_vtkjs(folder=viz_file.parent, name=viz_file.stem,
                   config=cfg_file, model_display_mode=DisplayMode.Wireframe)

    return viz_file, credits, space_summary


# get the run id
_, run_url, _ = st.columns([0.5, 3.5, 0.5])
with run_url:
    st.header(
        'LEED Option II report'
    )

    run = run_selector(
        api_key=api_key,
        default=defult_url,
        help='See the factsheet about the results of the LEED Option II simulation.'
    )

# download related results
if run is not None:

    with st.spinner('Downloading file...'):
        viz_file, credits, space_summary = download_files(run)

    try:
        with st.spinner('Downloading file...'):
            viz_file, credits, space_summary = download_files(run)
    except HTTPError as e:
        with run_url:
            st.error(
                'The app cannot access this run on Pollination. Ensure the url is '
                'correct. In case the run is from a private project you will need to '
                'provide an API key to the app.\n\n :point_left: See the sidebar for '
                'more information.'
            )
        st.stop()

    recipe_info = run.recipe
    if f"{run.recipe.owner}/{run.recipe.name}" != 'pollination/leed-daylight-illuminance':
        with run_url:
            st.error(
                'This app is designed to work with pollination/leed-daylight-illuminance '
                f"recipe. The input run is using {run.recipe.owner}/{run.recipe.name}"
            )
        st.stop()
    tag_number = sum(10**c * int(i) for c, i in enumerate(recipe_info.tag.split('.')))

    if tag_number < 30:
        with run_url:
            st.error(
                'Only versions pollination/leed-daylight-illuminance:0.3.0 or higher '
                f"are valied. Current version of the recipe:{run.recipe.tag}"
            )
        st.stop()

    with run_url:
        st_vtkjs(
            content=viz_file.read_bytes(), key='results-viewer', subscribe=False,
            style={"height": "500px"}
        )
    _, info_a, info_c, _ = st.columns([0.5, 2, 2, 0.5])

    data = json.loads(credits.read_text())
    with info_a:
        points = data['credits']
        if points > 1:
            color = 'Green'
        else:
            color = 'Gray'
        credit_text = f'<h2 style="color:{color};">LEED Credits: {points} points</h2>'
        st.markdown(credit_text, unsafe_allow_html=True)
        st.markdown(f'### Percentage passing: {round(data["percentage_passing"], 2)}%')
    with info_c:
        with st.expander('See model breakdown'):
            if points > 1:
                st.balloons()
            df = pd.DataFrame.from_dict(data, orient='index', columns=['values'])
            st.table(df.style.format(precision=1))

    # this is not good practice for creating the layout
    # but it is good enough for now
    _, table_column, _ = st.columns([0.5, 3.5, 0.5])
    with table_column:
        st.header('Space by space breakdown')
        df = pd.read_csv(space_summary.as_posix())
        st.table(df.style.format(precision=1))
