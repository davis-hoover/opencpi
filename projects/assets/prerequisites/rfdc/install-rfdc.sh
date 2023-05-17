#!/bin/bash --noprofile
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

# Requirements:
# 1. The drc_rfdc.rcc device proxy must build and run, using this supporting
#    prerequisite, on at least one of the supported RCC platforms
#    named xilinx*aarch*
#
# This page was referenced but not strictly followed when making this script:
# https://xilinx-wiki.atlassian.net/wiki/spaces/A/pages/84378586/Building+RFDC+application+from+git+sources+for+ZCU111

copy_include_files() {
  INCS=("${@:3}")
  for i in ${INCS[@]}; do
    # cp instead of link because of rm -rf for subsequent rcc platform builds
    #relative_link $2/$i.h $1
    mkdir -p $1
    cp $2/$i.h $1
  done
}

# TODO investigate removal of centos/ubuntu host compilation
#if [ -z $OcpiCrossHost ]; then
#  source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
#         "$1" \
#         rfdc \
#         "Xilinx RFDC Library" \
#         https://github.com/Xilinx/embeddedsw.git \
#         $OCPI_RFDC_VERSION \
#         embeddedsw \
#         1
#  echo Skipping rfdc build for unsupported host.
#else
  MASTER_BRANCH_AS_OF_NOW=7655f5abff6e05a7e3c6676d32275da3e6b6037c
  OCPI_RFDC_VERSION=xilinx_v2021.1
  [ -z "$OCPI_CDK_DIR" ] && echo Environment variable OCPI_CDK_DIR not set && \
      exit 1
  # TODO investigate removal of sysfs as a dependency, as it as not used at runtime but still heavily integrated into build
  source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
         "$1" \
         sysfs \
         "sysfs" \
         https://github.com/Distrotech/sysfsutils.git \
         $MASTER_BRANCH_AS_OF_NOW \
         sysfsutils \
         1
  base=$(basename `pwd`)
  (cd ..; cp -R $(ls . | grep -v ocpi-build-) $base)
  autoreconf -f -i
  ./configure --build=`./config.guess` ${OcpiCrossHost:+--host=$OcpiCrossHost} \
      --prefix=$OcpiInstallDir --exec-prefix=$OcpiInstallExecDir \
      --includedir=$OcpiInstallDir/include \
      CFLAGS="-g -fPIC" CXXFLAGS="-g -fPIC"
  make
  make install
  SYSFS_DIR=$OcpiInstallDir
  SYSFS_LIB_DIR=$OcpiInstallExecDir/lib
  _SYSFS_LIB_DIR=$PWD/lib
  echo_SYSFS_LIB_DIR=$_SYSFS_LIB_DIR
  RFDC_DIR=$OcpiThisPrerequisiteDir
  #OPENCPI_LIBMETAL_SYSTEM_DIR=$RFDC_DIR/opencpi
  PATCH_FILEPATH=$OcpiThisPrerequisiteDir/rfdc.patch
  source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
         "$1" \
         rfdc \
         "Xilinx RFDC Library" \
         https://github.com/Xilinx/embeddedsw.git \
         $OCPI_RFDC_VERSION \
         embeddedsw \
         1
  BUILD_DIR=../ThirdParty/sw_services/libmetal/src/libmetal
  cp $RFDC_DIR/io.c $BUILD_DIR/lib/system/linux/
  pushd $BUILD_DIR
  echo Patching API headers
  # ignore "skipping patch" exit status of 1 but error on all other errors
  OUT="$(patch -p0 -N < $PATCH_FILEPATH)" || echo "${OUT}" | \
      grep "Skipping patch" -q || (echo "$OUT" && false) || {
    echo "*******************************************************" >&2
    echo "ERROR: patch applied by rfdc.patch failed!!" >&2
    echo "$OUT" >&2
    echo "*******************************************************" >&2
    exit 1
  }
  # -p needed for builds of subsequent rcc platforms
  mkdir -p build_libm
  pushd build_libm
  rm -rf * # necessary to wipe out stale build from any previous rcc platform
  TMP_INC=lib/include/metal
  if [ -z $OcpiCrossHost ]; then
    cmake3 .. \
        -DCMAKE_LIBRARY_PATH=$SYSFS_LIB_DIR/ \
        -DCMAKE_INCLUDE_PATH=$SYSFS_DIR/include
  else
    TOOLC=../cmake/platforms/toolchain.cmake
    # -O is to prevent error related to FORTIFY
    echo "set (CMAKE_SYSTEM_PROCESSOR \"aarch64\" CACHE STRING \"\")
