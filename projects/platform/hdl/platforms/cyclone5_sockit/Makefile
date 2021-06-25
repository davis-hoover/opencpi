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

UseCyclone5:=$(filter cyclone5,$(HdlTargets))


# Modify the following files to reflect things for the Cyclone V SOC Kit
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
  ifndef UseCyclone5 
   QipFile=gen/soc_system.qip
   ifeq  ($(wildcard $(QipFile)),) # if soc_system.qip not copied over yet
    $(if $(call DoShell, mkdir -p gen && cp ../../primitives/cyclone5/gen/soc_system.qip ../../primitives/cyclone5/gen/soc_system.qsys \
      ../../primitives/cyclone5/gen/soc_system.sopcinfo ../../primitives/cyclone5/gen/soc_system.qsf gen && cd gen/ && \
      ../edit_generated_files.sh && patch -F 5 < ../soc_system_qsys.patch && \
      mv soc_system.qsf cyclone5_sockit.qsf,MyError),\
      $(error $(MyError)))
   endif
  endif
endif

SourceFiles=gen/soc_system.qip

include $(OCPI_CDK_DIR)/include/hdl/hdl-platform.mk

