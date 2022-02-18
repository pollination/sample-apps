from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D
import pathlib

from dragonfly.model import Model, Building
# We can use Dragonfly parameters instead
# from dragonfly.windowparameter import SimpleWindowRatio, RectangularWindows
# from dragonfly.shadingparameter import LouversByDistance, Overhang
from dragonfly.story import Story, Room2D

from streamlit_vtkjs import st_vtkjs
from honeybee_vtk.model import Model as VTKModel, DisplayMode


def generate_3d_model(room_2ds, height, wwr):
    rooms = []
    for space, vertices in room_2ds.items():
        pl = [Point3D(v[0], v[1], 0) for v in vertices]
        rooms.append(
            Room2D(space, Face3D(pl), floor_to_ceiling_height=height)
        )

    tolerance = 0.01
    story = Story('GroundFloor', room_2ds=rooms)
    story.intersect_room_2d_adjacency(tolerance)
    story.solve_room_2d_adjacency(tolerance)
    # use simple ratio parameter object
    # story.set_outdoor_window_parameters()
    building = Building('ArchitextBuilding', unique_stories=[story])
    model = Model('ArchitextModel', buildings=[building])

    hb_model = model.to_honeybee(object_per_model='Building')[0]
    hb_model.wall_apertures_by_ratio(wwr)

    vtk_model = VTKModel(hb_model) 

    vtk_file = vtk_model.to_vtkjs(
        folder='.', name='option_1',
        model_display_mode=DisplayMode.Surface
    )

    return vtk_file, hb_model


def add_viewer(vtk_file):
    try:
        # newer version
        st_vtkjs('lala', content=pathlib.Path(vtk_file).read_bytes(), menu=False)
    except:
        # fall back to the older version
        st_vtkjs(key='lala', file=pathlib.Path(vtk_file).read_bytes(), menu=False)
