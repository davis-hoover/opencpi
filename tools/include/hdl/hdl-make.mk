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

# This file contains various utilities for hdl makefiles.
# It is distinguishd from hdl-pre.mk in that it doesn't really mess with any variables
# Thus HDL utility stuff goes here unless it is order sensitive, in which case it
# is in hdl-pre.mk

ifndef __HDL_MAKE_MK__
__HDL_MAKE_MK__=x
Model:=hdl
# This file is included by the various levels of hdl makefiles (not the leaf makefiles)
# i.e. a Makefile file that does other makefiles.
# Note that targets are generally families except when a primitive core is actually part-specific.
ifdef HdlTarget
override HdlTarget:=$(patsubst %_pf,%,$(HdlTarget))
endif
ifdef HdlTargets
override HdlTargets:=$(patsubst %_pf,%,$(HdlTargets))
endif
ifdef OnlyTargets
override OnlyTargets:=$(patsubst %_pf,%,$(OnlyTargets))
endif
ifdef ExcludeTargets
override ExcludeTargets:=$(patsubst %_pf,%,$(ExcludeTargets))
endif
ifdef HdlPlatform
override HdlPlatform:=$(patsubst %_pf,%,$(HdlPlatform))
endif
ifdef HdlPlatforms
override HdlPlatforms:=$(patsubst %_pf,%,$(HdlPlatforms))
endif
ifdef OnlyPlatforms
override OnlyPlatforms:=$(patsubst %_pf,%,$(OnlyPlatforms))
endif
ifdef ExcludePlatforms
override ExcludePlatforms:=$(patsubst %_pf,%,$(ExcludePlatforms))
endif


$(call OcpiDbgVar,HdlPlatforms)
$(call OcpiDbgVar,HdlTargets)

include $(OCPI_CDK_DIR)/include/util.mk
include $(OCPI_CDK_DIR)/include/hdl/hdl-targets.mk

# This default is only overridden for testing the makefiles
HdlError:=error
HdlSourceSuffix=.v

$(call OcpiDbgVar,HdlTopTargets)
HdlAllParts:=$(call Unique,$(foreach t,$(HdlTopTargets),\
	              $(or $(foreach f,$(HdlTargets_$t),\
                             $(or $(HdlTargets_$f),$f)),$t)))
$(call OcpiDbgVar,HdlAllParts)

HdlAllPlatformParts:=$(call Unique,$(foreach pl,$(HdlAllPlatforms),$(firstword $(subst -, ,$(HdlPart_$(pl))))))
$(call OcpiDbgVar,HdlAllPlatformParts)

# Read the workers file and set things accordingly
# 1. Set the instance list, which is a list of <worker-name>:<instance-name>
# 2. The workers list, which is a list of worker names
# 3. Add the core file associated with each worker to the cores list,
#    doing the search through $(ComponentLibraries)
#    The core for the worker will be _rv if the assembly file is VHDL
# Note we are silent about workers that don't have cores.
# FIXME: put in the error check here, but avoid building platform modules like "occp" etc.
HdlInstanceWkr=$(word 1,$(subst :, ,$1))
HdlInstanceCfg=$(word 2,$(subst :, ,$1))
HdlInstanceName=$(word 3,$(subst :, ,$1))
HdlInstanceWkrCfg=$(call HdlInstanceWkr,$1)$(and $(HdlToolRealCore),$(filter %.vhd,$(ImplFile)),_rv)$(foreach c,$(call HdlInstanceCfg,$1),$(if $(filter 0,$c),,_c$c))

# Do the basic primitive core search, returning target-independent paths
HdlFindCores=$(infox HFC:$1)\
  $(foreach c,$1,\
    $(if $(findstring /,$c),\
      $(or $(and $(call HdlExists,$c),$c:$(notdir $c)),\
            $(error Primitive core $c (from Cores) not found.)),\
      $(call HdlSearchPrimitivePath,$c,,HPLx)))

HdlBuiltinWorkers=ocscp ocscp_rv metadata metadata_rv time_client time_client_rv unoc_node unoc_node_rv

HdlSourceLibPath=$(strip $(infox HSLP:$1)\
  $(foreach r,\
    $(if $(findstring /exports/lib/,$1),\
      $(foreach l,$(lastword $(subst /, ,$1)),$(infox HSLP0:$l)\
        $(foreach d,$(if $(filter components,$l),/,\
                      $(if $(filter devices cards adapters,$l),/hdl/,/components/)),$(infox HSLP1:$d)\
          $(subst /exports/lib/,$d,$1))),\
      $1),$(infox HSLPr:$r)$r))

################################################################################
# Genearate a rule to build the worker configuration
# $(call HdlAutoWorkerRule,<lib>,<target>,<worker>,<config>)
# 1: rawlib 2: top lib 3: target 4: worker 5: worker-core 6: config
define HdlAutoWorkerRule
$$(infox HAUTO:$1:$2:$3:$4:$5:$6)
$$(infox TARGET:$1/hdl/$3/$5$$(HdlBin))
# Note setting the project variables in the environment and not on the command line
# We are trying to run a "clean" make unrelated to this parent make.
# Since we don't have a good pattern for all potential exported variables, we just
# have to unset the ones we know, which is not really robust.
$1/hdl/$3/$5$$(HdlBin):
	$(AT)echo Building HDL worker $4 configuration $6 target $3 in library $2 now...
	$(AT)unset OCPI_PROJECT_REL_DIR OCPI_PROJECT_PACKAGE OCPI_PROJECT_DIR \
                   OCPI_PROJECT_COMPONENT_LIBRARIES OCPI_PROJECT_DEPENDENCIES MAKEFLAGS MFLAGS \
                   OCPI_COMPONENT_LIBRARIES ComponentLibrariesInternal ComponentLibraries && \
             make $$(foreach d,$(call HdlSourceLibPath,$2)/$4.hdl,\
                        -C $$d $$(if $$(wildcard $$d/Makefile),,-f $(OCPI_CDK_DIR)/include/worker.mk)) \
                     --no-print-directory HdlTarget=$3 ParamConfigurations=$6 AT=$(AT)

endef

