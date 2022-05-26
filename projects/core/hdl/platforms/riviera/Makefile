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

# The Riviera-PRO platform.
include $(OCPI_CDK_DIR)/include/hdl/hdl-platform.mk
ifneq ($(findstring riviera,$(HdlPlatforms)),)
# FIXME: integrate this with riviera.mk
# ModelsimExec=LD_PRELOAD=$(OCPI_CDK_DIR)/$(OCPI_TOOL_DIR)/lib/inode64.so $(OCPI_MODELSIM_DIR)/linuxpe/$1
probe.tgz:
	$(AT)echo Creating the tiny Riviera-PRO project for probing that Riviera-PRO is installed and licensed.
	$(AT)echo Output is in target-reiviera/probe.out
	$(AT)mkdir -p target-riviera
	$(AT)(rm -r -f tmp && mkdir -p tmp && cd tmp && \
	  export ALDEC_LICENSE_FILE=$(OCPI_RIVIERA_LICENSE_FILE) && \
	  echo 'module probe(); endmodule' > probe.v && \
	  $(OCPI_RIVIERA_DIR)/bin/vlib work && \
	  $(OCPI_RIVIERA_DIR)/bin/vdel -lib work -all && \
	  $(OCPI_RIVIERA_DIR)/bin/vlog -work work probe.v && \
	  tar czf ../probex.tgz work && \
	  $(OCPI_RIVIERA_DIR)/bin/vsim -c work.probe </dev/null && \
	  rm -f -r probe.v work && \
	  mv ../probe{x,}.tgz) > target-riviera/probe.out 2>&1

all: probe.tgz

clean::
	rm -r -f tmp
endif
