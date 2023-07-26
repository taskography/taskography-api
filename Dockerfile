# FROM nvidia/cuda:12.2.0-base-ubuntu20.04
FROM ubuntu:20.04
ENV DEBIAN_FRONTEND=noninteractive 
RUN apt update && apt install -y build-essential git cmake curl wget flex bison python3-pip
RUN rm -rf /var/lib/apt/lists/*
WORKDIR /opt

# # Get Conda
# ENV CONDA_DIR /opt/conda
# RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
#     /bin/bash ~/miniconda.sh -b -p /opt/conda
# ENV PATH=$CONDA_DIR/bin:$PATH

# Get Docker
RUN curl -fsSL https://get.docker.com -o get-docker.sh
RUN sh get-docker.sh

# Get Taskography
# RUN conda create -n taskography python=3.10 -y
# SHELL ["conda", "run", "-n", "taskography", "/bin/bash", "-c"]
# RUN conda activate taskography
RUN git clone https://github.com/jiadingfang/taskography-api.git --recurse-submodules
WORKDIR /opt/taskography-api
RUN pip install .
RUN pip install -r requirements.txt