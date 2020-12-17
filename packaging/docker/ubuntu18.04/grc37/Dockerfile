# Config used to override defaults in build.py. For path options, '...' means "OpenCPI root".
# Additional build time mounts.
# - build_mount: /opt/Xilinx:/opt/Xilinx:ro
# - build_mount: .../scripts:/scripts:ro

# This image takes about 24 hours to build from scratch

FROM ubuntu:18.04

# Needed when tzdata is installed to prevent prompting for timezone
ARG DEBIAN_FRONTEND=noninteractive
ARG TZ=UTC

# Install software needed to install OpenCPI
# iproute2, iputils-ping, and vim are for convenience
RUN apt update  \
 && apt -y upgrade \
 && apt -y install git iproute2 iputils-ping python-dev unzip vim wget zip \
 && rm -rf /var/lib/{apt,cache,dkpg,log}

# Clone all repos to prevent getting an out of date repo
# ARGs are used to allow overriding during build time
ARG OCPI_BRANCH=develop
RUN git clone --depth 1 --branch $OCPI_BRANCH https://gitlab.com/opencpi/opencpi.git /opencpi
ARG PLUTO_BRANCH=develop
RUN git clone --depth 1 --branch $PLUTO_BRANCH https://gitlab.com/opencpi/osp/ocpi.osp.plutosdr.git /opencpi/projects/osps/ocpi.osp.plutosdr

# Every RUN command for OpenCPI from now on needs to start in /opencpi
WORKDIR /opencpi

# We don't use install-opencpi.sh because it runs tests and it's annoying when
# the timer tests fails due to running in a VM.
RUN scripts/install-packages.sh \
 && rm -rf /var/lib/{apt,cache,dkpg,log}
RUN scripts/install-prerequisites.sh
RUN scripts/build-opencpi.sh

# Use Xilinx 2019.2 for everything
ENV OCPI_XILINX_VERSION=2019.2

# xsim HDL
RUN bash -c "source cdk/opencpi-setup.sh -s \
 && ocpiadmin install platform xsim"

# Pluto RCC
RUN bash -c "source cdk/opencpi-setup.sh -s \
 && ocpiadmin install platform adi_plutosdr0_32 -p ocpi.osp.plutosdr"

# Pluto HDL
RUN bash -c "source cdk/opencpi-setup.sh -s \
 && ocpiadmin install platform plutosdr"

# Build platform tests
RUN bash -c "source cdk/opencpi-setup.sh -s \
 && ocpidev -d projects/platform build test --hdl-platform plutosdr"

# Build mfsk mapper unit test for xsim and pluto
RUN bash -c "source cdk/opencpi-setup.sh -s \
 && ocpidev build test -d projects/assets/components/comms_comps/mfsk_mapper.test \
      --hdl-platform plutosdr --hdl-platform xsim"

# Build tutorial project
RUN bash -c "source cdk/opencpi-setup.sh -s \
 && ocpidev -d projects/tutorial build \
      --rcc-platform ubuntu18_04 --rcc-platform adi_plutosdr0_32 \
      --hdl-platform xsim --hdl-platform plutosdr"

## Generate GRC blocks last! ##
# Create empty project for GRC to use
RUN /bin/bash -c "source cdk/opencpi-setup.sh -s \
 && cd / \
 && ocpidev create -y dsp_comps -y util_comps -D ocpi.assets -D ocpi.platform -D ocpi.tutorial project grc_project"
ENV OCPI_GRC_PROJECT_DIR=/grc_project

# Needed for ocpigr37
ENV OCPI_LIBRARY_PATH=/grc_project/artifacts:/opencpi/projects/core/artifacts:/opencpi/projects/assets/artifacts:/opencpi/projects/tutorial/artifacts \
    GRC_BLOCKS_PATH=/opencpi/grc_blocks

# Generate GRC Radio Blocks
RUN mkdir /opencpi/grc_blocks \
 && /opencpi/exports/ubuntu18_04/bin/ocpigr37 -D /opencpi/grc_blocks

# Remove metadata block "OpenCPI Container"
RUN sed -i '/variable_ocpi_container/d' grc_blocks/ocpi_block_tree.xml


##### End OpenCPI Stuff #####

ARG GR_BRANCH=opencpi-v2.0.0
RUN /scripts/install-gnuradio.sh -g $GR_BRANCH -c /gnuradio \
 && rm -rf /var/lib/{apt,cache,dpkg,log}


##### Set some env vars needed for various things, but not for building
# Needed for GRC
ENV DISPLAY=:0 \
    PYTHONPATH="/usr/local/lib64/python2.7/site-packages:${PYTHONPATH}" \
    LD_LIBRARY_PATH=/usr/local/lib64:/usr/local/lib

# Needed to prevet 'Error: BadDrawable' when running QT sinks
ENV QT_X11_NO_MITSHM=1

# By default, pluto has this IP address
ENV OCPI_SERVER_ADDRESSES=192.168.2.1:12345

# Makes ocpirun -C complete faster
ENV OCPI_HDL_SIMULATOR=xsim

# Setup OpenCPI environment when container starts
RUN echo "source /opencpi/cdk/opencpi-setup.sh -r" >> /root/.bashrc


# This script will run when the container starts
COPY entrypoint.sh /root/
ENTRYPOINT ["/root/entrypoint.sh"]

# We want an interactice container by default
CMD ["/bin/bash"]
WORKDIR /

# Create a "version" file
RUN date > /build-date


