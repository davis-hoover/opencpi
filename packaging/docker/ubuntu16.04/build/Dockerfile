# Config used to override defaults in build.py. Currently only used to specify
# a build context. The '...' means "OpenCPI root"
# - build_context: .../projects/core/rcc/platforms/ubuntu16_04/

FROM registry.gitlab.com/opencpi/opencpi/ubuntu16.04-base:latest

COPY ubuntu16_04-packages.sh .

# env vars are to allow tzdata to be installed non-interactively
RUN DEBIAN_FRONTEND=noninteractive TZ=UTC ./ubuntu16_04-packages.sh

CMD ["/bin/bash"]
