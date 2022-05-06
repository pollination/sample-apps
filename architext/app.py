from pollination_streamlit_io import inputs, button, special
import streamlit as st
import requests
import json
import uuid

from helper import generate_3d_model, add_viewer

url='https://huggingface.co/gradioiframe/architext/Architext_deployed/api/predict/'

st.set_page_config(
    page_title='Architext',
    layout='wide',
    page_icon='https://app.pollination.cloud/favicon.ico',
    initial_sidebar_state='collapsed'
)

query = st.experimental_get_query_params()
platform = special.get_host()

submit= False
first_try = 'architext_layout' not in st.session_state
st.image('architext_header.png')
form, image, three_d = st.columns(3)

with form:
    with st.form('Generate Design Option'):
        user_input = st.text_input(
            label='DESCRIBE YOUR IDEAL APARTMENT',
            value='An apartment with two bedrooms and one bathroom',
            )

        creativity = st.selectbox(
            label='Creativity', options=['Low', 'Medium', 'High']
        )

        if not first_try:
            # only give these options when a design is available
            wwr = st.slider(
                'Window to wall ratio',
                min_value=0.1, max_value=0.8, step=0.1, value=0.4
            )

            height = st.slider(
                'Floor to floor height',
                min_value=2.8, max_value=3.6, step=0.1, value=3.0
            )
            regenerate = st.checkbox('Generate a new design option?', value=False)
        else:
            # set default values
            wwr = 0.4
            height = 3.0
            regenerate = True

        submit = st.form_submit_button('Submit')

if submit:
    # first design option
    regenerate = True if 'architext_layout' not in st.session_state else regenerate

    if regenerate:
        r = requests.post(
            url=url,
            json={
                "data": [user_input, creativity]
            }
        )
        layout = r.json()
        st.session_state['architext_layout'] = layout
        st.session_state['architext_layout_id'] = uuid.uuid4()  # a unique id
    else:
        layout = st.session_state['architext_layout']

    with image:
        st.image(layout['data'][0])

    vtk_file, hb_model = generate_3d_model(
        height, wwr, st.session_state['architext_layout_id']
    )
    with three_d:
        add_viewer(vtk_file)

    st.experimental_rerun()
else:
    # redraw the image and 3D
    if not first_try:
        layout = st.session_state['architext_layout']
        with image:
            st.image(layout['data'][0])
        room_2ds = json.loads(layout['data'][1])
        vtk_file, hb_model = generate_3d_model(
            height, wwr, st.session_state['architext_layout_id']
        )
        with three_d:
            add_viewer(vtk_file)


if not first_try and platform == 'rhino':
    inputs.send(
        data=hb_model.to_dict(),
        isPollinationModel=True,
        defaultChecked=True,
        label='View design option',
        uniqueId='unique-id-02',
        options={'layer': 'daylight_factor_results'},
        key='architext option',
    )

    button.send(
        'BakePollinationModel',
        hb_model.to_dict(),
        'bake-geometry-key',
        options={
            "layer": "architext_option",
            "units": "Meters"
        },
        key='bake-geometry',
        )
