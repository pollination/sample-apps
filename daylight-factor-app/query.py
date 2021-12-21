import streamlit as st
from uuid import uuid4


class Query:
    """Class to create the query to submit to Pollination."""
    _defaults = {
        'width': 10,
        'depth': 10,
        'glazing_ratio': 0.4,
        'job_id': None
    }

    def __init__(self):
        self._query_params = st.experimental_get_query_params()
        self._width = int(self._query_params.get('width', [10])[0])
        self._depth = int(self._query_params.get('depth', [10])[0])
        self._glazing_ratio = float(
            self._query_params.get('glazing-ration', [0.4])[0])
        self._job_id = self._query_params.get('job-id', [None])[0]
        self._owner = self._query_params.get('owner', [None])[0]
        self._project = self._query_params.get('project', [None])[0]
        self.model_id = self._query_params.get('model-id', [str(uuid4())])[0]

        self._update_query()

    @property
    def query_params(self):
        params = {
            'width': self._width,
            'depth': self._depth,
            'glazing-ratio': self._glazing_ratio,
            'model-id': self.model_id
        }

        if self._job_id is not None:
            params['job-id'] = self._job_id
        if self._owner is not None:
            params['owner'] = self._owner
        if self._project is not None:
            params['project'] = self._project

        return params

    def _update_query(self):
        st.experimental_set_query_params(**self.query_params)

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self._update_query()

    @property
    def depth(self):
        return self._depth

    @depth.setter
    def depth(self, value):
        self._depth = value
        self._update_query()

    @property
    def glazing_ratio(self):
        return self._glazing_ratio

    @glazing_ratio.setter
    def glazing_ratio(self, value):
        self._glazing_ratio = value
        self._update_query()

    @property
    def job_id(self):
        return self._job_id

    @job_id.setter
    def job_id(self, value):
        self._job_id = value
        self._update_query()

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, value):
        self._owner = value
        self._update_query()

    @property
    def project(self):
        return self._project

    @project.setter
    def project(self, value):
        self._project = value
        self._update_query()

