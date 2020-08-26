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

# Makefile fragment for HDL primitives, cores, and workers etc.
# 'pre' means should be included before anything else
# This file is target and tool independent: LET's KEEP IT THAT WAY
# This file will be included at the start of:
#  primitive libraries
#  imported cores
#  workers
#  device workers
#  platforms
#  assemblies
#  containers

ifndef __HDL_PRE_MK__
__HDL_PRE_MK__=x
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk

# Default for everything
ifndef ParamConfigurations
ParamConfigurations=0
endif
################################################################################
# Determine the Worker Name very early, and the name of its XML file, and its
# language, in all the modes that are worker
ifneq ($(filter platform assembly worker,$(HdlMode)),)
  ifdef Workers
    ifneq ($(words $(Workers)),1)
      $(error Only one HDL worker can be built here.  Workers is: $(Workers).  Use "Worker=")
    endif
  endif
#  HdlXmlFile:=$(Worker_$(Worker)_xml)
endif
#$(call OcpiDbgVar,HdlXmlFile)
$(call OcpiDbgVar,Worker)
#$(call OcpiDbgVar,Worker_$(Worker)_xml)

################################################################################
# Determine the language and suffix, which might mean looking in the xml file
#
HdlVerilogSuffix:=.v
HdlVerilogIncSuffix:=.vh
HdlVHDLSuffix:=.vhd
HdlVHDLIncSuffix:=.vhd

#ifndef OcpiLanguage
#  $(error NO LANGUAGE)
#endif # HdlLanguage not initially defined (probably true)

HdlLanguage:=$(OcpiLanguage)
$(call OcpiDbgVar,HdlLanguage)
ifeq ($(HdlLanguage),verilog)
HdlSourceSuffix:=$(HdlVerilogSuffix)
HdlIncSuffix:=$(HdlVerilogIncSuffix)
HdlOtherSourceSuffix:=$(HdlVHDLSuffix)
HdlOtherIncSuffix:=$(HdlVHDLIncSuffix)
HdlOtherLanguage:=vhdl
else
HdlSourceSuffix:=$(HdlVHDLSuffix)
HdlIncSuffix:=$(HdlVHDLIncSuffix)
HdlOtherSourceSuffix:=$(HdlVerilogSuffix)
HdlOtherIncSuffix:=$(HdlVerilogIncSuffix)
HdlOtherLanguage:=verilog
endif
$(call OcpiDbgVar,HdlSourceSuffix)

# This is redundant with what is in worker.mk, when that file is included, but sometimes it isn't
override HdlExplicitLibraries:=$(call Unique,$(HdlLibraries) $(Libraries) $(HdlExplicitLibraries))
####################################################################################################
# Construct (deferred) the list of all HDL primitive libraries needed for this asset.
# This includes searching for explicitly requested libraries (what the source code needs),
# and built-in/default libraries that are always needed. Note this is evaluated deferred in a
# context when HdlTarget is set, but can also just supply it as $1.  The returned list is of the
# form <path>:<lib>, where if the library is in the global namespace <lib> is the same as basename
# <path>, but when the library is in the qualified namespace it is qualified
override HdlLibrariesInternal=$(infox HLI:$1:$(HdlTarget):$(HdlExplicitLibraries))$(strip \
$(if $(findstring clean,$(MAKECMDGOALS)),,\
$(foreach l,$(call Unique,\
              $(- first process explicitly supplied libraries)\
              $(foreach p,$(HdlExplicitLibraries),\
                $(if $(findstring /,$p),\
                  $(info Warning:  HDL primitive libraries specified with pathnames is deprecated:$p)\
                  $(or $(and $(call HdlExists,$p),$p:$(notdir $p)),\
                       $(error Primitive library $p (from HdlLibraries or Libraries) not found.)),\
                  $(call HdlSearchPrimitivePath,$p,,HPLHLI)))\
              $(- second, unless suppressed, add the libraries that are automatically included all the time)\
              $(if $(HdlNoLibraries),,\
	        $(if $(filter library core,$(HdlMode)),,\
                  $(foreach f,$(call HdlGetFamily,$(or $(HdlTarget),$1)),\
                    $(foreach v,$(call HdlGetTop,$f),$(infox VVV:$v)\
	              $(foreach x,$(filter-out $(LibName),fixed_float ocpi ocpi.core.bsv cdc),\
                        $(call HdlSearchPrimitivePath,$x,,HLI))))))),\
  $(infox HLI:returning $l)$l)))

# For use by some tools
define HdlSimNoLibraries
HdlToolPost=$$(HdlSimPost)
HdlToolLinkFiles=$$(call Unique,\
  $$(HdlToolFiles) \
  $$(foreach f,$$(DefsFile) $$(ImplHeaderFiles),\
     $$(call FindRelative,$$(TargetDir),$$(f))))
