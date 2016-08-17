FROM ubuntu:14.04

MAINTAINER Peter Shin

RUN apt-get update && apt-get install -y python python-pip git && pip install -U setuptools==25.2.0

COPY . /src

CMD make -C /src test
