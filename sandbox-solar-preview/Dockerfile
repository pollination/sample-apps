FROM python:3.7-slim as base

RUN adduser ladybugbot --uid 1000 --disabled-password --gecos ""
USER ladybugbot

WORKDIR /home/ladybugbot/app
COPY . .

USER root

RUN apt-get update \
    && apt-get install ffmpeg libsm6 libxext6 curl unzip -y \
    && pip3 install -r requirements.txt || echo no requirements.txt file \
    && chown -R ladybugbot /home/ladybugbot/app

USER ladybugbot
