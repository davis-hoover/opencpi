# Config used to override defaults in build.py. Currently only used to specify
# a build context. The '...' means "OpenCPI root"
# - build_context: .../projects/core/rcc/platforms/ubuntu18_04/

ARG DEPENDENCY_TAG=latest

FROM registry.gitlab.com/opencpi/opencpi/ubuntu18.04-base:$DEPENDENCY_TAG

COPY ubuntu18_04-packages.sh .

# env vars are to allow tzdata to be installed non-interactively
RUN DEBIAN_FRONTEND=noninteractive TZ=UTC ./ubuntu18_04-packages.sh

CMD ["/bin/bash"]
