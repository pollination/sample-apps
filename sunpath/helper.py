"""Functions to help the Sunpath app."""

import csv
import pathlib

import streamlit as st

from typing import List, Tuple, Dict
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.sunpath import Sunpath
from ladybug.color import Color
from ladybug.epw import EPW, EPWFields


def epw_hash_func(epw: EPW) -> str:
    """Help streamlit hash an EPW object."""
    return epw.location.city if epw else ''


def hourly_data_hash_func(data: HourlyContinuousCollection) -> Tuple[str, float, float,
                                                                     float]:
    """Help streamlit hash a HourlyContinuousCollection object."""
    return data.header.data_type.name, data.average, data.min, data.max


def sunpath_hash_func(sunpath: Sunpath) -> Tuple[float, float, float]:
    """Help streamlit hash a Sunpath object."""
    return sunpath.latitude, sunpath.longitude, sunpath.north_angle


@st.cache()
def epw_fields() -> Dict[str, int]:
    """Get a dictionary of EPW fields and their corresponding numbers.

    The reason for using the fields from 6 to 34 is that 0 to 5 fields are;
    0 year, 1 month, 2 day, 3 hour, 4 minute, 5 Uncertainty Flags. And we're not
    interested in those fields.
    """
    return {EPWFields._fields[i]['name'].name: i for i in range(6, 35)}


@st.cache(hash_funcs={Sunpath: sunpath_hash_func, EPW: epw_hash_func})
def get_sunpath(latitude: float, longitude: float, north_angle: int,
                epw: EPW = None) -> Sunpath:
    """Get a Sunpath object.

    Args:
        latitude: A float number for latitude.
        longitude: A float number for longitude.
        north_angle: An integer for north angle in degrees.
        epw: An ladybug EPW object. Default is None.

    Returns:
        A ladybug Sunpath object.
    """
    if epw:
        return Sunpath.from_location(epw.location)

    return Sunpath(latitude, longitude, north_angle=north_angle)


@st.cache(hash_funcs={EPW: epw_hash_func,
                      HourlyContinuousCollection: hourly_data_hash_func},
          allow_output_mutation=True)
def get_data(selection: List[bool], fields: Dict[str, int], epw: EPW = None) -> \
        List[HourlyContinuousCollection]:
    """Get data to mount on sunpath and the CSV report.

    Args:
        selection: The values from fields (the next argument) will be chosen based on the
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
        for count, var in enumerate(fields):
            if selection[count]:
                data.append(epw._get_data_by_field(fields[var]))
    else:
        data = []

    return data


def get_sunpath_vtkjs(sunpath: Sunpath, projection: int = 3,
                      data: List[HourlyContinuousCollection] = None) -> Tuple[
                          pathlib.Path, Color]:
    """Create a VTKJS sunpath.

    Args:
        sunpath: A ladybug Sunpath object.
        projection: Projection type of the sunpath. 3 would create a 3D projection.
            2 will create a 2D projection. Defaults to 3.
        data: A list of hourly data to mount on the sunpath. Default is None.

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
        data: A list of ladybug hourly data mounted on the sunpath. Default is None.

    Returns:
        CSV file path.
    """

    filename: str = './data/sunpath.csv'
    header: List[str] = ['Month', 'Day', 'Hour', 'Altitude', 'Azimuth']

    with open(filename, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        # writing header of the csv file
        if epw:
            csv_writer.writerow(['City', epw.location.city])
        csv_writer.writerow(['Latitude', str(sunpath.latitude)])
        csv_writer.writerow(['Longitude', str(sunpath.longitude)])

        if data:
            data_headers = [
                f'{dt.header.data_type.name} ({dt.header.unit})' for dt in data]
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
