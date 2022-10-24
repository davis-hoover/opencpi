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

# The makefile fragment for component libraries

# A component library, consisting of different workers built for different targets.
# The library might have a <libname>.xml file for library-level attributes.
# Components are defined by a spec file in the specs subdir or a *.comp
# dir containing the spec file, or both (where the spec file is *not* in the *.comp dir).
# The Workers, ExcludeWorkers, Tests, ExcludeTests variables
# (and XML attributes) can control which workers, tests, and components are built.
# The name of an implementation subdirectory includes its authoring model as the
# file extension.
$(if $(wildcard $(OCPI_CDK_DIR)),,$(error OCPI_CDK_DIR environment variable not set properly.))

include $(OCPI_CDK_DIR)/include/util.mk
# Include library settings for this library, which are available here and for workers
# Thus library settings can depend on project settings
ifeq ($(filter speclinks workersfile clean%,$(MAKECMDGOALS)),)
$(OcpiIncludeAssetAndParent)
endif
ifneq ($(origin Workers),undefined)
  ifneq ($(origin Implementations),undefined)
    $(error You cannot set both Workers and Implementations variables.)
  else
    Implementations := $(Workers)
  endif
endif
unexport Workers
ifeq ($(origin Implementations),undefined)
Implementations=$(filter-out $(ExcludeWorkers),$(foreach m,$(Models),$(wildcard *.$m)))
endif
# This will only make sense when *.comp dirs can contain -test.xml etc.
ifeq ($(origin Components),undefined)
  Components:=$(filter-out $(ExcludeComponents),$(wildcard *.comp))
endif
CompImplementations=$(Components)

ifeq ($(filter clean%,$(MAKECMDGOALS)),)
$(shell mkdir -p lib; \
        workers_content="$(filter-out %.test, $(Implementations))"; \
        if [[ ! -e $(LibDir)/workers || "$$workers_content" != "$$(cat lib/workers)" ]]; then \
          echo $$workers_content > lib/workers; \
        fi)
endif

speclinks:
	$(AT)$(call OcpiSpecLinks,.,$(OutDir)lib)

ifneq ($(filter speclinks workersfile,$(MAKECMDGOALS)),)
# We define this empty make rule so that workers can generate the "workers" file
# by calling "make workersfile -C ../". Doing so will trigger the code block above
# which is executed for all make rules except clean%
workersfile:
	$(AT): # nothing - just suppress message
else
HdlInstallDir=lib
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
$(eval $(HdlPreprocessTargets))
$(infox HP2:$(HdlPlatform) HPs:$(HdlPlatforms) HT:$(HdlTarget) HTs:$(HdlTargets):$(CURDIR))
include $(OCPI_CDK_DIR)/include/rcc/rcc-make.mk
ifeq ($(OCPI_HAVE_OPENCL),1)
  include $(OCPI_CDK_DIR)/include/ocl/ocl-make.mk
endif
ifndef LibName
LibName=$(CwdName)
endif
# we need to factor the model-specifics our of here...
XmImplementations=$(filter %.xm,$(Implementations))
RccImplementations=$(filter %.rcc,$(Implementations))
HdlImplementations=$(filter %.hdl,$(Implementations))
ifeq ($(OCPI_HAVE_OPENCL),1)
OclImplementations=$(filter %.ocl,$(Implementations))
endif
TestImplementations=$(filter %.test,$(Implementations))
AssyImplementations=$(filter %.assy,$(Implementations))

