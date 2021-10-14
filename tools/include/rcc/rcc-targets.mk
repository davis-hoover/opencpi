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

##################################################################################################
# This file initializes the database of possible RCC Platforms, including os/os_version/arch info.
# This file is directly included when that info is needed.
# It does NOT read/include the software platform definition files for the details of the platform,
# but only teases out the os/os_version/arch aspects.
# It should be considered a leaf, light file, but it does depend on the project context
# since the set of available platforms is based on registered projects or OCPI_PROJECT_PATH.
# If it is not called in a project context, then the default registry is used.
#
# It does not call rcc-make or rcc-worker, they call it.
#
# This file will pull RCC platform information from the environment if is already set,
# avoiding any file system interaction/overhead.
# Otherwise it gets the database of rcc targets and associated tools from python
# The database is a set of variable assignments

ifndef RccAllPlatforms
ifdef OCPI_ALL_RCC_PLATFORMS
  # If the environment already has our database, import it into make variables
  RccAllPlatforms:=$(OCPI_ALL_RCC_PLATFORMS)
  RccAllTargets:=$(OCPI_ALL_RCC_TARGETS)
  $(foreach p,$(OCPI_RCC_PLATFORM_TARGETS),\
    $(eval RccTarget_$(word 1,$(subst =, ,$p)):=$(word 2,$(subst =, ,$p))))
else
  include $(OCPI_CDK_DIR)/include/util.mk
  # This is a big hammer here, since all we need is the registry.
  # FIXME: have a lighter weight way to do this.
  $(OcpiIncludeProject)

  # Initialize the RCC database from python
  RccTargetPython:=python3 -c "import _opencpi.util as ou; print(ou.get_platform_variables(False,\"rcc\"))"
  ifeq ($(filter clean%,$(MAKECMDGOALS)),)
    # take the assignments one per line, and set the variables (do the TRs in python?)
    $(if $(call DoShell,set -o pipefail && $(RccTargetPython)|tr "\n" "@"|tr " " "~",RccTargetProps),\
      $(error Failed to process RCC platforms and targets: $(RccTargetProps)),\
      $(foreach var,$(subst @, ,$(RccTargetProps)),$(eval $(subst ~, ,$(var)))))
    export OCPI_ALL_RCC_PLATFORMS:=$(RccAllPlatforms)
    export OCPI_ALL_RCC_TARGETS:=$(RccAllTargets)
    export OCPI_RCC_PLATFORM_TARGETS:=$(foreach p,$(RccAllPlatforms),$p=$(RccTarget_$p))
    $(call OcpiDbgVar,RccAllPlatforms)
    $(call OcpiDbgVar,RccAllTargets)
    $(foreach p,$(RccAllPlatforms),$(call OcpiDbgVar,RccTarget_$p))
  endif
endif # end of the info not being in the environment already
endif # end of variables not being set here
