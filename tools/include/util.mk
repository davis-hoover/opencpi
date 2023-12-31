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
ifndef __UTIL_MK__
__UTIL_MK__=x
# The /bin/sh shell in Debian/Ubuntu is explicitly strict/stupid
override SHELL=/bin/bash
export AT
export OCPI_DEBUG_MAKE
AT=@

# RPM-based options:
# Removing these since they cause all kinds of problems, but should discuss further...
# to see whether they still are relevant
#-include $(OCPI_CDK_DIR)/include/autoconfig_import-$(OCPI_TARGET_PLATFORM).mk
#ifneq (1,$(OCPI_AUTOCONFIG_IMPORTED))
#-include $(OCPI_CDK_DIR)/include/autoconfig_import.mk
#endif
# THIS IS THE make VERSION OF WHAT IS IN ocpibootstrap.sh
ifndef OCPI_PREREQUISITES_DIR
  ifneq ($(and $(OCPI_CDK_DIR),$(wildcard $(OCPI_ROOT_DIR)/prerequisites)),)
    export OCPI_PREREQUISITES_DIR:=$(abspath $(OCPI_ROOT_DIR)/prerequisites)
  else
    export OCPI_PREREQUISITES_DIR:=/opt/opencpi/prerequisites
  endif
endif
#FIXME  this registration should be somewhere else nicer
ifndef OCPI_PREREQUISITES_LIBS
  # Libraries used with ACI and our executables
  export OCPI_PREREQUISITES_LIBS:=lzma gmp gpsd
endif
ifndef OCPI_PREREQUISITES
  # All prerequisites we need to build and use
  export OCPI_PREREQUISITES:=$(OCPI_PREREQUISITES_LIBS) gtest patchelf ad9361
endif
OCPI_DEBUG_MAKE=
ifneq (,)
define OcpiDoInclude
ifndef OcpiThisFile
OcpiThisFile:=$(lastword $(MAKEFILE_LIST))
endif
OcpiSaveFile:=$(OcpiThisFile)
include $(OCPI_CDK_DIR)/include/$(1)
OcpiThisFile:=$(OcpiSaveFile)
endef
OcpiInclude=$(eval $(call OcpiDoInclude,$1))
endif

ifneq ($(OCPI_DEBUG_MAKE),)
define OcpiDbg
$(warning Debug: $(1))
endef
define OcpiDbgVar
$(call OcpiDbg,$(2)$(1) is <$(call $(1))> origin $(origin $(1)))
endef
endif

# Options we alway use and will assume everywhere (except when building framework; AV-3464)
.DELETE_ON_ERROR:
ifndef OCPI_AUTOCONFIG_IMPORTED
.SUFFIXES:
endif
.SECONDEXPANSION:

# Utilities used by many other makefile files
# Allow us to include this early by establishing the default initial target (all).
all:
.PHONY: all
Cwd:=$(realpath .)
$(call OcpiDbgVar,Cwd)
Empty:=
Space:=$(Empty) $(Empty)
# This variable is set to the character that is invalid in pathnames.
# It should be the one printable character that we will not support in pathnames.
Invalid:="
# end hanging quote above for some editors --> "
CwdDirName:=$(subst $(Invalid),$(Space),$(notdir $(subst $(Space),$(Invalid),$(Cwd))))
CwdName:=$(basename $(CwdDirName))
$(call OcpiDbgVar,CwdName)

# Avoid calling the shell to execute the TR command for this purpose (save two process/shell invocations)
OcpiUpper:=A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
OcpiLower:=a b c d e f g h i j k l m n o p q r s t u v w x y z
OcpiNumber:=0 1 2 3 4 5 6 7 8 9
OcpiSpecial:=! " \# $$ % & ' ( ) * + , - . / : ; < = > ? ` { | } ~
OcpiPrint:=$(OcpiUpper) $(OcpiLower) $(OcpiNumber) $(OcpiSpecial)
OcpiTranslate=$(strip\
                $(eval OcpiTranslate_:=$1)\
                $(foreach x,$(join $(2:%=%:),$3),\
                  $(eval OcpiTranslate_:=$(strip\
                    $(subst $(firstword $(subst :, ,$x)),$(word 2,$(subst :, ,$x)),$(OcpiTranslate_)))))\
                $(OcpiTranslate_))
OcpiToUpper=$(call OcpiTranslate,$1,$(OcpiLower),$(OcpiUpper))
OcpiToLower=$(call OcpiTranslate,$1,$(OcpiUpper),$(OcpiLower))
OcpiCapitalize=$(or $(strip $(foreach l,$(OcpiLower),\
	              $(if $(filter $l%,$1),$(call OcpiToUpper,$l)$(patsubst $l%,%,$1)))),$1)

# $(foreach s,abc =-09 AbC,$(info CAP:$s:$(call OcpiCapitalize,$s)))
# $(info ZU:$(call OcpiToUpper,abcd):$(call OcpiToUpper,Abce):$(call OcpiToUpper,ABCf):$(call OcpiToUpper,1abCg:3))
# $(info ZL:$(call OcpiToLower,abcd):$(call OcpiToLower,Abce):$(call OcpiToLower,ABCf):$(call OcpiToLower,1abCg:3))

# These need to be early since some immediate assignments use them below
#Capitalize=$(shell csh -f -c 'echo $${1:u}' $(1))
#UnCapitalize=$(shell csh -f -c 'echo $${1:l}' $(1))
#Capitalize=$shell awk -v x=$(1) 'BEGIN {print toupper(substr(x,1,1)) substr(x,2,length(x)-1) }')
#UnCapitalize=$(shell awk -v x=$(1) 'BEGIN {print tolower(substr(x,1,1)) tolower(x,2,length(x)-1) }')
#Capitalize=$shell awk -v x=$(1) 'BEGIN {print toupper(substr(x,1,1)) substr(x,2,length(x)-1) }')
UnCapitalize=$(error UnCapitalize no implementation)
Capitalize=$(call OcpiCapitalize,$1)
ToUpper=$(call OcpiToUpper,$1)
ToLower=$(call OcpiToLower,$1)

ifndef Model
Model:=$(strip $(subst ., ,$(suffix $(CwdDirName))))
endif
$(call OcpiDbgVar,Model)
Models:=xm rcc hdl ocl assy
Language_rcc:=c
Languages_rcc:=c c++
Suffix_rcc_c:=c
Suffix_rcc_c++:=cc

Suffix_hdl_verilog:=v
Suffix_hdl_vhdl:=vhd
Language_hdl:=vhdl
Languages_hdl:=vhdl verilog

Language_ocl:=ocl
Suffix_ocl_ocl:=cl
Suffix_xm:=xm
# Assign here for caching
CapModels:=$(foreach m,$(Models),$(call Capitalize,$m))
UCModel=$(call ToUpper,$(Model))
CapModel=$(call Capitalize,$(Model))
AT=@
RM=rm
ifeq ($(OCPI_TOOL_OS),linux)
# gnu version has nicer formatting options
TIME=/usr/bin/time -f %E
else
TIME=/usr/bin/time
endif
# this is to ensure support for the -n flag
ECHO=/bin/echo
#default assumes all generated files go before all authored files
CompiledSourceFiles=$(TargetSourceFiles_$(ParamConfig)) $(GeneratedSourceFiles) \
                    $(filter-out $(call OcpiCPPSources,$(AuthoredSourceFiles)),$(AuthoredSourceFiles))
# Just for history (thanks Andrew): this only works with tcsh, not traditional csh.  And csh isn't posix anywah
# function to add a ../ to pathnames, avoiding changing absolute ones
AdjustRelative2=$(foreach i,$(1),$(if $(filter /%,$(i)),$(i),../../$(patsubst ./%,%,$(filter-out .,$(i)))))
AdjustRelative=$(foreach i,$(1),$(if $(filter /%,$(i)),$(i),..$(patsubst %,/%,$(patsubst ./%,%,$(filter-out .,$(i))))))

# Physical and realpath are broken on some NFS mounts..
OcpiAbsDir=$(realpath $1)#$(foreach d,$(shell cd $1; pwd -L),$d)
OcpiAbsPath=$(strip \
  $(call OcpiCacheFunctionOnPath,OcpiAbsPathX,$(or $1,.)))
OcpiAbsPathX=$(strip \
  $(foreach p,$(strip \
    $(if $(filter /%,$1),$1,\
      $(if $(filter . ./,$1),$(call OcpiAbsDir,.),\
        $(if $(filter ./%,$1),$(call OcpiAbsDir,.)$(patsubst .%,%,$1),\
          $(call OcpiAbsDir,.)/$1)))),$(abspath $p)))

define OcpiParseXml
  $$(infox PARSE:$1:$2)
  $$(if $$(call DoShell,set -o pipefail && $$(ToolsDir)/ocpigen -R $1/$2.xml|tr "\n" "@"|tr " " "~",OcpiProps),\
    $$(error ocpigen failed),\
    $$(foreach var,$$(subst @, ,$$(OcpiProps)),$$(eval $$(subst ~, ,$$(var)))))
  $$(infox $0: OcpiProps is $$(subst @, ,$$(OcpiProps)))
endef

# Call a function ($1) with a single path argument ($2).
# If this is the first time that function has been called with that argument,
# cache the results. Otherwise, return the cached results.
# $(call OcpiCacheFunctionOnPath,<function-to-call>,<path-argument>)
OcpiCacheFunctionOnPath=$(strip \
  $(or \
    $(foreach c,$(filter $2:%,$(OcpiCacheFunctionOnPath_$1_cache)),\
        $(word 2,$(subst :, ,$c))),\
    $(foreach c,$(call $1,$2),$(eval OcpiCacheFunctionOnPath_$1_cache:=$(OcpiCacheFunctionOnPath_$1_cache) $2:$c)$c)))

# helper function to FindRelative, recursive
# arg 1 is from-list of path components, arg 2 is to-list
#$(info frs 1 $(1) 2 $(2))
FindRelativeStep=\
    $(if $(filter $(firstword $(1)),$(firstword $(2))),\
        $(call FindRelativeStep,$(wordlist 2,$(words $(1)),$(1)),$(wordlist 2,$(words $(2)),$(2))),\
	$(if $(1),$(subst $(Space),/,$(strip $(patsubst %,..,$(1))))$(if $(2),/),$(if $(2),,.))$(subst $(Space),/,$(2)))

# helper function for FindRelative
# arg1 is absolute-from arg2 is absolute-to arg3 is original from, arg4 is original to
#$(info 1 $(1) 2 $(2) 3 $(3) 4 $(4))
FindRelativeTop=$(infoxx FRT:$1:$2:$3:$4)$(strip\
  $(foreach t,\
        $(if $(strip $1),\
            $(if $(strip $2),\
	        $(if $(filter $(firstword $(strip $(subst /, ,$1))),$(firstword $(strip $(subst /, ,$2)))),\
                    $(call FindRelativeStep,$(strip $(subst /, ,$1)), $(strip $(subst /, ,$2))),\
		    $2),\
                $(error Invalid/non-existent path: to "$4" from "$3")),\
             $(error Invalid/non-existent path: from "$3" to "$4")),\
  $(infox FRTr:$t:$(CURDIR))$t))

