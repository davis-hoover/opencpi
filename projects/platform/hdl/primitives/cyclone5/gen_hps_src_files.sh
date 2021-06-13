#!/bin/bash
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
EmbeddedDir=$1
LicenseFile=$2
CurrentDir=$3

cd $CurrentDir
export LM_LICENSE_FILE=$LicenseFile
mkdir -p gen && cd gen && rm -rf tmp && mkdir -p tmp && cd tmp
cp -R $EmbeddedDir/examples/hardware/cv_soc_devkit_ghrd/{design_config.tcl,create_ghrd_quartus.tcl} .
qsys-script --script=../../gen_soc_system_qsys.tcl &> qsys_script.log
patch -F 5 < ../../soc_system_qsys.patch
quartus_sh --script=create_ghrd_quartus.tcl &> quartus_sh.log
qsys-generate soc_system.qsys --synthesis=VHDL &> qsys_generate.log
cp soc_system/synthesis/submodules/{*.sv,*.v,*.hex} ..
cp soc_system/synthesis/soc_system.qip ..
cp soc_system.{qpf,qsf,qsys,sopcinfo} ..
cp qsys_script.log quartus_sh.log qsys_generate.log ..
cd .. && rm -rf tmp && date > timestamp-gen_hps_src_files

