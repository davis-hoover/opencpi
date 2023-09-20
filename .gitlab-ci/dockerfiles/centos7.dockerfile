FROM centos:7

ENV LANG="en_US.UTF-8"
RUN touch /.dockerenv && \
    yum update -y && \
    yum install -y sudo git && \
    groupadd -g 1000 user && \
    useradd -ms /bin/bash -u 1000 -g 1000 user && \
    echo 'user ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers
USER user
COPY --chown=user:user . /home/user/opencpi
RUN cd /home/user/opencpi && \ 
    ./scripts/install-packages.sh && \
    cd / && \
    rm -rf /home/user/opencpi