# Function: return the relative path to get from $(1) to $(2).  Useful for creating symlinks
# Note return value must be nicely stripped
#$(info findrel 1 $(1).$(abspath $1) 2 $(2).$(abspath $2))
#$(info pwd:$(shell pwd) abs:$(abspath .) real:$(realpath .))
#FindRelative=$(strip $(call FindRelativeTop,$(call OcpiAbsPath,$1),$(call OcpiAbsPath,$2),$1,$2))
FindRelative=$(strip $(infox FR:$1:$2:$3)\
               $(foreach i,$(call FindRelativeTop,$(call OcpiAbsPath,$1),$(call OcpiAbsPath,$2),$(strip $1),$(strip $2)),$i))

# Function: retrieve the contents of a symlink
# It would be easier using csh
SymLinkContents= `X=(\`ls -l $(1)\`);echo $${X[$${\#X[*]}-1]}`

# Function:
# Make a symlink, but don't touch it if it is already correct
#  First arg is local file to point to, second arg is dir to put link in.
#  e.g. $(call MakeSymLink,foo,linkdir) makes a link: dir/$(notdir foo) link to foo
# Funky because it might be executed in a loop
MakeSymLink2=	$(infox MSL2:$1:$2:$3)SL=$(2)/$(3); SLC=$(call FindRelative,$2,$1); \
		if test -L $$SL; then \
		  OSLC="$(call SymLinkContents,$2/$3)"; \
		else \
		  OSLC=; \
		fi;\
		if test "$$OSLC" != $$SLC; then \
		  rm -f $$SL; \
		  ln -s $$SLC $$SL; \
		fi
MakeSymLink=$(call MakeSymLink2,$(1),$(2),$(notdir $(1)))


# function of that puts stuff in a temporary file and returns its name.
MakeTemp=\
$(shell export TMPDIR=$(TargetDir);\
  TF=`mktemp -t -u`;echo "$(1)" | tr " " "\n"> $$TF;echo $$TF)

# Output directory processing.  OutDir is the internal variable used everywhere.
# It is set based on the public OCPI_OUTPUT_DIR, and is created as needed
ifndef OutDir
ifdef OCPI_OUTPUT_DIR
OutDir=$(OCPI_OUTPUT_DIR)/$(CwdName)/
$(OutDir):
	$(AT)mkdir $@
endif
endif
GeneratedDir=$(OutDir)gen
$(GeneratedDir): | $(OutDir)
	$(AT)mkdir $@

# Make all target dirs
TargetDir=$(OutDir)target-$(or $(and $(CapModel),$($(CapModel)TargetDir)),$($(CapModel)Target))
#$(AT)echo Creating target directory: $@
$(OutDir)target-%: | $(OutDir)
	$(AT)mkdir $@

################################################################################
# $(call ReplaceIfDifferent,source-file-or-dir, dest-dir)
# A utility function to compare two trees that might contain binary files
# The first argument is the directory (or file) to be copied, and whose
# "tail" name should be placed in the destination directory
ifeq ($(OCPI_TOOL_OS),macos)
MD5=md5
else
MD5=md5sum -b -
endif
TreeHash=`(if test -f $(1); then \
             cat $(1); \
           elif test -e $(1); then \
             cd $(1); \
             find -L . -type f | sort | xargs cat; \
           fi) \
           | $(MD5)`
ReplaceIfDifferent=$(infox REPLACE:$1:$2:$3)\
  TAIL=`basename $(1)`; \
  while test 1; do \
    if test -f $(1); then OLD=$(2)/$$TAIL; else OLD=$(2); fi;\
    if test -e $1; then \
      NEWHASH=$(call TreeHash,$(1));\
      OLDHASH=$(call TreeHash,$$OLD);\
      if test "$$OLDHASH" = "$$NEWHASH"; then\
        echo Installation suppressed for $(1) in $(2). Destination is identical.; \
        break; \
      fi; \
      if test -e $$OLD; then \
        echo Removing previous installation for $(1) in $(2). ; \
        rm -r -f $$OLD; \
      else \
        echo No previous installation for $(1) in $(2). ;\
      fi; \
    fi; \
    if test ! -d $(2); then\
      mkdir -p $(2); \
    fi; \
    echo Installing $(1) into $(2); \
    if test -f $(1); then \
      cp -L -p $(1) $(2); \
    else \
      cp -L -R -p $(1)/* $(2); \
    fi; \
    touch $2; \
    break;\
  done
ReplaceContentsIfDifferent=\
  TAIL=`basename $(1)`; \
  while test 1; do \
    if test -e $(2); then \
      OLD=$(call TreeHash,$(1));\
      NEW=$(call TreeHash,$(2));\
      if test "$$OLD" = "$$NEW"; then\
        echo Installation suppressed for $(1). Destination is identical.; \
        break; \
      fi; \
      echo Removing previous installation for $(1) -\> $(2); \
      rm -r -f $(2); \
    fi; \
    if test ! -d $(2); then\
      mkdir -p $(2); \
    fi; \
    echo Installing $(1) -\> $(2); \
    cp -L -R -p $(1)/* $(2); \
    break;\
  done

################################################################################
# $(call Unique,words,already)
# A utility function to remove duplicates without reordering
# The second argument is just for recursion and should be blank on the call
Unique=$(infox Unique:$1)$(strip $(foreach x,$(call Unique2,$1,),$x))
Unique2=$(infox Unique2:$1:$2:)$(if $1,$(call Unique2,$(wordlist 2,$(words $1),$1),$(strip\
                               $(foreach w,$(firstword $1),$(if $(filter $w,$2),$2,$2 $w)))),$2)

# Take a list of paths, and return the list of
# paths that have unique notdir values
OcpiUniqueNotDir=\
  $(eval NotDiredList= )\
  $(foreach f,$1,\
    $(if $(filter $(notdir $f),$(NotDiredList)),,\
      $(eval NotDiredList+=$(notdir $f) )\
      $f ))

LibraryRefFile=$(call $(CapModel)LibraryRefFile,$1,$2)

################################################################################
# Tools for metadata and generated files
DateStamp := $(shell date +"%c")
ToolsDir=$(eval $(OcpiEnsureToolPlatform))$(OCPI_CDK_DIR)/$(OCPI_TOOL_DIR)/bin
# Here are the environment variables that might be set in the "make" environment,
# that must be propagated to ocpigen.
OcpiGenEnv=\
    OCPI_PROJECT_DIR="$(OCPI_PROJECT_DIR)" \
    OCPI_PROJECT_PACKAGE="$(OCPI_PROJECT_PACKAGE)" \
    OCPI_PROJECT_REL_DIR="$(OCPI_PROJECT_REL_DIR)" \
    OCPI_PREREQUISITES_DIR="$(OCPI_PREREQUISITES_DIR)" \
    OCPI_PROJECT_DEPENDENCIES="$(OCPI_PROJECT_DEPENDENCIES)" \
    OCPI_COMPONENT_LIBRARIES="$(call Unique,$(ComponentLibraries) $(ComponentLibrariesInternal))" \
    OCPI_ALL_PLATFORMS="$(strip $(HdlAllPlatforms:%=%.hdl) $(RccAllPlatforms:%=%.rcc) $(OclAllPlatforms:%=%.ocl))"\
    $(- this is a horrible modularity violation, but it basically would require a hdl-pre-pre.mk)\
    OCPI_HDL_LIBRARIES="$(call Unique,$(HdlExplicitLibraries))"\
    OCPI_ALL_HDL_TARGETS="$(OCPI_ALL_HDL_TARGETS)" \
    OCPI_ALL_RCC_TARGETS="$(OCPI_ALL_RCC_TARGETS)" \
    OCPI_ALL_OCL_TARGETS="$(OCPI_ALL_OCL_TARGETS)" \
    OCPI_AUTO_BUILD_WORKERS="$(OCPI_AUTO_BUILD_WORKERS)"

OcpiGenTool=$(OcpiGenEnv) $(OCPI_VALGRIND) $(ToolsDir)/ocpigen \
  $(call OcpiFixPathArgs,$(patsubst %,-I%,$(XmlIncludeDirsInternal)) $1)
# Given a collection of arguments, fix each path in the argument
# that starts with '/' or '-I/' for use with ocpigen or compilation.
# This will prevent absolute paths whenever possible and instead compute
# paths relative to the project's top or 'imports' when possible.
# $(call OcpiFixPathArgs,"-Igen -Itarget-zynq -M target-14-zynq/generics.vh.deps /data/...")
OcpiFixPathArgs=\
  $(foreach p,$1,\
    $(if $(filter /%,$p),\
      $(call OcpiPathThroughProjectTopOrImports,.,$p),\
      $(if $(filter -I/%,$p),\
        $(patsubst %,-I"%",$(call OcpiPathThroughProjectTopOrImports,.,$(patsubst -I%,%,$p))),\
        $p)))
OcpiGenArg=$(call OcpiGenTool, $1 -M $(dir $@)$(@F).deps $2)
OcpiGen=$(call OcpiGenArg,,$1)$(infox OGA:$(call OcpiGenArg,,$1))

# Return stderr and the exit status as variables
# Return non-empty on failure, empty on success, and set var
# $(call DoShell,<command>,<status var>,<value var>)
# 2 limitations:
# - The "#" character is changed to "<pound>" in the output
# - On success, the value will be a combination of stderr and stdout
# Example:
#  $(if $(call DoShell,ls -l,Value),$(error $(Value)),$(Value))
#DoShell=$(eval X:=$(shell X=`bash -c '$1; exit $$?' 2>&1`;echo $$?; echo "$$X" | sed "s/\#/<pound>/g"))$(strip \
#
define OcpiNewLine


endef
DoShell=$(eval X:=$(shell X=`bash -c '$1; exit $$?'`;echo $$?; echo "$$X" | sed "s/\#/<pound>/g"))$(strip \
	     $(call OcpiDbg,DoShell($1,$2):X:$X) \
             $(eval $2:=$(wordlist 2,$(words $X),$X))\
	     $(call OcpiDbgVar,$2) \
             $(filter-out 0,$(firstword $X)))

# Convert a space separated string (a make-list) to a python list containing '[,]'
# $(call OcpiConvertListToPythonList,<space-separated-string-list>)
OcpiConvertListToPythonList=$(strip \
  ["$(subst $(Space),"$(Comma) ",$(strip $1))"])

# Run the python code in $1
# Usage: $(call OcpiCallPythonFunc,this_is_a_python_function_with_output())
OcpiCallPythonFunc=\
  $(shell python3 -c '$1')

# Import the ocpiutil module and run the python code in $1
# Usage: $(call OcpiCallPythonUtil,ocpiutil.utility_function(arg1, arg2))
OcpiCallPythonUtil=$(infox OPYTHON:$1)\
  $(shell PYTHONPATH=$(PYTHONPATH) python3 -c 'import _opencpi.util as ocpiutil;$1')

# Like the builtin "dir", but without the trailing slash
OcpiDir=$(foreach d,$1,$(patsubst %/,%,$(dir $1)))

# Grab the language attribute out of an XML file the hard way
OcpiGetLangScript:="s/^.*[lL]anguage= *['\"]\([^'\"]*\).*/\1/"
OcpiGetLanguage=$(strip \
    $(call ToLower,\
       $(shell grep -i 'language *= *' $1 | sed $(OcpiGetLangScript))))

