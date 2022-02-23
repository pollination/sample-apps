"""Functions to help the Sunpath app."""

import csv
import pathlib

import streamlit as st

from typing import List, Dict
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.sunpath import Sunpath, Location
from ladybug.color import Color
from ladybug.epw import EPW, EPWFields


@st.cache()
def epw_fields() -> Dict[str, int]:
    """Get a dictionary of EPW fields and their corresponding numbers.

    The reason for using the fields from 6 to 34 is that 0 to 5 fields are;
    0 year, 1 month, 2 day, 3 hour, 4 minute, 5 Uncertainty Flags. And we're not
    interested in those fields.
    """
    return {EPWFields._fields[i]['name'].name: i for i in range(6, 35)}


st.cache(suppress_st_warning=True)
def sunpath_by_location(location: Location, north_angle: int) -> Sunpath:
    return Sunpath.from_location(location, north_angle=north_angle)


st.cache(suppress_st_warning=True)
def sunpath_by_lat_long(latitude: float, longitude: float, north_angle: int) -> Sunpath:
    """Get a Sunpath object.

    Args:
        latitude: A float number for latitude.
        longitude: A float number for longitude.
        north_angle: An integer for north angle in degrees.

    Returns:
        A ladybug Sunpath object.
    """
    return Sunpath(latitude, longitude, north_angle=north_angle)


def get_data(selection: List[str], fields: Dict[str, int], epw: EPW = None) -> \
        List[HourlyContinuousCollection]:
    """Get data to mount on sunpath and the CSV report.

    Args:
        selection: The list of selected values.
        fields: A dictionary of EPW variable to epw field (a number) structure.
        epw: An EPW object.

    Returns:
        A list of ladybug HourlyContinuousCollection objects.
    """

    data = [epw._get_data_by_field(fields[var]) for var in selection]

    return data


def get_sunpath_vtkjs(
    sunpath: Sunpath,
    file_path: pathlib.Path,
    projection: int = 3,
    data: List[HourlyContinuousCollection] = None
) -> pathlib.Path:
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

    folder = file_path.parent
    folder.mkdir(parents=True, exist_ok=True)
    name = file_path.stem

    make_2d = True if projection == 2 else False
    sp_vtkjs = sunpath.to_vtkjs(
        folder.as_posix(), file_name=name, data=data, sun_color=sun_color,
        make_2d=make_2d
    )

    return sp_vtkjs


def write_csv_file(
    sunpath: Sunpath,
    location: Location = None,
    data: List[HourlyContinuousCollection] = None
) -> str:
    """Write a csv file with the Sunpath data and EPW data if provided.

    Args:
        sunpath: A ladybug Sunpath object.
        location: A Ladybug location.
        data: A list of ladybug hourly data mounted on the sunpath. Default is None.

    Returns:
        CSV file path.
    """

    filename: str = './data/sunpath.csv'
    header: List[str] = ['Month', 'Day', 'Hour', 'Altitude', 'Azimuth']

    with open(filename, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        # writing header of the csv file
        if location:
            csv_writer.writerow(['City', location.city])
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
