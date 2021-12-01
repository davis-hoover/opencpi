FROM centos:7

ADD . /opencpi
WORKDIR /opencpi
ENTRYPOINT ["/bin/bash", "-lc"]
RUN groupadd gitlab-runner -g 994
RUN usermod -g gitlab-runner root
RUN echo "umask 002" >> ~/.bashrc

ARG SCRIPT
RUN eval $SCRIPT
ENV LANG="en_US.UTF-8"