# FROM nvidia/cuda:12.2.0-base-ubuntu20.04
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive 
RUN apt update && apt install -y build-essential git cmake curl wget flex bison python3-pip python-is-python3
RUN rm -rf /var/lib/apt/lists/*
WORKDIR /opt

# Get Docker
RUN curl -fsSL https://get.docker.com -o get-docker.sh
RUN sh get-docker.sh

# Get Taskography
RUN git clone https://github.com/jiadingfang/taskography-api.git --recurse-submodules
WORKDIR /opt/taskography-api
RUN pip install .
RUN pip install -r requirements.txt
ENV PYTHONPATH "${PYTHONPATH}:/opt/taskography-api"