# Search for the actual built core in any of the libraries, but if not found,
# report whether the worker is not there at all, or is simply not yet built
# $(call HdlFindWorkerCore,<target>,<worker>,<worker+rv+cfg>,<cfg>)
HdlFindWorkerCore=$(strip \
  $(eval HdlFoundInLib:=)\
  $(eval HdlFoundCore:=)\
  $(foreach l,$(call OcpiComponentLibraries),$(infox CORELIB:$l:$l/hdl/$1/$3$(HdlBin))\
    $(if $(HdlFoundCore),,\
      $(if $(call HdlExists,$l/hdl/$1/$3$(HdlBin)),\
         $(eval HdlFoundCore:=$l/hdl/$1/$3$(HdlBin)),\
         $(if $(HdlFoundInLib),,\
           $(if $(call HdlExists,$l/hdl/$2.xml),\
             $(eval HdlFoundInLib:=$l))))))\
  $(or $(HdlFoundCore),\
    $(if $(HdlFoundInLib),\
      $(foreach l,$(HdlFoundInLib:%/lib=%),\
	$(if $(OCPI_AUTO_BUILD_WORKERS),\
          $(info Warning:  HDL worker "$2" found in component library "$l" $(strip\
               ($(realpath $l)), but build config "$4" not built for target "$1")),\
          $(info Error:  HDL worker "$2" found in component library "$l" $(strip\
               ($(realpath $l)), but build config "$4" not built for target "$1"))$(error ))\
        $(eval $(call HdlAutoWorkerRule,$(HdlFoundInLib),$l,$1,$2,$3,$4))\
	$(eval HdlAutoCores+=$(HdlFoundInLib)/hdl/$1/$3$(HdlBin))\
        $(HdlFoundInLib)/hdl/$1/$3$(HdlBin)),\
      $(if $(filter-out $(HdlBuiltinWorkers),$2),\
        $(info Error:  Worker "$2" was not found built for target "$1" in any of the component libraries)\
        $(error )))))

################################################################################
# This is called with a target argument in the context of generating recipes
# and dependencies.  It assigns the SubCores_<target> variable and as a side
# effect, generates rules and recipes for auto-building dynamic worker
# configurations
define HdlSetWorkerCores

  $$(eval HdlAutoCores:=)
  SubCores_$1:=$$(call Unique,\
    $(- Process explicit Cores) \
    $$(call HdlFindCores,$(Cores))\
    $(- Find worker cores)\
    $$(foreach f,$$(call HdlGetFamily,$1),\
       $$(foreach i,$$(HdlInstances),\
          $$(foreach n,$$(call HdlInstanceWkr,$$i),\
             $$(foreach w,$$(call HdlInstanceWkrCfg,$$i),$$(infox HSWC:$1:$$f:$$i:$$n:$$w)\
                $$(call HdlFindWorkerCore,$$f,$$n,$$w,$$(call HdlInstanceCfg,$$i)))))))
  $$(infox Cores SubCores_$1 is $$(origin SubCores_$1) $$(flavor SubCores_$1):$$(SubCores_$1))

endef

################################################################################
# $(call HdlGetTop,family)
# Return the top name from a family
HdlGetTop=$(strip $(foreach v,$(HdlTopTargets),$(or $(filter $1,$v),$(and $(filter $1,$(HdlTargets_$v)),$v))))

################################################################################
# $(call HdlGetFamilies,hdl-target)
# Return all the families for this target
# HdlGetFamilies=$(call OcpiDbg,Entering HdlGetFamilies($1))$(strip
HdlGetFamilies=$(strip \
  $(foreach fs,$(call Unique,$(foreach t,$1,\
                         $(if $(findstring $(t),all),\
                             $(HdlAllFamilies),\
                             $(call HdlGetFamily,$t,x)))),\
     $(call OcpiDbg,HdlGetFamilies_core($1)->$(fs))$(fs)))

################################################################################
# $(call HdlGetPart,platform)
HdlGetPart=$(call OcpiDbg,Entering HdlGetPart($1))$(strip \
$(foreach gp,$(firstword $(subst -, ,$(HdlPart_$1))),\
   $(call OcpiDbg,HdlGetPart($1)->$(gp))$(gp)))


# model-specific getting a platform for a target
# which is inherently problematic for HDL...
HdlGetPlatform=$(or $(HdlPlatform),$(error Getting platform for HDL target $1 is ambiguous))
# The model-specific determination of the "tail end" of the target directory,
# after the prefix (target), and build configuration.
# The argument is a TARGET
HdlTargetDirTail=$(infox HTDT:$1)$(foreach t,$(or $1,$(HdlTarget)),$(infox HTDTr:$t)$t)

################################################################################
# The generic hdl compile that depends on HdlToolCompile
HdlName=$(or $(Core),$(LibName))
# if $(findstring $(HdlMode),library),$(LibName),$(Core))
HdlLog=$(HdlName)-$(HdlToolSet).out
HdlTime=$(HdlName)-$(HdlToolSet).time
HdlCompile=\
  $(infox Compile0:$(HdlWorkers):$(Cores):$(ImplWorkersFile):$(ImplFile):to-$@) \
  $(infox Compile:$(HdlWorkers):$(Cores):$(ImplWorkersFile)) \
  $(and $(SubCores_$(HdlTarget)),$(call HdlRecordCores,$(basename $@))$(infox DONERECORD:$(HdlTarget))) \
  $(HdlSourceListCompile)\
  $(infox SUBCORES:$(SubCores_$(HdlTarget))) \
  cd $(TargetDir) && \
  $(infox PRECOMPILE:$(HdlPreCompile))$(and $(HdlPreCompile), $(HdlPreCompile) &&)\
  export HdlCommand="set -e; $(HdlToolCompile)"; \
  touch $(HdlLog) $(HdlTime); \
  $(TIME) bash -c \
   '(/bin/echo Commands to execute tool:@@@"$$HdlCommand" | sed "s/\([^\\]\); */\1;@@@/g" | sed "s/@@@/\n/g"; /bin/echo Output from executing commands above:;eval "$$HdlCommand") > $(HdlLog) 2>&1' \
    > $(HdlTime) 2>&1; \
  HdlExit=$$?; \
  (cat $(HdlTime) | tr -d "\n"; $(ECHO) -n " at "; date +%T) >> $(HdlLog); \
  egrep -i 'error|fatal' $(HdlLog)| grep -v Command: |\
    grep -v '^WARNING:'|grep -v " 0 errors," | grep -i -v -e '[_a-z]error' -e 'error[a-rt-z_]' $(HdlGrepExclude_$(HdlToolSet)); \
  if grep -q '^ERROR:' $(HdlLog); then HdlExit=1; fi; \
  if test "$$OCPI_HDL_VERBOSE_OUTPUT" != ''; then \
    cat $(HdlLog); \
  fi; \
  if test $$HdlExit != 0; then \
    $(ECHO) -n Error: $(HdlToolSet) failed\($$HdlExit\). See $(TargetDir)/$(HdlLog).'  '; \
  else \
    $(ECHO) -n ' Tool "$(HdlToolSet)" for target "$(HdlTarget)" succeeded.  '; \
  fi; \
  (cat $(HdlTime) | tr -d "\n"; $(ECHO) -n " at "; date +%T); \
  rm -f $(HdlTime); \
  exit $$HdlExit

