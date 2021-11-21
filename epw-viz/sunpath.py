from ladybug.sunpath import Sunpath, Point3D, Vector3D
from ladybug.color import Color

from honeybee_vtk.to_vtk import convert_polyline, create_polyline
from honeybee_vtk.vtkjs.schema import IndexJSON
from honeybee_vtk.vtkjs.helper import convert_directory_to_zip_file
from honeybee_vtk.types import ModelDataSet

import math
import tempfile
import os
import shutil
import pathlib


from streamlit_vtkjs import st_vtkjs


def _to_vtkjs(polydatas, folder: str = '.', name: str = None) -> str:
    """Write a list of polydata a vtkjs file.

    This is a hack for now until we can support visualizing vtk and vtp files
    This will be replaced with functions from ladybug-vtk in the near future.

    Args:
        polydatas: A list of polydata objects.
        folder: A valid text string representing the location of folder where
            you'd want to write the vtkjs file. Defaults to current working
            directory.
        name : Name for the vtkjs file. File name will be Model.vtkjs if not
            provided.

    Returns:
        A text string representing the file path to the vtkjs file.
    """

    # name of the vtkjs file
    file_name = name or 'model'
    # create a temp folder
    temp_folder = tempfile.mkdtemp()
    # The folder set by the user is the target folder
    target_folder = os.path.abspath(folder)
    if not os.path.exists(target_folder):
        os.makedirs(target_folder, exist_ok=True)
    # Set a file path to move the .zip file to the target folder
    target_vtkjs_file = os.path.join(target_folder, file_name + '.vtkjs')

    # write
    data = ModelDataSet(file_name, polydatas, color=Color())
    path = data.to_folder(temp_folder)
    if path:
        scene = [data.as_data_set()]
    else:
        scene = []

    # write index.json
    index_json = IndexJSON()
    index_json.scene = scene
    index_json.to_json(temp_folder)

    # zip as vtkjs
    temp_vtkjs_file = convert_directory_to_zip_file(temp_folder, extension='vtkjs',
                                                    move=False)

    # Move the generated vtkjs to target folder
    shutil.move(temp_vtkjs_file, target_vtkjs_file)

    try:
        shutil.rmtree(temp_folder)
    except Exception:
        pass

    return target_vtkjs_file


def _create_sunpath(location, folder='./data'):
    """Create sunpath as a vtkjs file for 3D visualization.

    NOTE: This method will be replaced by ladybug-vtk in the near future.
    """

    # Initiate sunpath
    # We can eventually extend ladybug-geometry to support the translation to VTK
    sp = Sunpath.from_location(location)

    radius = 100
    origin = Point3D(0, 0, 0)
    north = origin.move(Vector3D(0, radius, 0))
    polylines = sp.hourly_analemma_polyline3d(
        origin=origin, daytime_only=True, radius=radius)
    sp_pls = [convert_polyline(pl) for pl in polylines]

    # TODO: add support for creating arcs
    # daily_pls = sp.monthly_day_arc3d(origin=origin, radius=radius, daytime_only=True)

    # add a circle
    plot_points = [
        north.rotate_xy(math.radians(angle), origin)
        for angle in range(0, 365, 5)
    ]

    plot = create_polyline(plot_points)
    # add plot
    sp_pls.append(plot)
    vtkjs_file = _to_vtkjs(
        sp_pls,
        folder=folder,
        name=f'{location.latitude}_{location.longitude}' # create a unique name
    )
    return vtkjs_file


def st_sunpath(location):
    """Create a streamlit sunpath using vtkjs-streamlit."""
    spf = _create_sunpath(location)
    inf = pathlib.Path(spf)
    return st_vtkjs(inf.read_bytes(), True)
