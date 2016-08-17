FROM ubuntu:14.04

MAINTAINER Peter Shin

RUN apt-get update && apt-get install -y python python-pip git

RUN pip install -U setuptools 

COPY . /src

CMD make -C /src test