HdlPost=\
  $(and $(HdlToolPost),\
    set -e; \
    cd $(TargetDir) && \
    $(HdlToolPost))
################################################################################
# The post processing by tools that do not produce any intermediate
# build results
HdlSimPost=\
  rm -r -f links; \
  if test $$HdlExit = 0; then \
    if ! test -d $(LibName); then \
      mkdir $(LibName); \
    else \
      rm -f $(LibName)/*; \
    fi;\
    for s in $(HdlToolLinkFiles); do \
      if [[ $$s == /* ]]; then \
        ln -s $$s $(LibName); \
      else \
        ln -s ../$$s $(LibName); \
      fi; \
    done; \
  fi;

HdlExists=$(call OcpiExists,$1)

# Default for all tools: libraries are directories whose name is the library name itself
# Return the name of the thing in the build directory (whose name is target-<target>)
# But if there is a single file there, that should be returned
HdlToolLibraryBuildFile=$1
# Default for all tools: installed libraries are just the directory whose name is the target
# Return the name of the thing in the install directory (whose name is the target)
# But if there is a single file there, that should be returned
HdlToolLibraryInstallFile=

################################################################################
# $(call HdlGetToolSet,hdl-target)
# Return the tool set for this target
HdlGetToolSet=$(infox HdlGetToolSet ($1) HdlTopTargets="$(HdlTopTargets)" HdlTargets_$(1)="$(HdlTargets_$(1))" HdlToolSet_$1="$(HdlToolSet_$1)" HdlToolSet_$(call HdlGetFamily,$(1))="$(HdlToolSet_$(call HdlGetFamily,$(1)))" HdlToolSet_$(HdlTargets_$(1))="$(HdlToolSet_$(HdlTargets_$(1)))"  )$(strip \
  $(or $(and $(findstring $(1),$(HdlTopTargets)),$(strip \
           $(or $(HdlToolSet_$(1)),$(strip \
                $(if $(word 2,$(HdlTargets_$(1))),,\
                   $(HdlToolSet_$(HdlTargets_$(1)))))))),$(strip \
       $(HdlToolSet_$(call HdlGetFamily,$(1)))),$(strip \
       $(call $(HdlError),Cannot infer tool set from '$(1)' Family='$(call HdlGetFamily,$(1))'))))

HdlGetBinSuffix=$(HdlBin_$(call HdlGetToolSet,$1))
################################################################################
# $(call HdlGetTargetsForToolSet,toolset,targets)
# Return all the targets that work with this tool
HdlGetTargetsForToolSet=$(call Unique,\
    $(foreach t,$(2),\
       $(and $(filter $(1),$(call HdlGetToolSet,$(t))),$(t))))

################################################################################
# $(call HdlGetConstraintsSuffix,<platform>)
# Return the suffix for constraints files for this platform
HdlGetConstraintsSuffix=$(strip \
  $(HdlConstraintsSuffix_$(HdlToolSet_$(call HdlGetFamily,$(HdlPart_$1)))))
################################################################################
# $(call HdlGetConstraintsFile,<file,platform>)
# Return the constraints file name adding suffix if not present
HdlGetConstraintsFile=$(strip $(and $1,\
  $(foreach s,$(call HdlGetConstraintsSuffix,$2),\
    $1$(if $(filter %$s,$1),,$s))))

$(call OcpiDbgVar,HdlPlatform)
$(call OcpiDbgVar,HdlPlatforms)
$(call OcpiDbgVar,HdlTargets)

#  $(foreach c,$(ComponentLibraries),\
#    $(foreach o,$(ComponentLibraries),\
#       $(if $(findstring $o,$c),,\
#          $(and $(filter $(notdir $o),$(notdir $c)),
#            $(error The component libraries "$(c)" and "$(o)" have the same base name, which is not allowed)))))

# define HdlSearchComponentLibraries
#   $(info HdlSearchComponentLibraries NOT NEEDED?)
#  override XmlIncludeDirsInternal := $(call Unique,$(XmlIncludeDirsInternal) $(call HdlXmlComponentLibraries))
#endef
HdlRmRv=$(if $(filter %_rv,$1),$(patsubst %_rv,%,$1),$1)

# Grep a file and collect all non-comment lines into a space-separated list
HdlGrepExcludeComments=$(infox GREP:$1:$2)$(shell grep -v '\#' $1 2>/dev/null)

#########################################################################################################
#  An OpenCPI 'core' is really any core-like asset that results in a netlist-like artifact for later reuse.
#  Assets that function like cores are all assets except primitive libraries. So, the list is:
#    primitive core, worker, platform, config, assembly, container
#
#  Certain tools require that all core-dependencies are captured at every level of compilation. This means
#  that if a worker includes a primitive core, that information needs to be reiterated not only during
#  compilation of the worker, but also during compilation of the containing assembly AND finally the
#  container.
#
#  Furthermore, certain tools (e.g. Quartus Pro) require that each core/netlist be mapped to a specific HDL
#  instance in the design. This further compilicates this logic because the instance hierarchy changes and
#  expands at every level of OpenCPI's incremental compilation.
#
#  So, everytime an OpenCPI asset is compiled and includes another 'core' asset(s) (or plain old netlist),
#  the included core's path (from the project top when possible) and optionally the HDL instance that it maps
#  to (if the tool requires it) must be recorded. This information is recorded in the *.cores file for an
#  OpenCPI asset.
#
#  While an asset is being compiled, the mapping of cores to instances in the HDL hierarchy must be considered.
#
#    Based on the HdlMode, we can determine an instance hierarchy prefix that will be prepended to any cores'
#    instances in the current design. So, if the user specifies an instance for a core via
#    <mycore>:<its-instance>, the resulting instance name in the current design would be
#    <prefix>|<its-instance>. The prefix is determined using the HdlInstancePrefix function.
#
#    If a subcore is user-specified via Cores=<core>:<inst>, this is simple enough, but when the core is
#    included by OpenCPI itself (e.g. when an assembly includes app workers), there is more information
#    we need to gather. HdlInstancesForCore accesses the HdlInstances list to determine which HDL instance
#    a worker/core in an assembly corresponds to. The results of HdlInstancesForCore are prepended with the
#    results of HdlInstancePrefix to determine the full instance hierarchy for a core.
#
#    HdlCollectCores is used to iterate through SubCores_<target>, collect core names, paths and instances, and
#    iterate down to the '.cores' files for each SubCore (when appropriate) using the HdlGetSubCoresFromFile
#    function. Each core discovered in a .cores file is then prepended with the current HdlInstancePrefix, and
#    the paths are processed. This results in a list of format:
#    <corename/partialpath>:<full-core-path>:<core-instance>. This three part list allows us to index
#    the list of Cores (set by the user) by 'corename'. This is important because if a user set
#    'Cores=<corename/path>:<instance>', we may want to handle it differently in the <tool>.mk. So, we store the
#    user-set <corename/path> before modifications so that we can check an entry against the Cores variable
#    to determine if a core (returned by HdlCollectCores) corresponds to one listed in the user-set Cores
#    variable.
#
#    HdlRecordCores writes the list of cores (from HdlCollectCores) to a file. It writes each in the format
#    <partial-core-path>:<instance>. HdlCoresToRecord modifies the core paths so that they are relative to the
#    top level of the current project (e.g. hdl/devices/lib/hdl/arria10soc/sdp_node_rv.qdb or
#    imports/ocpi.core/exports/lib/devices/hdl/arria10soc/sdp_node_rv.qdb), and then records them alongside the
#    instance names for respective cores as used when compiling the current asset.

# For each instance mapping listed in HdlInstances:
#   If the instance maps (via HdlInstanceWkrCfg) to the worker/config provided by $1:
#     return the instance name (last colon-separated word in inst)
# If there is no mapping for the provided core ($1):
#   default to <core>_i
HdlInstancesForCore=$(infox HIFC:$1)$(strip \
  $(or $(strip \
         $(foreach inst,$(HdlInstances)$(infox HdlInstances:$(HdlInstances)),\
           $(if $(filter $(basename $(notdir $1)),$(call HdlInstanceWkrCfg,$(inst))),\
             $(lastword $(subst :, ,$(inst)))))),\
       $(call RmRv,$(basename $(notdir $1)))))

# For some modes, instances should by default be appended with _i
HdlDefaultInstanceSuffix=$(strip \
  $(if $(filter-out assembly worker,$(HdlMode)),\
    _i))

# '|' needs to be escaped
# switch HdlMode:
#   case container: pref = "ftop|"
#   case assembly : pref =  "assy|"
#   case worker \
#     or config   : if HdlUsesRv: pref = "worker|", else pref = "rv|worker|"
#   case */default: pref = ""
# return pref
HdlInstancePrefix=$(strip \
  $(if $(filter container,$(HdlMode)),ftop\\|,\
    $(if $(filter assembly,$(HdlMode)),assy\\|,\
       $(if $(filter worker platform,$(HdlMode)),$(if $(HdlUsesRv),,rv\\|)worker\\|))))

