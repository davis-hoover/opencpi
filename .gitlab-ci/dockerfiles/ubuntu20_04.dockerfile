FROM ubuntu:20.04
WORKDIR /tmp/opencpi
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG="en_US.UTF-8"
SHELL ["/bin/bash", "-c"]
RUN --mount=type=bind,source=build,target=/tmp/opencpi/build/ \
    --mount=type=bind,source=scripts,target=/tmp/opencpi/scripts/ \
    --mount=type=bind,source=Framework.exports,target=/tmp/opencpi/Framework.exports \
    --mount=type=bind,source=tools/scripts,target=/tmp/opencpi/tools/scripts/ \ 
    --mount=type=bind,source=bootstrap,target=/tmp/opencpi/bootstrap/ \ 
    --mount=type=bind,source=projects/core/rcc/platforms/ubuntu20_04,target=/tmp/opencpi/projects/core/rcc/platforms/ubuntu20_04/ \ 
    touch /.dockerenv && ln -s exports cdk \
    && ./scripts/install-packages.sh \
    && apt install python3-pip -y && pip3 install rich \
    && locale-gen en_US.UTF-8 \
    && update-locale
RUN rm -rf /tmp/opencpi
ENV LC_ALL="en_US.UTF-8"