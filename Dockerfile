FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y \
    python3.10 \
    python3.10-distutils \
    python3-pip \
    ffmpeg \
    ffmpeg-doc \
    ffmpeg2theora \
    ffmpegfs \
    ffmpegthumbnailer \
    ffmpegthumbs \
    ffmsindex \
    git \
    && apt-get clean

RUN python3.10 -m pip install --upgrade pip

COPY requirements.txt /tmp/

RUN pip install -r /tmp/requirements.txt

COPY .env /env/.env

COPY cook_convert.txt /cook_convert.txt

COPY ./src /src

WORKDIR /

CMD ["python3.10", "/src/main.py"] 
