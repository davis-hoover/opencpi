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

# This file should be include in makefiles for hdl primitive libraries,
# compiled from sources.  The idea is to do as much precompilation as possible.
# Some tools do more than others, but this is a LIBRARY, which means we are not
# combining things together such that they can't be used separately.

# Tell all the general purpose and toolset make scripts we are building libraries
HdlMode:=library
Model:=hdl
include $(OCPI_CDK_DIR)/include/util.mk
$(call OcpiIncludeAssetAndParent)
include $(OCPI_CDK_DIR)/include/hdl/hdl-pre.mk
.PHONY: stublibrary
ifndef HdlSkip
ifdef LibName
  $(error Unexpected LibName vairable set to $(LibName))
else
LibName:=$(CwdName)
endif
OcpiLibDot:=_
QualifiedLibName:=$(and $(filter qualified,$(NameSpace)),$(subst .,$(OcpiLibDot),$(OCPI_PROJECT_PACKAGE).))$(CwdName)
ifndef WorkLib
WorkLib:=$(QualifiedLibName)
endif
ifdef HdlToolNeedBB
stublibrary: install
else
stublibrary:
	$(AT)echo No stub library necessary for: $(HdlActualTargets)
endif

include $(OCPI_CDK_DIR)/include/hdl/hdl-lib2.mk

# if there isnt a install dir set assume we are in a primitives library ans install them in ../lib
ifeq ($(HdlInstallDir)$(HdlInstallLibDir),)
  HdlInstallDir=../lib
  $(call OcpiIncludeAssetAndParent,..,hdl)
endif

# This can be overriden
HdlInstallLibDir=$(HdlInstallDir)/$(LibName)
$(HdlInstallLibDir):
	$(AT)echo Creating directory $@ for library $(LibName)
	$(AT)mkdir -p $@

install: $(OutLibFiles) | $(HdlInstallLibDir)
	$(AT)for f in $(HdlActualTargets); do \
	  $(call ReplaceIfDifferent,$(strip \
             $(OutDir)target-$$f/$(WorkLib)),$(strip \
             $(HdlInstallLibDir)/$$f)); \
	  $(call ReplaceIfDifferent,$(GeneratedDir)/$(LibName).libs,$(HdlInstallLibDir));\
	done

endif

ifneq ($(Imports)$(ImportCore)$(ImportBlackBox),)
include $(OCPI_CDK_DIR)/include/hdl/hdl-import.mk
endif

ifndef OcpiDynamicMakefile
$(OutLibFiles): Makefile
endif

$(eval $(HdlInstallLibsAndSources))

build: $(OutLibFiles)
install: build
all: install
