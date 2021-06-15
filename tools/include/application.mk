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

# This file is for an application directory whose name is the name of the app.
#
# The "app" is either the foo.{cc,cxx,cpp} or foo.xml

include $(OCPI_CDK_DIR)/include/util.mk

ifeq ($(filter speclinks workersfile,$(MAKECMDGOALS)),)
$(OcpiIncludeAssetAndParent)
# If library path is unset, provide a default
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
  $(eval $(OcpiEnsureToolPlatform))
  ifndef OCPI_LIBRARY_PATH
    $(call OcpiSetDefaultLibraryPath)
  endif
  ifndef AT
    $(info OCPI_LIBRARY_PATH=$(OCPI_LIBRARY_PATH))
  endif
endif

# Allow old-style "APP" to rename
ifdef APP
OcpiApp:=$(APP)
endif
ifndef OcpiApp
OcpiApp:=$(CwdName)
endif

# The existence of a C++ app file determines if this is an ACI app
OcpiAppCC:=$(strip\
  $(foreach s,cc cxx cpp,$(wildcard $(addsuffix .$s,$(call Unique,$(OcpiApp) $(OcpiApps))))))
ifdef OcpiAppCC
  OcpiApps:=$(call Unique,$(OcpiApp) $(OcpiApps))
  include $(OCPI_CDK_DIR)/include/aci.mk
  # If we are running in this Makefile, then we are running the TOOL_PLATFORM
  ifndef OcpiRunCC
    OcpiRunCC=$(OcpiRunBefore) $(OCPI_VALGRIND) $(call AciExe,$(OCPI_TOOL_PLATFORM),$(OcpiApp)) $(OcpiRunArgs) \
              $(OcpiRunAfter)
  endif
  all: aciapps
  ifndef OcpiAppNoRun
    run: all
	$(AT)echo Executing the $(OcpiApp) application.
	$(AT)$(OcpiRunCC)
  endif
else ifneq ($(wildcard $(OcpiApp).xml),)
  ifndef OcpiAppNoRun
    ifndef OcpiRunXML
      OcpiRunXML=$(OcpiRunBefore) $(OCPI_VALGRIND) $(OCPI_CDK_DIR)/$(OCPI_TOOL_DIR)/bin/ocpirun $(OcpiRunArgs) $1 \
                 $(OcpiRunAfter)
    endif
    run: all
	$(AT)echo Executing the $(OcpiApp).xml application.
	$(AT)$(call OcpiRunXML,$(OcpiApp).xml)
  endif
else
  $(info No application found when looking for: $(OcpiApp).xml, $(OcpiApp).{cc,cxx,cpp})
  ifndef OcpiAppNoRun
    run:
  endif
endif
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
  ifneq ($(wildcard components),)
    ifeq ($(call OcpiGetDirType,components),library)
        export OCPI_PROJECT_DIR
        export OCPI_PROJECT_REL_DIR
        export OCPI_PROJECT_PACKAGE
        export OCPI_PROJECT_DEPENDENCIES
        export OCPI_PROJECT_COMPONENT_LIBRARIES
        export OCPI_PROJECT_DIR
all:
	$(AT)OCPI_PROJECT_REL_DIR=$(OCPI_PROJECT_REL_DIR)/.. MAKEFLAGS= \
	     ocpidev -d components build
clean::
	$(AT)ocpidev -d components clean
    endif
  endif
endif

clean::
	$(AT)[ ! -d components ] || \
             $(MAKE) clean -C components \
               $(if $(wildcard components/Makefile),,-f $(OCPI_CDK_DIR)/include/library.mk)
	$(AT)rm -r -f *~ timeData.raw simulations lib gen
endif # avoid speclinks and workersfile