endef

################################################################################
# Target processing.
$(call OcpiDbgVar,HdlTarget)
$(call OcpiDbgVar,HdlTargets)
$(call OcpiDbgVar,HdlPlatform)
$(call OcpiDbgVar,HdlPlatforms)
$(eval $(HdlPreprocessTargets))
$(call OcpiDbgVar,HdlTarget)
$(call OcpiDbgVar,HdlTargets)
$(call OcpiDbgVar,HdlPlatform)
$(call OcpiDbgVar,HdlPlatforms)

ifneq ($(xxfilter platform container,$(HdlMode)),)
  HdlPlatform:=$(or $(HdlMyPlatform),$(CwdName))
  ifdef HdlPlatforms
    ifeq ($(filter $(HdlPlatform),$(HdlPlatforms)),)
      $(info Skipping this platform ($(HdlPlatform)) since it is not in HdlPlatforms ($(HdlPlatforms)))
      HdlSkip:=1
    endif
  endif
  HdlPlatforms:=$(HdlPlatform)
  HdlExactPart:=$(HdlPart_$(HdlPlatform))
  override HdlTarget:=$(call HdlGetFamily,$(HdlPlatform))
  override HdlActualTargets:=$(HdlTarget)
else # now for builds that accept platforms and targets as inputs
  ifneq ($(MAKECMDGOALS),clean)
    # Make sure all the platforms are present
    $(foreach p,$(HdlPlatforms) $(HdlPlatform),\
      $(if $(filter $p,$(HdlAllPlatforms)),,$(error $p not an available HDL platform)))
  endif
# The general pattern is:
# If Target is specified, build for that target.
# If Targets is specified, build for all, BUT, if they need
# different toolsets, we recurse into make for each set of targets that has a common
# set of tools

$(call OcpiDbgVar,OnlyTargets)
# Map "all" and top level targets down into "families"
HdlActualTargets:=$(strip \
  $(call Unique,\
    $(foreach t,$(HdlTargets),\
              $(if $(findstring $t,all)$(findstring $t,$(HdlTopTargets)),\
                   $(call HdlGetFamily,$t,x),\
                   $t))))
$(call OcpiDbgVar,HdlActualTargets)
# Map "only" targets down to families too
HdlOnlyTargets:=$(strip \
  $(call Unique,\
     $(foreach t,\
               $(or $(OnlyTargets),all),\
               $(if $(findstring $(t),all)$(findstring $(t),$(HdlTopTargets)),\
                    $(call HdlGetFamily,$(t),x),\
                    $(t)))))
$(call OcpiDbgVar,HdlOnlyTargets)
# Now prune to include only targets mentioned in OnlyTargets
# Question is:  for each target, is it in onlytargets?
# We know that we all at the family level or the part level
# So we have several cases, other than pure matches
# target is family, only is part
#  -- replace with part.
# target is part, only is family
#  -- replace with part
HdlPreExcludeTargets:=$(HdlActualTargets)
$(call OcpiDbgVar,HdlPreExcludeTargets,Before only: )
HdlActualTargets:=$(call Unique,\
              $(foreach t,$(HdlActualTargets),\
		 $(or $(filter $(t),$(HdlOnlyTargets)), \
                   $(and $(filter $(t),$(HdlAllFamilies)), \
		     $(foreach o,$(HdlOnlyTargets), \
		       $(if $(filter $(t),$(call HdlGetFamily,$(o))),$(o)))), \
                   $(foreach o,$(HdlOnlyTargets),\
		      $(if $(filter $(o),$(call HdlGetFamily,$(t))),$(t))))))
$(call OcpiDbgVar,HdlActualTargets,After only: )
# Now prune to exclude targets mentioned in ExcludeTargets
# We don't expand families into constituents, but we do
# convert a family into its parts if some of the parts are excluded
$(call OcpiDbgVar,ExcludeTargets,Makefile exclusions: )
$(call OcpiDbgVar,OCPI_EXCLUDE_TARGETS,Environment exclusions: )
ExcludeTargetsInternal:=\
$(call Unique,$(foreach t,$(ExcludeTargets) $(OCPI_EXCLUDE_TARGETS),\
         $(if $(and $(findstring $t,$(HdlTopTargets)),$(HdlTargets_$t)),\
             $(HdlTargets_$t),$t)))

$(call OcpiDbgVar,ExcludeTargetsInternal)
HdlActualTargets:=$(call Unique,\
 $(foreach t,$(HdlActualTargets),\
   $(if $(findstring $t,$(ExcludeTargetsInternal)),,\
      $(if $(findstring $t,$(HdlAllFamilies)),\
	  $(if $(filter $(HdlTargets_$t),$(ExcludeTargetsInternal)),\
	      $(filter-out $(ExcludeTargetsInternal),$(HdlTargets_$t)),\
              $(t)),\
          $(if $(findstring $(call HdlGetFamily,$t),$(ExcludeTargetsInternal)),,\
               $t)))))
