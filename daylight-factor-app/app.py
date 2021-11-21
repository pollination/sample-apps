import json
import pathlib
import zipfile
from typing import Any, Dict
from uuid import uuid4

import streamlit as st
from honeybee.model import Model, Room
from honeybee_radiance.properties.model import ModelRadianceProperties
from honeybee_radiance.sensorgrid import SensorGrid
from honeybee_vtk.actor import Actor
from honeybee_vtk.camera import Camera
from honeybee_vtk.config import load_config
from honeybee_vtk.model import DisplayMode
from honeybee_vtk.model import Model as VTKModel
from honeybee_vtk.model import SensorGridOptions
from honeybee_vtk.scene import Scene
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

api_client = ApiClient(api_token=api_key)


class Query:

    _defaults = {
        'width': 10,
        'depth': 10,
        'glazing_ratio': 0.4,
        'job_id': None
    }

    def __init__(self):
        self._query_params = st.experimental_get_query_params()
        self._width = int(self._query_params.get('width', [10])[0])
        self._depth = int(self._query_params.get('depth', [10])[0])
        self._glazing_ratio = float(
            self._query_params.get('glazing-ration', [0.4])[0])
        self._job_id = self._query_params.get('job-id', [None])[0]
        self._owner = self._query_params.get('owner', [None])[0]
        self._project = self._query_params.get('project', [None])[0]
        self.model_id = self._query_params.get('model-id', [str(uuid4())])[0]

        self._update_query()

    @property
    def query_params(self):
        params = {
            'width': self._width,
            'depth': self._depth,
            'glazing-ratio': self._glazing_ratio,
            'model-id': self.model_id
        }

        if self._job_id is not None:
            params['job-id'] = self._job_id
        if self._owner is not None:
            params['owner'] = self._owner
        if self._project is not None:
            params['project'] = self._project

        return params

    def _update_query(self):
        st.experimental_set_query_params(**self.query_params)

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self._update_query()

    @property
    def depth(self):
        return self._depth

    @depth.setter
    def depth(self, value):
        self._depth = value
        self._update_query()

    @property
    def glazing_ratio(self):
        return self._glazing_ratio

    @glazing_ratio.setter
    def glazing_ratio(self, value):
        self._glazing_ratio = value
        self._update_query()

    @property
    def job_id(self):
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        self._job_id = value
        self._update_query()

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, value):
        self._owner = value
        self._update_query()

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, value):
        self._project = value
        self._update_query()


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
                "identifier": "Daylight factor...nuanced",
                "object_type": "grid",
                "unit": "Percentage",
                "path": res_folder.as_posix(),
                "hide": False,
                "legend_parameters": {
                        "hide_legend": False,
                        "min": 0,
                        "max": 20,
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
    res_model.update_display_mode(DisplayMode.Wireframe)
    scene = Scene()
    actors = Actor.from_model(res_model)
    bounds = Actor.get_bounds(actors)
    centroid = Actor.get_centroid(actors)
    cameras = Camera.aerial_cameras(bounds=bounds, centroid=centroid)
    scene.add_actors(actors)
    scene.add_cameras(cameras)
    res_model = load_config(config_file, res_model, scene)

    return res_model.to_vtkjs(output_folder.as_posix(), 'model')


query = Query()

with st.expander('Model Configuration'):
    c1, c2, c3 = st.columns(3)

    query.width = c1.slider(
        label='Width of the room', min_value=4, max_value=20,
        value=query.width,
    )

    query.depth = c2.slider(
        label='Depth of the room', min_value=4, max_value=20,
        value=query.depth,
    )

    query.glazing_ratio = c3.slider(
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
    vtk_path = VTKModel.from_hbjson(model_path, SensorGridOptions.Sensors).to_vtkjs(
        folder='data', name=model.identifier)

    st_vtkjs(
        pathlib.Path(vtk_path).read_bytes(),
        key=model.identifier
    )

with st.expander('Simulation'):

    c1, c2, c3 = st.columns(3)

    query.owner = c1.text_input(
        'Project Owner', value=query.owner
    )

    query.project = c2.text_input(
        'Project Name', value=query.project
    )

    if c3.button('Run Simulation'):
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
            st_vtkjs(pathlib.Path(res_model_path).read_bytes(), key='results')
