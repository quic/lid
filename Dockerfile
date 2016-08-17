FROM ubuntu:14.04

MAINTAINER Shaoyan Zhang

RUN apt-get update 

RUN apt-get install -y python python-pip 

RUN apt-get install -y git

RUN pip install -U setuptools 

COPY . /src

RUN cd /src &&  make test



