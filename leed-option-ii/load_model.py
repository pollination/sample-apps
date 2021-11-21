"""Load HBJSON model with data.

We should probably package this as a helper function in honeybee-vtk or even
insider pollination-streamlit. I imagine it will be used frequently.
"""
import pathlib
from typing import Dict
from honeybee_vtk.model import HBModel, Model, SensorGridOptions, DisplayMode
from honeybee_vtk.config import load_config
from honeybee_vtk.scene import Scene
from honeybee_vtk.camera import Camera
from honeybee_vtk.actor import Actor


def get_model_with_results(
        model_dict: Dict, file_path: pathlib.Path,
        config_file: str = None, display_mode='Shaded'
    ):
    hb_model = HBModel.from_dict(model_dict)
    model = Model(hb_model, SensorGridOptions.Sensors)

    if display_mode == 'shaded':
        model.update_display_mode(DisplayMode.Shaded)
    elif display_mode == 'surface':
        model.update_display_mode(DisplayMode.Surface)
    elif display_mode == 'surfacewithedges':
        model.update_display_mode(DisplayMode.SurfaceWithEdges)
    elif display_mode == 'wireframe':
        model.update_display_mode(DisplayMode.Wireframe)
    elif display_mode == 'points':
        model.update_display_mode(DisplayMode.Points)

    if config_file:
        scene = Scene()
        actors = Actor.from_model(model)
        bounds = Actor.get_bounds(actors)
        centroid = Actor.get_centroid(actors)
        cameras = Camera.aerial_cameras(bounds=bounds, centroid=centroid)
        scene.add_actors(actors)
        scene.add_cameras(cameras)
        model = load_config(config_file, model, scene)

    return model.to_vtkjs(file_path.parent, file_path.stem)
