import os
import json
import zipfile
import pathlib
from requests.exceptions import HTTPError

from pandas import DataFrame
import streamlit as st
from pollination_streamlit.selectors import job_selector
from pollination_streamlit.interactors import Job
from streamlit_vtkjs import st_vtkjs

from honeybee_vtk.model import HBModel, Model
from ladybug.sql import SQLiteResult


st.set_page_config(
    page_title='Energy use app', layout='wide',
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
    'https://app.pollination.cloud/projects/chriswmackey/demo/jobs/' \
    '9f7360bd-704c-49ae-8c29-f600f43c9b2b'


try:
    job = job_selector(
        api_key=api_key,
        default=defult_url
    )
except Exception:
    st.error(
        'The app cannot access this job on Pollination. Ensure the url is '
        'correct. In case the job is from a private project you will need to '
        'provide an API key to the app.\n\n :point_left: See the sidebar for '
        'more information.'
    )
    st.stop()


@st.cache(suppress_st_warning=True)
def download_results(job: Job) -> pathlib.Path:
    """Download all of the SQL files associated with the results of a job."""
    df = job.runs_dataframe.dataframe
    job_id = job.id
    runs = job.runs
    results_folder = pathlib.Path('data', job_id)
    progress_bar = st.progress(0)
    total_run = len(runs)
    for count, (index, row) in enumerate(df.iterrows()):
        run = runs[count]
        progress_bar.progress((count + 1) / total_run)
        run_folder = results_folder.joinpath(run.id)
        run_folder.mkdir(parents=True, exist_ok=True)
        try:
            # download the sql output
            sql_zip = run.download_zipped_output('sql')
            with zipfile.ZipFile(sql_zip) as zip_folder:
                zip_folder.extractall(run_folder.as_posix())
            # load model and save it to a vtkjs file
            model_dict = json.load(job.download_artifact(row.model))
            hb_model = HBModel.from_dict(model_dict)
            model = Model(hb_model)
            model.to_vtkjs(run_folder, 'model')
        except HTTPError:
            st.warning(
                'Some of the runs of the job have failed.\n'
                'It may not be possible to scroll through all results.'
            )
    progress_bar.empty()


@st.cache
def extract_user_inputs(job: Job):
    """Extract the various combinations of user inputs for a job."""
    # variables to be used while looping through the runs
    input_map, all_inputs = {}, {}
    avoid_inputs = (
        'additional-string', 'ddy', 'epw', 'model', 'units', 'viz-variables')

    # loop through the runs and find all unique user inputs
    for run in job.runs:
        inp_key = []
        for inp in run.status.inputs:
            if inp.name not in avoid_inputs:
                try:
                    inp_key.append(float(inp.value))
                except (TypeError, ValueError):  # not numerical values
                    inp_key.append(inp.value)
                try:
                    all_inputs[inp.name].add(inp.value)
                except KeyError:
                    all_inputs[inp.name] = {inp.value}
        input_map[tuple(inp_key)] = run.id

    # clean and sort the all_inputs variable
    input_set = {}
    for inp_name, inp_vals in all_inputs.items():
        try:
            input_set[inp_name] = sorted([float(v) for v in inp_vals])
        except (TypeError, ValueError):  # not numerical values
            input_set[inp_name] = list(inp_vals)

    return input_map, input_set


def build_sliders(input_set):
    """Create the slider objects from the user inputs"""
    sliders_ui = []
    for inp_name, inp_vals in input_set.items():
        sl = st.sidebar.select_slider(
            label=inp_name, options=inp_vals, key=inp_name)
        sliders_ui.append(sl)
    return sliders_ui


def load_eui_from_sql(job_id, run_id):
    """Get a dictionary of end uses from an SQL file."""
    sql_path = os.path.join('.', 'data', job_id, run_id, 'eplusout.sql')
    sql_obj = SQLiteResult(sql_path)
    # get the total floor area of the model
    area_dict = sql_obj.tabular_data_by_name('Building Area')
    areas = tuple(area_dict.values())
    total_floor_area = areas[0][0]
    # get the energy use
    total_energy, end_uses = 0, {}
    eui_dict = sql_obj.tabular_data_by_name('End Uses By Subcategory')
    for catgory, vals in eui_dict.items():
        total_use = sum([val for val in vals[:12]])
        if total_use != 0:
            total_energy += total_use
            cat, sub_cat = catgory.split(':')
            eu_cat = cat if sub_cat == 'General' or sub_cat == 'Other' \
                else sub_cat
            try:
                end_uses[eu_cat] += total_use
            except KeyError:
                end_uses[eu_cat] = total_use
    # assemble all of the results into a final dictionary
    result_dict = {
        'eui': round(total_energy / total_floor_area, 3),
        'total_floor_area': total_floor_area,
        'total_energy': round(total_energy, 3)
    }
    result_dict['end_uses'] = {key: round(val / total_floor_area, 3)
                               for key, val in end_uses.items()}
    return result_dict


def load_peak_from_sql(job_id, run_id):
    """Get a dictionary of end uses from an SQL file."""
    sql_path = os.path.join('.', 'data', job_id, run_id, 'eplusout.sql')
    sql_obj = SQLiteResult(sql_path)
    base = {}
    base['cooling'] = [z.calculated_design_load for z in sql_obj.zone_cooling_sizes]
    base['heating'] = [z.calculated_design_load for z in sql_obj.zone_heating_sizes]
    return base


@st.cache(suppress_st_warning=True)
def add_viewer(job_id, run_id, count):
    """Add a viewer of the model to the scene."""
    return st_vtkjs(
        pathlib.Path('data', job_id, run_id, 'model.vtkjs').read_bytes(),
        key=str(count) + run_id
    )


if job is not None:
    # download the result files and get all of the user inputs
    with st.spinner('Downloading files...'):
        download_results(job)
    with st.spinner('Building sliders ...'):
        input_map, input_set = extract_user_inputs(job)

    # build the sliders from the various combinations of user inputs
    sliders_ui = build_sliders(input_set)

    # listen to the sliders and use them to compute the EUI values to display
    run_id = input_map[tuple(sliders_ui)]
    eui_dict = load_eui_from_sql(job.id, run_id)
    peak_dict = load_peak_from_sql(job.id, run_id)

    # create columns to display the resulting data
    graphics = ['image', 'bar chart', 'another chart']
    for count, column in enumerate(st.columns(3)):
        if count == 2:
            with column:
                peak_heat = sum(peak_dict['heating'])
                peak_cool = sum(peak_dict['cooling'])
                peak_data = DataFrame([peak_cool, peak_heat])
                st.header('Cooling: {} W | Heating: {} W'.format(
                    round(peak_cool), round(peak_heat)))
                st.bar_chart(peak_data, height=600)
        elif count == 1:
            with column:
                eui_data = DataFrame([[v for v in eui_dict['end_uses'].values()]])
                eui_data.columns = list(eui_dict['end_uses'].keys())
                st.header('EUI: {} kWh/m2'.format(eui_dict['eui']))
                st.bar_chart(eui_data, height=600)
        else:
            with column:
                add_viewer(job.id, run_id, count)