set (CROSS_PREFIX \"$OcpiCrossHost-\" CACHE STRING \"\")
set (CMAKE_C_FLAGS \"-O2 -g -fPIC\" CACHE STRING \"\")
include (cross-linux-gcc)" > $TOOLC
    cmake3 .. \
        -DCMAKE_LIBRARY_PATH=$SYSFS_LIB_DIR/ \
        -DCMAKE_INCLUDE_PATH=$SYSFS_DIR/include \
        -DCMAKE_TOOLCHAIN_FILE=$TOOLC
  fi
  make metal-static
  popd # build_libm
  popd # libmetal
  cp ../XilinxProcessorIPLib/drivers/rfdc/src/* .
  SRCNAMES=(xrfdc xrfdc_ap xrfdc_clock xrfdc_dp xrfdc_g xrfdc_intr xrfdc_mb \
      xrfdc_mixer xrfdc_mts xrfdc_sinit)
  SRCS=(${SRCNAMES[@]/%/.c})
  INCS=(xrfdc xrfdc_hw)
  TMP_DIR=../ThirdParty/sw_services/libmetal/src/libmetal/build_libm
  METAL_INC_DIR=$TMP_DIR/lib/include
  $CC -g -fPIC -I$METAL_INC_DIR -I$SYSFS_DIR/include -c *.c
  $AR -rs librfdc.a \
      $_SYSFS_LIB_DIR/*.o \
      $TMP_DIR/lib/CMakeFiles/metal-static.dir/*.o \
      $TMP_DIR/lib/CMakeFiles/metal-static.dir/system/linux/*.o \
      *.o
  relative_link librfdc.a $OcpiInstallExecDir/lib
  dir=$OcpiInstallDir/include
  copy_include_files $dir . "${INCS[@]}"
  INCS=(alloc assert atomic cache compiler condition config cpu device \
      dma io irq_controller irq list log mutex shmem sleep softirq \
      spinlock sys time utilities)
  dir=$OcpiInstallDir/include/metal
  mkdir -p $dir
  copy_include_files $dir $METAL_INC_DIR/metal "${INCS[@]}"
  INCS=(alloc assert io irq log sleep sys)
  dir=$OcpiInstallDir/include/metal/system/linux
  mkdir -p $dir
  copy_include_files $dir $METAL_INC_DIR/metal/system/linux "${INCS[@]}"
  INCS=(atomic compiler)
  dir=$OcpiInstallDir/include/metal/compiler/gcc
  mkdir -p $dir
  copy_include_files $dir $METAL_INC_DIR/metal/compiler/gcc "${INCS[@]}"
  INCS=(atomic cpu)
  if [ -z $OcpiCrossHost ]; then
    dir=$OcpiInstallDir/include/metal/processor/x86_64
    mkdir -p $dir
    copy_include_files $dir $METAL_INC_DIR/metal/processor/x86_64 "${INCS[@]}"
  else
    dir=$OcpiInstallDir/include/metal/processor/aarch64
    mkdir -p $dir
    copy_include_files $dir $METAL_INC_DIR/metal/processor/aarch64 "${INCS[@]}"
  fi
  cp -rp $SYSFS_DIR/include/* $OcpiInstallDir/include/
#fi
