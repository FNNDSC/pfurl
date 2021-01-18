# debian is preferred over alpine for installing pycurl seamlessly
FROM python:3.9.1-buster
LABEL version="2.3.1" maintainer="FNNDSC <dev@babyMRI.org>" 

WORKDIR /usr/local/src
COPY . .
RUN pip install -r requirements.txt && pip install .

ENTRYPOINT ["pfurl"]
CMD ["--synopsis"]
