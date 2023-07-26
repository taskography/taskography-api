docker build -t taskography .
docker run -it --rm -v $DATA/3dscenegraph/:/data/3dscenegraph -v /var/run/docker.sock:/var/run/docker.sock taskography