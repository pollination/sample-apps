import pathlib
import json

import streamlit as st

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D

from dragonfly.model import Model, Building
# We can use Dragonfly parameters instead - this will make the app easier to use
# from dragonfly.windowparameter import SimpleWindowRatio, RectangularWindows
# from dragonfly.shadingparameter import LouversByDistance, Overhang
from dragonfly.story import Story, Room2D

from streamlit_vtkjs import st_vtkjs
from honeybee_vtk.model import Model as VTKModel, DisplayMode


st.cache(suppress_st_warning=True)
def generate_3d_model(height, wwr, design_id):
    layout = st.session_state['architext_layout']
    room_2ds = json.loads(layout['data'][1])
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
    vtk_file = pathlib.Path('data', f'{design_id}_{height}_{wwr}.vtkjs')
    if not vtk_file.is_file():
        vtk_file.parent.mkdir(parents=True, exist_ok=True)
        vtk_model.to_vtkjs(
            folder=vtk_file.parent, name=vtk_file.stem,
            model_display_mode=DisplayMode.Surface
        )

    return vtk_file, hb_model


def add_viewer(vtk_file):
    st_vtkjs(
        '3d_viewer', content=pathlib.Path(vtk_file).read_bytes(), toolbar=False,
        style={'height': '500px'}, subscribe=False
    )
