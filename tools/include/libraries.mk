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

# This file is the make file for a group of component libraries

include $(OCPI_CDK_DIR)/include/util.mk

ifndef Libraries
  Libraries=$(call OcpiFindSubdirs,library)
endif

DoLibGoal=$(AT)\
  set -e; \
  $(foreach l,$(Libraries),\
    echo ====== Entering library $l for goal: $@; \
    $(MAKE) -C $l $(if $(wildcard $l/Makefile),,-f $(OCPI_CDK_DIR)/include/library.mk) \
            OCPI_PROJECT_REL_DIR=../$(OCPI_PROJECT_REL_DIR) $@ &&):

Goals=run all declarehdl clean $(Models) $(Models:%=clean%) $(OcpiTestGoals)

.PHONY: $(Goals)

$(Goals):
	$(call DoLibGoal,$(MAKE))