# Each line in a .cores file must have an instance name for each core. This instance
# is the text after the ':'.
# This must hold true whenever HdlTooLRequiresInstanceMap_<tool> is set.
# After being read from a file, the '|' hierarchy separator must be re-escaped in the
# instance string.
#
# $1 = coreline from .cores file <core>:<hdl-instance>
HdlInstanceForCoreFromFile=$(strip \
  $(if $(filter $(words $(subst :, ,$1)),2),\
     $(subst |,\|,$(lastword $(subst :, ,$1))),\
     $(error Format of .cores file should be <core>:<core-path>:<hdl-instance> for tools that require HDL instance mapping.)))

# If checking for core instances from the command line (e.g. directly from SubCores variable), the instance/2nd-word
# can be blank
HdlUserInstanceForCore=$(strip \
  $(if $(filter $(words $(subst :, ,$1)),2),\
     $(lastword $(subst :, ,$1))))

# Recorded paths to cores are either absolute paths (e.g. to non-OpenCPI ngc files),
# or partial paths from the top of the containing project. Here, we convert these
# paths to real/full paths.
#
# $1 = name of core as seen in .cores files
# $2 = path to top of project containing core
HdlConvertRecordedCoreToPath=$(strip \
  $(if $(filter /%,$(1)),\
    $(1),\
      $(or $(call OcpiExists,$(2)/$(1)),\
           $(call OcpiExists,$(2)/$(subst /lib/,/,$(patsubst hdl/platforms/%,lib/platforms/%,$(1)))),\
           $(call OcpiExists,$(2)/$(subst /lib/,/,$(patsubst hdl/devices/%,lib/devices/%,$(1)))),\
           $(call OcpiExists,$(2)/$(subst /lib/,/,$(patsubst hdl/primitives/%,lib/hdl/%,$(1)))))))

# For each line of this SubCore's .cores file,
#   assume the first element is the core (partial path),
#   and the second element is the instance (if the tool requires instance maps).
#   Get the real path to the core
#   (Optionally) Get the HDL instance for the core
# return a space separated list of elements in the format <core-name>:<path-to-core>:<instance-for-core>
#   here, core-name is the pre-: text from the file before being transformed
# $1 is the path to the core that might have a .cores file
HdlGetSubCoresFromFile=$(infox GetSubCoresFrom:$(call HdlRmRv,$(basename $1)).cores:arg3=$3)$(strip \
  $(foreach coresfile,$(call HdlExists,$(call HdlRmRv,$(basename $1)).cores),$(infox CoreFile:$(coresfile))\
    $(foreach pjtop,$(call OcpiAbsPathToContainingProject,$(coresfile)),$(infox pjtop:$(pjtop))\
      $(foreach coreline,$(call HdlGrepExcludeComments,$(coresfile)),$(infox CoreLine:$(coreline):from:$(coresfile))\
          $(subst $(Space),,\
            $(corename):\
            $(foreach corename,$(firstword $(subst :, ,$(coreline))),\
              $(call HdlConvertRecordedCoreToPath,$(corename),$(pjtop)))\
            $(if $(filter $3,noinstances),,\
              $(if $(HdlToolRequiresInstanceMap_$(HdlToolSet)),\
                :$2\\|$(call HdlInstanceForCoreFromFile,$(coreline))))) ))))

