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

# IncludeProject so that platforms in current project are discovered
$(OcpiIncludeProject)

# This file is the database of hdl targets and associated tools
# It is a "leaf file" that is used in several places.

# This is the list of top level targets.
# All other targets are some level underneath these
# The levels are: top, family, part, speed

###############################################################################
# Notes regarding HdlTargets:
#
# The HdlDefaultTarget_<family> is the one used for core building (primitives, workers...).
# If the default is unset, the first part in a family is the one used for core building.
# Usually the default should be the smallest so that you ensure each worker will fit
# on the smaller parts. If you want to ensure that worker-synthesis uses as many
# resources as necessary, you can set it to a larger part or set HdlExactPart
# for a worker or library.
#
# HdlPart_<platform> in a <platform>.mk file will define a full part. That part
# can be mapped to a part here and therefore a family as well.
# E.g. in zed.mk, HdlPart_zed=xc7z020-1-clg484, which maps to xc7z020, which
# maps to the 'zynq' family with a default target of xc7z020 for building pre-platform cores.
# In OpenCPI parts are always three hypen-separated fields roughly meaning:
# <die>-<speed_grade>-<package>
# Since vendors name parts in a variety of ways, and change their minds about
# part ordering formats, and use different formats between data sheets and tools,
# there is a tool-specific function, HdlFullPart_<tool> to translate between
# our canonical form, and the format that the tools like, which is *not*
# necessarily the "part ordering number" in data sheets etc.
###############################################################################

# Vendors
HdlTopTargets:=xilinx altera modelsim # icarus # verilator

###############################################################################
# Xilinx targets
###############################################################################
HdlTargets_xilinx:=isim virtex5 virtex6 artix7 spartan3adsp spartan6 zynq_ise zynq zynq_ultra xsim

HdlTargets_virtex5:=xc5vtx240t xc5vlx50t xc5vsx95t xc5vlx330t xc5vlx110t
HdlTargets_virtex6:=xc6vlx240t
HdlTargets_artix7:=xc7a50t

HdlTargets_spartan6:=xc6slx45
HdlTargets_spartan3adsp:=xc3sd3400a

# Zynq targets - supported by both ISE and Vivado
HdlTargets_zynq:=xc7z007s xc7z012s xc7z014s xc7z010 xc7z015 xc7z020 xc7z030 xc7z035 xc7z045 xc7z100 xc7z035i
# If building for zynq and no target is specified, default to the xc7z020
HdlDefaultTarget_zynq:=xc7z020
# Parts for zynq in ISE are the same as Vivado but with _ise_alias appended for internal differentiation
HdlTargets_zynq_ise:=$(foreach tgt,$(HdlTargets_zynq),$(tgt)_ise_alias)
# The line below is not needed because for ISE we just hand the tools the word "zynq" when
# compiling any zynq parts unless given an HdlExactPart
#HdlDefaultTarget_zynq_ise:=xc7z020_ise_alias
# Zynq UltraScale+ parts
# The last two letters mean: (ds891)
# ev: quad core, mali gpu, H.264
# eg: quad core, mali gpu
# cg: dual core
HdlTargets_zynq_ultra:=xczu28dr xczu9eg xczu7ev xczu3cg
# Zynq UltraScale+ chips require full part to be specified
# The default is based on the zcu104 dev board, which is the cheapest, and supported by webpack.
HdlDefaultTarget_zynq_ultra:=xczu3cg-2-sbva484e
# This is zcu104, but it is not available for older versions of Vivado: xczu7ev-2-ffvc1156e

###############################################################################
# Altera targets
###############################################################################
HdlTargets_altera:=arria10soc arria10soc_std stratix4 stratix5 cyclone5 # altera-sim

# The "k", when present indicates the transceiver count (k = 36)
# But in many places it is left off..
HdlTargets_stratix4:=ep4sgx230k ep4sgx530k ep4sgx360
HdlDefaultTarget_stratix4:=AUTO
HdlTargets_stratix5:=ep5sgsmd8k2
HdlDefaultTarget_stratix5:=AUTO

HdlTargets_arria10soc:=10AS066N3F40E2SG
# Quartus Pro (and maybe newer versions of standard) does not
# support the 'AUTO' part for arria10 because you cannot reuse
# synthesized partitions from different devices.
# We must enforce one exact part per target for Quartus Pro
# (and maybe newer/17+ versions of standard).
HdlDefaultTarget_arria10soc:=10AS066N3F40E2SG

