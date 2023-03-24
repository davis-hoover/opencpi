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

make_include_links() {
  INCS=("${@:3}")
  for i in ${INCS[@]}; do
    relative_link $2/$i.h $1
  done
}

MASTER_BRANCH_AS_OF_NOW=7655f5abff6e05a7e3c6676d32275da3e6b6037c
OCPI_RFDC_VERSION=xilinx_v2021.1
[ -z "$OCPI_CDK_DIR" ] && echo Environment variable OCPI_CDK_DIR not set && \
    exit 1
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
    --includedir=$OcpiInstallDir/include
make
make install
SYSFS_INCLUDE_DIR=$OcpiInstallDir/include
OPENCPI_LIBMETAL_SYSTEM_DIR=$OcpiThisPrerequisiteDir/opencpi
source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
       "$1" \
       rfdc \
       "Xilinx RFDC Library" \
       https://github.com/Xilinx/embeddedsw.git \
       $OCPI_RFDC_VERSION \
       embeddedsw \
       1
BUILD_DIR=../ThirdParty/sw_services/libmetal/src/libmetal
ln -fs $OPENCPI_LIBMETAL_SYSTEM_DIR $BUILD_DIR/lib/system/opencpi
pushd $BUILD_DIR
# -p needed for builds of subsequent rcc platforms
mkdir -p build_libm
pushd build_libm
TOOLCHAIN=../cmake/platforms/toolchain.cmake
TMP_INC=lib/include/metal
echo "set (CMAKE_SYSTEM_NAME \"Opencpi\" CACHE STRING \"\")" > $TOOLCHAIN
if [ ! -z $OcpiCrossHost ]; then
  echo "set (CMAKE_SYSTEM_PROCESSOR \"arm\" CACHE STRING \"\")
set (MACHINE \"zynqmp_a53\")
set (CROSS_PREFIX \"$OcpiCrossHost\" CACHE STRING \"\")
set (CMAKE_C_FLAGS \"-O2 -c -g -Wall -Wextra -I$TMP_INC\" CACHE STRING \"\")
include (CMakeForceCompiler)
CMAKE_FORCE_C_COMPILER (\"\${CROSS_PREFIX}gcc\" GNU)
CMAKE_FORCE_CXX_COMPILER (\"\${CROSS_PREFIX}g++\" GNU)
set (CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER CACHE STRING \"\")
set (CMAKE_FIND_ROOT_PATH_MODE_LIBRARY NEVER CACHE STRING \"\")
set (CMAKE_FIND_ROOT_PATH_MODE_INCLUDE NEVER CACHE STRING \"\")" > $TOOLCHAIN
fi
#cmake .. -DCMAKE_INCLUDE_PATH=$SYSFS_INCLUDE_DIR -DCMAKE_TOOLCHAIN_FILE=$TOOLCHAIN
cmake .. -DCMAKE_INCLUDE_PATH=$SYSFS_INCLUDE_DIR
popd
popd
cp ../XilinxProcessorIPLib/drivers/rfdc/src/* .
SRCNAMES=(xrfdc xrfdc_ap xrfdc_clock xrfdc_dp xrfdc_g xrfdc_intr xrfdc_mb \
    xrfdc_mixer xrfdc_mts xrfdc_sinit)
SRCS=(${SRCNAMES[@]/%/.c})
INCS=(xrfdc xrfdc_hw)
TMP_DIR=../ThirdParty/sw_services/libmetal/src/libmetal/build_libm
METAL_INC_DIR=$TMP_DIR/lib/include
$CC -g -fPIC -I$METAL_INC_DIR -I. -I$SYSFS_INCLUDE_DIR -c ${SRCS[@]} \
    -L$LIBMETALL_INSTALL_LIB_DIR/lib/include -lmetal
$AR -rs librfdc.a ${SRCNAMES[@]/%/.o}
relative_link librfdc.a $OcpiInstallExecDir/lib
dir=$OcpiInstallDir/include
make_include_links $dir . "${INCS[@]}"
INCS=(alloc assert atomic cache compiler condition config cpu device \
    dma errno io irq_controller irq list log mutex shmem sleep softirq \
    spinlock sys time utilities)
dir=$OcpiInstallDir/include/metal
mkdir -p $dir
make_include_links $dir $METAL_INC_DIR/metal "${INCS[@]}"
INCS=(alloc assert cache condition io irq log mutex sleep sys)
dir=$OcpiInstallDir/include/metal/system/opencpi
mkdir -p $dir
make_include_links $dir $METAL_INC_DIR/metal/system/opencpi "${INCS[@]}"
INCS=(atomic compiler)
dir=$OcpiInstallDir/include/metal/compiler/gcc
mkdir -p $dir
make_include_links $dir $METAL_INC_DIR/metal/compiler/gcc "${INCS[@]}"
INCS=(atomic cpu)
dir=$OcpiInstallDir/include/metal/processor/x86_64
mkdir -p $dir
make_include_links $dir $METAL_INC_DIR/metal/processor/x86_64 "${INCS[@]}"