# Foreach subcore listed in SubCores:
#   Determine the corename (text before :)
#     Determine the path to this core
#       Get all subsubcores for this core if it has a .cores file (HdlGetSubCoresFromFile)
#         Only perform this step if the tool requires a full core hierarchy (e.g. might not need to recures to subcores)
# return a space separated list with elements of format <core-name>:<core-path>
#   One element for each SubCore (and each of ITS subcores if it has a .cores file)
#
#   If we DO want an instancemap (if $1 != noinstances and tool does needs instances):
#     elements in the returned list will have format: <core-name>:<core-path>:<instance>
#       <instance> will have a prefix (HdlInstancePrefix) preppended and a suffix (HdlDefaultInstanceSuffix) appended
#     <instance> is determined by first  checking for user provided instance mappings (HdlUserInstanceForCore), and
#                                 second checking for OpenCPI defined mappings (HdlInstancesForCore - e.g. .wks file)
#       if there are > 1 instances mapped to by a single core, each instance string must have its prefix and suffix applied before
#         being assigned to "subcoreinst" and inserted in the constructed/returned element (format <core-name>:<core-path:<instance>)
HdlCollectCores=$(infox CollectCore:$(SubCores_$(HdlTarget)):$(HdlTarget))$(strip \
  $(foreach subcore,$(SubCores_$(HdlTarget)),$(infox subcore=$(subcore))\
    $(foreach corename,$(firstword $(subst :, ,$(subcore))),$(infox corename=$(corename))\
      $(foreach corepath,$(or $(filter $(corename),$(HdlAutoCores)),$(call HdlCoreRefMaybeTargetSpecificFile,$(corename),$(HdlTarget))),$(infox CorePath:$(corepath))\
        $(if $(or $(filter $1,noinstances),$(if $(HdlToolRequiresInstanceMap_$(HdlToolSet)),,noinstances)),\
          $(corename):$(corepath) $(if $(HdlToolRequiresFullCoreHierarchy_$(HdlToolSet)),$(call HdlGetSubCoresFromFile,$(corepath),,$1)),\
          $(if $(HdlToolRequiresInstanceMap_$(HdlToolSet)),\
            $(foreach subcoreinst,$(strip $(foreach oneormoreinsts,$(or $(call HdlUserInstanceForCore,$(subcore)),\
                                                                        $(call HdlInstancesForCore,$(corepath))),\
                                            $(HdlInstancePrefix)$(oneormoreinsts)$(HdlDefaultInstanceSuffix))),\
              $(corename):$(corepath):$(subcoreinst)$(infox SubCoreInst:$(subcoreinst)) \
              $(if $(HdlToolRequiresFullCoreHierarchy_$(HdlToolSet)),$(call HdlGetSubCoresFromFile,$(corepath),$(subcoreinst),$1)))))))))

# Collect all cores of interest, but just return the list of paths (do no care about core names or instances here)
# This is a simple list of cores used by certain tools and in HdlCoreDependencies (in HdlPrepareAssembly)
HdlCollectCorePaths=$(strip \
  $(foreach c,$(call HdlCollectCores,noinstances),$(infox COLLECTED CORE:$c)\
    $(word 2,$(subst :, ,$c))))
#
# Iterate through all collected cores, and determine the partial path (and optionally instance) to record in the .cores file
# Make sure to escape any '|' characters found in HDL instance strings
HdlCoresToRecord=$(strip \
  $(foreach corenamepathandinst,$(call HdlCollectCores,$(if $(HdlToolRequiresInstanceMap_$(HdlToolSet)),,noinstances)),$(infox CPAI:$(corenamepathandinst))\
      $(foreach partialpath,$(call OcpiPathFromProjectTopOrImports,$(dir $1),$(word 2,$(subst :, ,$(corenamepathandinst)))),$(infox PartialPath:$(partialpath))\
        $(partialpath)$(if $(HdlToolRequiresInstanceMap_$(HdlToolSet)),:$(subst |,\|,$(lastword $(subst :, ,$(corenamepathandinst)))))) ))

# Determine cores to record and write them to the .cores file
HdlRecordCores=\
  $(infox Record:$1:$(SubCores_$(HdlTarget)):$(HdlTarget))\
  $(and $(call HdlExists,$(dir $1)),\
    (\
     echo '\#' This generated file records cores necessary to build this $(LibName) $(HdlMode); \
     $(foreach core,$(HdlCoresToRecord)$(infox Recording:$(HdlCoresToRecord)),\
       echo $(core); )\
    ) > $(call HdlRmRv,$1).cores;)

#########################################################################################################
# Record all of the libraries and sources required for this asset (sources only when a tool requires this is done)
# When recording sources for a core, we only record the stub files since those will be needed later.
HdlSourceListCompile=$(infox HSLC:$@:$(basename $@):$(HdlLibrariesInternal))\
  $(foreach v,$(.VARIABLES),$(and $(filter Pack%,$v),$(infox HI: $v=$($v))))\
  $(HdlRecordLibraries) \
  $(if $(HdlToolNeedsSourceList_$(HdlToolSet)),\
    $(and $(or $(HdlSources),$(if $(filter $(HdlMode),core),$(CoreBlackBoxFiles))),$(call HdlRecordSources,$(basename $@))))