HdlTargets_arria10soc_std:=10AS066N3F40E2SG_std_alias
HdlDefaultTarget_arria10soc_std:=10AS066N3F40E2SG_std_alias

HdlTargets_cyclone5:=5CSXFC6D6F31C8ES
HdlDefaultTarget_cyclone5:=AUTO


###############################################################################

HdlSimTools=isim icarus verilator ghdl xsim modelsim

# Tools are associated with the family or above
HdlToolSet_ghdl:=ghdl
HdlToolSet_isim:=isim
HdlToolSet_xsim:=xsim
HdlToolSet_modelsim:=modelsim
HdlToolSet_spartan3adsp:=xst
HdlToolSet_virtex5:=xst
HdlToolSet_virtex6:=xst
HdlToolSet_artix7:=vivado
HdlToolSet_spartan6:=xst
HdlToolSet_zynq_ise:=xst
HdlToolSet_zynq:=vivado
HdlToolSet_zynq_ultra:=vivado
HdlToolSet_verilator:=verilator
HdlToolSet_icarus:=icarus
HdlToolSet_stratix4:=quartus
HdlToolSet_stratix5:=quartus
HdlToolSet_arria10soc:=quartus_pro
HdlToolSet_arria10soc_std:=quartus
HdlToolSet_cyclone5:=quartus

# Call the tool-specific function to get the full part incase the
# tool needs to rearrange the different part elements
# If the tool does not define this function, return part as-is
# Arg1 is the full/exact part number
#HdlFullPart=$(or $(call HdlFullPart_$(HdlToolSet),$1),$1)
# In the platform and post-platform stages, get the part from the <platform>.mk
# In other stages, use the HdlExactPart if set, or the Default part if set,
# or the first part for this target
# Note that the return part is still in the opencpi canonical form
HdlChoosePart=$(foreach c,\
  $(if $(filter $(HdlMode),platform config container),\
    $(HdlPart_$(HdlPlatform)),\
    $(or \
      $(foreach p,$(HdlExactParts),$(strip\
        $(foreach f,$(word 1,$(subst :, ,$p)),\
          $(and $(filter $f,$(HdlTarget)),$(word 2,$(subst :, ,$p)))))),\
      $(HdlExactPart),\
      $(HdlDefaultTarget_$(HdlTarget)),\
      $(firstword $(HdlTargets_$(HdlTarget))))),$(infox CHOOSEPART:$c)$c)

# Make the initial definition as a simply-expanded variable
HdlAllPlatforms:=
HdlBuiltPlatforms:=

################################################################################
# These functions are here because this file is leaf and used when callers
# only want to know the facts about targets, without pulling in any other
# aspects of the HDL building machinery.
# Otherwise various HDL utilities are in hdl-make.mk which this file does not
# depend on.
################################################################################
HdlError:=error

# Deal with source vs. exported directories.
# <projdir>/hdl/platforms/<plat> (not exported at all)
# <projdir>/hdl/platforms/<plat>/lib (exported locally)
# <projdir>/exports/hdl/platform/<plat> (exported by project)

HdlProjectFromPlatformDir=$(infox HPFPD:$1)$(strip\
  $(or $(strip \
    $(foreach r,$(realpath $1),$(infox R:$r)\
      $(foreach path,$(if $(filter lib,$(notdir $r)),$(patsubst %/,%,$(dir $r)),$r),\
        $(foreach proj,$(patsubst %/hdl/platforms/$(notdir $(path)),%,$(path)),\
          $(infox HPFPDr:$(proj))$(proj))))),\
    $(error Platform directory $1 does not exist)))


# Return the list of project dependencies given the project dir
# Deal with old Project.mk vs newer Project.xml vs. exported project
OcpiProjectDependencies=$(infox HPD:$1)$(strip\
  $(if $(wildcard $1/project-dependencies),$(- are we an exported project?)\
    $(shell cat $1/project-dependencies),\
    $(if $(wildcard $1/Project.xml),\
      $(if $(call DoShell,\
             $(ToolsDir)/ocpixml  -t project -a '?ProjectDependencies' parse $1/Project.xml,\
             OcpiDeps),\
        $(error Failed to parse $1/Project.xml),\
        $(OcpiDeps)),\
      $(if $(wildcard $1/Project.mk),\
        $(shell sed -n 's/^ *ProjectDependencies:*= *\([^\#]*\)/\1/p' $1/Project.mk),\
        $(error Project directory $1 has no Project.xml or Project.mk file)))))

