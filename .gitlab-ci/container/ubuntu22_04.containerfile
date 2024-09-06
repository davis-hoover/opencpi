FROM ubuntu:22.04 as base
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG="en_US.UTF-8"
WORKDIR /home/user/opencpi
RUN touch /.dockerenv && apt update -y && apt install -y git python3-pip
