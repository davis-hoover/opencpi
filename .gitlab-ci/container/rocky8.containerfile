FROM rockylinux:8 as base
ENV LANG="en_US.UTF-8"
WORKDIR /home/user/opencpi
RUN touch /.dockerenv && yum update -y && yum install -y git