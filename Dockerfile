FROM python:3.7 as base

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
  && apt-get -y install --no-install-recommends libjemalloc-dev libboost-dev \
  libboost-filesystem-dev \
  libboost-system-dev \
  libboost-regex-dev \
  python-dev \
  autoconf \
  flex \
  bison \
  ffmpeg \
  libsm6 \
  libxext6 \
  xvfb

RUN pip install --upgrade pip

WORKDIR /app
CMD streamlit run app.py --server.port=${PORT} --browser.serverAddress="0.0.0.0"

ARG APP_NAME=design_explorer

COPY ${APP_NAME} .
RUN [ -e "./requirements.txt" ] && pip install --no-cache-dir -r requirements.txt || echo no requirements.txt file
