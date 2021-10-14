FROM centos:7

ADD . /opencpi
WORKDIR /opencpi

ARG SCRIPT
RUN eval $SCRIPT
ENV LANG="en_US.UTF-8"