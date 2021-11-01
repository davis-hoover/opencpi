FROM centos:7

ADD . /opencpi
WORKDIR /opencpi
ENTRYPOINT ["/bin/bash", "-lc"]

ARG SCRIPT
RUN eval $SCRIPT
ENV LANG="en_US.UTF-8"