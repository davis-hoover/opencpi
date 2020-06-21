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

# Generic top level worker makefile
include $(OCPI_CDK_DIR)/include/util.mk
# Plain workers do not have their own package-id file
# They inherit the containing library's package-id
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
$(call OcpiIncludeAssetAndParent)
endif
ifndef Model
  $(error This directory named $(CwdName) does not end in any of: $(Models))
endif
ifdef Worker
  ifdef Workers
    $(error Cannot set both Worker and Workers variables in Makefile)
  else
    override Workers:=$(Worker)
  endif
else ifeq ($(origin Workers),file)
  override Worker:=$(firstword $(Workers))
else
  override Worker:=$(CwdName)
  override Workers:=$(Worker)
endif
$(call OcpiDbgVar,Worker)
$(call OcpiDbgVar,Workers)
# Now we must figure out the language since so many other things depend on it.
# But we want to keep the language in the XML and not in the Makefile
ImplXmlFiles:=$(Workers:%=%.xml)
$(foreach w,$(Workers),$(eval Worker_$w_xml:=$w.xml))

ifeq ($(MAKECMDGOALS),clean)
# Clean default OWD files when they are the default
$(foreach w,$(Workers),\
  $(if $(wildcard $(Worker_$w_xml)),\
    $(and $(call OcpiDefaultSpec,$w),$(shell if echo "$(call OcpiDefaultOWD,$w,$(Model))" | cmp -s - $(Worker_$w_xml); \
                  then echo hi; fi),\
	$(info The file $(Worker_$w_xml) has default contents and could be removed.))))

#        $(shell rm $(Worker_$w_xml)))))

else
# Create default OWD files when they don't exist
$(foreach w,$(Workers),\
     $(if $(wildcard $(Worker_$w_xml)),,\
	 $(and \
            $(info Creating a default OWD in $(Worker_$w_xml) since it does not exist.)\
            $(shell echo "$(call OcpiDefaultOWD,$w,$(Model))" > $(Worker_$w_xml)),\
          )))
endif

$(eval $(call OcpiSetLanguage,$(ImplXmlFiles)))
$(call OcpiDbgVar,Workers)
$(call OcpiDbgVar,Worker)

ifeq (X$(filter rcc,$(Model))$(filter clean%,$(MAKECMDGOALS))$($(CapModel)Target)$($(CapModel)Targets)$($(CapModel)Platform)$($(CapModel)Platforms),)
  $(info This $(UCModel) worker $(Worker) was not built since no $(UCModel) targets or platforms specified)
else
  # Add any inbound command line libraries to what is specified in the makefile
  # This list is NOT target dependent
  # This variable is immediately assigned here and indicates what libraries might be
  # explicitly referenced by local source code.
  # This assignment is redundant with what is in hdl-pre.mk, but it is needed here earlier than that
  # and we don't yet have something like: include $(Model)-pre.mk
  override $(CapModel)ExplicitLibraries:=$(call Unique,$($(CapModel)Libraries) $(Libraries) $($(CapModel)ExplicitLibraries))
  $(info override $(CapModel)ExplicitLibraries:=$(call Unique,$($(CapModel)Libraries) $(Libraries) $($(CapModel)ExplicitLibraries)))
  $(call OcpiDbgVar,$(CapModel)ExplicitLibraries)
  $(if $(filter clean%,$(MAKECMDGOALS)),,$(eval $(OcpiProcessBuildFiles)))
  include $(OCPI_CDK_DIR)/include/$(Model)/$(Model)-worker.mk
endif
