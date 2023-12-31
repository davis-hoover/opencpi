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

# This file is the make file for a project
PMF := -f $(lastword $(MAKEFILE_LIST))
include $(OCPI_CDK_DIR)/include/util.mk

# This is mandatory since it signifies that this directory is a project
ifeq ($(wildcard Project.mk)$(wildcard Project.xml),)
  $(error This project directory "$(CURDIR)" is corrupted since neither Project.xml(expected) nor Project.mk(backward compatibility) is present.)
endif

ifneq ($(wildcard Project.xml),)
  PROJ_FILE=Project.xml
else
  PROJ_FILE=Project.mk
endif

# Do the OcpiIncludeProject unless we are only importing or exporting or cleaning
ifneq ($(if $(MAKECMDGOALS),$(filter-out imports exports clean%,$(MAKECMDGOALS)),1),)
$(OcpiIncludeProject)
endif
# FIXME: can we test for licensing?
# FIXME: Error message makes no sense if give hdltargets but not platforms
doimports=$(shell $(OcpiExportVars) $(MAKE) $(PMF) imports NoExports=1)
ifeq ($(HdlPlatform)$(HdlPlatforms),)
  ifeq ($(filter clean%,$(MAKECMDGOALS))$(filter imports projectpackage,$(MAKECMDGOALS)),)
    $(infox $(doimports))
    ifeq ($(findstring export,$(MAKECMDGOALS))$(findstring import,$(MAKECMDGOALS)),)
      include $(OCPI_CDK_DIR)/include/hdl/hdl-targets.mk
      $(info No HDL platforms specified.  No HDL assets will be targeted.)
      $(info Possible HdlPlatforms are: $(sort $(HdlAllPlatforms)).)
    endif
  endif
endif

# imports need to be created before exports etc.
ifeq ($(filter imports projectpackage clean%,$(MAKECMDGOALS)),)
  ifeq ($(wildcard imports),)
    $(info Setting up imports)
    $(infox $(doimports))
  else
    # If the imports already exist, we still want to make sure they are up to date
    $(infox Updating imports. $(doimports))
  endif
endif

ifeq ($(NoExports)$(wildcard exports)$(filter projectpackage,$(MAKECMDGOALS)),)
  doexports=$(shell $(OcpiExportVars) $(OCPI_CDK_DIR)/scripts/export-project.sh -)
  ifeq ($(filter clean% imports,$(MAKECMDGOALS)),)
    $(info Setting up exports)
    $(infox $(doexports))
  else
    # we are assuming that exports are not required for any clean goal.
    # $(nuthin $(doexports))
  endif
endif

ifeq (@,$(AT))
  .SILENT: clean imports exports components hdlprimitives hdlcomponents hdldevices hdladapters \
	hdlcards hdlplatforms hdlassemblies cleanhdl rcc cleanrcc ocl cleanocl applications run \
	cleancomponents cleanapplications cleanimports cleanexports cleaneverything $(OcpiTestGoals) \
	projectpackage projectdeps projectincludes
endif

OcpiToProject=$(subst $(Space),/,$(patsubst %,..,$(subst /, ,$1)))
MaybeMake=$(infox MAYBE:$1:$2)\
  $(foreach f,$(if $(wildcard $1/Makefile),Makefile,\
                $(foreach t,$(call OcpiGetDirType,$1),$(infox DT:$1:$t)\
                  $$OCPI_CDK_DIR/include/$(and $(filter hdl-%,$t),hdl/)$t.mk)),\
     if [ -d $1 ] ; then \
       $(MAKE) -f $f --no-print-directory -r -C $1 OCPI_PROJECT_REL_DIR=$(call OcpiToProject,$1) $2; fi)

# Three parameters - $1 is before platform, $2 is after platform, $3 is call to $(MAKE)
MaybeMakePlatforms=\
$(foreach p,$(HdlPlatform) $(HdlPlatforms),\
   echo =============Building platform $p/$2 for $3 &&\
   $(call MaybeMake,$1/$p/$2,$3) &&) true

.PHONY: all applications clean imports exports components cleanhdl $(OcpiTestGoals) projectpackage projectdeps projectincludes
.PHONY: hdl hdlassemblies hdlprimitives hdlcomponents hdldevices hdladapters hdlplatforms hdlassemblies hdlportable
all: applications