HdlProjectDepsFromPlatformDir=$(strip\
  $(call OcpiProjectDependencies,$(call HdlProjectFromPlatformDir,$1)))

HdlDoXmlPlatform=\
  $(foreach x,$(or $(wildcard $1/$2.xml),$(wildcard $1/lib/hdl/$2.xml),-),\
    $(and $(filter -,$x),\
      $(error HDL platform $2, at $1, has no $2.xml file?))\
    $(if $(call DoShell,\
           $(ToolsDir)/ocpixml  -t hdlplatform -a '?part' -a '?family' parse $x,\
           HdlPartAndFamily),\
      $(error Failed to parse $x: $(HdlPartAndFamily)),\
      $(eval HdlPart_$2:=$(firstword $(HdlPartAndFamily)))\
      $(if $(HdlPart_$2),,$(error No "part" attribute found in XML file $x for HDL Platform $2))\
      $(- if a family was specified for the part, check it against previous settings)\
      $(foreach f,$(word 2,$(HdlPartAndFamily)),\
        $(foreach t,$(HdlGetTargetFromPart),\
          $(if $(HdlFamily_$t),\
            $(if $(filter-out $f,$(HdlFamily_$t)),\
              $(error the HDL platform $2 specified family $f for part $(HdlPart_$2), but the family for that part was already specified as $(HdlFamily_$t)),\
              $(eval HdlFamily_$t:=$f)))))))

# Add a platform to the database.
# Arg 1: The directory where the *.mk file is
# Arg 2: The name of the platform
# Arg 3: The actual platform directory for using the platform (which may not exist).
#
# Include the <platform>.mk file found in the HDL platform directory
# If the HdlPart_<platform> set in the .mk file corresponds to a valid family,
#   add this platform to the list of all platforms, and record the directoy where it was found
#   if the family-specific directory exists in the platform's lib/ dir, an attempt has been
#     made to build it and therefore we add it to HdlBuiltPlatforms
# Otherwise (we cannot determine the family for HdlPart_<platform>, either warn or error
#   We only error here if the user actually specified this platform at the command line
#     (e.g. via HdlPlatform(s) or OCPI_HDL_PLATFORM)
HdlAddPlatform=\
  $(if $(HdlPlatformDir_$2),,\
    $(if $(wildcard $1/$2.mk),\
      $(- we assume the <plat>.mk file sets HdlPart_$2, and cannot set HdlFamily_$(HdlPart_$2))\
      $(eval include $1/$2.mk),\
      $(- otherwise we parse it out of the XML file, and maybe the family too)\
      $(call HdlDoXmlPlatform,$1,$2))\
    $(if $(call HdlGetFamily,$(HdlPart_$2)),\
      $(eval HdlAllPlatforms:=$(strip $(HdlAllPlatforms) $2))\
      $(eval HdlPlatformDir_$2:=$3)\
      $(if $(or \
             $(call OcpiExists,$3/lib/hdl/$(HdlFamily_$(HdlPart_$2))),\
             $(call OcpiExists,$3/hdl/$(HdlFamily_$(HdlPart_$2)))),\
        $(eval HdlBuiltPlatforms+=$2)),\
      $(call $(if $(filter $2,$(HdlPlatforms) $(HdlPlatform) $(OCPI_HDL_PLATFORM)),$(HdlError),warning),$(strip \
        HDL Platform '$2' was specified by user, but an appropriate HDL family cannot be \
        determined for its HdlPart_$2 of '$(HdlPart_$2)'. \
        Check '$(realpath $1/$2.mk)' to make sure HdlPart_$2 is set to a valid target part \
        supported by $(OCPI_CDK_DIR)/include/hdl/hdl-targets.mk. Reference other existing HDL \
        platforms for assistance))))