# Set the language attribute from the list of xml files in $1
define OcpiSetLanguage
  OcpiLanguage:=$$(sort $$(foreach f,$1,\
		    $$(and $$(realpath $$f),$$(call OcpiGetLanguage,$$f))))
  $$(and $$(word 2,$$(OcpiLanguage)),\
     $$(error Multiple languages found in the worker xml files: $$(OcpiLanguage)))
  $$(call OcpiDbgVar,OcpiLanguage)
  ifndef OcpiLanguage
    OcpiLanguage:=$(Language_$(Model))
  endif
  ifndef Suffix_$(Model)_$$(OcpiLanguage)
    $$(error The language "$$(OcpiLanguage)" is not supported for the "$(Model)" model.)
  endif
endef

# Generate the default XML contents for $1 a worker and $2 a model
# Executed with CWD being the worker directory
OcpiDefaultSpec=$(or $(wildcard ../specs/$1_spec.xml),$(wildcard ../specs/$1-spec.xml))
OcpiDefaultOWD=$(if $(call OcpiDefaultSpec,$1),,$(error No default spec found for worker $1))$(strip \
  <$(call Capitalize,$2)Worker name='$1' \
    language='$(Language_$(Model))' \
    spec='$(notdir $(call OcpiDefaultSpec,$1))'/>)

# Function to generate target dir from target: $(call WkrTargetDir,target,config)
# FIXME: shouldn't really be named "Wkr"
WkrTargetDir=$(if $1,,$(error Internal error: WkrTargetDir called without a target))$(strip \
              $(foreach d,\
                $(OutDir)target$(if $(filter 0,$2),,-$2)-$(or $(call $(CapModel)TargetDirTail,$1),$1),\
                $d))

Comma:=,
ParamMsg=$(and $(ParamConfigurations), $(strip \
  '($(foreach n,$(WorkerParamNames),$n=$(ParamMsg_$(ParamConfig)_$n)$(eval o:=1)))'))

RmRv=$(if $(filter %_rv,$1),$(patsubst %_rv,%,$1),$1)

OcpiAdjustLibraries=$(call Unique,$(foreach l,$1,$(if $(findstring /,$l),$(call AdjustRelative,$l),$l)))
OcpiAdjustLibraries2=$(call Unique,$(foreach l,$1,$(if $(findstring /,$l),$(call AdjustRelative2,$l),$l)))

################################################################################
# This works when wildcard doesn't.
# (Note: make's wildcard function caches results so can't probe something that
# might come into existence during execution of make)
# There are strange NFS mount use cases that might not return the real path,
# so if that happens, drop to the older/slower Shell call.
OcpiExists=$(infox OEX:$1)$(foreach y,$(foreach x,$(realpath $1),$(if $(filter /%,$x),$1,$(strip $(shell if test -e $1; then echo $1; fi)))),$(infox OEX return $y)$y)

OcpiCheckLinks=$(strip \
  $(foreach d,$1,$d$(shell test -L $d -a ! -e $d && echo " (a link to non-existent/unbuilt?)")))

define OcpiComponentSearchError
The component library "$1" was not found in any of these locations: $(call OcpiCheckLinks,$2)
OCPI_COMPONENT_LIBRARY_PATH is: $(OCPI_COMPONENT_LIBRARY_PATH)
Internal Project Path is: $(OcpiGetProjectPath)
OCPI_CDK_DIR is: $(OCPI_CDK_DIR)
endef

# Given a location of a component library, return the relevant subdirectory
# This normalizes between exported libraries and source libraries
OcpiComponentLibraryExists=$(or $(call OcpiExists,$1/lib),$(call OcpiExists,$1))

# Return per-library export directories in this project that exist, ignore libs with slashes
# THIS MUST BE IN SYNC WITH THE C++ VERSION in platforms.cxx
# arg1: the project's directory
# arg2: the set of cmponent libraries (non-slash)
# arg3: whether it is local
# arg4: whether to include top-level specs directory
# Second arg means it is a local project rather than a project-path (ProjectDependencies) project
# $(call OcpiSearchComponentLibrariesInProject,<project-dir>,<local-project?>)
OcpiSearchComponentLibrariesInProject=$(infox OSCLIP:$1:$2:$3:$4)$(strip \
  $(if $3,\
    $(foreach l,$2,\
      $(foreach d,$(if $(filter devices cards adapters,$l),hdl/$l,components$(if $(filter components,$l),,/$l)),\
        $(call OcpiExists,$1/$d/lib))),\
    $(foreach p,$(or $(call OcpiExists,$1/exports/lib),$1/lib),\
      $(foreach l,$2,\
	$(call OcpiExists,$p/$l)))))

# Search for a component library by name, independent of target
# This is not used for component libraries specified by location (with slashes)
# OCPI_COMPONENT_LIBRARY_PATH is used BEFORE other libraries in the project
# The second arg is a boolean as to whether to include specs or not
# for when we are being called for XML searching
# $(call OcpiSearchComponentPath,lib,x)
# OcpiSearchComponentPath=\
#   $(eval OcpiTempPlaces:=$(strip\
#        $(subst :, ,$(OCPI_COMPONENT_LIBRARY_PATH)) \
#        $(foreach d,$(OcpiProjectDir) $(OcpiGetProjectPath),$($d/lib)))\
#   $(eval OcpiTempDirs:= $(strip \
#     $(foreach p,$(OcpiTempPlaces),\
#        $(foreach d,$p/$1,$(call OcpiComponentLibraryExists,$d)))))\
#   $(or $(OcpiTempDirs)$(infox HTD:$(OcpiTempDirs)),\
#     $(if $(filter clean,$(MAKECMDGOALS)),,$(error $(call OcpiComponentSearchError,$1,$(OcpiTempPlaces)))))

# Collect component libraries independent of targets, across projects
# Explicit directories (with slashes) come first, then
# then project by project (starting with the current project), and within that, library by library
# First argument is whether to include project-level specs directories for xml searching or not
OcpiComponentLibraries=$(infox OCL:$(OCPI_PROJECT_REL_DIR):$(OCPI_PROJECT_DIR):$(OcpiProjectDir))$(strip\
  $(eval OcpiTempLibs:=$(call Unique,$(ComponentLibraries) $(ComponentLibrariesInternal)))\
  $(foreach l,$(OcpiTempLibs),\
    $(and $(findstring /,$l),\
      $(or $(call OcpiExists,$l/lib),$(call OcpiExists,$l),\
        $(error Component library at "$l" does not exist or is not built.))))\
  $(eval OcpiTempLibs:=$(foreach l,$(OcpiTempLibs),$(if $(findstring /,$l),,$l)))\
  $(eval OcpiTempFound:=$(call OcpiSearchComponentLibrariesInProject,$(OCPI_PROJECT_REL_DIR),$(OcpiTempLibs),true,$1))\
  $(foreach p,$(OcpiProjectDir) $(OcpiGetProjectPath),\
    $(eval OcpiTempFound+=$(call OcpiSearchComponentLibrariesInProject,$p,$(OcpiTempLibs),,$1)))\
  $(foreach l,$(OcpiTempLibs),$(if $(filter %/$l,$(patsubst %/lib,%,$(OcpiTempFound))),,\
    $(error Component library "$l" was not found in this or any of these projects: $(OcpiGetProjectPath)))) \
  $(and $(filter 1,$(OCPI_SEARCH_VERBOSE)),\
    $(if $1,\
       $(info For XML searching of ComponentLibraries, found directories are:),\
       $(info For searching for ComponentLibraries, found directories are:))\
    $(foreach d,$(OcpiTempFound),$(infox * $d)))\
  $(OcpiTempFound))

# Return a colon separated default OCPI_LIBRARY_PATH. It contains:
# 1. arg1 if present
# 2. the core project's artifacts
# 3. the artifacts exported from the projects in the project path (its dependencies)
# 4. the global core rcc artifacts in the runtime package for the host
OcpiGetDefaultLibraryPath=$(foreach p,$(strip \
  $(and $1,$1:)$(foreach p,$(call OcpiAbsPathToContainingProject,$1),$p/artifacts)$(strip\
  $(subst $(Space),,$(foreach p,$(OcpiGetProjectPath),:$p/artifacts)\
                    :$(OCPI_CDK_DIR)/$(OCPI_TOOL_DIR)/artifacts))),$(infox OGDLPr:$p)$p)

# Export the library path as the default
OcpiSetDefaultLibraryPath=$(eval export OCPI_LIBRARY_PATH=$(call OcpiGetDefaultLibraryPath))

# Collect the projects in path from the different sources.
# OCPI_PROJECT_PATH comes first and is able to shadow the others.
# ProjectDependencies comes next which can be user-defined and is appended with
# the 'required' projects (e.g. core/cdk).
# If CDK is not in the resulting list of projects, add it at the end.
# Warning is suppressed during RPM builds
OcpiGetProjectPath=$(strip \
                     $(foreach p,$(subst :, ,$(OCPI_PROJECT_PATH)) $(OcpiGetProjectDependencies),\
                       $(or $(call OcpiExists,$p/exports),$(call OcpiExists,$p),$(RPM_BUILD_ROOT),\
                         $(info Warning: The path $p in Project Path does not exist.))))

