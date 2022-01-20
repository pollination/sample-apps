import json

try:  # import the ladybug dependencies
    from ladybug.location import Location
    from ladybug_geometry.geometry2d.pointvector import Point2D
    from ladybug_geometry.geometry3d.face import Face3D
    from ladybug_geometry.geometry3d.mesh import Mesh3D
    from ladybug_geometry.geometry3d.pointvector import Point3D
    from ladybug_geometry.geometry3d.polyface import Polyface3D
except ImportError as e:
    raise ImportError('\nFailed to import ladybug_geometry:\n\t{}'.format(e))

try:  # import the core dragonfly dependencies
    from dragonfly.projection import (lon_lat_to_polygon,
                                      meters_to_long_lat_factors,
                                      origin_long_lat_from_location)
except ImportError as e:
    raise ImportError('\nFailed to import dragonfly:\n\t{}'.format(e))

def get_json_array(data, lat, lon):
    # set base point and location
    pt = Point2D(0, 0)
    location = Location(longitude=lon, latitude=lat)

    # parse the geoJSON into a dictionary and get lat/lon converters
    origin_lon_lat = origin_long_lat_from_location(location, pt)
    _convert_facs = meters_to_long_lat_factors(origin_lon_lat)
    convert_facs = 1 / _convert_facs[0], 1 / _convert_facs[1]

    # get all features
    geo_types = ('LineString', 'Polygon')
    geo_data = [geo for geo in data['features'] if 'geometry' in geo
                and geo['geometry']['type'] in geo_types and
                'height' in geo['properties']]

    height = [geo['properties']['height'] for 
              geo in data['features'] if 'height' in geo['properties']]

    # convert all of the geoJSON to ladybug geometry
    buildings = []
    for geo_dat, h in zip(geo_data, height):
        coords = lon_lat_to_polygon(geo_dat['geometry']['coordinates'][0],
                                    origin_lon_lat, convert_facs)
        pts = tuple(Point3D(pt[0], pt[1], 0) for pt in coords)
        face = Face3D(pts, enforce_right_hand=True)
        polyface = Polyface3D.from_offset_face(face, -h)

        buildings.append(polyface.to_dict())

    return json.dumps(buildings)
