#
# Dockerfile for pfurl repository.
#
# Build with
#
#   docker build -t <name> .
#
# For example if building a local version, you could do:
#
#   docker build -t local/pfurl .
#
# In the case of a proxy (located at say 10.41.13.4:3128), do:
#
#    export PROXY="http://10.41.13.4:3128"
#    docker build --build-arg http_proxy=${PROXY} --build-arg UID=$UID -t local/pfurl .
#
# To run an interactive shell inside this container, do:
#
#   docker run -ti --entrypoint /bin/bash local/pfurl
#
# To pass an env var HOST_IP to container, do:
#
#   docker run -ti -e HOST_IP=$(ip route | grep -v docker | awk '{if(NF==11) print $9}') --entrypoint /bin/bash local/pfurl
#

FROM python:3.8-alpine
MAINTAINER fnndsc "dev@babymri.org"

# Alpine apk package manager installs to /usr/lib whereas
# python pip installs to /usr/local/lib.
# Pycurl native modules must be installed using apk.
# It's necessary to set PYTHONPATH here for python to see
# packages installed by apk. It won't be needed anymore after
# we switch to pure python dependencies, like requests
ENV PYTHONPATH=/usr/lib/python3.8/site-packages

COPY . /usr/local/src

RUN apk add py3-curl && \
    pip install /usr/local/src/

ENTRYPOINT ["/usr/local/bin/pfurl"]
