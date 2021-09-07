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

# This is the makefile for container directories where the assembly might be elsewhere.
# If containers are built in subdirectories of assemblies, then the assembly one level
# up (in ..)
# One container will be built here, but it may be build for multiple platforms.
# The HdlAssembly variable must be set to point to the relative or absolute path
# to the assembly's directory, ending in the name of the assembly.
HdlMode:=container
Model:=hdl
override XmlIncludeDirs:=$(XmlIncludeDirs) $(OCPI_CDK_DIR)/include/hdl
$(infox MYCL:$(ComponentLibraries):$(ComponentLibrariesInternal):$(XmlIncludeDirs))
ifndef HdlPlatforms
HdlPlatforms:=$(HdlPlatform)
endif
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
# These next lines are similar to what worker.mk does
override Workers:=$(CwdName:container-%=%)
override Worker:=$(Workers)
XmlName:=$(Worker).xml
# XML file is either here or generated in the assembly or generated here
Worker_$(Worker)_xml:=$(or $(wildcard $(XmlName)),\
                           $(wildcard $(HdlAssembly)/gen/$(XmlName)),\
                           $(wildcard $(GeneratedDir)/$(XmlName)))
Worker_xml:=$(Worker_$(Worker)_xml)
Assembly:=$(notdir $(HdlAssembly))
# Unless we are cleaning, figure out our platform, its dir, and the platform config
ifneq ($(MAKECMDGOALS),clean)
  ifndef Worker_xml
    $(error The XML for the container assembly, $(Worker).xml, was not found)
  endif
  ifeq ($(wildcard $(Worker_xml)),)
    $(error Cannot find an XML file for container: $(Worker))
  endif
  ifndef HdlConfig
    # This is only for standalone container directories
    $(and $(call DoShell,$(call OcpiGen, -X $(Worker_xml)),HdlContPfConfig),\
       $(error Processing container XML $(Worker_xml): $(HdlContPfConfig)))
    HdlContPf:=$(patsubst %_pf,%,$(word 3,$(HdlContPfConfig)))
    ifdef HdlContPf
      HdlConfig:=$(word 1,$(HdlContPfConfig))
      HdlConstraints:=$(foreach c,$(filter-out -,$(word 2,$(HdlContPfConfig))),\
                        $(foreach s,$(call HdlGetConstraintsSuffix,$(HdlConfPf)),\
                           $c$(if $(filter %$s,$c),,$s)))
    else
      HdlContPf:=$(or $(HdlPlatform) $(word 1,$(HdlPlatforms)))
      HdlConfig:=base
    endif
    ifdef HdlPlatforms
      ifeq ($(filter $(HdlContPf),$(HdlPlatforms)),)
        $(info Nothing built: container platform is $(HdlContPf), which is not in HdlPlatforms: $(HdlPlatforms))
        HdlSkip:= 1
      endif
    endif
    ifeq ($(filter $(HdlContPf),$(HdlAllPlatforms)),)
      $(error The platform $(HdlContPfConfig) in $(Worker_xml) is unknown.)
    endif
    override HdlPlatform:=$(HdlContPf)
    override HdlPlatforms:=$(HdlPlatform)
  endif
  HdlPlatformDir:=$(HdlPlatformDir_$(HdlPlatform))
  HdlPart:=$(call HdlGetPart,$(HdlPlatform))
  override HdlTargets:=$(call HdlGetFamily,$(HdlPart))
  override HdlTarget:=$(HdlTargets)
  Platform:=$(HdlPlatform)
  PlatformDir:=$(HdlPlatformDir)
endif

# Make sure the platform's containing project is searched.
# It may not be in the project dependencies, but it may depend
# on devices in the current project's hdl/devices library.
export OCPI_PROJECT_PATH:=$(call OcpiAbsPathToContainingProject,$(HdlPlatformDir_$(HdlPlatform)))$(and $(OCPI_PROJECT_PATH),:$(OCPI_PROJECT_PATH))

OcpiLanguage:=vhdl
override HdlLibraries+=sdp axi platform
# ComponentLibraries and XmlIncludeDirs are already passed to us on the command line.
# Note that the platform directory should be first XML dir since the config file name should be
# scoped to the platform.

# Ideally, when processing platform files, the platform's project's project dependencies should be
# used, but NOT used when the app is processed.
# I.e. The platform developer should get consistent results without being damaged
# by the app project, and the app developer should not get damaged by the platform developer's
# projects.  This is probably best fixed by forcing the platform files to to have fully
# qualified names...
override XmlIncludeDirsInternal:=\
   $(call Unique,$(HdlPlatformDir) \
                 $(HdlPlatformDir)/hdl \
                 $(HdlPlatformDir)/devices/ \
                 $(HdlPlatformDir)/devices/hdl \
                 $(realpath $(HdlPlatformDir))/../../../../exports/lib/devices \
                 $(realpath $(HdlPlatformDir))/../../../../exports/lib/devices/hdl \
                 $(realpath $(HdlPlatformDir))/../../../../exports/lib/cards \
                 $(realpath $(HdlPlatformDir))/../../../../exports/lib/cards/hdl \
                 $(XmlIncludeDirs) \
                 $(XmlIncludeDirsInternal) \
                 $(HdlAssembly) \
                 $(foreach p,$(call HdlProjectDepsFromPlatformDir,$(HdlPlatformDir_$(HdlPlatform))),\
                   $(foreach d,$(realpath $(OCPI_PROJECT_REL_DIR)/imports)/$p,\
                     $d/exports/lib/devices $d/exports/lib/devices/hdl \
                     $d/exports/lib/cards $d/exports/lib/cards/hdl)))