####################################################################################################
# Record the list of libraries required by this asset/library in the gen/<lib>.libs file.
# The first line in the file is whether this library is in the global or qualified namespace.
# Other lines indicate <project-package>:<libname>:<hdl-lib>
HdlRecordLibraries=\
  $(infox Record:$(HdlLibrariesInternal):$(HdlTarget))\
  mkdir -p $(GeneratedDir);\
  (\
   echo '\#' This generated file records libraries necessary to build this $(LibName) $(HdlMode); \
   echo '\#' The first line contains the namespace mode:  qualified, global, or both; \
   echo $(or $(NameSpace),global);\
   $(foreach l,$(HdlLibrariesInternal),$(infox RECORDING LIB PATH:$l)\
     $(foreach p,$(word 1,$(subst :, ,$l)),\
       $(foreach r,$(if $(findstring /imports/,$p),\
                     $(firstword $(filter-out .. imports,$(subst /, ,$p))),\
                     $(OCPI_PROJECT_PACKAGE)),$(infox RRR:$r:$(patsubst %/imports/,,$p))\
         $(foreach x,$r:$(notdir $p):$(lastword $(subst :, ,$l)),\
           $(infox RECORDING LIB=$x)echo $x;))))\
  ) > $(GeneratedDir)/$(or $(Worker),$(LibName)).libs;

# Extract the list of libraries required by an asset/library $2 for target $1
HdlExtractLibrariesFromFile=$(infox Extract:$2:$1)$(call Unique,\
  $(foreach f,$(call HdlExists,$(call HdlRmRv,$2)/$(HdlTarget)/$(notdir $(call HdlRmRv,$2)).libs),$(infox ZF:$f)\
    $(foreach z,$(call HdlGrepExcludeComments,$f),$(infox found:$z)$z )))

# If the libname consists of one word, search the primitive path.
# If the libname is an absolute path, return it abspath of $2,
# otherwise, return $1/$2 (path $2 starting from $1).
HdlNotdirAbsOrRelPath=$(infox NORP:$1:$2)\
  $(if $(findstring $2,$(notdir $2)),\
    $(patsubst %/,%,$(call HdlSearchPrimitivePath,$2,,CollectLibs)),\
    $(if $(filter /%,$2),\
      $(abspath $2),\
      $(if $(findstring /imports/,$2),$2,$1/$2)))


HdlProjectFromLibPath=$(strip\
  $(foreach p,$(if $(findstring /imports/,$1),\
                $(if $(filter $(OCPI_PROJECT_REL_DIR)/imports/%,$1),\
                  $(word 1,$(subst /, ,$(patsubst $(OCPI_PROJECT_REL_DIR)/imports/%,%,$1))),\
                  $(error unexpected imports not in project: $1)),\
                $(OCPI_PROJECT_PACKAGE)),\
    $(infox PATH:$1 Project:$p)$p))

HdlSameLibrary=$(strip \
  $(foreach s,$(and $(filter $(notdir $1),$(notdir $2)),\
	            $(filter $(call HdlProjectFromLibPath,$1),$(call HdlProjectFromLibPath,$2))),\
    $(infox SAME:$1:$2:$s)$s))

HdlMatchLibrary=$(strip $(infox MATCH:$1:$2)\
  $(foreach m,$(foreach l,$2,$(call HdlSameLibrary,$1,$l)),$(infox MATCHr:$m)$m))


# Args are 1: library path, 2: is-qualified?
HdlAddLibrary=$(if $(call HdlMatchLibrary,$1,$(HCLTemp)),,\
                 $(or $(infox ADDING $1: $(HCLTemp)),\
                      $(eval HCLTemp+=$1)))

# look for the .libs file for either a primitive or a worker in a library
# and remember that the work/core might have a _cN config suffix
HdlGetLibsFile=\
  $(or $(wildcard $1/$(notdir $1).libs),$(strip\
       $(foreach r,$(dir $(patsubst %/,%,$(dir $1))),\
         $(foreach w,$(notdir $1),$(infox WWW:$w)\
           $(or $(wildcard $r$w.libs),$(strip\
                $(foreach n,$(shell shopt -s extglob;X=$w;echo $${X%_c+([0-9])}),$(infox NNN:$n)\
                  $(wildcard $r$n.libs))),\
                $(error the primitive/core/worker at $1 appears to be not built yet.))))))

# $(call HdlCollectLibsRecurse,<path-to-library>,<namespace>)
HdlCollectLibsRecurse=$(infox Collecting for dependency $1($2), already have $(HCLTemp))\
 $(foreach path,$(word 1,$(subst :, ,$1)),$(infox path:$(path))\
   $(foreach lib,$(word 2,$(subst :, ,$1)),$(infox lib:$(lib))\
     $(eval HCLLines:=$(call HdlGrepExcludeComments,$(call HdlGetLibsFile,$(path))))\
     $(foreach namespace,$(word 1,$(HCLLines)),$(infox namespace:$(namespace))\
       $(foreach l,$(wordlist 2,$(words $(HCLLines)),$(HCLLines)),$(infox deplib:$l)\
         $(foreach p,$(word 1,$(subst :, ,$l)),\
           $(foreach n,$(word 2,$(subst :, ,$l)),\
             $(foreach h,$(word 3,$(subst :, ,$l)),\
               $(foreach r,$(if $(filter $p,$(OCPI_PROJECT_PACKAGE)),\
                             $(OCPI_PROJECT_REL_DIR)/hdl/primitives/lib/$n:$h,\
                             $(OCPI_PROJECT_REL_DIR)/imports/$p/exports/lib/hdl/$n:$h),\
                 $(call HdlCollectLibsRecurse,$r,)))))))))\
  $(if $2,,$(call HdlAddLibrary,$1))

# Accumulate a list of the pathnames of libraries required by the current asset
# This is for use by tools.  The returned values are paths with an optional
# "actual", scoped library name after a colon.
HdlCollectLibraries=$(infox PPPP:$(HdlLibrariesInternal):$1:$2:$(HdlTarget))\
  $(eval HCLTemp:=$2)\
  $(foreach p,$(HdlLibrariesInternal),$(infox HCLp:$p)\
    $(call HdlCollectLibsRecurse,$p))\
  $(eval HCLTemp:=$(filter-out $2,$(HCLTemp)))\
  $(infox HCLret:$(HCLTemp))$(HCLTemp)

# When all you have is core paths...
HdlCollectCoreLibraries=$(infox PPPCx=$1=$2=$(notdir $1)=)\
  $(eval HCLTemp:=$2)\
  $(call HdlCollectLibsRecurse,$1:x,x)\
  $(eval HCLTemp:=$(filter-out $2,$(HCLTemp)))\
  $(infox HCLretc:$(HCLTemp))$(HCLTemp)

