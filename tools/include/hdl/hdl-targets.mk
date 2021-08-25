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

ifndef _HDL_TARGETS_
_HDL_TARGETS_=here
# Include this here so that hdl-targets.mk (this file) can be included on its own when
# things like HdlAllPlatforms is required.
include $(OCPI_CDK_DIR)/include/util.mk

# IncludeProject is so that platforms in the current project are discovered even if not registered
# because this will set OCPI_PROJECT_DIR etc.
$(OcpiIncludeProject)

# This file gets the database of hdl targets and associated tools from python
# It is a "leaf file" that is used in several places.
# The database is a set of variable assignments

# Initialize the HDL database from python
HdlTargetPython:=python3 -c "import _opencpi.util as ou; print(ou.get_platform_variables(False,\"hdl\"))"
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
  # take the assignments one per line, and set the variables (do the TRs in python?)
  $(if $(call DoShell,set -o pipefail && $(HdlTargetPython)|tr "\n" "@"|tr " " "~",HdlTargetProps),\
    $(error Failed to process HDL platforms and targets: $(HdlTargetProps)),\
    $(foreach var,$(subst @, ,$(HdlTargetProps)),$(eval $(subst ~, ,$(var)))))
  $(call OcpiDbgVar,HdlAllFamilies)
  $(call OcpiDbgVar,HdlAllPlatforms)
  $(call OcpiDbgVar,HdlBuiltPlatforms)
  # The environment variables that will flow to subprocesses and submakes
  export OCPI_ALL_HDL_TARGETS:=$(HdlAllTargets)
  export OCPI_ALL_HDL_PLATFORMS:=$(strip $(HdlAllPlatforms))
  export OCPI_BUILT_HDL_PLATFORMS:=$(strip $(HdlBuiltPlatforms))
endif
endif
