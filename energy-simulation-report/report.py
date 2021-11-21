import pathlib
import re
import shutil

import streamlit as st


def copy_static_assets():
    asset_folders = ['js', 'css']
    for af in asset_folders:
        local_asset_path = pathlib.Path(
            __file__).parent.joinpath(f'static/{af}')
        streamlit_asset_path = pathlib.Path(st.__file__)\
            .parent.joinpath(f'static/static/{af}')

        for f in local_asset_path.iterdir():
            shutil.copyfile(f, streamlit_asset_path.joinpath(f.name))


def replace_links_in_report(report: str):

    link_replace_args = [
        ('http://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/3.2.0/css/bootstrap.min.css',
         './static/css/bootstrap.min.css'),
        ('http://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js',
         './static/js/jquery.min.js'),
        ('http://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/js/bootstrap.min.js',
         './static/js/bootstrap.min.js'),
        ('http://cdnjs.cloudflare.com/ajax/libs/d3/3.4.8/d3.min.js',
         './static/js/d3.min.js'),
        ('http://dimplejs.org/dist/dimple.v2.1.2.min.js',
         './static/js/dimple.min.js')
    ]

    for args in link_replace_args:
        report = report.replace(*args)
    return report