# Record the list of sources required by this asset/library in the .sources file
# Here we check the flag indicating that there are tool-specific source collections for this asset
# in which case we create <asset>.<tool>.sources
# If this is a true core, we record the black box stub files
HdlRecordSources=\
  $(infox Record:$1:$(HdlSources):$(HdlTarget):$(call HdlExists,$(dir $1)))\
  $(and $(call HdlExists,$(dir $1)),$(infox WRITING)\
  (\
   echo '\#' This generated file records sources necessary to build this $(LibName) $(HdlMode); \
   $(foreach s,$(if $(filter $(HdlMode),core),$(wildcard $(CoreBlackBoxFiles)),$(call OcpiUniqueNotDir,$(HdlSources))),echo $(notdir $s);) \
  ) > $(dir $1)$(LibName).sources ;)

#  ) > $(patsubst %/,%,$(call HdlRmRv,$1)).sources ;)

# Here, we use HdlLibraryRefDir to determine the path to the library
# asset $2 in question. If we are working with an absolute path,
# just return the result of HdlLibraryRefDir. Otherwise, we are
# working with a relative path. Return the path relative to $3.
HdlRelativeOrAbsolutePathToLib=$(infox HRAPL:$1:$2:$3)$(strip \
  $(if $(filter /%,$2),\
    $(patsubst %/,%,$(call HdlLibraryRefDir,$2,$1,,X4)),\
    $(call FindRelative,$3,$(strip \
      $(call HdlLibraryRefDir,$2,$1,,X4)))))

# For a given library $2 and target $1, extract the library's source
# files from <lib>.sources
#
# Find the path relative or absolute path to '.' to determine a usable
# path for the .sources file. Grep the .sources file to collect source file
# names.
#
# Return the paths (relative or absolute) to each file listed in .sources
# relative to $3.
HdlExtractSourcesForLib=$(infox Extract:$2:$1)\
  $(foreach p,$(word 1,$(subst :, ,$2)),\
    $(foreach f,\
      $(call HdlRelativeOrAbsolutePathToLib,$1,$2,.),$(infox ZF:$f)\
        $(foreach z,$(call HdlGrepExcludeComments,$f/$(notdir $p).sources),$(infox foundsource:$z)\
          $(call HdlRelativeOrAbsolutePathToLib,$1,$2,$3)/$z)))

#########################################################################################################

HdlPassTargets=$(and $(HdlTargets),HdlTargets="$(HdlTargets)") \
               $(and $(HdlTarget),HdlTargets="$(HdlTarget)") \
               $(and $(HdlPlatforms),HdlPlatforms="$(HdlPlatforms)") \
               $(and $(HdlPlatform),HdlPlatforms="$(HdlPlatform)")

