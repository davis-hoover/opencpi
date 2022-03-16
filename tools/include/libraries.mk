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

ifndef OCPI_PROJECT_REL_DIR
  $(eval $(call OcpiSetProject,..))
endif
ifndef Libraries
  Libraries=$(call OcpiFindSubdirs,library)
endif

DoLibGoal=$(AT)\
  set -e; \
  $(foreach l,$(Libraries),\
    echo ====== Entering library $l for goal: $(or $2,$@); \
    $(MAKE) -C $l $(if $(wildcard $l/Makefile),,-f $(OCPI_CDK_DIR)/include/library.mk) \
            OCPI_PROJECT_REL_DIR=../$(OCPI_PROJECT_REL_DIR) $(or $2,$@) &&):

Goals=run declare $(Models) comp $(Models:%=clean%) cleancomp $(OcpiTestGoals)

.PHONY: $(Goals) allx docs clean

$(Goals):
	$(call DoLibGoal,$(MAKE))

docs:
	$(AT)ocpidoc build -b

allx:
	$(AT)$(call DoLibGoal,$(MAKE),all)

all: $(if $(filter 1,$(OCPI_DOC_ONLY)),docs,allx $(if $(filter 1,$(OCPI_NO_DOC)),,docs))

clean:
	$(AT)$(call DoLibGoal,$(MAKE),clean)
	$(AT)rm -r -f gen

# these ensure that recursive makes do not build docs
override export OCPI_NO_DOC=1
override export OCPI_DOC_ONLY=
