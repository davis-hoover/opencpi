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

# This is the makefile contents for the hdl/primitives directory in a project.
# The variables that drive it are:
#
# Libraries
# Cores

include $(OCPI_CDK_DIR)/include/util.mk
# Set the hdl/primitives' parent asset to be the Project, and enforce that it
# use the authoring model prefix of 'hdl'.
# So, Package-ID of the hdl/primitives dir will be default look like:
#   <project>.hdl.primitives
# Default the PrimitiveLibraries and PrimitiveCores variables
ifeq ($(filter-out undefined,$(origin PrimitiveLibraries) $(origin Libraries)),)
  Libraries:=$(foreach d,$(notdir $(wildcard *)),$(infox d:$d)\
               $(and $(wildcard $d/Makefile $d/$d.xml),\
                 $(foreach t,$(call OcpiGetDirType,$d),$(infox t:$t)\
                   $(and $(filter hdl-library hdl-lib,$t),$d))))
  $(infox FOUND PRIMITIVE LIBRARIES:$(Libraries))
else
  Libraries:=$(call Unique,$(Libraries) $(PrimitiveLibraries))
endif
ifeq ($(filter-out undefined,$(origin PrimitiveCores) $(origin Cores)),)
  Cores:=$(foreach d,$(wildcard */Makefile),$(infox d:$d)\
                    $(foreach p,$(patsubst %/,%,$(dir $d)),$(infox p:$p)\
                      $(foreach t,$(call OcpiGetDirType,$p),$(infox t:$t)\
                        $(and $(filter hdl-core,$t),$p))))
  $(infox FOUND PRIMITIVE CORES:$(PrimitiveCores))
else
  Cores:=$(call Unique,$(Cores) $(PrimitiveCores))
endif
$(call OcpiIncludeAssetAndParent,,hdl)

include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk

ifndef HdlInstallDir
  HdlInstallDir:=lib
endif
MyMake=$(MAKE) $(and $(HdlTargets),HdlTargets="$(HdlTargets)") -r --no-print-directory -C $1 \
  $(if $(wildcard $1/Makefile),,\
    -f $(foreach t,$(call OcpiGetDirType,$1),$(OCPI_CDK_DIR)/include/hdl/$t.mk))\
  OCPI_PROJECT_REL_DIR=$(call AdjustRelative,$(OCPI_PROJECT_REL_DIR)) \
  HdlInstallDir=$(call AdjustRelative,$(HdlInstallDir)) \

# If not cleaning and no platforms, don't bother
# Note we disable this check here since building with no platforms actually has beneficial side-effects
# for error checking workers etc.
ifeq (xxx$(HdlPlatform)$(HdlPlatforms)$(HdlTarget)$(HdlTargets)$(filter-out clean%,$(MAKECMDGOALS)),)
all:
	$(AT)echo No HDL platforms specified.  Skipping building of hdl primitives.
else
all: $(Libraries) $(Cores)
endif

hdl: all
# enable cores to use libs
$(Cores): $(Libraries)

clean: uninstall
	$(AT)$(foreach l,$(Libraries) $(Cores), $(call MyMake,$l) clean &&):

cleanimports:
	$(AT)$(foreach l,$(Libraries) $(Cores), $(call MyMake,$l) cleanimports &&):

install:
	$(AT)set -e;$(foreach l,$(Libraries) $(Cores),$(call MyMake,$l) install &&):

uninstall:
	$(AT)echo Removing all installed HDL primitives and codes from: ./lib
	$(AT)rm -r -f lib

.PHONY: $(Libraries) $(Cores)

define MakeCoreOrLib
	$(AT)$(call MyMake,$@)
endef

$(Libraries):
	$(AT)echo ============== For library $@:
	$(MakeCoreOrLib)

$(Cores):
	$(AT)echo ============== For core $@:
	$(MakeCoreOrLib)

ifdef ShellTestVars
showpackage:
	$(info Package="$(Package)";)
endif