# Call this with a directory that is a platform's directory, either source (with "lib" subdir
# if built) or project-exported. For the individual platform directories we need to deal with
# the prebuilt, postbuilt, and exported scenarios.  Hence the complexity.
# The *.xml is always needed, but the *.mk may be used (and processed) on older platforms
# So we key on the *.xml file.
# If we are pointing at a non-exported platform directory, we prefer its local export subdir
# ("lib"), if the lib/hdl/*.xml is present.
# (under hdl since it is in fact a worker in a library)
HdlDoPlatform=\
  $(foreach p,$(notdir $1),\
    $(if $(wildcard $1/lib/hdl/$p.xml),\
      $(call HdlAddPlatform,$d,$p,$1/lib),\
      $(if $(call OcpiExists,$d/$p.xml),\
        $(call HdlAddPlatform,$d,$p,$d),\
        $(error no $p.xml file found for platform under: $1))))
# Handle a directory named "platforms", exported or not
HdlDoPlatformsDir=\
  $(- if the project has been exported at all, even without building, the $1/xml will be there)\
  $(if $(wildcard $1/xml),\
    $(foreach d,$(wildcard $1/xml/*.xml),\
      $(foreach p,$(basename $(notdir $d)),\
        $(- the 3rd arg is a directory that may not exist yet)\
        $(call HdlAddPlatform,$1/xml,$p,$1/$p))),\
    \
    $(- no $1/xml means we are pointing into the source tree, so the platform dir points into "lib")\
    $(- and the lib subdir may not exist yet)\
    $(foreach d,$(wildcard $1/*),\
      $(foreach p,$(notdir $d),\
        $(and $(wildcard $d/$p.xml),$(call HdlDoPlatform,$d)))))

################################################################################
# $(call HdlGetTargetFromPart,hdl-part)
# Return the target name from a hyphenated partname
HdlGetTargetFromPart=$(firstword $(subst -, ,$1))

################################################################################
# $(call HdlGetFamily,hdl-target,[multi-ok?])
# Return the family name associated with the target(usually a part)
# If the target IS a family, just return it.
# If it is a top level target with no family, return itself
# If it is a top level target with one family, return that family
# Otherwise return the family of the supplied part
# If the second argument is present, it is ok to return multiple families
# (The second argument should not contain spaces)
# If no appropriate family is found, warn
# StringEq=$(if $(subst x$1,,x$2)$(subst x$2,,x$1),,x)
HdlGetFamily=$(eval m1=$(subst $(Space),___,$1))$(strip \
  $(if $(HdlGetFamily_cached<$(m1)__$2>),,\
    $(call OcpiDbg,HdlGetFamily($1,$2) cache miss)$(eval export HdlGetFamily_cached<$(m1)__$2>=$(call HdlGetFamily_core,$1,$2)))\
  $(infox HdlGetFamily($1,$2)->$(HdlGetFamily_cached<$(m1)__$2>))$(HdlGetFamily_cached<$(m1)__$2>))

HdlGetFamily_core=$(call OcpiDbg,Entering HdlGetFamily_core($1,$2))$(strip \
  $(foreach gf,\
     $(or $(findstring $(1),$(HdlAllFamilies)),$(strip \
          $(if $(findstring $(1),all), \
	      $(if $(2),$(HdlAllFamilies),\
		   $(call $(HdlError),$(strip \
	                  HdlFamily is ambiguous for '$(1)'))))),$(strip \
          $(and $(findstring $(1),$(HdlTopTargets)),$(strip \
	        $(if $(and $(if $(2),,x),$(word 2,$(HdlTargets_$(1)))),\
                   $(call $(HdlError),$(strip \
	             HdlFamily is ambiguous for '$(1)'. Choices are '$(HdlTargets_$(1))')),\
	           $(or $(HdlTargets_$(1)),$(1)))))),$(strip \
	  $(foreach f,$(HdlAllFamilies),\
	     $(and $(filter $(call HdlGetTargetFromPart,$1),$(HdlTargets_$f)),$f))),$(strip \
	  $(and $(filter $1,$(HdlAllPlatforms)), \
	        $(call HdlGetFamily_core,$(call HdlGetTargetFromPart,$(HdlPart_$1))))),\
	  $(warning The build target '$1' is not a family or a part in any family)),\
     $(gf)))

# Families are either top level targets with nothing underneath or one level down
# HdlAllFamilies should be set before the HdlDoPlatform calls below so that it is set
# for use in any sub-calls to HdlGetFamily_core
HdlAllFamilies:=$(call Unique,$(foreach t,$(HdlTopTargets),$(or $(HdlTargets_$(t)),$(t))))
HdlAllTargets:=$(call Unique,$(HdlAllFamilies) $(HdlTopTargets))
export OCPI_ALL_HDL_TARGETS:=$(HdlAllTargets)

$(call OcpiDbgVar,HdlAllPlatforms)
# This is dirs where platforms might be found
HdlPlatformPaths=$(call Unique,$(infox PRD:$(OCPI_PROJECT_REL_DIR))\
  $(foreach p,$(OCPI_PROJECT_REL_DIR),$(infox PPPPPP:$p:$(CURDIR))\
    $(call OcpiExists,$p/hdl/platforms))\
  $(foreach p,$(OcpiGetExtendedProjectPath),\
    $(or $(call OcpiExists,$p/exports/hdl/platforms),$(strip\
         $(call OcpiExists,$p/hdl/platforms)))))
$(call OcpiDbgVar,HdlPlatformPaths)
# The warning below would apply, e.g. if a new project has been registered.
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
$(foreach d,$(HdlPlatformPaths),\
  $(if $(filter platforms,$(notdir $d)),\
    $(call HdlDoPlatformsDir,$d),\
    $(call HdlDoPlatform,$d)))
endif
export OCPI_ALL_HDL_PLATFORMS:=$(strip $(HdlAllPlatforms))
export OCPI_BUILT_HDL_PLATFORMS:=$(strip $(HdlBuiltPlatforms))
$(call OcpiDbgVar,HdlAllFamilies)
$(call OcpiDbgVar,HdlAllPlatforms)
$(call OcpiDbgVar,HdlBuiltPlatforms)
#$(info OCPI_ALL_HDL_PLATFORMS is $(OCPI_ALL_HDL_PLATFORMS))
#$(info OCPI_ALL_HDL_TARGETS is $(OCPI_ALL_HDL_TARGETS))
# Assignments that can be used to extract make variables into bash/python...
ifdef ShellHdlTargetsVars
all:
$(info HdlTopTargets="$(HdlTopTargets)";\
       HdlSimTools="$(HdlSimTools)";\
       HdlAllFamilies="$(HdlAllFamilies)";\
       HdlAllPlatforms="$(HdlAllPlatforms)";\
       HdlBuiltPlatforms="$(HdlBuiltPlatforms)";\
       HdlAllTargets="$(HdlAllTargets)";\
       HdlTargets="$(foreach t,$(HdlTopTargets),$(or $(HdlTargets_$t),$t))";\
       $(foreach p,$(HdlAllPlatforms),HdlPart_$p=$(HdlPart_$p); HdlPlatformDir_$p=$(HdlPlatformDir_$p);)\
       $(foreach p,$(HdlAllPlatforms),HdlAllRccPlatforms_$p="$(HdlAllRccPlatforms_$p)"; )\
       $(foreach f,$(HdlAllTargets),\
         $(if $(HdlTargets_$f),HdlTargets_$f="$(HdlTargets_$f)";)\
         $(if $(HdlToolSet_$f),HdlToolSet_$f="$(HdlToolSet_$f)";)\
         $(foreach t,$(HdlTargets_$f),\
           $(if $(HdlTargets_$t),HdlTargets_$t="$(HdlTargets_$t)";)))\
       $(foreach t,$(call Unique,\
                     $(foreach f,$(HdlAllTargets),$(if $(HdlToolSet_$f),$(HdlToolSet_$f) ))),\
         $(eval __ONLY_TOOL_VARS__:=true)\
         $(eval include $(OCPI_CDK_DIR)/include/hdl/$t.mk)\
         HdlToolName_$t="$(or $(HdlToolName_$t),$t)";)\
       $(foreach p,$(HdlAllPlatforms),\
         HdlFamily_$(HdlPart_$p)=$(call HdlGetFamily,$(HdlPart_$p));)\
       $(foreach p,$(HdlAllPlatforms),\
         $(- only use realpath if its there.  If not we are bootstrapping and leave it alone)\
         HdlPlatformDir_$(p)="$(or $(realpath $(HdlPlatformDir_$p)),$(HdlPlatformDir_$p))";))
endif
endif
