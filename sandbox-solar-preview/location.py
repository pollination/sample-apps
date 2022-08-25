import streamlit as st
import pandas as pd

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from ladybug_geometry.geometry2d import Point2D
from ladybug.epw import EPW

import pathlib
from math import radians, cos, sin, asin, sqrt

LOCATIONS = {
    'USA_CO_Golden-NREL.724666_TMY3': {'value': 'Denver Golden', 'index': 0},
    'USA_CO_Fort.Collins.AWOS.724769_TMY3': {'value': 'Fort Collins', 'index': 1},
    'USA_CO_Grand.Junction-Walker.Field.724760_TMY3': {'value': 'Grand Junction', 'index': 2},
    'USA_MN_Minneapolis-St.Paul.Intl.AP.726580_TMY3': {'value': 'Minneapolis', 'index': 3},
    'USA_NE_Omaha.WSFO.725530_TMY3': {'value': 'Omaha', 'index': 4},
    'USA_MO_Kansas.City.Downtown.AP.724463_TMY3': {'value': 'Kansas City', 'index': 5},
    'USA_ID_Boise.Air.Terminal.726810_TMY3': {'value': 'Boise', 'index': 6},
    'USA_WA_Seattle-Tacoma.Intl.AP.727930_TMY3': {'value': 'Seattle', 'index': 7},
    'USA_OR_Eugene-Mahlon.Sweet.AP.726930_TMY3': {'value': 'Eugene', 'index': 8},
    'USA_CA_Sacramento.724835_TMY2': {'value': 'Sacramento', 'index': 9},
    'USA_CA_Fresno.Air.Terminal.723890_TMY3': {'value': 'Fresno Yosemite', 'index': 10},
    'USA_CA_San.Diego-Lindbergh.Field.722900_TMY3': {'value': 'San Diego', 'index': 11},
    'USA_NV_Las.Vegas-McCarran.Intl.AP.723860_TMY3': {'value': 'Las Vegas', 'index': 12},
    'USA_AZ_Davis-Monthan.AFB.722745_TMY3': {'value': 'Tucson', 'index': 13},
    'USA_TX_Houston-William.P.Hobby.AP.722435_TMY3': {'value': 'Houston', 'index': 14},
    'USA_OK_Oklahoma.City-Tinker.AFB.723540_TMY3': {'value': 'Oklahoma City', 'index': 15},
    'USA_TN_Memphis.Intl.AP.723340_TMY3': {'value': 'Memphis', 'index': 16},
    'USA_KY_Louisville.Intl.AP.724230_TMY3': {'value': 'Louisville', 'index': 17},
    'USA_IL_Springfield-Capital.AP.724390_TMY3': {'value': 'Springfield IL', 'index': 18},
    'USA_MI_Lansing-Capital.City.AP.725390_TMY3': {'value': 'Lansing', 'index': 19},
    'USA_IA_Des.Moines.Intl.AP.725460_TMY3': {'value': 'Des Moines', 'index': 20},
    'USA_MA_Boston-Logan.Intl.AP.725090_TMY3': {'value': 'Boston', 'index': 21},
    'USA_GA_Atlanta-Hartsfield-Jackson.Intl.AP.722190_TMY3': {'value': 'Atlanta', 'index': 22},
    'USA_VA_Richmond.Intl.AP.724010_TMY3': {'value': 'Richmond', 'index': 23},
    'USA_FL_Miami.Intl.AP.722020_TMY3': {'value': 'Miami', 'index': 24},
    'USA_AK_Juneau.Intl.AP.703810_TMY3': {'value': 'Juneau', 'index': 25},
    'USA_HI_Honolulu.Intl.AP.911820_TMY3': {'value': 'Honolulu', 'index': 26},
    'CAN_ON_Toronto.716240_CWEC': {'value': 'Toronto', 'index': 27},
    'MEX_Mexico.City.766790_IWEC': {'value': 'Cuidad Mexico', 'index': 28},
    'PRI_SJ_San.Juan.994043_TMYx': {'value': 'San Juan', 'index': 29},
}

@st.cache()
def load_location_data(weather_folder):
    # map weather files to human readable location names

    folder = pathlib.Path(weather_folder)
    data = []
    for wf in folder.glob('*.epw'):
        epw = EPW(wf)
        location = epw.location
        data.append(
            {
                'location': Point2D(location.latitude, location.longitude), 'path': wf,
                'info': LOCATIONS[wf.stem]
            }
        )
    return data


def get_distance(user_location: Point2D, location: Point2D):
    return user_location.distance_to_point(location)


def get_location_distance(user_location: Point2D, location: Point2D):
    """Return location distance in miles.
    
    The formula is based on this page:
        https://www.geeksforgeeks.org/program-distance-two-points-earth/
    """
    lon1 = radians(user_location.y)
    lon2 = radians(location.y)
    lat1 = radians(user_location.x)
    lat2 = radians(location.x)
      
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
 
    c = 2 * asin(sqrt(a))
    
    # Radius of earth in kilometers. Use 3956 for miles
    r = 6371

    # calculate the result
    return round(c * r, 2)


@st.cache(suppress_st_warning=True)
def get_location_info(city, country):
    geolocator = Nominatim(user_agent="GTA Lookup")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    location = geolocator.geocode(f'{city}, {country}')
    return location


def add_map(city, country='United States'):

    location = get_location_info(city, country)
    if not location:
        st.error(f'We could not find any information for {city}. Check the location and try again.')
        st.stop()
    lat = location.latitude
    lon = location.longitude

    user_location = Point2D(lat, lon)
    __here__ = pathlib.Path(__file__).parent
    location_data = load_location_data(__here__.joinpath('epw'))

    closet_location = sorted(location_data, key=lambda x:get_distance(x['location'], user_location))[0]

    epw = EPW(closet_location['path'])
    location = epw.location
    map_data = pd.DataFrame(
        {'lat': [lat, location.latitude], 'lon': [lon, location.longitude]}
    )

    st.map(map_data, zoom=5)
    distance = get_location_distance(user_location, closet_location['location'])
    location_name = closet_location['info']['value']
    st.info(
        f'Closet available location to your location is **{location_name}** '
        f'(Lat: {epw.location.latitude}, Lon: {epw.location.longitude}). '
        f'The distance between the two locations is {distance} km '
        f'({round(distance * 0.621371, 2)} miles). You can review the weather data '
        'summary below. 👇\n\n'
        'We offer additional studies for additional locations. Contact us!'
    )

    figure = epw.diurnal_average_chart()
    st.plotly_chart(figure_or_data=figure)

    return closet_location['info']
