FROM centos:7

FROM centos:7
WORKDIR /tmp/opencpi
ENV LANG="en_US.UTF-8"
SHELL ["/bin/bash", "-c"]
RUN --mount=type=bind,source=build,target=/tmp/opencpi/build/ \
    --mount=type=bind,source=scripts,target=/tmp/opencpi/scripts/ \
    --mount=type=bind,source=Framework.exports,target=/tmp/opencpi/Framework.exports \
    --mount=type=bind,source=tools/scripts,target=/tmp/opencpi/tools/scripts/ \ 
    --mount=type=bind,source=bootstrap,target=/tmp/opencpi/bootstrap/ \ 
    --mount=type=bind,source=projects/core/rcc/platforms/centos7,target=/tmp/opencpi/projects/core/rcc/platforms/centos7/ \ 
    touch /.dockerenv && ln -s exports cdk \
    && yum update -y \
    && yum install -y git \
    && ./scripts/install-packages.sh \
    && yum install python3-pip -y && pip3 install rich
RUN rm -rf /tmp/opencpi