FROM ubuntu:18.04

MAINTAINER Craig Northway

RUN apt-get update && apt-get install -y python python-pip python3.6 python3-distutils git && pip install -U setuptools==25.2.0 && pip install tox && pip install pyyaml && pip install chardet

RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:pypy/ppa && apt-get update && apt-get install -y pypy3

COPY . /src

CMD cd /src && tox -r
