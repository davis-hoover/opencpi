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

# This makefile is for building a set of assemblies, each in their own subdirectory

# Capture whatever is in the current file, allowing more to be reset in the project file
include $(OCPI_CDK_DIR)/include/util.mk
$(OcpiIncludeProject)
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk

ifndef
JOB_STARTTIME:=$(shell date +"%H:%M:%S")
endif

# We make this sort of like building a component library because
# for each application we are indeed making a "worker", and then we go
# on to make bitstreams for platforms.
LibDir=$(OutDir)lib
GenDir=$(OutDir)gen
ifndef OutDir
ifdef OCPI_OUTPUT_DIR 
PassOutDir=OutDir=$(call AdjustRelative,$(OutDir:%/=%))/$@
endif
endif
# We use the "internal" versions of variables to allow subsidiary makefiles to
# simply set those variables again
ifeq ($(origin Assemblies),undefined)
  Assemblies:=$(shell for i in *; do if test -d $$i -a -f $$i/$$(basename $$i).xml; then echo $$i; fi; done)
endif
override Assemblies:=$(filter-out $(ExcludeAssemblies),$(Assemblies))

all: $(Assemblies)

.PHONY: $(Assemblies) $(Platforms) $(Targets) clean

ifdef Assemblies
$(Assemblies):
ifneq (none,$(Assemblies))
	$(AT)echo =============Building assembly $@
ifneq (,$(JENKINS_HOME))
	$(AT)echo "============= ($(shell date +"%H:%M:%S"), started $(JOB_STARTTIME))"
endif
	$(AT)$(MAKE) -L -C $@ \
               $(if $(wildcard $@/Makefile),,-f $(OCPI_CDK_DIR)/include/hdl/hdl-assembly.mk) \
               $(HdlPassTargets) \
	       $(and $(OCPI_PROJECT_REL_DIR),OCPI_PROJECT_REL_DIR=../$(OCPI_PROJECT_REL_DIR)) \
	       LibDir=$(call AdjustRelative,$(LibDir)) \
	       GenDir=$(call AdjustRelative,$(GenDir)) \
	       ComponentLibrariesInternal="$(call OcpiAdjustLibraries,$(ComponentLibrariesInternal))" \
	       $(PassOutDir)
else
	$(AT)true
endif
endif

clean:
	$(AT)set -e;\
             $(foreach a,$(Assemblies),\
		echo Cleaning assembly: $a ; \
		$(MAKE) -C $a $(if $(wildcard $a/Makefile),,-f $(OCPI_CDK_DIR)/include/hdl/hdl-assembly.mk) clean;)
	$(AT)rm -r -f $(LibDir) $(GenDir)

ifdef ShellAssembliesVars
showassemblies:
	$(info Assemblies="$(Assemblies)";)
endif