# We might be called from an assembly directory, in which case many of the
# component libraries are passed through to us, but we might be standalone.
# Thus we add "devices/adapters/cards" and the platforms own libraries.
# Note we do not expect this Makefile to have any ComponentLibrary setting
override ComponentLibraries:=$(call Unique,\
   $(HdlAssembly) \
   $(ComponentLibrariesInternal) \
   $(HdlPlatformDir_$(Platform):%/lib=%) \
   $(foreach p,$(HdlPlatformDir_$(Platform)),\
     $(foreach d,$(if $(filter lib,$(notdir $p)),$(dir $p),$p/),\
       $(wildcard $ddevices) \
       $(foreach l,$(ComponentLibraries_$(Platform)),\
         $(if $(filter /%,$l),$l,$d$l)))\
      $(foreach pp,$(call HdlProjectDepsFromPlatformDir,$p),\
        $(foreach dd,$(realpath $(OCPI_PROJECT_REL_DIR)/imports)/$(pp),\
          $(wildcard $(dd)/exports/lib/devices $(dd)/exports/lib/cards))))\
   devices cards)
override LibDir=$(HdlAssembly)/lib/hdl
ifneq ($(MAKECMDGOALS),clean)
  $(eval $(OcpiProcessBuildFiles))
  override Platform:=$(if $(filter 1,$(words $(HdlPlatforms))),$(HdlPlatforms))
  $(eval $(HdlSearchComponentLibraries))
  $(infox XMLI3:$(XmlIncludeDirsInternal):$(ComponentLibraries):$(HdlPlatform):$(HdlPlatformDir_$(HdlPlatform)))
  include $(OCPI_CDK_DIR)/include/hdl/hdl-pre.mk
  ifndef HdlSkip
    $(eval $(HdlPrepareAssembly))
    $(infox XMLI4:$(XmlIncludeDirsInternal):$(ComponentLibraries):$(HdlPlatform):$(HdlPlatformDir_$(HdlPlatform)))
    include $(OCPI_CDK_DIR)/include/hdl/hdl-worker.mk
    ifndef HdlSkip
      HdlContName=$(Worker)$(if $(filter 0,$1),,_$1)
      ArtifactXmlName=$(call WkrTargetDir,$(HdlTarget),$1)/$(Worker)-art.xml
      UUIDFileName=$(call WkrTargetDir,$(HdlTarget),$1)/$(Worker)_UUID.v
      MetadataRom=$(call WkrTargetDir,$(HdlTarget),$1)/metadatarom.dat
      HdlContPreCompile=\
        echo Generating UUID, artifact xml file and metadata ROM file for container $(Worker) "($1)". && \
        (cd .. && \
         $(call OcpiGen, -D $(call WkrTargetDir,$(HdlTarget),$1) -A -S $(Assembly) -P $(HdlPlatform) \
                    -e $(HdlPart) -F $(PlatformDir) $(ImplXmlFile)) && \
         rom_words=`$(OcpiHdl) -v bram $(call ArtifactXmlName,$1) $(call MetadataRom,$1)` && \
         echo Compressed metadata ROM is $$$$rom_words dwords. && \
	 sed -i 's/\(rom_words *=> *to_ushort(\)[^)]*)/\1'$$$$rom_words')/' $(ImplFile) \
        )
      # Now we need to make a bit file from every paramconfig for this worker
      HdlBitName=$(call BitFile_$(HdlToolSet_$(HdlTarget)),$(call HdlContName,$1))
      HdlContBitName=$(call WkrTargetDir,$(HdlTarget),$1)/$(call HdlBitName,$1)
      HdlContBitZ=$(basename $(call HdlContBitName,$1)).bitz
      define ContDoConfig
        $(infox ART:$(call ArtifactXmlName,$1):UUID:$(call UUIDFileName,$1):BIT:$(call HdlBitName,$1):ROM:$(call MetadataRom,$1):BIN:$(call WkrBinary,$(HdlTarget),$1))
        $(infox HCBF:$(call HdlContBitName,$1))
        $(call UUIDFileName,$1):
        $(call WkrBinary,$(HdlTarget),$1): HdlPreCompile=$(call HdlContPreCompile,$1)
        $(call WkrBinary,$(HdlTarget),$1): TargetSourceFiles_$1+=$(call UUIDFileName,$1)
        $(call WkrBinary,$(HdlTarget),$1): HdlExactPart=$(HdlPart_$(Platform))
        $(call HdlContBitName,$1): $(call WkrBinary,$(HdlTarget),$1)
        $(call HdlContBitZ,$1): $(call HdlContBitName,$1)
	   $(AT)echo Making compressed bit file: $$@ from $$< and $(call ArtifactXmlName,$1)
	   $(AT)gzip -c $(call HdlContBitName,$1) > $$@
	   $(AT)$$(call OcpiPrepareArtifact,$(call ArtifactXmlName,$1),$$@,$(OCPI_PROJECT_PACKAGE),0,$(Platform))
	   $(AT)$(OCPI_CDK_DIR)/scripts/export-file.sh - $$@

        all: $(call HdlContBitZ,$1)

        # Invoke tool build: <target-dir>,<assy-name>,<core-file-name>,<config>,<platform>
        $(eval $(call HdlToolDoPlatform_$(HdlToolSet_$(HdlTarget)),$(call WkrTargetDir,$(HdlTarget),$1),$(Assembly),$(Worker),$(HdlConfig),$(HdlPlatform),$1))
      endef
      $(call OcpiDbgVar,ParamConfigurations)
      $(foreach c,$(ParamConfigurations),$(eval $(call ContDoConfig,$c)))
    endif # skip from hdl-worker.mk
  endif # skip from hdl-pre.mk
endif # cleaning
clean::
	$(AT) rm -r -f target-* gen lib