# if no tests are in the explicit workers list...
# must eval here hence ifeq
ifeq ($(TestImplementations),)
  ifeq ($(origin Tests),undefined)
    TestImplementations:=$(filter-out $(ExcludeTests),$(patsubst %/,%,$(dir $(wildcard *.test/*-test.xml))))
  else
    TestImplementations:=$(filter-out $(ExcludeTests),$(Tests))
  endif
endif
override LibDir=$(OutDir)lib
override GenDir=$(OutDir)gen
# In case this library is a subdirectory that might receive XmlIncludeDirs from the
# parent (e.g. when a platform directory has a "devices" library as a subdirectory
override XmlIncludeDirs+=$(XmlIncludeDirsInternal)

# Utility to show what WOULD be built (e.g. for packaging)
.PHONY:  showxm showrcc showhdl showocl showtest showassy showall workersfile
.SILENT: showxm showrcc showhdl showocl showtest showassy showall workersfile
showxm:
	echo $(XmImplementations)

showrcc:
	echo $(RccImplementations)

showhdl:
	echo $(HdlImplementations)

showocl:
	echo $(OclImplementations)

showtest:
	echo $(TestImplementations)

showassy:
	echo $(AssyImplementations)

# Do NOT sort these or proxies may be out-of-order:
showall:
	echo $(XmImplementations) $(RccImplementations) $(HdlImplementations) $(OclImplementations) $(TestImplementations) $(AssyImplementations)

# default is what we are running on

build_targets := speclinks

ifneq "$(XmTargets)" ""
build_targets += xm
endif

ifneq ($(RccImplementations),)
build_targets += hdl rcc
endif

ifeq ($(OCPI_HAVE_OPENCL),1)
ifneq ($(OclImplementations),)
build_targets += ocl
endif
endif

ifneq ($(HdlImplementations),)
build_targets += hdl
endif

ifneq ($(AssyImplementations),)
build_targets += assy
endif

#ifneq ($(TestImplementations),)
#build_targets += test
#endif

$(call OcpiDbgVar,build_targets)
# function to build the targets for an implemention.
#  First arg is model
#  second is implementation directory
ifdef OCPI_OUTPUT_DIR
PassOutDir=OCPI_OUTPUT_DIR=$(call AdjustRelative,$(OutDir:%/=%))
endif
MyMake=$(MAKE) --no-print-directory
#BuildImplementation=\
#    set -e; \
#    tn="$(call Capitalize,$(1))Targets"; \
#    t="$(or $($(call Capitalize,$1)Target),$($(call Capitalize,$(1))Targets))"; \
#    $(ECHO) =============Building $(call ToUpper,$(1)) implementation $(2) for targets: $$t; \
#    $(MyMake) -C $(2) OCPI_CDK_DIR=$(call AdjustRelative,$(OCPI_CDK_DIR)) \
#               $$tn="$$t" \

HdlLibrariesCommand=$(call OcpiAdjustLibraries,$(HdlLibraries))
RccLibrariesCommand=$(call OcpiAdjustLibraries,$(RccLibraries))
TestTargets:=$(call Unique,$(HdlPlatforms) $(HdlTargets) $(RccTargets))
# set the directory flag to make, and use the desired Makefile
GoWorker=$(infox GW:$1:$(wildcard $1/Makefile))-C $1 $(if $(wildcard $1/Makefile),,\
                 -f $(OCPI_CDK_DIR)/include/$(strip $(foreach d,$(notdir $1),\
                                                      $(if $(filter %.test,$d),test,\
                                                        $(if $(filter %.comp,$d),component,worker)).mk)))
BuildImplementation=$(infox BI:$1:$2:$(call HdlLibrariesCommand):$(call GoWorker,$2)::)\
    set -e; \
    if [ $1 = hdl -a  -z "$3$(HdlTarget)$(HdlTargets)$(HdlPlatform)$(HdlPlatforms)" ] ; then \
      echo "=============Skipping building $2 since no HDL targets or platforms specified."; exit 0; fi; \
    t="$(foreach t,$(or $($(call Capitalize,$1)Target),$($(call Capitalize,$1)Targets)),\
         $(call $(call Capitalize,$1)TargetDirTail,$t))";\
    $(ECHO) $(strip $(if $(filter comp,$1),\
	  =============Building tests in component directory $2,\
	  =============$(if $3,Performing \"$3\" for,Building) $(call ToUpper,$(1)) implementation $(2) for target'(s)': $$t)); \
    $(MyMake) $(call GoWorker,$2) \
	       LibDir=$(call AdjustRelative,$(LibDir)/$(1)) \
	       GenDir=$(call AdjustRelative,$(GenDir)/$(1)) \
	       $(PassOutDir) \
	       $(and $(OCPI_PROJECT_REL_DIR),OCPI_PROJECT_REL_DIR=../$(OCPI_PROJECT_REL_DIR)) \
	       ComponentLibrariesInternal="$(call OcpiAdjustLibraries,$(ComponentLibraries))" \
	       $(call Capitalize,$1)LibrariesInternal="$(call OcpiAdjustLibraries,$($(call Capitalize,$1)Libraries))" \
	       $(call Capitalize,$1)IncludeDirsInternal="$(call AdjustRelative,$($(call Capitalize,$1)IncludeDirs))" \
               XmlIncludeDirsInternal="$(call AdjustRelative,$(XmlIncludeDirs))" $3;\

BuildModel=\
$(AT)set -e;\
  $(foreach i,$($(call Capitalize,$(1))Implementations),\
    if test ! -d $i; then \
      echo Implementation \"$i\" has no directory here.; \
      exit 1; \
    else \
      $(call BuildImplementation,$(1),$i,$2) \
    fi;)\

CleanModel=$(infox CLEANING MODEL $1)\
  $(AT)$(if $($(call Capitalize,$1)Implementations), \
	 $(foreach i,$($(call Capitalize,$1)Implementations),\
	   if test -d $$i; then \
	     tn="$(call Capitalize,$1)Targets"; \
	     t="$(or $(CleanTarget),$($(call Capitalize,$1)Targets))"; \
	     $(ECHO) $(strip $(if $(filter comp,$1),\
	     =============Cleaning component directory $i,\
             =============Cleaning $(call ToUpper,$1) implementation $i for targets: $$t)); \
	     $(MyMake) $(call GoWorker,$i) $(PassOutDir) $$tn="$$t" clean; \
          fi;),:)\
	  rm -r -f lib/$1 gen/$1

# This only makes sense when tests are in *.comp directories
comp:
	$(AT)set -e;\
	  $(foreach i,$(Components),$(call OcpiInfo,COMPIS:$i)\
	    if test ! -d $i; then \
	      echo Component \"$i\" has no directory here.; \
	      exit 1; \
	    else \
	      $(call BuildImplementation,comp,$i) \
	    fi;)\

# This is the doc that will not be built anyway as a side-effect of building elsewhere, i.e. workers
cleancomp:
	$(call CleanModel,comp)

all: $(if $(filter 1,$(OCPI_DOC_ONLY)),docs,declare workers $(if $(filter 1,$(OCPI_NO_DOC)),,docs))
# these ensure that recursive makes do not build docs at lower levels
override export OCPI_NO_DOC=1
override export OCPI_DOC_ONLY=

docs:
	$(AT)ocpidoc build -b

workers: $(build_targets)

$(OutDir)lib:
	$(AT)mkdir $@
speclinks: | $(OutDir)lib
	$(AT)$(call OcpiSpecLinks,.,$(OutDir)lib)

$(Models:%=$(OutDir)lib/%): | $(OutDir)lib
	$(AT)mkdir $@

$(Models:%=$(OutDir)gen/%): | $(OutDir)gen
	$(AT)mkdir $@

xm: speclinks $(XmImplementations)

rcc: speclinks $(RccImplementations)

test tests: speclinks $(TestImplementations)

checkocl:
	$(AT)if ! test -x $(ToolsDir)/ocpiocltest || ! $(ToolsDir)/ocpiocltest test; then echo Error: OpenCL is not available; exit 1; fi

ifeq ($(OCPI_HAVE_OPENCL),1)
ocl: checkocl speclinks $(OclImplementations)
else
ocl:
	$(AT)echo No OpenCL installed so no OCL workers built.
endif

.PHONY: hdl
hdl: speclinks $(HdlImplementations)
	$(AT)for i in $(HdlTargets); do mkdir -p lib/hdl/$$i; done

assy: speclinks $(AssyImplementations)
	$(AT)for i in $(HdlTargets); do mkdir -p lib/hdl/$$i; done

cleanxm:
	$(call CleanModel,xm)

cleanassy:
	$(call CleanModel,assy)

cleanrcc:
	$(call CleanModel,rcc)

cleantest:
	$(call CleanModel,test)

cleanocl:
	$(call CleanModel,ocl)

cleanhdl:
	$(call CleanModel,hdl)

clean:: cleanocl

clean:: cleanxm cleanrcc cleanhdl cleantest cleancomp
	$(AT)echo Cleaning \"$(CwdName)\" component library directory for all targets.
	$(AT)find . -depth -name gen -exec rm -r -f "{}" ";"
	$(AT)find . -depth -name "target-*" -exec rm -r -f "{}" ";"
	$(AT)rm -fr $(OutDir)lib $(OutDir)gen $(OutDir)

$(HdlImplementations): | $(OutDir)lib/hdl $(OutDir)gen/hdl
	$(AT)$(call BuildImplementation,hdl,$@)

$(RccImplementations): | $(OutDir)lib/rcc
	$(AT)$(call BuildImplementation,rcc,$@)

$(TestImplementations): | $(OutDir)/$@
	$(AT)$(call BuildImplementation,test,$@)

$(OclImplementations): | $(OutDir)lib/ocl
	$(AT)$(call BuildImplementation,ocl,$@)

$(XmImplementations): | $(OutDir)lib/xm
	$(AT)$(call BuildImplementation,xm,$@)

$(AssyImplementations): | $(OutDir)lib/assy
	$(AT)$(call BuildImplementation,assy,$@)

.PHONY: $(XmImplementations) $(RccImplementations) $(TestImplementations) $(OclImplementations) $(HdlImplementations) $(AssyImplementations) speclinks hdl

cleanall:
	$(AT)find . -depth -name gen -exec rm -r -f "{}" ";"
	$(AT)find . -depth -name "target-*" -exec rm -r -f "{}" ";"
	$(AT)rm -r -f lib
endif # else of workersfile

.PHONY: generate run $(OcpiTestGoals) showincludes showpackage showworkers showtests
.SILENT: showincludes showpackage showworkers showtests
run: runtest # generic "run" runs test
$(filter-out test cleantest,$(OcpiTestGoals)):
	$(AT)set -e; $(foreach i,$(TestImplementations), \
	  echo ==============================================================================;\
	  echo ==== Performing goal \"$@\" for unit tests in $i;\
	  $(MAKE) $(and $(OCPI_PROJECT_REL_DIR),OCPI_PROJECT_REL_DIR=../$(OCPI_PROJECT_REL_DIR)) \
                  --no-print-directory $(call GoWorker,$i) $@ ;) \

# The ordering here assumes HDL cannot depend on RCC.
generate:
	$(call BuildModel,hdl,generate)
	$(call BuildModel,ocl,generate)
	$(call BuildModel,rcc,generate)
	$(call BuildModel,test,generate)

# In order to generate preprocessed XML from specs in a library (that are not in a *.comp directory),
# we need a goal that does it, and respects the XML search rules for the library (and project)
# The spec file is specified in the XmlFile variable
# This is related to the XML goal in the xxx-worker.mk file
xml:
	@$(if $(XmlFile),,$(error missing XmlFile variable))\
         $(if $(AT),,set -x;) $(OcpiGenEnv) ocpigen -G specs/$(XmlFile)

# declare all HDL workers in the library
# suppress all targets, mostly for printing what is going on
ifneq ($(filter declare,$(MAKECMDGOALS)),)
  MAKEOVERRIDES+=HdlPlatforms= HdlPlatform= HdlTargets= HdlTarget=
  override HdlPlatforms=
  override HdlPlatform=
  override HdlTargets=
  override HdlTarget=
endif

declare: speclinks
	$(call BuildModel,hdl,declare)
	$(call BuildModel,ocl,declare)
	$(call BuildModel,rcc,declare)

ifdef ShellLibraryVars
showlib:
	$(info Tests="$(TestImplementations); Workers="$(Implementations)"; Package="$(Package)";)
showtests:
	$(info Tests="$(TestImplementations)";)
showworkers:
	$(info Workers="$(Implementations)";)
showpackage:
	$(info Package="$(Package)";)
showincludes:
	$(call OcpiSetXmlIncludes)
	$(info XmlIncludeDirsInternal="$(XmlIncludeDirsInternal)";)
endif
