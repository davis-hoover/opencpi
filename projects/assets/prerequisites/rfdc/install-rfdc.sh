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

OCPI_LIBMETAL_VERSION=v2021.04.0
[ -z "$OCPI_CDK_DIR" ] && echo Environment variable OCPI_CDK_DIR not set && exit 1
source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
       "$1" \
       libmetal \
       "OpenAMP libmetal" \
       https://github.com/OpenAMP/libmetal.git \
       $OCPI_LIBMETAL_VERSION \
       libmetal \
       1
cmake3 ..
LIBMETAL_INSTALL_LIB_DIR=$OcpiInstallExecDir/lib
make VERBOSE=1 DESTDIR=$LIBMETAL_INSTALL_LIB_DIR install
OCPI_RFDC_VERSION=xilinx_v2021.1
source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
       "$1" \
       rfdc \
       "Xilinx RFDC Library" \
       https://github.com/Xilinx/embeddedsw.git \
       $OCPI_RFDC_VERSION \
       embeddedsw \
       1
dir=../XilinxProcessorIPLib/drivers/rfdc/src/
cp $dir/* .
SRCNAMES=(xrfdc xrfdc_ap xrfdc_clock xrfdc_dp xrfdc_g xrfdc_intr xrfdc_mb xrfdc_mixer xrfdc_mts xrfdc_sinit)
SRCS=(${SRCNAMES[@]/%/.c})
INCS=(xrfdc xrfdc_hw)
$CC -g -fPIC -I$LIBMETAL_INSTALL_LIB_DIR/usr/local/include -I. -c ${SRCS[@]} -L$LIBMETALL_INSTALL_LIB_DIR/usr/local/lib -lmetal
$AR -rs librfdc.a ${SRCNAMES[@]/%/.o}
relative_link librfdc.a $OcpiInstallExecDir/lib
for i in ${INCS[@]}; do
  relative_link $dir/$i.h $OcpiInstallDir/include
done
LIBMETAL_INCS=(alloc assert atomic cache compiler condition config cpu device \
    dma errno io irq_controller irq list log mutex shmem sleep softirq \
    spinlock sys time utilities)
# this directory's existence is assumed by rfdc source code
metal_dir=$OcpiInstallDir/include/metal
mkdir -p $metal_dir
for i in ${LIBMETAL_INCS[@]}; do
  relative_link $LIBMETAL_INSTALL_LIB_DIR/usr/local/include/metal/$i.h $metal_dir
done
LIBMETAL_SYSTEM_INCS=(alloc assert cache condition io irq log mutex sleep sys)
metal_system_dir=$OcpiInstallDir/include/metal/system/linux/
mkdir -p $metal_system_dir
for i in ${LIBMETAL_SYSTEM_INCS[@]}; do
  relative_link $LIBMETAL_INSTALL_LIB_DIR/usr/local/include/metal/system/linux/$i.h $metal_system_dir
done
LIBMETAL_COMPILER_INCS=(atomic compiler)
metal_compiler_dir=$OcpiInstallDir/include/metal/compiler/gcc/
mkdir -p $metal_compiler_dir
for i in ${LIBMETAL_COMPILER_INCS[@]}; do
  relative_link $LIBMETAL_INSTALL_LIB_DIR/usr/local/include/metal/compiler/gcc/$i.h $metal_compiler_dir
done
LIBMETAL_COMPILER_INCS=(atomic cpu)
metal_compiler_dir=$OcpiInstallDir/include/metal/processor/x86_64/
mkdir -p $metal_compiler_dir
for i in ${LIBMETAL_COMPILER_INCS[@]}; do
  relative_link $LIBMETAL_INSTALL_LIB_DIR/usr/local/include/metal/processor/x86_64/$i.h $metal_compiler_dir
done
