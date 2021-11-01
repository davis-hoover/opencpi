FROM ubuntu:18.04

ENV DEBIAN_FRONTEND=noninteractive
ADD . /opencpi
WORKDIR /opencpi
ENTRYPOINT ["/bin/bash", "-lc"]

ARG SCRIPT
RUN eval $SCRIPT
RUN locale-gen en_US.UTF-8 && update-locale
ENV LANG="en_US.UTF-8"
ENV LC_ALL="en_US.UTF-8"