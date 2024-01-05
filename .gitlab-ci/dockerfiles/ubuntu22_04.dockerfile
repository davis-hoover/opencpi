FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG="en_US.UTF-8"
RUN touch /.dockerenv && \
    groupadd -g 1000 user && \
    useradd -ms /bin/bash -u 1000 -g 1000 user
COPY . /tmp/opencpi
RUN cd /tmp/opencpi && \
    ./scripts/install-packages.sh && \
    cd / && \
    rm -rf /tmp/opencpi
USER user
