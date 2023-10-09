FROM ubuntu:22.04

LABEL maintainer "Alexander Rubattino"

USER root

# Install some packages
RUN apt-get update && \
      DEBIAN_FRONTEND=noninteractive apt-get install -y \ 
      python3 \ 
      python3-dev \ 
      python3-pip \
      net-tools \
      ffmpeg \
      libsm6 \
      libxext6 \
      vim \
      git \
      xorg \
      unzip \
      wget \
      gdal-bin \
      libgdal-dev \
      curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install the python packages for this new user
ADD requirements.txt .
RUN pip3 install -r requirements.txt


WORKDIR /src