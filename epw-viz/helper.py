"""Functions to support the epw-viz app."""

import pathlib
import shutil
import streamlit as st

from icrawler.builtin import GoogleImageCrawler
from geopy.geocoders import Nominatim


@st.cache(suppress_st_warning=True)
def get_image(keyword):
    # nuke the images folder if exists
    path = pathlib.Path('./assets/image')
    if path.is_dir():
        shutil.rmtree(path)
    # create a new folder to download the image
    path.mkdir(parents=True, exist_ok=True)
    filters = dict(size='medium', type='photo',
                   license='commercial,modify')
    google_crawler = GoogleImageCrawler(storage={'root_dir': './assets/image'})
    google_crawler.crawl(keyword=keyword, max_num=1, filters=filters)


def city_name(latitude: float, longitude: float) -> str:
    """Get the city name from latitude and longitude"""
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(str(latitude)+","+str(longitude), language='en')
    address = location.raw['address']
    city = address.get('city', '')
    return city
