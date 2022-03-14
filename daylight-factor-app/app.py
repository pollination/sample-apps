import json
import pathlib
import zipfile
from uuid import uuid4
from query import Query

import streamlit as st
from honeybee.model import Model, Room
from honeybee_radiance.properties.model import ModelRadianceProperties
from honeybee_radiance.sensorgrid import SensorGrid
from honeybee_vtk.model import DisplayMode
from honeybee_vtk.model import Model as VTKModel
from honeybee_vtk.vtkjs.schema import SensorGridOptions
from queenbee.job.job import JobStatusEnum
from streamlit_autorefresh import st_autorefresh
from pollination_streamlit.api.client import ApiClient
from pollination_streamlit.interactors import Job, NewJob, Recipe
from streamlit_vtkjs import st_vtkjs

pathlib.Path(__file__).parent.joinpath('data').mkdir(exist_ok=True)


st.set_page_config(
    page_title='Daylight Factor App', layout='wide',
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


@st.cache(suppress_st_warning=True)
def view_results(owner, project, job_id, api_key):
    client = ApiClient(api_token=api_key)
    job = Job(owner, project, job_id, client)

    run = job.runs[0]
    input_model_path = job.runs_dataframe.dataframe['model'][0]

    output_folder = pathlib.Path('data', run.id)
    res_folder = output_folder.joinpath('results')
    res_folder.mkdir(parents=True, exist_ok=True)
    res_zip = run.download_zipped_output('results')
    with zipfile.ZipFile(res_zip) as zip_folder:
        zip_folder.extractall(res_folder.as_posix())

    cfg = {
        "data": [
            {
                "identifier": "Daylight factor",
                "object_type": "grid",
                "unit": "Percentage",
                "path": res_folder.as_posix(),
                "hide": False,
                "legend_parameters": {
                        "hide_legend": False,
                        "min": 0,
                        "max": 10,
                        "color_set": "nuanced",
                        "label_parameters": {
                            "color": [34, 247, 10],
                            "size": 0,
                            "bold": True
                        }
                }
            }
        ]
    }

    config_file = output_folder.joinpath('config.json')
    config_file.write_text(json.dumps(cfg))
    model_dict = json.load(job.download_artifact(input_model_path))
    hb_model = Model.from_dict(model_dict)
    res_model = VTKModel(hb_model, SensorGridOptions.Sensors)
    vtkjs_file = pathlib.Path(output_folder.as_posix(), f'model.vtkjs')
    if not vtkjs_file.is_file():
        res_model.to_vtkjs(folder=output_folder.as_posix(), name='model',
                              config=config_file.as_posix(),
                              model_display_mode=DisplayMode.Wireframe)
    return vtkjs_file


query = Query()

query.owner = st.sidebar.text_input(
    'Project Owner', value=query.owner
)

query.project = st.sidebar.text_input(
    'Project Name', value=query.project
)

run_simulation = st.sidebar.button('Run Simulation')
api_client = ApiClient(api_token=api_key)


c1, c2, c3 = st.columns([1, 1, 2])

query.width = c1.slider(
    label='Width of the room', min_value=4, max_value=20,
    value=query.width,
)

query.depth = c2.slider(
    label='Depth of the room', min_value=4, max_value=20,
    value=query.depth,
)

query.glazing_ratio = c1.slider(
    label='Glazing ratio', min_value=0.1, max_value=0.9,
    value=query.glazing_ratio,
)
room = Room.from_box(
    identifier=str(uuid4()),
    width=query.width,
    depth=query.depth,
)
room.wall_apertures_by_ratio(query.glazing_ratio)

grid = SensorGrid.from_mesh3d(str(uuid4()), room.generate_grid(x_dim=0.5))
model = Model(identifier=query.model_id, rooms=[room])
model._properties._radiance = ModelRadianceProperties(model, [grid])
model_path = model.to_hbjson(name=model.identifier, folder='data')
vtk_path = pathlib.Path('data', f'{model.identifier}.vtkjs')
if not vtk_path.is_file():
    VTKModel.from_hbjson(model_path, SensorGridOptions.Sensors).to_vtkjs(
        folder='data', name=model.identifier)

with c3:
    st_vtkjs(
        content=vtk_path.read_bytes(),
        key=model.identifier, subscribe=False
    )


if run_simulation:
    query.job_id = None

    recipe = Recipe('ladybug-tools', 'daylight-factor',
                    'latest', api_client)
    new_job = NewJob(query.owner, query.project, recipe, client=api_client)
    model_project_path = new_job.upload_artifact(
        pathlib.Path(model_path), 'streamlit-job')
    new_job.arguments = [
        {'width': query.width, 'depth': query.depth,
            'glazing-ration': query.glazing_ratio, 'model': model_project_path}
    ]
    job = new_job.create()

    query.job_id = job.id

    if query.job_id is not None and query.owner is not None and query.project is not None:

        job = Job(query.owner, query.project, query.job_id, client=api_client)

        st.write(
            f'Checkout your job [here](https://app.pollination.cloud/projects/{query.owner}/{query.project}/jobs/{query.job_id})')

        if job.status.status in [
                JobStatusEnum.pre_processing,
                JobStatusEnum.running,
                JobStatusEnum.created,
                JobStatusEnum.unknown]:
            with st.spinner(text="Simulation in Progres..."):
                st.warning(f'Simulation is {job.status.status.value}...')
                st_autorefresh(interval=2000, limit=100)

        elif job.status.status in [JobStatusEnum.failed, JobStatusEnum.cancelled]:
            st.warning(f'Simulation is {job.status.status.value}')
        else:
            job.runs_dataframe.parameters
            res_model_path = view_results(
                query.owner, query.project, query.job_id, api_key)
            st_vtkjs(
                content=pathlib.Path(res_model_path).read_bytes(), key='results',
                subscribe=False
            )
