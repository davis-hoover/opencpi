#!/bin/bash

set -e  # exit on any error

function usage {
  echo -n "\
Usage: $(basename "$0") [-c CLONE_DEST] [-g GIT_REV] [-r GR_RELEASE]

Will download, build, and install OpenCPI modified version of GNU Radio 3.7 for
the detected host OS.

Supported host OSs:
  - centos7

Optional args:
  -c CLONE_DEST, --clone-dest CLONE_DEST
                        Where GNU Radio will be cloned to.
                        [default: ${CLONE_DEST}]
  -g GIT_REV, --git-revision GIT_REV
                        The branch, tag, or other valid git revision to checkout
                        after cloning OpenCPI's fork of GNU Radio.
                        GIT_REV defaults to the currently checked out OpenCPI
                        git revision prefixed with 'opencpi-'.
                        Ex. 'opencpi-develop' will be used if the current
                        OpenCPI branch is 'develop'.
                        [default: ${GIT_REV}]
  -r GR_RELEASE, --gr-release GR_RELEASE
                        The version of GNU Radio to build. This is different
                        from the GIT_REV argument as it controls which packages
                        are installed to build GNU Radio. For example, one
                        would specify '-r 3.8' (without quotes) to install
                        packages needed to build GNU Radio 3.8.
                        [default: ${GR_RELEASE}]
"
  exit 1
}

function bad {
  echo "Error: $@" 1>&2
  exit 1
}

function detect_os {
  local host_os
  if [ -f /etc/os-release ]; then
    source /etc/os-release
    host_os="${ID}${VERSION_ID}"
  else
    bad 'Could not detect host OS using /etc/os-release'
  fi

  echo "${host_os}"
}

function install_centos7_packages {
  local pkgs

  # Update package metadata cache
  ${SUDO} yum makecache fast

  # Install needed packages
  # EPEL is always first. The epel package installed is not always the most
  # up-to-date.
  ${SUDO} yum -y install epel-release
  ${SUDO} yum -y update epel-release

  # Pointless for now, but anticipate support for future versions
  if [ "${GR_RELEASE}" = 3.7 ]; then
    pkgs=(
      alsa-lib-devel
      boost-devel
      codec2-devel
      cmake3
      cppunit-devel
      cppzmq-devel
      doxygen
      fftw-devel
      gcc-c++
      git
      gsl-devel
      gsm-devel
      jack-audio-connection-kit-devel
      libusbx-devel
      make
      orc-devel
      portaudio-devel
      pygtk2
      python-cheetah
      python-devel
      python-lxml
      python2-numpy
      python-sphinx
      SDL-devel
      swig
    )
  elif [ "${GR_RELEASE}" = 3.8 ]; then
    pkgs=(
      alsa-lib-devel
      boost-devel
      codec2-devel
      cmake3
      cppunit-devel
      cppzmq-devel
      doxygen
      fftw-devel
      gcc-c++
      git
      gsl-devel
      gsm-devel
      jack-audio-connection-kit-devel
      libusbx-devel
      make
      orc-devel
      portaudio-devel
      gtk3-devel
      python-devel
      python3-lxml
      python3-numpy
      python3-sphinx
      python3-zmq
      SDL-devel
      swig
    )
  fi

  # Install packages
  ${SUDO} yum -y --setopt=skip_missing_names_on_install=False install "${pkgs[@]}"
}

