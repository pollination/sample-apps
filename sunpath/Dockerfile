FROM python:3.7 as base

RUN apt-get update \
    && apt-get -y install ffmpeg libsm6 libxext6 xvfb --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

WORKDIR /app

COPY . .

RUN [ -e "./requirements.txt" ] && pip install -r requirements.txt || echo no requirements.txt file
