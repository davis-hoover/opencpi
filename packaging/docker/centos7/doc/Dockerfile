# Config used to override defaults in build.py. Currently only used to specify
# a build context. The '...' means "OpenCPI root"
# - build_context: .../scripts/

# Override when building an image using '--build-arg DEPENDENCY_TAG=blah'
ARG DEPENDENCY_TAG=latest

FROM registry.gitlab.com/opencpi/opencpi/centos7-base:$DEPENDENCY_TAG

COPY install-opencpi-docs.sh .

RUN ./install-opencpi-docs.sh --no-build

CMD ["/bin/bash"]
