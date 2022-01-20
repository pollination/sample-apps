import streamlit as st
from dragonfly.room2d import Room2D
from dragonfly.model import Model as dgModel
from dragonfly.building import Building
from ladybug_geometry.geometry2d import Point2D
from honeybee.boundarycondition import Outdoors
from honeybee.orientation import (angles_from_num_orient, 
  orient_index)
from honeybee.room import Room
from dragonfly.windowparameter import SimpleWindowRatio
from honeybee.model import Model
from pollination_streamlit_io import button

# create a first room
identifier = "my-first-room"
vertices = [
  Point2D(0,0),
  Point2D(10,0),
  Point2D(10,10),
  Point2D(0,10)
]
floor_height=0
floor_to_ceiling_height=3

my_first_room = Room2D.from_vertices(
  identifier=identifier,
  vertices=vertices,
  floor_height=floor_height,
  floor_to_ceiling_height=floor_to_ceiling_height,
  is_ground_contact=True,
  is_top_exposed=True
)

# create a second room
identifier = "my-second-room"
vertices = [
  Point2D(10,0),
  Point2D(20,0),
  Point2D(20,10),
  Point2D(10,10)
]
floor_height=0
floor_to_ceiling_height=3

my_second_room = Room2D.from_vertices(
  identifier=identifier,
  vertices=vertices,
  floor_height=floor_height,
  floor_to_ceiling_height=floor_to_ceiling_height,
  is_ground_contact=True,
  is_top_exposed=True
)

# intersect and solve adjacency
room_2ds = [my_first_room, my_second_room]
room_2ds = Room2D.intersect_adjacency(room_2ds)
adj_info = Room2D.solve_adjacency(room_2ds)

# add apertures
win_ratios = [0.1, 0.2, 0.3, 0.4]

win_par = [SimpleWindowRatio(r) for r in win_ratios]
angles = angles_from_num_orient(len(win_par))
for room in room_2ds:
    room_win_par = []
    for bc, orient in zip(room.boundary_conditions, room.segment_orientations()):
        orient_i = orient_index(orient, angles)
        win_p = win_par[orient_i] if isinstance(bc, Outdoors) else None
        room_win_par.append(win_p)
    room.window_parameters = room_win_par

# get honeybee rooms
hb_rooms = [r.to_honeybee()[0] for r in room_2ds]
# solve adjacency with honeybee
adj_info = Room.solve_adjacency(hb_rooms)

# generate hbmodel
identifier = "my-streamlit-model"
my_model = Model(identifier=identifier,
  rooms=hb_rooms,
  units='Meters')

# rhino integration!
query = st.experimental_get_query_params()
platform = query['__platform__'][0] if '__platform__' in query else 'web'

if platform == 'Rhino':
  button.send('BakePollinationModel',
          my_model.to_dict(), 'my-secret-key', 
          key='my-secret-key')