function install_ubuntu18_04_packages {
  local pkgs

  # Update package metadata cache
  ${SUDO} apt update

  # Pointless for now, but anticipate support for future versions
  if [ "${GR_RELEASE}" = 3.7 ]; then
    pkgs=(
      cmake
      doxygen
      git
      g++
      libasound2-dev
      libboost-all-dev
      libcomedi-dev
      libcodec2-dev
      libcppunit-dev
      libfftw3-dev
      libgsl-dev
      libgsm1-dev
      libjack-jackd2-dev
      liborc-dev
      libsdl1.2-dev
      libusb-1.0-0-dev
      libzmq3-dev
      portaudio19-dev
      python-cheetah
      python-dev
      python-gtk2
      python-lxml
      python-numpy
      python-sphinx
      swig
    )
  elif [ "${GR_RELEASE}" = 3.8 ]; then
     pkgs=(
      git
      cmake
      g++
      libboost-all-dev
      libgmp-dev
      swig
      python3-numpy
      python3-mako
      python3-sphinx
      python3-lxml
      doxygen
      libfftw3-dev
      libsdl1.2-dev
      libgsl-dev
      libqwt-qt5-dev
      libqt5openg15-dev
      python3-pyqt5
      liblog4cpp5-dev
      libzmq3-dev
      python3-yaml
      python3-click
      python3-click-plugins
      python3-zmq
      python3-scipy
      python3-pip
      pygtk3
    )
  fi

  # Install packages. Exports needed to suppress prompts when installing
  # python-sphinx.
  export DEBIAN_FRONTEND=noninteractive
  export TZ=UTC
  ${SUDO} apt -y install "${pkgs[@]}"
}

function install_gnuradio {
  mkdir -p "${CLONE_DEST}"
  git clone --depth 1 --branch "${GIT_REV}" \
    https://gitlab.com/opencpi/gnuradio.git "${CLONE_DEST}"
  cd "${CLONE_DEST}"
  git submodule update --init
  mkdir build
  cd build
  ${CMAKE} "${CMAKE_FLAGS[@]}" ../
  make -j ${NPROC}
  make -j ${NPROC} install
  ldconfig
  make test || true  # don't exit if tests fail
  cd ..
  rm -rf build
}

##### MAIN #####

# Set arg defaults
CLONE_DEST="${PWD}/gnuradio"
GIT_REV=opencpi-v2.0.0
GR_RELEASE=3.7

# Parse args
while [ $# -gt 0 ]; do
  case $1 in
    -c|--clone-dest)
      CLONE_DEST="$2"
      shift
      ;;
    -g|--git-revision)
      GIT_REV=$2
      shift
      ;;
    -r|--gr-release)
      GR_RELEASE=$2
      shift
      ;;
    *)
      usage
      ;;
  esac
  shift
done

# Validate args
case "${GR_RELEASE}" in
  3.7) ;;
  *) bad "Unsupported GR Release: ${GR_RELEASE}" ;;
esac

# There is no sudo in docker land
SUDO=
if [[ ! (-e /.dockerenv || -e /run/.containerenv) ]]; then
  SUDO=$(command -v sudo)
fi

# Get max(numcpus - 1, 1)
NPROC=$(nproc 2> /dev/null)
if [[ -z "${NPROC}" || ${NPROC} -le 1 ]]; then
  NPROC=1
else
  NPROC=$((${NPROC} - 1))
fi

# Common cmake flags, host specifics are set after we know the host.
declare CMAKE_FLAGS
CMAKE_FLAGS=(-Wno-dev)

# Do host specific stuff
HOST_OS="$(detect_os)"
case "${HOST_OS}" in
  centos7)
    install_centos7_packages
    CMAKE="$(command -v cmake3)"
    ;;
  ubuntu18.04)
    install_ubuntu18_04_packages
    # Suppress annoying warnings
    export CFLAGS='-Wno-deprecated-declarations -Wno-deprecated'
    export CXXFLAGS='-Wno-deprecated-declarations -Wno-deprecated'
    ;;
  *)
    bad "Unsupported host OS: ${HOST_OS}"
    ;;
esac

if [ -z "${CMAKE}" ]; then
  CMAKE="$(command -v cmake)"
fi

install_gnuradio

echo -n "\
!!!!!!!!!! IMPORTANT !!!!!!!!!!
You will need to set these environment variables:
export PYTHONPATH=/usr/local/lib64/python2.7/site-packages${PYTHONPATH:+:${PYTHONPATH}}
export LD_LIBRARY_PATH=/usr/local/lib64:/usr/local/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
!!!!!!!!!! IMPORTANT !!!!!!!!!!
"

exit 0
