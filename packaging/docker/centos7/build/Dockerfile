# Config used to override defaults in build.py. Currently only used to specify
# a build context. The '...' means "OpenCPI root"
# - build_context: .../projects/core/rcc/platforms/centos7/

# Override when building an image using '--build-arg DEPENDENCY_TAG=blah'
ARG DEPENDENCY_TAG=latest

FROM registry.gitlab.com/opencpi/opencpi/centos7-base:$DEPENDENCY_TAG

COPY centos7-packages.sh .

RUN ./centos7-packages.sh

CMD ["/bin/bash"]