$(call OcpiDbgVar,HdlActualTargets,After exclusion: )
override HdlTargets:=$(HdlActualTargets)

endif # End of else of platform-specific modes

ifndef HdlSkip
HdlFamilies=$(call HdlGetFamilies,$(HdlActualTargets))
$(call OcpiDbgVar,HdlFamilies)

HdlToolSets=$(call Unique,$(foreach t,$(HdlFamilies),$(call HdlGetToolSet,$t)))
# We will already get an error if there are no toolsets.
$(call OcpiDbgVar,HdlToolSets)
ifneq ($(HdlMode),worker)
# In all non-worker cases, if SourceFiles is not specified in the Makefile,
# we look for any relevant
$(call OcpiDbgVar,SourceFiles,Before searching: )
ifneq ($(origin SourceFiles),undefined)
AuthoredSourceFiles:=$(SourceFiles)
else
AuthoredSourceFiles:=$(call OcpiPullPkgFiles,$(wildcard *.[vV]) $(wildcard *.vhd) $(wildcard *.vhdl))
endif
$(call OcpiDbgVar,AuthoredSourceFiles,After searching: )
endif

################################################################################
# Now we decide whether to recurse, and run a sub-make per toolset, or, if we
# have only one toolset for all our targets, we just build for those targets in
# this make process.
ifneq ($(word 2,$(HdlToolSets)),)
################################################################################
# So here we recurse.  Note we are recursing for targets and NOT platforms.
$(call OcpiDbg,=============Recursing with all: HdlToolSets=$(HdlToolSets))
all: $(HdlToolSets)
install: $(HdlToolSets:%=install_%)
stublibrary: $(HdlToolSets:%=stublibrary_%)
define HdlDoToolSet
$(1):
	$(AT)$(MAKE) -L --no-print-directory \
	   HdlPlatforms="$(call HdlGetTargetsForToolSet,$(1),$(HdlPlatforms))" HdlTarget= \
           HdlTargets="$(call HdlGetTargetsForToolSet,$(1),$(HdlActualTargets))"

stublibrary_$(1):
	$(AT)$(MAKE) -L --no-print-directory HdlPlatforms= HdlTarget= \
           HdlTargets="$(call HdlGetTargetsForToolSet,$(1),$(HdlActualTargets))" \
	   stublibrary

install_$(1):
	$(AT)$(MAKE) -L --no-print-directory HdlPlatforms= HdlTarget= \
           HdlTargets="$(call HdlGetTargetsForToolSet,$(1),$(HdlActualTargets))" \
           install
endef
$(foreach ts,$(HdlToolSets),$(eval $(call HdlDoToolSet,$(ts))))
# this "skip" tells the file that included this file, that it shouldn't do anything
# after including this file, and thus "skip" the rest of its makefile.
HdlSkip:=1

################################################################################
# Here is where we ended up with nothing to do due to filtering
else ifeq ($(HdlToolSets)$(filter skeleton,$(MAKECMDGOALS)),)
$(call OcpiDbg,=============No tool sets at all, skipping)
ifneq ($(MAKECMDGOALS),clean)
  ifdef HdlPreExcludeTargets
    $(info Not building $(HdlMode) for these filtered (only/excluded) HDL targets: $(HdlPreExcludeTargets))
  else
    $(infox No HDL targets to build for.  Perhaps you want to set OCPI_HDL_PLATFORM for a default?)
  endif
endif
HdlSkip:=1
install:
else
################################################################################
# Here we are NOT recursing, but simply build targets for one toolset in this
# make.
$(call OcpiDbg,=============Performing for one tool set: $(HdlToolSets).)
HdlSkip=
HdlToolSet=$(HdlToolSets)
$(call OcpiDbgVar,HdlToolSet)

ifneq ($(HdlToolSet),)
include $(OCPI_CDK_DIR)/include/hdl/$(HdlToolSet).mk
#ifneq ($(findstring platform,$(HdlMode)),)
#HdlToolNeedBB:=
#endif
ifneq ($(findstring $(HdlToolSet),$(HdlSimTools)),)
HdlSimTool=yes
endif
endif # we have a tool set
endif # for multiple tool sets.

################################################################################
# These are rules for both recursive and non-recursive cases.
clean:: cleanfirst
	$(AT)$(if $(findstring $(HdlMode),worker),,\
		echo Cleaning HDL $(HdlMode) `pwd` for all targets.;)\
	rm -r -f $(OutDir)target-* $(OutDir)gen

cleanfirst::
cleanimports::
	rm -r -f imports

ImportsDir=imports

endif # include this once
endif # top level skip
