import streamlit as st


def branding():
    # branding, api-key and url
    st.sidebar.image('logo.png', use_column_width=True)


def active_controls():
    cfg_options = [
        "Fixed South Facing", "Fixed South Facing Canopy", "North-South Tracking",
        "Fixed East Facing", "Fixed East-West Peak Canopy"
    ]
    configuration = st.sidebar.selectbox(
        'Select your panel configuration',
        options=cfg_options
    )

    transparency_values = [0, 20, 40, 60, 80, 100]
    transparency = st.sidebar.selectbox(
        'Select panel transparency', options=transparency_values, index=2
    )

    locations = [
        'Denver Golden', 'Fort Collins', 'Grand Junction', 'Minneapolis', 'Omaha',
        'Kansas City', 'Boise', 'Seattle', 'Eugene', 'Sacramento', 'Fresno Yosemite',
        'San Diego', 'Las Vegas', 'Tucson', 'Houston', 'Oklahoma City', 'Memphis',
        'Louisville', 'Springfield IL', 'Lansing', 'Des Moines', 'Boston', 'Atlanta',
        'Richmond', 'Miami', 'Juneau', 'Honolulu', 'Toronto', 'Cuidad Mexico',
        'San Juan'
    ]
    location = st.sidebar.selectbox(
        'Select your location',
        options=locations
    )

    return [
        {'value': configuration, 'index': cfg_options.index(configuration)},
        {'value': transparency, 'index': transparency_values.index(transparency)},
        {'value': location, 'index': locations.index(location)}
    ]


def place_holder_controls():

    with st.sidebar.expander('Panel Geometry'):
        panel_length = st.slider(
            'Panel Length', min_value=1, max_value=10, value=2, disabled=True
        )
        panel_width = st.slider(
            'Panel Width', min_value=1, max_value=20, value=12, disabled=True
        )
        protrait = st.checkbox('Make panels protrait', value=False, disabled=True)

    with st.sidebar.expander('Table Geometry'):
        panel_count_x = st.slider(
            'Panels in Row', min_value=1, max_value=10, value=2, disabled=True
        )
        panel_count_y = st.slider(
            'Panels in Column', min_value=1, max_value=10, value=2, disabled=True
        )
        height = st.slider(
            'Height', min_value=1, max_value=10, value=2, disabled=True
        )
        spacing_x = st.slider(
            'Row Spacing', min_value=1, max_value=10, value=2, disabled=True
        )
        spacing_y = st.slider(
            'Column Spacing', min_value=1, max_value=10, value=2, disabled=True
        )
        mirror_gap = st.slider(
            'Mirror Gap', min_value=0, max_value=10, value=0, disabled=True
        )

    with st.sidebar.expander('Array Geometry'):
        spacing_array_x = st.slider(
            'Row Spacing', min_value=1, max_value=10, value=2, disabled=True,
            key='Array Row Spacing'
        )
        spacing_array_y = st.slider(
            'Column Spacing', min_value=1, max_value=10, value=2, disabled=True,
            key='Array Column Spacing'
        )
        surronding_count_x = st.slider(
            'Surrounding Column Count', min_value=1, max_value=10, value=2, disabled=True
        )
        surronding_count_y = st.slider(
            'Surrounding Row Count', min_value=1, max_value=10, value=2, disabled=True
        )
        array_azimuth = st.slider(
            'Azimuth [deg]', min_value=90, max_value=270, step=5,
            value=180, disabled=True
        )
        surface_offset = st.slider(
            'Ground Surface Offset', min_value=0, max_value=10,
            value=2, disabled=True
        )
