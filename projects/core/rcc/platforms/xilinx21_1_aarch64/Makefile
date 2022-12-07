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

AT=@
ALL=exports
.DELETE_ON_ERROR:
.PHONY: kernel-artifacts release-artifacts mod-release-artifacts exports
$(if $(wildcard $(OCPI_CDK_DIR)),,$(error OCPI_CDK_DIR not set or non-existent. This file requires it.))

include $(notdir $(CURDIR)).mk

OcpiXilinxDir=$(strip $(foreach t,$(or $(OCPI_XILINX_DIR),$(wildcard /opt/Xilinx),/tools/Xilinx),$(infox TT is $t)\
	                       $(if $(shell test -d $t && echo 1),$t,\
			                           $(call $(or $1,error), Directory $(if $(OCPI_XILINX_DIR),"$t" from OCPI_XILINX_DIR,/opt/Xilinx or /tools/Xilinx) not found))))

local_repo:=$(or $(OCPI_XILINX_GIT_REPOSITORY),$(call OcpiXilinxDir)/git)
xilinx_releases:=$(or $(OCPI_XILINX_ZYNQ_RELEASE_DIR),$(call OcpiXilinxDir,warning)/ZynqReleases)
exports_file:=$(notdir $(CURDIR)).exports

all: exports

gen:
	$(AT)mkdir gen

gen/kernel-artifacts.done: | gen 
	$(AT)rm -f $@
#	$(AT)echo Download Yocto source           These scripts were previously used to build 
#	$(AT)bash scripts/getYoctoSource.sh         the toolchain package now downloaded in the
#	$(AT)echo Build Yocto source                getToolchain.sh script and will remain here as a reference. 
#	$(AT)bash scripts/buildYoctoSource.sh
	$(AT)echo Download toolchain
	$(AT)bash scripts/getToolchain.sh	
	$(AT)echo Extract SDK and Wrap Toolchain
	$(AT)bash scripts/wrapToolchain.sh
	$(AT)touch $@

kernel-artifacts: gen/kernel-artifacts.done

# Retrieve the artifacts we need from the Xilinx Zynq binary release
gen/release-artifacts.done:
	$(AT)rm -f $@
	$(AT)bash scripts/importXilinxRelease.sh \
	    $(xilinx_version_tag) $(xilinx_releases) gen/release-artifacts $(local_repo)
	$(AT)touch $@

release-artifacts: gen/release-artifacts.done

# Retrieve the artifacts we need from the Xilinx Zynq binary release
gen/mod-release-artifacts.done:
	$(AT)rm -f $@
	$(AT)bash scripts/modifyXilinxRelease.sh
	$(AT)touch $@

release-artifacts: gen/mod-release-artifacts.done

exports: kernel-artifacts release-artifacts mod-release-artifacts
	$(AT)if [ -e $(exports_file) ] ; then \
               $$OCPI_CDK_DIR/scripts/export-platform.sh lib/; \
             else \
               echo Exports file \"$(exports_file)\" is not present.  No exporting done.; \
             fi

clean: 
	rm -r -f gen