# Do target and vendor-specific file shadowing
# Note family/target files shadow vendor ones which shadow top-level ones
# Family and vendor directories may have ancillary/support files.
# These ancillary files must be uniquely named if they exist for both target and vendor directories
# Thus target ancillary files shadow vendor ancillary files.
# A SourceFiles_<target-or-vendor) variable may be defined to specify ordering of the ancillary
# files, but if there is no such variable, a simple wildcard is used in the shadow directory.
HdlShadowFiles=\
 $(foreach t,$(call HdlGetTop,$(HdlTarget)),\
   $(- first, include the files that are not shadowed)\
   $(foreach f,$(filter-out $(filter-out %.vhd,$(call CoreBlackBoxFiles,$1,$2)),\
               $(CompiledSourceFiles)),\
     $(if $(or $(wildcard $(HdlTarget)/$f),$(wildcard $t/$f)),,$f))\
   $(- second, include all target files)\
   $(or $(SourceFiles_$(HdlTarget)),$(wildcard $(HdlTarget)/*.v $(HdlTarget)/*.vhd))\
   $(- third, include all vendor files that are not shadowed by target files)\
   $(foreach f,$(or $(SourceFiles_$t),$(wildcard $t/*.v $t/*.vhd)),\
     $(if $(wildcard $(HdlTarget)/$(notdir $f)),,$f)))

# This is the list of files that will be generated in the TARGET
# directory.
# The VHDL defs file must preceed the generics file
# Return nothing if no parameters
# FIXME: this has worker stuff in it - should it be elsewhere?
# $(call HdlTargetSrcFiles,target-dir,paramconfig)
HdlTargetSrcFiles=\
  $(if $(filter-out library core,$(HdlMode)),\
    $(call HdlVHDLTargetDefs,$1,$2)\
    $(if $(HdlToolRequiresEntityStubs_$(HdlToolSet)),$(call HdlVHDLTargetEnts,$1,$2))\
    $(call HdlVerilogTargetDefs,$1,$2)\
    $(call WkrTargetDir,$1,$2)/generics$(HdlVHDLIncSuffix)\
    $(call WkrTargetDir,$1,$2)/generics$(HdlVerilogIncSuffix)\
    $(call HdlVHDLTargetImpl,$1,$2)\
    $(TargetSourceFiles_$2) \
    $(ImplFile),\
    $(TargetSourceFiles_$2)) # only use TargetSourceFiles for primitives

$(OutDir)target-%/generics.vhd: $$(ImplXmlFile) | $(OutDir)target-%
	$(AT)echo Generating the VHDL constants file for config $(ParamConfig): $@
	$(AT)$(call OcpiGen, -D $(@D) \
	                $(and $(Assembly),-S $(Assembly)) $(and $(Platform),-P $(Platform)) \
	                $(and $(PlatformDir),-F $(PlatformDir)) \
	                -g$(ParamConfig) $(and $(filter verilog,$(HdlLanguage)),-w) $(ImplXmlFile))

$(OutDir)target-%/generics.vh: $$(ImplXmlFile) | $(OutDir)target-%
	$(AT)echo Generating the Verilog constants file for config $(ParamConfig): $@
	$(AT)$(call OcpiGen, -D $(dir $@) \
	                $(and $(Assembly),-S $(Assembly)) $(and $(Platform),-P $(Platform)) \
	                $(and $(PlatformDir),-F $(PlatformDir)) \
	                -g$(ParamConfig) $(and $(filter vhdl,$(HdlLanguage)),-w) $(ImplXmlFile))

ifneq (,)
# Establish where the platforms are
ifndef HdlPlatformsDir
  HdlPlatformsDir:=$(OCPI_CDK_DIR)/lib/platforms
    ifeq ($(realpath $(HdlPlatformsDir)),)
      $(error No HDL platforms found. Looked in $(OCPI_CDK_DIR)/lib/platforms)
    endif
#  endif
endif
endif
# Do the stuff necessary when building an assembly
# This applies to platform configurations, application assemblies, and containers
define HdlPrepareAssembly
  $$(infox PREPARE0:$$(OCPI_PROJECT_REL_DIR))
  # 1. Scan component libraries to add to XmlIncludeDirs
  $$(call OcpiSetXmlIncludes)
  $$(eval $$(HdlSearchComponentLibraries))
  # 2. Generate (when needed) the workers file immediately to use for dependencies
  AssyWorkersFile:=$$(GeneratedDir)/$$(Worker).wks
  $$(if\
    $$(call DoShell,$$(MAKE) -f $$(OCPI_CDK_DIR)/include/hdl/hdl-get-workers.mk\
                    $$(OcpiGenEnv) \
                    Platform=$(Platform) \
                    PlatformDir=$(PlatformDir) \
                    Assembly=$(Assembly) \
	            ComponentLibrariesInternal="$$(call Unique,$$(ComponentLibraries) $$(ComponentLibrariesInternal))" \
                    XmlIncludeDirsInternal="$$(XmlIncludeDirsInternal)" \
                    AssyWorkersFile=$$(AssyWorkersFile) \
                    Worker=$$(Worker) Worker_xml=$$(Worker_xml) \
                    AT=$(AT), \
                    Output), \
    $$(error Error deriving workers from file $$(Worker).xml: $$(Output)),\
   )
  # 3. Generated the assembly source file
  ImplFile:=$$(GeneratedDir)/$$(Worker)-assy$$(HdlSourceSuffix)
  $$(ImplFile): $$$$(ImplXmlFile) | $$$$(GeneratedDir)
	$(AT)echo Generating the $$(HdlMode) source file: $$@ from $$<
	$(AT)$$(call OcpiGen, -D $$(GeneratedDir) \
                         $(and $(Assembly),-S $(Assembly)) $(and $(Platform),-P $(Platform)) \
			 $(and $(PlatformDir),-F $(PlatformDir)) \
                         -a $$<)
  # 4. Make the generated assembly source file one of the files to compile
  WorkerSourceFiles=$$(ImplFile)
  # 5. Set the workers-required variables from the generated AssyWorkersFile, target independent
  HdlInstances:=$$(and $$(AssyWorkersFile),$$(strip\
                   $$(foreach i,$$(shell grep -h -v '\\\#' $$(AssyWorkersFile)),\
	              $$(if $$(filter $$(call HdlInstanceWkr,$$i),$$(HdlPlatformWorkers)),,$$i))))
  HdlWorkers:=$$(call Unique,$$(foreach i,$$(HdlInstances),$$(call HdlInstanceWkrCfg,$$i)))

  generate: $$(ImplFile)
endef

#ifndef OCPI_HDL_PLATFORM
#OCPI_HDL_PLATFORM=zed
#endif
define HdlPreprocessTargets
  ifdef HdlPlatform
    override HdlPlatforms:=$$(call Unique,$$(HdlPlatform) $$(HdlPlatforms))
  endif
  ifeq ($$(origin HdlPlatforms),undefined)
    ifdef HdlPlatform
      ifneq ($$(words $$(HdlPlatform)),1)
        $$(error HdlPlatform variable must only have one platform)
      endif
      HdlPlatforms:=$$(HdlPlatform)
    else
      HdlPlatforms:=$$(if $$(filter platform,$$(HdlMode)),$$(CwdName),$$(OCPI_HDL_PLATFORM))
    endif
  else ifeq ($$(HdlPlatforms),all)
    override HdlPlatforms:=$$(HdlAllPlatforms)
  else ifdef HdlPlatforms
    # Leave it alone if it was specifically defined as nothing
    override HdlPlatforms:=$$(filter-out $$(ExcludePlatforms),$$(HdlPlatforms))
    ifdef OnlyPlatforms
     override HdlPlatforms:=$$(filter $$(OnlyPlatforms),$$(HdlPlatforms))
    endif
  endif
  ifndef HdlTargets
    ifdef HdlTarget
      HdlTargets:=$$(HdlTarget)
    else
      ifdef HdlPlatforms
        override HdlTargets:=\
          $$(call Unique,$$(foreach p,$$(HdlPlatforms),\
            $$(if $$(HdlPart_$$p),$$(call HdlGetFamily,$$(HdlPart_$$p)),\
               $$($$(if $$(filter clean%,$$(MAKECMDGOAL)),warning,error) Unknown platform: $$p))))
      else
        override HdlTargets:=$$(and $$(OCPI_HDL_PLATFORM),$$(call HdlGetFamily,$$(OCPI_HDL_PLATFORM)))
      endif
    endif
  else ifeq ($$(HdlTargets),all)
    override HdlTargets:=$$(HdlAllFamilies)
  endif
endef

OcpiPullPkgFiles=$(call Unique,$(filter %_pkg.vhd,$1) $(filter-out %_pkg.vhd,$1))

define HdlInstallLibsAndSources
  HdlLibsList=install_libs

  $$(HdlLibsList):
	$(AT) if test -f $(GeneratedDir)/$(call RmRv,$(LibName)).libs; then \
	    $$(call ReplaceIfDifferent,$$(strip \
	        $(GeneratedDir)/$(call RmRv,$(LibName)).libs),$(strip \
	        $(HdlInstallLibDir)))\
          fi;\

  ifdef HdlToolNeedsSourceList_$(HdlToolSet)
    HdlSourcesList=install_sources

    $$(HdlSourcesList):
	$(AT)for f in $$(HdlActualTargets); do \
          if test -f $(OutDir)target-$$$$f/$(call RmRv,$(LibName)).sources; then \
            $$(call ReplaceIfDifferent,$(strip \
	        $(OutDir)target-$$$$f/$(call RmRv,$(LibName)).sources),$(strip \
	        $(OutDir)target-$$$$f/$(WorkLib)));\
          fi;\
	done
  endif

  install: $$(HdlLibsList) $$(HdlSourcesList)

endef

include $(OCPI_CDK_DIR)/include/hdl/hdl-search.mk
endif # __HDL_MAKE_MK__
