ARG IMAGE
ARG TAG=develop
FROM $IMAGE:$TAG

ARG WORKDIR=/home/user/opencpi
COPY --chown=user:user . $WORKDIR
ARG WORKDIR=/home/user/opencpi
RUN echo "source ${WORKDIR}/cdk/opencpi-setup.sh -r" >> ~/.bashrc
ARG WORKDIR=/home/user/opencpi
WORKDIR $WORKDIR
ENTRYPOINT /bin/bash
