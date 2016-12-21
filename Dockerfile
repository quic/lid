FROM ubuntu:16.10

MAINTAINER Peter Shin

RUN apt-get update && apt-get install -y python python-pip python3 pypy git && pip install -U setuptools==25.2.0 && pip install tox

COPY . /src

CMD cd /src && tox
