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

$(if $(realpath $(OCPI_CDK_DIR)),,\
  $(error The OCPI_CDK_DIR environment variable is not set correctly.))

# Note moving this to the platform worker xml didn't work
# the tools complained about axi and sdp not being compiled
# moving them back here fixed those issues
Libraries=cyclone5 axi sdp

include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk

SourceFiles=gen/soc_system.qip

# Below gets a little ugly due to generation dates or unique generation IDs showing up 
# in the lines of context in the .qip and .qsf patch files, creating a modified
# version of the patch files that contain the dates and unique IDs so that the patch 
# works correctly

all: gen/soc_system.qip gen/soc_system.qsf gen/soc_system.qsys gen/soc_system.sopcinfo

gen/soc_system.qip:
	@cp ../../primitives/cyclone5/gen/soc_system.qip gen && cd gen && string1=$$(grep SLD_INFO soc_system.qip) && \
	sed "16s/.*/ $$string1/" ../soc_system_qip.patch > soc_system_qip.patch2 && \
	patch -F 5 < soc_system_qip.patch2 && rm -rf soc_system_qip.patch2

gen/soc_system.qsf:
	@cp ../../primitives/cyclone5/gen/soc_system.qsf gen && cd gen && string2=$$(grep ORIGINAL_QUARTUS_VERSION soc_system.qsf) && \
	string3=$$(grep PROJECT_CREATION_TIME_DATE soc_system.qsf) && string4=$$(grep LAST_QUARTUS_VERSION soc_system.qsf) && \
	sed "11s/.*/ $$string2/" ../soc_system_qsf.patch > soc_system_qsf.patch2 && sed -i "12s/.*/ $$string3/" soc_system_qsf.patch2 && \
	sed -i "13s/.*/ $$string4/" soc_system_qsf.patch2 && patch -F 5 < soc_system_qsf.patch2 && rm -rf soc_system.qsf.orig soc_system_qsf.patch2 && \
	mv soc_system.qsf cyclone5_sockit.qsf

gen/soc_system.qsys:
	@cp ../../primitives/cyclone5/gen/soc_system.qsys gen && cd gen && patch -F 5 < ../soc_system_qsys.patch

gen/soc_system.sopcinfo:
	@cp ../../primitives/cyclone5/gen/soc_system.sopcinfo gen && cd gen && patch -F 5 < ../soc_system_sopcinfo.patch

include $(OCPI_CDK_DIR)/include/hdl/hdl-platform.mk

