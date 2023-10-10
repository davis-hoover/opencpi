FROM centos:7

ENV LANG="en_US.UTF-8"
RUN touch /.dockerenv && \
    yum update -y && \
    yum install -y sudo git && \
    groupadd -g 1000 user && \
    useradd -ms /bin/bash -u 1000 -g 1000 user && \
    echo 'user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
USER user
COPY --chown=user:user . /tmp/opencpi
RUN cd /tmp/opencpi && \
    ./scripts/install-packages.sh && \
    cd / && \
    rm -rf /tmp/opencpi