# Package issue - if we have a top level specs directory, we must make the
# associate package name available to anything that includes it, both within the
# project and outside it (when this project is accessed via OCPI_PROJECT_PATH)
ifneq ($(wildcard specs),)
  ifeq ($(filter clean%,$(MAKECMDGOALS))$(filter projectpackage,$(MAKECMDGOALS)),)
    # package-id needs to be created early on by any non-clean make command.
    # This can be accomplished by having imports depend on it.
    imports: specs/package-id
    # If Project.<mk|xml> changes, recreate specs/package-id file unless the package-id file contents
    # exactly match OCPI_PROJECT_PACKAGE.
    specs/package-id: $(PROJ_FILE)
	$(AT)if [ -n "$(OCPI_PROJECT_PACKAGE)" ]; then \
               if [ ! -e specs/package-id ] || \
                  [ "$$(cat specs/package-id)" != "$(OCPI_PROJECT_PACKAGE)" ]; then \
	         echo Recording the PackageID for this project as: $(OCPI_PROJECT_PACKAGE) >&2; \
	         echo "$(OCPI_PROJECT_PACKAGE)" > specs/package-id; \
	       fi; \
	     fi
  endif
endif

hdlassemblies applications: imports exports

# Perform test-related goals where they might be found.
DoTests=$(foreach t,\
          components hdl/devices hdl/adapters hdl/cards $(wildcard hdl/platforms/*/devices),\
          $(call MaybeMake,$t,$1) &&) true
$(OcpiTestGoals):
	$(call DoTests,$@)

# Make the imports link to the registry if it does not exist.
# If imports exists and is a link, leave it alone
# If imports is not a link, error
# If imports exists, but does not match the environment variable, warn
# If imports exists but is a broken link, replace it
imports:
	if [ ! -L imports ]; then \
	  if [ -e imports ]; then \
	    echo "Error: This project's imports is not a symbolic link and is therefore invalid." >&2 ; \
	    echo "Remove the imports file at the top level of the project before proceeding." >&2 ; \
	    exit 1 ; \
	  fi; \
	  if [ -d "$(OcpiProjectRegistryDir)" ]; then \
            $(call MakeSymLink2,$(OcpiProjectRegistryDir),$(realpath .),imports); \
	  else \
	    echo "Warning: The project registry '$(OcpiProjectRegistryDir)' does not exist" >&2 ; \
	  fi; \
	else \
	  if [ -n "$(OCPI_PROJECT_REGISTRY_DIR)" ]; then \
	    if [ "$(realpath $(OCPI_PROJECT_REGISTRY_DIR))" != "$(realpath imports)" ]; then \
	      echo "Warning: OCPI_PROJECT_REGISTRY_DIR is globally set to \"$(OCPI_PROJECT_REGISTRY_DIR)\"," >&2 ; \
	      echo "         but the '$(OCPI_PROJECT_PACKAGE)' project located at '$$(pwd)' is using" >&2 ; \
	      echo "         'imports -> $(realpath imports)'" >&2 ; \
	      echo "         The project's 'imports' link will take precedence when within the project." >&2 ; \
	    fi; \
	  fi; \
	  if [ ! -e imports ]; then \
	    if [ -d "$(OcpiProjectRegistryDir)" ]; then \
	      echo "Warning: 'imports' is a broken link and will be replaced with the default \"$(OcpiProjectRegistryDir)\"" >&2 ; \
	      rm imports; \
              $(call MakeSymLink2,$(OcpiProjectRegistryDir),$(realpath .),imports); \
	    else \
	      echo "Warning: Tried to update the broken 'imports' link, but the project registry '$(OcpiProjectRegistryDir)' does not exist" >&2 ; \
	    fi; \
	  elif [ ! -d "$(realpath imports)" ]; then \
	    echo "Warning: The project registry '$(realpath imports)' pointed to by 'imports' is not a directory" >&2 ; \
	  fi; \
	fi

exports:
	$(OCPI_CDK_DIR)/scripts/export-project.sh "$(or $(OCPI_TARGET_DIR),-)"

components: hdlprimitives
	$(MAKE) $(PMF) imports
	$(call MaybeMake,components,rcc hdl)
	$(MAKE) $(PMF) exports

hdlprimitives: imports
	$(MAKE) $(PMF) imports
	$(call MaybeMake,hdl/primitives)
	$(MAKE) $(PMF) exports

hdlcomponents: hdlprimitives
	$(MAKE) $(PMF) imports
	$(call MaybeMake,components,hdl)
	$(MAKE) $(PMF) exports

hdldevices: hdlprimitives
	$(MAKE) $(PMF) imports
	$(call MaybeMake,hdl/devices)
	$(MAKE) $(PMF) exports

hdladapters: hdlprimitives
	$(MAKE) $(PMF) imports
	$(call MaybeMake,hdl/adapters)
	$(MAKE) $(PMF) exports

hdlcards: hdlprimitives
	$(MAKE) $(PMF) imports
	$(call MaybeMake,hdl/cards)
	$(MAKE) $(PMF) exports

hdlplatforms: hdldevices hdlcards hdladapters
	$(MAKE) $(PMF) imports
	$(call MaybeMake,hdl/platforms)
	$(MAKE) $(PMF) exports

hdlassemblies: hdlcomponents hdlplatforms hdlcards hdladapters
	$(MAKE) $(PMF) imports
	$(call MaybeMake,hdl/assemblies)
	$(MAKE) $(PMF) exports

# Everything that does not need platforms
hdlportable: hdlcomponents hdladapters hdldevices hdlcards

hdl: hdlassemblies

# FIXME: cleaning should not depend on imports.  Fix *that* - see below
cleanhdl cleanrcc cleanocl cleancomponents cleanapplications: imports

cleanhdl:
	$(call MaybeMake,components,cleanhdl)
	$(foreach d,primitives devices adapters cards platforms assemblies,\
	  $(call MaybeMake,hdl/$d,clean) &&): \

rcc ocl hdl: imports exports

# rcc proxies may need to see rcc or hdl slaves
rcc:
	$(call MaybeMake,components,declare)
	$(call MaybeMake,hdl/devices,declare)
	$(call MaybeMake,hdl/cards,declare)
	$(call MaybeMake,hdl/adapters,declare)
	$(call MaybeMake,hdl/platforms,declare)
	$(call MaybeMake,components,rcc)
	$(call MaybeMake,hdl/devices,rcc)
	$(call MaybeMake,hdl/cards,rcc)
	$(call MaybeMakePlatforms,hdl/platforms,devices,rcc)

cleanrcc:
	$(call MaybeMake,components,cleanrcc)
	$(call MaybeMake,hdl/devices,cleanrcc)
	$(call MaybeMakePlatforms,hdl/platforms,devices,cleanrcc)

ocl:
	$(call MaybeMake,components,ocl)

cleanocl:
	$(call MaybeMake,components,cleanocl)

applications: rcc hdl
	$(call MaybeMake,applications)

run: all test
	$(AT)echo ==============================================================================
	$(AT)echo ==== Running all unit tests in this project.
	$(call MaybeMake,components,run)
	$(AT)echo ==============================================================================
	$(AT)echo ==== Running all applications in this project.
	$(call MaybeMake,applications,run)

runonly:
	$(call MaybeMake,components,run)
	$(call MaybeMake,applications,run)

cleancomponents:
	$(call MaybeMake,components,clean)

cleanapplications:
	$(call MaybeMake,applications,clean)

# Note that imports must be cleaned last because the host rcc platform directory
# needs to be accessible via imports for projects other than core
# (e.g. for cleaning rcc) FIXME: cleaning should not depend on imports.  Fix *that*
clean: cleanapplications cleanrcc cleanhdl cleanocl cleanexports cleanimports
	$(call MaybeMake,components,clean)
	rm -r -f artifacts project-metadata.xml

# Remove the imports link only if it is the default or it is broken
cleanimports:
	if [ \( -L imports -a "$(realpath imports)" == "$(realpath $(OcpiGlobalDefaultProjectRegistryDir))" \) \
	     -o \( -L imports -a ! -e imports \) ]; then \
	  rm imports; \
	fi

cleanexports:
	rm -r -f exports

cleaneverything: clean
	find . -name '*~' -exec rm {} \;
	find . -depth -name '*.dSym' -exec rm -r {} \;
	find . -depth -name 'target-*' -exec rm -r -f {} \;
	find . -depth -name gen -a -type d -a ! -path "*/rcc/platforms/*" -exec  rm -r -f {} \;
	find . -depth -name lib -a -type d -a ! -path "*/rcc/platforms/*" -exec  rm -r -f {} \;

ifdef ShellProjectVars
projectpackage:
	$(info ProjectPackage="$(OCPI_PROJECT_PACKAGE)";)
projectdeps:
	$(info ProjectDependencies="$(ProjectDependencies)";)
projectincludes:
	$(call OcpiSetXmlIncludes)
	$(info XmlIncludeDirsInternal="$(XmlIncludeDirsInternal)";)
endif
