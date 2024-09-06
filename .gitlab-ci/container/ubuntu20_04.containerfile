FROM ubuntu:20.04 as base
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG="en_US.UTF-8"
WORKDIR /home/user/opencpi
RUN touch /.dockerenv && apt update -y && apt install -y git python3-pip locales \
    && locale-gen en_US.UTF-8 \
    && update-locale
ENV LC_ALL="en_US.UTF-8"
