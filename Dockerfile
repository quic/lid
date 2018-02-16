FROM ubuntu:17.10

MAINTAINER Peter Shin

RUN apt-get update && apt-get install -y python python-pip python3 pypy git && pip install -U setuptools==25.2.0 && pip install tox && pip install pyyaml && pip install chardet

COPY . /src

CMD cd /src && tox