# There are certain cases where we will want all projects that are 'registered'
# (not just the ones explicitly or implicitly depended on by the current project).
# For example, available platforms can be determined based on all known projects.
# Warning is suppressed during RPM builds
# This may be called from outside of a project
# This function returns project directories, NOT their export subdirectories
OcpiGetExtendedProjectPath=$(strip\
  $(if $(OCPI_PROJECT_DIR),\
    $(foreach p,$(OcpiGetProjectPath),\
      $(if $(filter $(notdir $p),exports),$(patsubst %/,%,$(dir $p)),$p)) \
    $(foreach p,$(OcpiGetImportsNotInDependencies),\
      $(or $(call OcpiExists,$p),$(RPM_BUILD_ROOT),\
           $(info Warning: The path $p in Project Path does not exist.))),\
    $(subst :, ,$(OCPI_PROJECT_PATH)) $(wildcard $(OcpiGlobalDefaultProjectRegistryDir)/*)))

# Loop through all imported projects and check for 'exports' and then try to find
# rcc/platforms. Return a list of paths to 'rcc/platforms' directories found in each
# imported project. Search the current project's rcc/platforms first. If the current
# project is in OcpiGetExtendedProjectPath, filter it out.
#
# Note: the path 'platforms' without a leading 'rcc/' is searched as well for legacy
#       compatibilty before rcc platforms were supported outside of the CDK
#       exports/lib/rcc/platforms is deprecated
OcpiGetRccPlatformPaths=$(strip \
                          $(foreach p,$(OCPI_PROJECT_DIR),\
                            $(call OcpiExists,$p/rcc/platforms))\
                          $(foreach p,$(OcpiGetExtendedProjectPath),\
                            $(if $(filter-out $(realpath $(OCPI_PROJECT_DIR)),\
                                              $(realpath $(call OcpiAbsPathToContainingProject,$p))),\
                              $(or $(call OcpiExists,$p/exports/rcc/platforms),$(strip \
                                   $(call OcpiExists,$p/rcc/platforms))))))

# Search for a given platform ($1) in the list of 'rcc/platform' directories found
# by OcpiGetRccPlatformPaths.  The search priority is:
# 1. if the project is exported, just use rcc/platforms/$1
# 2. if not exported, look for a platform export in rcc/platforms/$1/lib
# 3. assume a raw source tree with no project or platform exports, and use rcc/platforms/$1
OcpiGetRccPlatformDir=$(strip $(firstword \
		        $(foreach p,$(OcpiGetRccPlatformPaths),\
                          $(if $(findstring /exports/rcc/,$p/$1),$(call OcpiExists,$p/$1),\
                               $(or $(call OcpiExists,$p/$1/lib),$(call OcpiExists,$p/$1))))))

##################################################################################
# Functions for collecting Project Dependencies and imports for use with project
# path
##################################################################################
# Project Dependencies are defined by those explicitly listed in a Project.<mk|xml>
# as well as the 'required' projects such as core/cdk
OcpiProjectDependenciesInternal=$(call Unique,$(ProjectDependencies)\
                                   $(if $(filter ocpi.core,$(OCPI_PROJECT_PACKAGE)),,ocpi.core))
# If a project dependency is a path, use it as is. Otherwise, check for it in the
# project's registry, whether explicit imports or implicit global registry
OcpiGetProjectDependencies=$(strip \
  $(foreach r,$(or $(wildcard $(OCPI_PROJECT_REL_DIR)/imports),\
              $(OcpiGlobalDefaultProjectRegistryDir)),\
    $(foreach d,$(OCPI_PROJECT_DEPENDENCIES),$(infox DEP:$d:$(OCPI_PROJECT_PACKAGE):$(OCPI_PROJECT_PACKAGE_ID))\
      $(if $(findstring /,$d),\
        $d,\
	$(or $(wildcard $r/$d),\
          $(error In $(CWD), for project at $(realpath $(OCPI_PROJECT_REL_DIR)), dependency $d is not registered at $r))))))

#      $(call OcpiGetProjectInImports,.,$d)) ))
# These are the leftover imports that are not listed in the ProjectDependencies
OcpiGetImportsNotInDependencies=$(strip \
  $(foreach i,$(OcpiGetProjectImports),\
    $(if $(filter $(notdir $i),$(OCPI_PROJECT_DEPENDENCIES)),\
      ,\
      $i) ))

###################################################################################
# Functions for collecting paths to/through/from the top level of a project
# and potentially through a project's 'imports' directory
###################################################################################
# This is the global default 'project registry'
# where symlinks exist to any projects created
# on a system. Unlike OcpiProjectRegistryDir,
# this function does not consider the current
# project's 'imports' link:
# OCPI_PROJECT_REGISTRY_DIR or CDK/../project-registry
OcpiGlobalDefaultProjectRegistryDir=$(strip \
  $(or \
    $(strip $(OCPI_PROJECT_REGISTRY_DIR)),\
    $(if $(strip $(OCPI_CDK_DIR)),\
      $(OCPI_ROOT_DIR)/project-registry,\
      $(error Error: OCPI_CDK_DIR is unset))))

# This is the 'project registry' where symlinks
# exist to any projects created on a system.
# If inside a project, try to use its imports:
# Local 'imports' or OCPI_PROJECT_REGISTRY_DIR or CDK/../project-registry
OcpiProjectRegistryDir=$(strip \
  $(or \
    $(and $(OCPI_PROJECT_DIR),$(call OcpiExists,$(call OcpiImportsDirForContainingProject,$1))),\
    $(OcpiGlobalDefaultProjectRegistryDir)))

# Return the path to the 'imports' directory for the project containing $1
# $(call OcpiImportsDirForContainingProject,.)
OcpiImportsDirForContainingProject=$(strip $(foreach p,$(call OcpiAbsPathToContainingProject,$1),$p/imports))

# Return the list of projects that are imported by the project containing.
# Do no include the current project if it is found in imports.
# $(call OcpiGetProjectImports)
OcpiGetProjectImports=$(strip \
  $(foreach p,$(foreach i,$(if $(filter clean%,$(MAKECMDGOALS)),\
                            $(OcpiProjectRegistryDir),\
                            $(call OcpiImportsDirForContainingProject,.)),\
	        $(wildcard $i/*)),\
    $(if $(filter $(realpath $p),$(realpath $(call OcpiAbsPathToContainingProject,.))),\
      ,\
      $p )))

# Given an 'origin' path ($1) and a path to a 'destination' project $2,
# if the 'destination' project is imported in 'origin's project,
# return the path to that import.
#
# If $2 is just a name (not a path), just check a link with that name is
# imported.
#
# If $2 is not found in imports by name, check if it is actually the CDK,
# in which case use the CDK import alias
#
# If no import with the correct name exists, make one last attempt to find
# the requested import by checking the 'realpath' of each import against $2
# $(call OcpiGetProjectInImports,<origin-path>,<destination-project>)
OcpiGetProjectInImports=$(strip \
  $(foreach i,$(if $(filter clean%,$(MAKECMDGOALS)),\
                $(call OcpiProjectRegistryDir,$1),\
                $(call OcpiImportsDirForContainingProject,$1)),\
    $(or \
      $(if $(filter $2,$(notdir $2)),\
        $(call OcpiExists,$i/$2)),\
      $(foreach a,$(call OcpiExists,$i/$(notdir $2)),\
        $(if $(filter $(realpath $a),$(realpath $2)),$a)),\
      $(foreach a,$(wildcard $i/*),\
        $(if $(filter $(realpath $a),$(realpath $2)),$a)))))

# Given an 'origin' path ($1) and a 'destination' path $2,
# if the 'destination's project is imported in 'origin's project,
# return that import (imports/<destination-project>
# $(call OcpiGetRelevantProjectImport,<origin-path>,<destination-path>)
OcpiGetRelevantProjectImport=$(strip $(infox OGRPI:$1:$2)\
  $(foreach a,$(call OcpiAbsPathToContainingProject,$2),$(infox OGRPIa:$a)\
    $(foreach i,$(call OcpiGetProjectInImports,$1,$a),$(infox OGRPIr:imports/$(notdir $i))\
      imports/$(notdir $i))))

# Given a path, determine the relative path to the project containing it
# $(call OcpiRelPathToContainingProject,<path>)
OcpiRelPathToContainingProject=$(strip $(infox ORPTCP:$1)\
  $(call OcpiCacheFunctionOnPath,OcpiRelPathToContainingProjectX,$(call OcpiAbsPath,$(or $1,.))))
OcpiRelPathToContainingProjectX=$(infox ORPTCPX:$1:$2)$(strip \
  $(if $(filter project,$(call OcpiGetDirType,$1)),\
    $(or $2,.),\
    $(if $(call OcpiExists,$1),\
      $(if $(filter $(dir $1),"/"),\
        $(warning Path $1 is not inside a project.),\
        $(call OcpiRelPathToContainingProjectX,$(call OcpiDir,$1),$(and $2,$2/)..)))))

# Given a path, determine the absolute path to the project containing it
# $(call OcpiAbsPathToContainingProject,<path>)
OcpiAbsPathToContainingProject=$(strip $(infox OAPTCP:$1)\
  $(call OcpiCacheFunctionOnPath,OcpiAbsPathToContainingProjectX,$(call OcpiAbsPath,$(or $1,.))))
OcpiAbsPathToContainingProjectX=$(strip \
  $(if $(wildcard $1/Project.mk $1/Project.xml),\
    $1,\
    $(if $(call OcpiExists,$1),\
      $(if $(filter $(dir $1),"/"),\
        $(warning Path $1 is not inside a project.),\
        $(call OcpiAbsPathToContainingProjectX,$(call OcpiDir,$1))))))

# If two paths are contained in the same project, return the path to the project
# Otherwise return empty
# Note: We need to get the real/abs path to ensure that they are of the same form.
#       This will allow 'filter' to correctly determine if they are the same.
#
# $(call OcpiArePathsInSameProject,<path1>,<path2>)
OcpiArePathsInSameProject=$(strip $(infox OAPISP:$1:$2)\
  $(filter $(realpath $(call OcpiAbsPathToContainingProject,$1)),$(realpath $(call OcpiAbsPathToContainingProject,$2))))

# Given a path, determine the path from the top level of the containing project.
# This path will NOT include the path TO the current project.
# E.g: /data/myproject/hdl/platforms -> hdl/platforms
# $(call OcpiGetPathFromProjectTop,<path>)
OcpiPathFromProjectTop=$(strip $(infox OPFPT:$1)\
  $(patsubst %/,%,$(call OcpiCacheFunctionOnPath,OcpiPathFromProjectTopX,$(call OcpiAbsPath,$1))))
OcpiPathFromProjectTopX=$(strip \
  $(if $(wildcard $1/Project.xml $1/Project.mk),\
    ,\
    $(if $(call OcpiExists,$1),\
      $(if $(filter $(dir $1),$1),\
        $(warning CWD is not inside a project.),\
        $(call OcpiPathFromProjectTopX,$(call OcpiDir,$1))$(notdir $1)/))))

# Given an 'origin' path ($1) and a 'destination' path $2:
# If the 'destination's project is imported in 'origin's project,
#   return the path from $1 to $2 through 'origin's imports.
# Otherwise, just return the absolute path to $2
# $(call OcpiPathToAssetOutsideProject,<origin-path>,<destination-path>)
OcpiPathToAssetOutsideProject=$(strip $(infox OPTAOP:$1:$2)\
  $(or \
    $(strip $(foreach i,$(call OcpiGetRelevantProjectImport,$1,$2),\
      $(call OcpiRelPathToContainingProject,$1)/$i/$(call OcpiPathFromProjectTop,$2))),\
    $(call OcpiAbsPath,$2)))

# Given an 'origin' path ($1) and a 'destination' path $2:
# If the 'destination's project is imported in 'origin's project,
#   return the path from the top level of 'origin's project to $2
#   through 'origin's imports.
# Otherwise, just return the absolute path to $2
# $(call OcpiPathFromProjectTopToAssetOutsideProject,<origin-path>,<destination-path>)
OcpiPathFromProjectTopToAssetOutsideProject=$(strip $(infox OPFPTAOP:$1:$2)\
  $(or \
    $(strip $(foreach i,$(call OcpiGetRelevantProjectImport,$1,$2),\
      $i/$(call OcpiPathFromProjectTop,$2))),\
    $(call OcpiAbsPath,$2)))

# Given an 'origin' path ($1) and a 'destination' path $2:
# If the paths are in the same project,
#   return the path from $1 to $2 through the project top.
# Otherwise,
#   return the path through 'origin's imports or the return absolute path.
# $(call OcpiPathThroughProjectTopOrImports,<origin-path>,<destination-path>)
OcpiPathThroughProjectTopOrImports=$(strip $(infox OPTPTOI:$1:$2)\
  $(and $(call OcpiExists,$2),\
    $(if $(call OcpiArePathsInSameProject,$1,$2),\
      $(call OcpiRelPathToContainingProject,$1)/$(call OcpiPathFromProjectTop,$2),\
      $(call OcpiPathToAssetOutsideProject,$1,$2))))

# Return the paths from $1 through the project top (and possibly imports) to each
# path in $2
# $(call OcpiRelativePathsInsideProjectOrImports,<origin-path>,<destination-paths>)
OcpiRelativePathsInsideProjectOrImports=$(strip $(infox ORPIPOI:$1:$2)\
  $(foreach p,$2,$(call OcpiPathThroughProjectTopOrImports,$1,$p) ))

# Given an 'origin' path ($1) and a 'destination' path $2:
# If the paths are in the same project,
#   return the path to $2 from the project top.
# Otherwise,
#   return the path through 'origin's imports or return the absolute path
# $(call OcpiPathFromProjectTopOrImports,<origin-path>,<destination-path>)
OcpiPathFromProjectTopOrImports=$(strip $(infox OPFPTOI:$1:$2)\
  $(and $(call OcpiExists,$2),\
    $(if $(call OcpiArePathsInSameProject,$1,$2),\
      $(call OcpiPathFromProjectTop,$2),\
      $(call OcpiPathFromProjectTopToAssetOutsideProject,$1,$2))))

# Return the paths from $1's project top (and possibly through imports) to each
# path in $2
# $(call OcpiPathsFromProjectTopOrImports,<origin-path>,<destination-paths>)
OcpiPathsFromProjectTopOrImports=$(strip $(infox ORPIPOI:$1:$2)\
  $(foreach p,$2,$(call OcpiPathFromProjectTopOrImports,$1,$p) ))

###################################################################################

# Add a directory to the front of a path in the environment
# $(call OcpiPrependEnvPath,var-name,dir)
OcpiPrependEnvPath=\
  $(eval tmp:=$(wildcard $2))\
  $(infox PREPEND:$1:$2:$(tmp))\
  $(and $(tmp),$(eval export $1:=$(subst $(Space),:,$(call Unique,$(tmp) $(subst :, ,$($1))))))

############ Project related functions

define OcpiParseProjectPackageID
  # Save the Package, PackagePrefix, and PackageName variables
  # so that they can be used as is later on (if set at the command
  # or in a 'Makefile' file), but so they do not interfere with
  # ProjectPackage results
  PackageSaved:=$$(Package)
  Package:=
  PackagePrefixSaved:=$$(PackagePrefix)
  PackagePrefix:=
  PackageNameSaved:=$$(PackageName)
  PackageName:=
  ComponentLibrariesSaved:=$$(ComponentLibraries)
  ComponentLibraries:=
  ProjectDependenciesSaved:=$$(ProjectDependencies)
  ProjectDependencies:=
  # Include Project.<mk|xml> to determine ProjectPackage
  $$(infox PR0:$1:$$(Package):$$(PackagePrefix):$$(PackageName):$$(ProjectPackage):$$(ParentPackage))
  ifneq ($(wildcard $1/Project.xml),)
    # Handle XML, aka make-less, properties for project assets
    ifneq ($(wildcard $1/Project.mk),)
      $$(warning Found both Project.mk and Project.xml, using Project.xml)
    endif
    # The following would be useful, but fails for bootstrapping
    #(call OcpiParseXml,$1,Project)
    # This just uses bash
    $$(if $$(call DoShell,cd $1 && \
                          source $$(OCPI_CDK_DIR)/scripts/util.sh && \
                          getproject && \
                          echo $$$$packageid,Package),\
          $$(error Failed to get project packageID at $1))
  else
    # Legacy support for project assets
    $(infox $0: Could not find Project.xml, using Project.mk)
    include $1/Project.mk
  endif
  $$(infox PR1:$$(Package):$$(PackagePrefix):$$(PackageName):$$(ProjectPackage):$$(ParentPackage))

  # Determine ProjectPackage as follows:
  # If it is already set, use it as-is
  # If ProjectPackage or Package is set, use that as-is
  # Otherwise, use PackagePrefix.PackageName
  # PackagePrefix defaults to 'local'
  # PackageName defaults to directory name
  # PackageID is the documented, preferred user-specified value.
  # FIXME: All this code could be changed to use PackageID rather than Package someday
  ifndef Package
    ifdef PackageID
      Package:=$$(PackageID)
    else
      ifndef PackagePrefix
        PackagePrefix:=local
      endif
      ifndef PackageName
        PackageName:=$$(notdir $$(call OcpiAbsDir,$1))
      endif
      Package:=$$(if $$(PackagePrefix),$$(patsubst %.,%,$$(PackagePrefix)).)$$(PackageName)
    endif
  endif
  $2:=$$(Package)
  Package:=$$(PackageSaved)
  PackagePrefix:=$$(PackagePrefixSaved)
  PackageName:=$$(PackageNameSaved)
  ComponentLibraries:=$$(ComponentLibrariesSaved)
  ProjectDependencies:=$$(ProjectDependenciesSaved)
endef

# Given a project's directory return its package id
# First try to get it via exports (without creating a subshell process)


OcpiGetProjectPackageIDX=$(shell echo OGPPIX:$1 > /dev/tty)$(strip\
  $(foreach i,\
    $(or $(foreach p,$(wildcard $1/project-package-id:* $1/exports/project-package-id:*),\
           $(patsubst project-package-id:%,%,$(notdir $p))),$(strip\
      $(eval $(call OcpiParseProjectPackageID,$1)))),$(shell echo OGPPIXr:$i>/dev/tty)$i

# Assign the packageID of the given project to the given variable
OcpiGetProjectPackageID=$(strip\
  $(or $(foreach i,$(filter $1:%,$(OcpiProjectPackageIDs)),\
	 $(patsubst $1:%,%,$i)),\
       $(eval $(call OcpiParseProjectPackageID,$1,OcpiTmpGetProjectPackageID))\
       $(eval OcpiProjectPackageIDs+=$1:$(OcpiTmpGetProjectPackageID))\
       $(infox OcpiProjectPackageIDs is now:$(OcpiProjectPackageIDs))\
       $(OcpiTmpGetProjectPackageID)))

# Set the given directory as the project directory, include the Project.mk file that is there
# and setting an environment variable OCPI_PROJECT_DIR to that place.
# This allows any path-related settings to be relative to the project dir
#TODO all the cooments within this define should probably be moved out for perfromance reasons
#     because this function is used by $(call ...)
define OcpiSetProject
  $(infox @@@@@@@@@@@@@@@@:$1:$(OCPI_PROJECT_REL_DIR))
  ifneq ($(OCPI_PROJECT_REL_DIR),${1:./%=%})
    $(call OcpiSetProjectX,$1)
  endif
endef
define OcpiSetProjectX
  # This might already be set
  $$(call OcpiDbg,Setting project directory to $1)
  OcpiTempProjDir:=$$(call OcpiAbsDir,$1)
  ifdef OCPI_PROJECT_DIR
    ifneq ($$(OcpiTempProjDir),$$(OCPI_PROJECT_DIR))
      $$(error OCPI_PROJECT_DIR in environment is $$(OCPI_PROJECT_DIR), but found Project.<mk|xml> in $1)
    endif
  endif
  override OCPI_PROJECT_DIR=$$(OcpiTempProjDir)
  override OCPI_PROJECT_REL_DIR=$(1:./%=%)
  export OCPI_PROJECT_DIR
  export OCPI_PROJECT_REL_DIR

  # Save the Package, PackagePrefix, and PackageName variables
  # so that they can be used as is later on (if set at the command
  # or in a 'Makefile' file), but so they do not interfere with
  # ProjectPackage results
  PackageSaved:=$$(Package)
  Package:=
  PackagePrefixSaved:=$$(PackagePrefix)
  PackagePrefix:=
  PackageNameSaved:=$$(PackageName)
  PackageName:=

  # Include Project.<mk|xml> to determine ProjectPackage
  $$(infox PR0:$$(Package):$$(PackagePrefix):$$(PackageName):$$(ProjectPackage):$$(ParentPackage))
  ifneq ($(wildcard $1/Project.xml),)
    # Handle XML, aka make-less, properties for project assets
    ifneq ($(wildcard $1/Project.mk),)
      $$(warning Found both Project.mk and Project.xml, using Project.xml)
    endif
    $(call OcpiParseXml,$1,Project)
  else
    # Legacy support for project assets
    $$(infox $0: Could not find Project.xml, using Project.mk)
    include $1/Project.mk
  endif
  $$(infox PR1:$$(Package):$$(PackagePrefix):$$(PackageName):$$(ProjectPackage):$$(ParentPackage))

  # Determine ProjectPackage as follows:
  # If it is already set, use it as-is
  # If ProjectPackage or Package is set, use that as-is
  # Otherwise, use PackagePrefix.PackageName
  # PackagePrefix defaults to 'local'
  # PackageName defaults to directory name
  # PackageID is the documented, preferred user-specified value.
  # FIXME: All this code could be changed to use PackageID rather than Package someday
  ifndef ProjectPackage
    ifdef Package
      ProjectPackage:=$$(Package)
    else ifdef PackageID
      ProjectPackage:=$$(PackageID)
    else
      ifndef PackagePrefix
        PackagePrefix:=local
      endif
      ifndef PackageName
        PackageName:=$$(notdir $$(call OcpiAbsDir,$1))
      endif
      ProjectPackage:=$$(if $$(PackagePrefix),$$(patsubst %.,%,$$(PackagePrefix)).)$$(PackageName)
    endif
  endif
  export OCPI_PROJECT_PACKAGE=$$(ProjectPackage)
  override OCPI_PROJECT_DEPENDENCIES=$$(OcpiProjectDependenciesInternal)
  export OCPI_PROJECT_DEPENDENCIES
  export OCPI_PROJECT_COMPONENT_LIBRARIES:=$$(ComponentLibraries)
  $$(infox OCPI_PROJECT_COMPONENT_LIBRARIES=$$(OCPI_PROJECT_COMPONENT_LIBRARIES)=$$(origin OCPI_PROJECT_COMPONENT_LIBRARIES))
  # Restore the Package* variables in case they were set at the command line
  # for a library or in a library 'Makefile'
  Package:=$$(PackageSaved)
  PackagePrefix:=$$(PackagePrefixSaved)
  PackageName:=$$(PackageNameSaved)
  $$(infox PR2:$$(Package):$$(PackagePrefix):$$(PackageName):$$(ProjectPackage):$$(ParentPackage))
  # A project is always added to the below-project/non-project search paths
  # I.e. where the project path looks for other projects, and their exports,
  # the current project is searched internally, not in exports
  # when looking for (non-slash) primitives, look in this project, not exports
  $$(call OcpiPrependEnvPath,OCPI_HDL_PRIMITIVE_PATH,$$(OcpiTempProjDir)/hdl/primitives/lib)
  # when looking for XML specs and protocols, look in this project
  $$(call OcpiPrependEnvPath,OCPI_XML_INCLUDE_PATH,$$(OcpiTempProjDir)/specs)
  # when looking for component libraries, look in this project, without depending on
  # exports, and also include the hdl/devices library
  # 1. specifically add each library in the project to "componentlibraries"
  # 2. add each place in the project where libraries live to the component library search path.
  # $$(foreach l,$$(wildcard $$(OcpiTempProjDir)/hdl/devices) \
  #   $$(if $$(filter libraries,$$(call OcpiGetDirType,$$(OcpiTempProjDir)/components)),\
  #     $$(foreach m,$$(wildcard $$(OcpiTempProjDir)/components/*/Makefile),$$(infox MMM:$$m)\
  #        $$(foreach d,$$(m:%/Makefile=%),$$(infox DDD:$$d)\
  #           $$(and $$(filter library,$$(call OcpiGetDirType,$$d)),$$d))),\
  #     $$(OcpiTempProjDir)/components),\
  #   $$(eval override ComponentLibrariesInternal:=$$(call Unique,$(ComponentLibrariesInternal) $$(notdir $$l))) \
  #   $$(call OcpiPrependEnvPath,OCPI_COMPONENT_LIBRARY_PATH,$$(patsubst %/,%,$$(dir $$l))))
endef
ifdef NEVER
  # when executing applications, look in this project
  ifndef OCPI_PROJECT_ADDED_TARGET_DIRS
    $$(warning Adding all target directories in the project to OCPI_LIBRARY_PATH)
    $$(call OcpiPrependEnvPath,OCPI_LIBRARY_PATH,\
       $$(OcpiTempProjDir)/components/lib/rcc \
       $$(OcpiTempProjDir)/components/*.test/assemblies/*/container*/target-* \
       $$(OcpiTempProjDir)/components/*/lib/rcc \
       $$(OcpiTempProjDir)/components/*/*.test/assemblies/*/container*/target-* \
       $$(OcpiTempProjDir)/hdl/assemblies/*/container*/target-*)
    $$(warning Adding all target directories in the project to OCPI_LIBRARY_PATH)
    export OCPI_PROJECT_ADDED_TARGET_DIRS:=1
  endif
endif
# Look into a directory in $1 and determine which type of directory it is
# Return null if there is no type to be found
OcpiGetDirType=$(strip\
  $(foreach t,$(call OcpiCacheFunctionOnPath,OcpiGetDirTypeX,$1),$(infox GDTr:$1:$t)$t))
OcpiGetDirTypeX=$(strip $(infox GDT1:$1)\
  $(foreach t,$(call OcpiCallPythonUtil,print(ocpiutil.get_dirtype("$1"))),\
     $(infox GDT1: found type: $t for $1)$t))

# Get the directory type of arg1, and return the portion after the last dash.
# E.g. in an hdl-platform directory, this will return platform
OcpiGetShortenedDirType=$(infox OGSDT:$1)$(strip \
  $(foreach t,$(call OcpiGetDirType,$1),\
    $(if $(filter hdl-lib% hdl-core,$t),primitive,$(lastword $(subst -, ,$t)))))

###############################################################################
# Functions for including an asset and its parents
###############################################################################

# Recursive
OcpiIncludeProjectX=$(infox OIPX:$1:$2:$3)\
  $(if $(wildcard $1/Project.mk)$(wildcard $1/Project.xml),\
    $(eval $(call OcpiSetProject,$1))\
    $(infox PROJECT:$(OCPI_PROJECT_PACKAGE):$(PackagePrefix):$(ProjectPackage)=$(Package)),\
    $(if $(foreach r,$(realpath $1/..),$(filter-out /,$r)),\
      $(call OcpiIncludeProjectX,$(and $(filter-out .,$1),$1/)..,$2,$3),\
      $(call $2,$2: no Project.<mk|xml> was found here ($3) or in any parent directory)))

# One arg is what to do if not found: error, warning, nothing
OcpiIncludeProject=$(infox OIP:$1:$2:$(MAKECMDGOALS):$(OCPI_PROJECT_PACKAGE):$(OCPI_PROJECT_REL_DIR))\
  $(if $(or $(filter clean%,$(MAKECMDGOALS)),$(OCPI_PROJECT_PACKAGE)),$(infox OIPSKIPPED),\
    $(call OcpiIncludeProjectX,$(or $(OCPI_PROJECT_REL_DIR),.),$1,$(call OcpiAbsDir,.)))\
  $(eval ComponentLibraries+=$(OCPI_PROJECT_COMPONENT_LIBRARIES))

# OcpiIncludeParentAsset_<asset-type> defines how to include an asset's parent.
# This is done on a per-asset-type basis (e.g. platform, platforms, library ...).
# If an asset-type does not define an OcpiIncludeParentAsset_<asset-type> function,
# it is assumed that the project itself is the parent.
#
# For OcpiIncludeParentAsset_* functions, arguments are as follows:
#   Arg1 = reference directory
#   Arg2 = authoring model prefix (optional) - <parent>.<auth>.<package-name>
#   Arg3 = error/warning/info mode

# So, for library, first check if this is a platform's devices library.
# If so, include the parent (../) with type Platform so it can
# find Platform.mk if it exists. Otherwise, the parent is just the project
OcpiIncludeParentAsset_library=\
  $(if $(filter devices cards,$(notdir $(realpath $1))),\
    $(eval ComponentLibraries+=devices))\
  $(if $(filter %-platform application,$(call OcpiGetDirType,$(and $1,$1/)..)),\
    $(call OcpiIncludeAssetAndParentX,$(and $(filter-out .,$1),$1/)..,$2,$3),\
    $(call OcpiIncludeProject,$3,lib))

# For a platform directory, we include the platforms directory in ../
# We provide it with type Platforms so it can find the Platforms.mk
# file if it exists. If the platform is not inside a platforms directory,
# then it is not in a project at all and does not have a parent.
OcpiIncludeParentAsset_platform=\
  $(if $(filter %-platforms,$(call OcpiGetDirType,$(and $(filter-out .,$1),$1/)..)),\
    $(call OcpiIncludeAssetAndParentX,$(and $(filter-out .,$1),$1/)..,$2,$3))

# For a primitive directory, we include the primitives directory in ../
# We provide it with type Platforms so it can find the Platforms.mk
# file if it exists. If the primitive is not inside a primitives directory,
# then it is not in a project at all and does not have a parent.
 OcpiIncludeParentAsset_primitive=\
   $(call OcpiIncludeAssetAndParentX,$(and $(filter-out .,$1),$1/)..,$(Model),$3)

 OcpiIncludeParentAsset_primitives=$(infox PRIMITIVES:$(Model))\
   $(call OcpiIncludeAssetAndParentX,$(and $(filter-out .,$1),$1/)../..,,$3)

 OcpiIncludeParentAsset_worker=$(infox WORKER:$(Model))\
   $(call OcpiIncludeAssetAndParentX,$(and $(filter-out .,$1),$1/)..,,$3)

 OcpiIncludeParentAsset_hdl=\
   $(call OcpiIncludeAssetAndParentX,$(and $(filter-out .,$1),$1/)..,$2,$3)

 OcpiIncludeParentAsset_application=$(infox PRIMITIVES:$(Model))\
   $(call OcpiIncludeAssetAndParentX,$(and $(filter-out .,$1),$1/)../..,,$3)

# For asset in directory arg1, look for makefile <arg2>.mk and include it to
# extract any variables that are set.  Clear the package variables so that the
# current asset's environment is not polluted with package variables from a
# parent assets settings
#   Arg1 = reference directory
#   Arg2 = shortened directory type with capitalized first letter
#            this is the word used to find the .mk  file
#            e.g. Library, Platform, Platforms, Worker
define OcpiSetAsset
  OcpiAssetName:=$$(notdir $$(realpath $1))
  $$(infox SETASSET:$1:$2:$$(OcpiAssetName):$$(CURDIR):$$(wildcard $1/$$(OcpiAssetName).xml))
  Package:=
  PackageID:=
  PackagePrefix:=
  PackageName:=
  # Library can be Library.mk for backward compatibility
  ifeq ($2,Library)
    ifneq ($$(wildcard $1/$$(OcpiAssetName).xml),)
      ifneq ($$(wildcard $1/$2.mk),)
         $$(error In $1, both $2.mk and $$(OcpiAssetName).xml exist, which is not supported.)
      endif
      $$(eval $$(call OcpiParseXml,$1,$$(OcpiAssetName)))
    else ifneq ($$(wildcard $1/$2.mk),)
      include $1/$2.mk
    endif
  # Project (actually handled in OcpiSetProject)
  else ifeq ($2,Project)
    $$(if $$(OCPI_PROJECT_PACKAGE),,$$(error internal error: OCPI_PROJECT_PACKAGE not set))
    Package:=$$(OCPI_PROJECT_PACKAGE)
    $$(infox Not including Project.mk twice)
  # Worker is handled specially inParamShell
  else ifeq ($2,Worker)
    $$(infox Not including worker XML directly for make variables)
  else ifeq ($2,Platform)
    $$(infox Not including platform worker XML directly for make variables)
  else ifeq ($2,Test)
    $$(eval $$(call OcpiParseXml,$1,$$(subst .,-,$$(OcpiAssetName))))
  else ifneq ($(filter-out Platforms Primitive Primitives Applications Application,$2),)
    $$(error Unexpected asset type: $2)
  else ifeq ($2,Application)
    ifneq ($$(wildcard $1/$$(OcpiAssetName).xml),)
      $$(eval $$(call OcpiParseXml,$1,$$(OcpiAssetName)))
    endif
  else ifeq ($2,Primitives)
    # We are overloading the Libraries and Cores variables.
    # At the primitives level they are specifying which things should be built or cleaned
    # and *not* dependencies of the underlying libs and cores
    # So we make sure they do *not* propagate into the lower level assets

    # Capture what was in the Makefile (if there is one), at whatever level we are at
    # Then erase/undefine them
    TmpLibraries:=$$(call Unique,$$(strip $$(Libraries) $$(HdlLibraries)))
    TmpCores:=$$(Cores)
    undefine Libraries
    undefine Cores
    undefine HdlLibraries
    # Next parse the XML file if present, again at whatever level we are at
    ifneq ($$(wildcard $1/$$(OcpiAssetName).xml),)
      $$(eval $$(call OcpiParseXml,$1,$$(OcpiAssetName)))
    endif
    # Any variable settings here are from the XML file
    ifeq ($1,.)
      # This is the actual primitives directory so merge them all
      Libraries:=$$(call Unique,$$(TmpLibraries) $$(Libraries) $$(HdlLibraries))
      ifndef Libraries
        undefine Libraries
      endif
      Cores:=$$(call Unique,$$(TmpCores) $$(Cores))
      ifndef Cores
        undefine Cores
      endif
    else
      # This is not the actual primitives directory so just restore the ones from any Makefile
      ifdef TmpLibraries
        Libraries:=$$(TmpLibraries)
      else
        undefine Libraries
      endif
      ifdef TmpCores
        Cores:=$$(Cores)
      else
        undefine Cores
      endif
    endif
    undefine HdlLibraries
  else ifneq ($$(wildcard $1/$$(OcpiAssetName).xml),)
    # Platforms, Primitive, Applications
    $$(eval $$(call OcpiParseXml,$1,$$(OcpiAssetName)))
  else
    $$(infox MAKEFILE:$1:$2:$$(HdlLibraries):$$(Libraries))
  endif
  $$(infox SETASSETEND:$1:$2:$$(HdlLibraries):$$(Libraries))
endef

# First determine the shortened directory type which is the portion
# of dirtype after the last '-' (e.g. hdl-platforms -> platforms).
#   Store this value in s
# Next, save a version of this shortened dirtype with the first letter
# capitalized so that the *.mk file can be found (e.g. Library.mk)
#   Store this in c
# Note: the two outer loops will only ever have one iteration. They
#       are essentially just saying:
#         s = shortened_dir_type(<arg1>)
#         c = capitalize_first_letter(s)
#
# If the current asset's parent defines an OcpiIncludeParentAsset_<asset-type>
# function, call that to include the parent. Otherwise parent is the project,
# so include the project. Next, include the current asset by importing its
# *.mk file and determining its package via OcpiSetAndGetPackageId
#   Arg1 = reference directory (optional) - defaults to '.' in subcalls
#   Arg2 = authoring model prefix (optional) - <parent>.<auth>.<package-name>
#   Arg3 = error/warning/info mode (optional)
OcpiIncludeAssetAndParentX=$(infox OIAAPX:$1:$2:$3:$(realpath $1))$(strip \
  $(foreach t,$(call OcpiGetDirType,$1),\
    $(foreach s,$(if $(filter hdl-lib% hdl-core,$t),primitive,$(lastword $(subst -, ,$t))),\
      $(foreach c,$(call Capitalize,$s),$(infox OIAAPXi:$t:$s:$c:$(ParentPackage))\
        $(if $(filter-out undefined,$(origin OcpiIncludeParentAsset_$s)),\
          $(call OcpiIncludeParentAsset_$s,$1,$2,$3)\
          $(eval ParentPackage:=$(Package)),\
          $(call OcpiIncludeProject,$3,asset))\
        $(eval $(call OcpiSetAsset,$1,$c))\
        $(call OcpiSetAndGetPackageId,$1,$2,$t)\
        $(infox PARENT:$(origin ParentPackage):$(ParentPackage))))))

# Wrapper function for OcpiIncludeAssetAndParentX. package.mk is included here
# so that it is not included many times during recursive calls of the *X
# function above. This function assumes Arg1 should be the current directory if
# none is provided. Finally, it determines the shortened and capitalized
# directory type to be used for finding *.mk files.
#   Arg1 = reference directory (optional) - defaults to '.' in subcalls
#   Arg2 = authoring model prefix for package-ID (optional) - <parent>.<auth>.<package-name>
#   Arg3 = error/warning/info mode (optional)
OcpiIncludeAssetAndParent=\
  $(if $(filter clean%,$(MAKECMDGOALS)),\
    $(- here is when we are cleaning - just look for cleanfiles attribute by itself)\
    $(foreach d,$(or $1,.),\
      $(foreach x,$(wildcard $d/$(CwdName).xml $d/$(CwdName).*.xml $d/$(CwdName)-test.xml $d/$(CwdName)-app.xml),\
	$(infox FOUND XML:$x)\
        $(eval CleanFiles:=$(shell $(ToolsDir)/ocpixml -a '?cleanfiles' parse $x))\
	$(infox FOUND CLEANFILES:$(CleanFiles)))),\
    $(- here is when we are not cleaning)\
    $(eval ParentPackage:=)\
    $(eval Package:=)\
    $(eval PackageID:=)\
    $(eval include $(OCPI_CDK_DIR)/include/package.mk)\
    $(call OcpiIncludeAssetAndParentX,$(or $1,.),$2,$3))


###############################################################################

# Find the subdirectories that make a Makefile that includes something
OcpiFindSubdirs=$(foreach a,$(wildcard *),$(and $(filter $1,$(call OcpiGetDirType,$a)),$a))

OcpiHavePrereq=$(realpath $(OCPI_PREREQUISITES_DIR)/$1)
OcpiPrereqDir=$(call OcpiHavePrereq,$1)
OcpiCheckPrereq=$(strip\
   $(if $(realpath $(OCPI_PREREQUISITES_DIR)/$1),,\
      $(error The $1 prerequisite package is not installed)) \
   $(and $2,$(foreach t,$2,$(if $(realpath $(OCPI_PREREQUISITES_DIR)/$1/$t,, \
               $(error The $1 prerequisite package is not build for target $t)))\
            $(and $3,$(if $(realpath $(OCPI_PREREQUISITES_DIR)/$1/$t/$3),,\
                         $(error For the $1 prerequisite package, $t/$3 is missing))))))

define OcpiEnsureToolPlatform
  ifndef OCPI_TOOL_OS
    GETPLATFORM=$$(OCPI_CDK_DIR)/scripts/getPlatform.sh
    vars:=$$(shell $$(OcpiExportVars) $$(GETPLATFORM))
    ifneq ($$(words $$(vars)),6)
      $$(error $$(OcpiThisFile): Could not determine the platform after running $$(GETPLATFORM)).
    endif
    export OCPI_TOOL_OS:=$$(word 1,$$(vars))
    export OCPI_TOOL_OS_VERSION:=$$(word 2,$$(vars))
    export OCPI_TOOL_ARCH:=$$(word 3,$$(vars))
    export OCPI_TOOL_PLATFORM:=$$(word 5,$$(vars))
    export OCPI_TOOL_PLATFORM_DIR:=$$(word 6,$$(vars))
    export OCPI_TOOL_DIR:=$$(OCPI_TOOL_PLATFORM)
  endif
endef
# First arg is a list of exported variables/patterns that must be present.
# Second arg is a list of exported variables/patterns that may be present.
# This arg is the command to execute
OcpiShellWithEnv=$(shell $(foreach e,$1,\
                           $(if $(filter $e,$(.VARIABLES)),\
                             $(foreach v,$(filter $e,$(.VARIABLES)),$v=$($v)),\
                             $(error for OcpiShellWithEnv, variable $v not set))) \
                          $(foreach e,$2,\
                            $(foreach v,$(filter $e,$(.VARIABLES)),$v=$($v))) \
                         $3)

$(call OcpiDbg,End of util.mk)

# Set up the standard set of places to look for xml files.
# Here we add access to:
# 0. The current directory
# 1. The generated directory
# 2. What is locally set in the worker's Makefile (perhaps to override specs/protocols)
# 3. What was passed from the library Makefile above (perhaps to override specs/protocols)
# 4. The library's export directory to find other (slave or emulated) workers
# 5. The library's specs directory
# 6. Any other component library's XML dirs
# 6. The standard component library for specs
# 7. The standard component library's exports for proxy slaves
define OcpiSetXmlIncludes
$(eval override XmlIncludeDirsInternal:=\
  $(call Unique,\
    . $(GeneratedDir) \
    $(XmlIncludeDirs) \
    $(XmlIncludeDirsInternal) \
    $(comment this is unreliable: Models:%=../lib/%) ../lib\
    ../specs \
    $(comment we are out of the component library so look in projects, including ours) \
    $(comment we let c++ add the Xml ComponentLibraries)))
endef

# Used wherever test goals are processed.  runtests is for compatibility
# These are goals that *only* apply to testing.
# .test directories also support more generic targets, in particular "clean" and "cleanrun"
OcpiTestGoals=test cleantest runtest verifytest cleansim runtests runonlytest cleanrun
# Used globally when building executables
OcpiPrereqLibs=lzma gmp gpsd

OcpiBuildFile=$(or $(call OcpiExists,$(Worker).build),$(call OcpiExists,$(Worker)-build.xml))

# Something to insert into $(shell) as first argument
OcpiExportVars=$(foreach v,$(filter OCPI_%,$(.VARIABLES)),export $v='$($v)';)

# Easy help message in Makefiles:
# Typical usage:
# define help
# this is the help message with variables like $(something)
# endef
# $(OcpiHelp)
OcpiHelp=help:;@:$(and $(filter help,$(MAKECMDGOALS)),$(info $(help)))

OcpiDirName=$(patsubst %/,%,$(dir $1))
# Prepare an artifact in the project.
# First, add the artifact xml (from the file in $2) to the binary file ($1) IN PLACE.
#  Next, if we are in a project, ensure there is a symlink in the artifacts/ directory at the
#  project's top level.
#  We actually use two symlinks in the artifacts/ directory per artifact, for several reasons.
#  The first link is a functional (not dead) link to the artifact that is a relative link within
#    the project.  The name of this link is <uuid>:<basename-of-artifact>.
#    The name is of bounded length, which is required by some tools, notably modelsim.
#    The uuid ensures uniqueness even when artifacts from different projects are ultimately
#    combined into one directory - i.e. it allows for that.
#    Example: 06bcdc80-4803-11e8-97d5-a7ad40a16f1f:bias_0_modelsim_base.tar.gz
#  The second link is a dead link (the target does not point to a real file).  Its name is:
#    <project-relative-pathname-with-slashes-and-periods-replaced-with-hypens>
#    Its target is <uuid>, which does not exist as a file.
#    This link does not have bounded length (since it is a fully navigable name with multiple
#    directory levels etc.
#    If serves several purposes:
#      - It annotates the first uuid-based functional links by showing the relative pathname
#        that they in fact point it.  "ls -l" allows you to know where the first links point.
#      - It serves as a placeholder to show that a symlink already exists to the pathname,
#        and thus does not need to be created or modified - without reading the link.
#      - It is a dead link so that an unbounded pathname is never used as an artifact that will
#        break some tools.
#      - It is a dead so that the artifact searching machinery efficiently avoids it
#  Note that the first time these links are created, the UUID used for the links comes from
#  the artifact, but later, when the links are reused, the UUID in the links is not changed
#  because there is no value in changing it.
# $(call OcpiPrepareArtifact,
#    <artifact-file-input>,<output-file-to-modify>,<packageparent>,<config>,<platform>)
# old name based on xml uuid not used anymore since we rely on package ids
#    $(comment uuid=`sed -n '/artifact uuid/s/^.*artifact uuid="\([^"]*\)".*$$/\1/p' $1` &&)
OcpiPrepareArtifact=$(infox PREPARE:$1:$2:$3:$4:$5=$(OCPI_PROJECT_DIR))\
  $(ToolsDir)/ocpixml add $2 $1 \
  $(and $(OCPI_PROJECT_DIR), &&\
    adir=$(OCPI_PROJECT_DIR)/artifacts &&\
    uuid=$3.$(Worker).$(Model).$4.$5 &&\
    mkdir -p $(OCPI_PROJECT_DIR)/artifacts &&\
    $(call MakeSymLink2,$2,$(OCPI_PROJECT_DIR)/artifacts,$${uuid}$(suffix $2)) \
   )

# What to do early in each top level Makefile to process build files.
# Process the build file one of two ways:
# 1. If there is a build file, process it.
# 2. If there is no build file, create one in gen/, based on what is found in the Makefile
#    which uses MakeRawParams to feed the parameter in the Makefile into ocpigen -r
# Either option generates gen/<wkr>.mk
# Note:  RCC worker directories that build multiple workers in a common source file
# are not supported to have non-default build parameters, nor any parameter values
# specified in the Makefile itself.
ParamShell=\
  if [ -n "$(OcpiBuildFile)" -a -r "$(OcpiBuildFile)" ] ; then \
    (mkdir -p $(GeneratedDir) &&\
    $(call MakeSymLink2,$(OcpiBuildFile),$(GeneratedDir),$(Worker)-build.xml); \
    $(call OcpiGenTool, -D $(GeneratedDir) $(and $(Package),-p $(Package))\
      $(and $(Platform),-P $(Platform)) \
      $(and $(PlatformDir), -F $(PlatformDir)) \
      $(HdlVhdlLibraries) \
      $(and $(Assembly),-S $(Assembly)) \
      -b $(Worker_$(Worker)_xml))) || echo 1;\
  else \
    mkdir -p $(GeneratedDir);\
    $(foreach w,$(Workers),\
      $(MakeRawParams) |\
      $(call OcpiGenTool, -D $(GeneratedDir) $(and $(Package),-p $(Package))\
        $(and $(Platform),-P $(Platform)) \
        $(and $(PlatformDir), -F $(PlatformDir)) \
        $(HdlVhdlLibraries) \
        $(and $(Assembly),-S $(Assembly)) \
        -r $(Worker_$w_xml) || (echo 1 && exit 1));)\
  fi

# Create the internal, transient XML document to convey property values in the Makefile
# to the tool which will generate a build file, and an internal Makefile which will
# then be included
# 1. The core syntax is from our textual encoding of data types.
# 2. "Make" pretty much allows anything but # and newline in an assignment - both can
#    be escaped using backslash, so in fact there are three special characters
#    #, \, and <newline>, but newlines will never be included.
# 3. When we output the file as XML, we need to deal with XML quoting conventions.
#    But XML textual data has only two things to protect: < and &.
#    But our format also has backslash encoding too.
# 4. The Values string has slashes to separate values
# 5. We need a shell command to produce the output.
#    Metacharacters for the shell are: | & ; ( ) < > space tab
#    Backslash protects everything
#    Single quotes can't protect single quotes
#    Double quotes don't protect $ ` \ !
# Since XML already has a mechanism to encode single quotes (&apos;), using single quotes is best.
MakeRawParams= \
  (echo "<parameters>"; \
   $(foreach i,$(RawParamVariables),\
     echo "<parameter name='$(call RawParamName,$i)'$(strip \
                      )$(if $(filter ParamValues_%,$i), values='true')>";\
     echo '$(subst <,&lt;,$(subst ',&apos;,$(subst &,&amp;,$($i))))';\
     echo "</parameter>";) \
   echo "</parameters>")

# A single quote ' to balance the one above when some editors/colorizers get confused.

# This must be done early to allow the make file fragment that is generated from the -build.xml
# file to be processed as if it was a user-written Makefile, before most other processing
define OcpiProcessBuildFiles

ifeq ($(filter clean,$(MAKECMDGOALS)),)

# PreProcess any parameters defined in the Makefile itself, for use by MakeRawParams
RawParamVariables:=$$(filter Param_%,$$(.VARIABLES)) $$(filter ParamValues_%,$$(.VARIABLES))
RawParamName=$$(if $$(filter Param_%,$$1),$$(1:Param_%=%),$$(1:ParamValues_%=%))
RawParamNames:=$$(foreach v,$$(RawParamVariables),$$(call RawParamName,$$v))
ifneq ($$(words $$(RawParamNames)),$$(words $$(sort $$(RawParamNames))))
  $$(error Both Param_ and ParamValues_ used for same parameter.)
endif

# These are included to know the universe of possible platforms, which is required when
# the build files are processed
# FIXME: make this generated by the list of known models
include $(OCPI_CDK_DIR)/include/hdl/hdl-targets.mk
include $(OCPI_CDK_DIR)/include/rcc/rcc-targets.mk

# This is called here since some xml include dirs may be set in the original Makefile
# But if some are set in the build file, they will be processed internally in ocpigen
# when it is parsed before reading the OWD
$$(call OcpiDbgVar,XmlIncludeDirsInternal)
$$(call OcpiSetXmlIncludes)
$$(call OcpiDbgVar,XmlIncludeDirsInternal)

# Process the build file using ParamShell one of two ways:
# 1. If there is a build file, process it.
# 2. If there is no build file, create one in gen/, based on what is found in the Makefile
#    which uses MakeRawParams to feed the parameter in the Makefile into ocpigen -r
# In both cases, a gen/<wkr>.mk file is created and then included

$$(call OcpiDbgVar,ParamShell)
X:=$$(shell $$(ParamShell))
$$(and $$X,$$(error Failed to process initial parameters for this worker: $$X))
$$(foreach w,$$(Workers),$$(eval include $$(GeneratedDir)/$$w.mk))
WorkerParamNames:=\
    $$(foreach w,$$(Workers),\
        $$(foreach p,$$(filter ParamMsg_$$(firstword $$(ParamConfigurations))_$$(WorkerName_$$w)_%,$$(.VARIABLES)),\
          $$(p:ParamMsg_$$(firstword $$(ParamConfigurations))_$$(WorkerName_$$w)_%=$$(WorkerName_$$w)_%)))
$$(call OcpiDbgVar,WorkerParamNames)
$$(call OcpiDbgVar,ParamConfigurations)

endif # if not cleaning

endef # OcpiProcessBuildFiles

# This function reads the RCC platform's target definition file <platform>.mk, against the defaults,
# and assigns the platform-specific variables
define OcpiSetPlatformVariables
  ifndef OcpiPlatformDir_$1 # avoid all the work if its already done
    # reset default variables for the platform.
    include $(OCPI_CDK_DIR)/include/platform-defaults.mk
    OcpiPlatformDir_$1:=$$(or $$(call OcpiGetRccPlatformDir,$1),\
                          $$(error Unknown RCC/Software platform: $1))
    OcpiPlatformFile_$1:=$$(wildcard $$(OcpiPlatformDir_$1)/$1.mk)
    ifeq ($$(wildcard $$(OcpiPlatformFile_$1)),)
      $$(error The RCC/Software Platform file $$(OcpiPlatformFile_$1) is missing.)
    endif
    OcpiPlatformDir:=$$(OcpiPlatformDir_$1)
    OcpiPlatformFile:=$$(OcpiPlatformFile_$1)
    OcpiPlatformPrevars:=$$(.VARIABLES)
    include $$(OcpiPlatformFile_$1)
    AllowedVars=OcpiAltera% OcpiXilinx% OCPI_ALTERA_VERSION OCPI_XILINX_VIVADO_SDK_VERSION
    $$(foreach v,$$(filter-out $$(AllowedVars),$$(filter Ocpi% OCPI%,$$(.VARIABLES))),\
       $$(if $$(strip $$(filter $$v,OcpiPlatformPrevars $$(OcpiPlatformPrevars))\
		      $$(filter $$v,$$(OcpiAllPlatformVars))),,\
          $$(warning Software platform file $$(OcpiPlatformDir)/$1.mk has $$(strip\
                   illegal variable: $$v))))
    $$(foreach v,$$(OcpiAllPlatformVars),\
      $$(eval $$v_$1:=$$($$v)))
  endif
endef

################################################################################
# Definitions for preprocessing source files that are not C or C++ files
# with the suffix cpp_<foo> where <foo> is the ultimate suffix.
# These functions were previously specific to workers, but are collected here
# so that they may also be used in primitive libraries etc.
# Since the result can be specific to parameters, they must go in the target directory
# rather than the "gen" directory.
# FIXME:  Workers use redundant functions in xxx-worker.mk

# $(call OcpiCPPGenFile,<file>,<target>,<config>)
OcpiCPPGenFile=$(call WkrTargetDir,$2,$3)/$(basename $(notdir $1))$(patsubst .cpp_%,.%,$(suffix $1))
# $(call OcpiCPPSource,<file>,<target>,<config>,<goal-binary>)
define OcpiCPPSource
  TargetSourceFiles_$3+=$$(call OcpiCPPGenFile,$1,$2,$3)
  $4: $$(call OcpiCPPGenFile,$1,$2,$3)
  $$(call OcpiCPPGenFile,$1,$2,$3): $1 | $(call WkrTargetDir,$2,$3)
	$(AT)gcc -MMD -MP -MT $$@ -MF $$@.deps -E -P -std=c99 -xc \
	       $$(foreach d,$$(OcpiCPPDefines), '-D$$d') \
               $$(foreach n,$$(WorkerParamNames), '-DOCPI_PARAM_$$n()=$$(Param_$3_$$n)') $$< | \
               tr '$$$$@`' "\n '" | sed '/^ *$$$$/d' > $$@
endef
# Return CPP sources from list in $1
OcpiCPPSources=$(strip $(foreach f,$1,$(and $(filter .cpp_%,$(suffix $f)),$f)))

OcpiSpecLinks=mkdir -p $2;$(foreach f,$(wildcard $1/specs/*.xml),$(call MakeSymLink,$f,$2);)

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

# Deal with source vs. exported directories.
# <projdir>/hdl/platforms/<plat> (not exported at all)
# <projdir>/hdl/platforms/<plat>/lib (exported locally)
# <projdir>/exports/hdl/platform/<plat> (exported by project)
# Arg 1 is platform dir, Arg 2 is model (lower case)
OcpiProjectFromPlatformDir=$(infox OPFPD:$1:$2)$(strip\
  $(or $(strip \
    $(foreach r,$(realpath $1),$(infox R:$r)\
      $(foreach path,$(if $(filter lib,$(notdir $r)),$(patsubst %/,%,$(dir $r)),$r),\
        $(foreach proj,$(patsubst %/$2/platforms/$(notdir $(path)),%,$(path)),\
          $(infox OPFPDr:$(proj))$(proj))))),\
    $(error Platform directory $1 does not exist)))

endif # ifndef __UTIL_MK__
