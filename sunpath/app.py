"""The Pollination sunpath app."""


import pathlib
import streamlit as st
from streamlit_vtkjs import st_vtkjs

from ladybug.compass import Compass
from ladybug.color import Color
from ladybug.epw import EPW, EPWFields
from pollination_streamlit_io import inputs

from helper import get_sunpath_vtkjs, get_sunpath, write_csv_file, get_data

# make it look good by setting up the title, icon, etc.
st.set_page_config(
    page_title='Sunpath',
    page_icon='https://app.pollination.cloud/favicon.ico'
)
st.sidebar.image(
    'https://uploads-ssl.webflow.com/6035339e9bb6445b8e5f77d7/616da00b76225ec0e4d975ba'
    '_pollination_brandmark-p-500.png',
    use_column_width=True
)


def main():
    # control panel
    with st.sidebar:

        with st.form('Parameters'):
            latitude = st.slider('Latitude', -90.0, 90.0, 0.0, 0.5)
            longitude = st.slider('Longitude', -90.0, 90.0, 0.0, 0.5)
            north = st.slider('North', -180, 180, 0, 1)
            projection = st.slider('Projection', 2, 3, value=3,
                                   help='Choose between 2D and 3D.')

            # load EPW
            with st.expander('Sunpath for EPW'):
                epw_data = st.file_uploader('Load EPW', type='epw')
                # if epw file is uploaded, load it
                if epw_data:
                    epw_file = pathlib.Path('./data/sample.epw')
                    epw_file.parent.mkdir(parents=True, exist_ok=True)
                    epw_file.write_bytes(epw_data.read())
                    epw = EPW(epw_file)
                else:
                    epw = None

            # select data from EPW to mount on Sunpath
            fields = {EPWFields._fields[i]['name'].name: i for i in range(6, 34)}
            with st.expander('Load data on sunpath'):
                st.text('*Load EPW first*')
                selection = []
                for var in fields.keys():
                    selection.append(st.checkbox(var, value=False))

            st.form_submit_button('Run')

        st.markdown('----')

        menu = st.checkbox('Show viewer controls', value=False)

    # Main page
    with st.container():

        st.title('Interactive Sunpath App!')

        # set header
        if epw:
            st.markdown(f'Sunpath for {epw.location.city}')
        else:
            st.markdown(f'Sunpath for latitude: {latitude} and longitude: {longitude}')

        # get sunpath
        sunpath = get_sunpath(latitude, longitude, north, epw)

        # get data
        data = get_data(selection, fields, epw)

        # get sunpath vtkjs
        sunpath_vtkjs, sun_color = get_sunpath_vtkjs(sunpath, projection, data)

        # update the viewer
        st_vtkjs(sunpath_vtkjs.read_bytes(), menu=menu, key='viewer')

        # generate a csv file
        col2 = st.columns(3)[1]
        with col2:
            write_csv = st.checkbox('Download CSV', value=False)
            if write_csv:
                csv_file_path = write_csv_file(sunpath, epw, data)
                with open(csv_file_path, 'r') as f:
                    st.download_button('Download CSV', f, file_name='sunpath.csv')

    # rhino integration

    # get the platform from the query uri
    query = st.experimental_get_query_params()
    platform = query['__platform__'][0] if '__platform__' in query else 'web'

    if platform == 'Rhino':
        def get_colored_geometry_json_strings(geometries, hex_color):
            rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            geometry_dicts = [g.to_dict() for g in geometries]
            for d in geometry_dicts:
                d['color'] = Color(*rgb).to_dict()
            return geometry_dicts

        # layout
        col1, col2, col3 = st.columns(3)

        # values here
        radius = st.slider('Sun path radius', 0, 500, 100)

        # create the compass
        co = Compass(radius=radius,
                     north_angle=north,
                     spacing_factor=0.15)

        with col1:
            # analemma
            col = st.color_picker('Analemma Color', '#000000',
                                  key='poly-col').lstrip('#')
            polylines = sunpath.hourly_analemma_polyline3d(radius=radius)
            polylines_dicts = get_colored_geometry_json_strings(polylines, col)

            # arcs
            col = st.color_picker('Arcs Color', '#bcbec0',
                                  key='arc-col').lstrip('#')
            arcs = sunpath.monthly_day_arc3d(radius=radius)
            arcs_dicts = get_colored_geometry_json_strings(arcs, col)

        with col2:
            # circles
            col = st.color_picker('Circles Color', '#eb2126',
                                  key='circl-col').lstrip('#')
            circles = co.all_boundary_circles
            circles_dicts = get_colored_geometry_json_strings(circles, col)

            # ticks
            col = st.color_picker('Ticks Color', '#2ea8e0',
                                  key='tick-col').lstrip('#')
            major_ticks = co.major_azimuth_ticks
            minor_ticks = co.minor_azimuth_ticks
            ticks = major_ticks + minor_ticks
            ticks_dicts = get_colored_geometry_json_strings(ticks, col)

        with col3:
            # altitude circles
            col = st.color_picker('Circle Color', '#05a64f',
                                  key='tick-col').lstrip('#')
            altitude_circ = co.stereographic_altitude_circles
            altitude_circ_dicts = get_colored_geometry_json_strings(altitude_circ, col)

            # suns
            points = []
            col = st.color_picker('Sun Color', '#f2b24d',
                                  key='sun-col').lstrip('#')
            hourly_suns = sunpath.hourly_analemma_suns()
            for suns in hourly_suns:
                for sun in suns:
                    if sun.is_during_day:
                        pt = sun.position_3d(radius=radius)
                        points.append(pt)
            suns_dicts = get_colored_geometry_json_strings(points, col)

        # group them
        geometries = polylines_dicts + arcs_dicts + circles_dicts + \
            ticks_dicts + altitude_circ_dicts + suns_dicts

        inputs.send(geometries, 'my-secret-key', key='goo')


if __name__ == '__main__':
    main()
