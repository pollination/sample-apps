"""Functions to help the Sunpath app."""

import csv
import pathlib

import streamlit as st

from typing import List, Tuple, Union, cast
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.sunpath import Sunpath
from ladybug.color import Color
from ladybug.epw import EPW


def epw_hash_func(epw: EPW) -> str:
    """Help streamlit hash an EPW object."""
    return epw.location.city if epw else ''


def hourly_data_hash_func(data: HourlyContinuousCollection) -> str:
    """Help streamlit hash a HourlyContinuousCollection object."""
    return data.header.data_type, data.average, data.min, data.max


def sunpath_hash_func(sunpath: Sunpath) -> str:
    """Help streamlit hash a Sunpath object."""
    return sunpath.latitude, sunpath.longitude, sunpath.north_angle


@st.cache(hash_funcs={Sunpath: sunpath_hash_func, EPW: epw_hash_func})
def get_sunpath(latitude: float, longitude: float, north: int) -> Sunpath:
    """Get latitude and longitude to plot Sunpath."""
    return Sunpath(latitude, longitude, north_angle=north)


@st.cache(hash_funcs={EPW: epw_hash_func, HourlyContinuousCollection: hourly_data_hash_func},
          allow_output_mutation=True)
def get_data(selection: List[bool], fields: dict, epw: EPW = None) -> List[HourlyContinuousCollection]:
    """Get data to load on sunpath and CSV report.

    Args:
        selection: A list of booleans. The values from fields will be chosen based on the
            True values in this list.
        fields: A dictionary of EPW variable to epw field (a number) structure.
        epw: An EPW object.

    Returns:
        A list of ladybug HourlyContinuousCollection objects.
    """
    if any(selection) and not epw:
        load_data = False
    elif not any(selection) and epw:
        load_data = False
    else:
        load_data = True

    if load_data:
        data = []
        for count, var in enumerate(selection):
            if var:
                data.append(epw._get_data_by_field(
                    fields[list(fields.keys())[count]]))
    else:
        data = []

    return data


def get_sunpath_vtkjs(sunpath: Sunpath, projection: int = 3,
                      data: List[HourlyContinuousCollection] = None) -> Tuple[
                          pathlib.Path, Color]:
    """Create a VTKJS sunpath.

    Args:
        sunpath: A ladybug Sunpath object.
        projection: An integer to indicate the projection type. Default is 3D projection.
        data: A list of ladybug HourlyContinuousCollection objects. Default is None.

    Returns:
        A tuple of two objects:

        -  A pathlib.Path object of the VTKJS file.

        -  A ladybug Color object for sun color.
    """

    sun_color = Color(235, 33, 38)
    folder = pathlib.Path('./data')

    folder.mkdir(parents=True, exist_ok=True)
    name = f'{sunpath.latitude}_{sunpath.longitude}_{sunpath.north_angle}'

    if projection == 3:
        sp_vtkjs = sunpath.to_vtkjs(folder.as_posix(), file_name=name,
                                    data=data, sun_color=sun_color)
    else:
        sp_vtkjs = sunpath.to_vtkjs(folder.as_posix(), file_name=name,
                                    data=data, sun_color=sun_color, make_2d=True)

    return sp_vtkjs, sun_color


@st.cache(hash_funcs={Sunpath: sunpath_hash_func, EPW: epw_hash_func,
                      HourlyContinuousCollection: hourly_data_hash_func})
def write_csv_file(sunpath: Sunpath, epw: EPW = None,
                   data: List[HourlyContinuousCollection] = None) -> str:
    """Write a csv file with the Sunpath data and EPW data if provided.

    Args:
        sunpath: A ladybug Sunpath object.
        epw: An EPW object.
        data: A list of ladybug HourlyContinuousCollection objects. Default is None.

    Returns:
        CSV file path.
    """

    filename = './data/sunpath.csv'
    header = ['Month', 'Day', 'Hour', 'Altitude', 'Azimuth']

    # writing to csv files
    with open(filename, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        if epw:
            csv_writer.writerow(['City', epw.location.city])
        csv_writer.writerow(['Latitude', str(sunpath.latitude)])
        csv_writer.writerow(['Longitude', str(sunpath.longitude)])

        if data:
            data_headers = [dt.header.data_type for dt in data]
            header.extend(data_headers)
            csv_writer.writerow(header)
        else:
            csv_writer.writerow(header)

        # write values for all hours of the year
        for hr in range(8760):
            sun = sunpath.calculate_sun_from_hoy(hr)
            date_time = sun.datetime

            if data:
                csv_writer.writerow([date_time.month, date_time.day,
                                    date_time.hour, sun.altitude, sun.azimuth] +
                                    [dt.values[hr] for dt in data])
            else:
                csv_writer.writerow([date_time.month, date_time.day,
                                    date_time.hour, sun.altitude, sun.azimuth])

    return filename
