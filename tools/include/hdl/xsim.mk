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

################################################################################
# Name of the tool that needs to be installed to use this compilation flow
HdlToolName_xsim=Vivado

# This variable is needed when including this file
# for the sole purpose of extracting variable information
# E.g. if you want to know some information about a supported tool,
# you should not need the corresponding toolchain installed
ifndef __ONLY_TOOL_VARS__

include $(OCPI_CDK_DIR)/include/xilinx/xilinx.mk

################################################################################
# $(call HdlToolLibraryFile,target,libname)
# Function required by toolset: return the file to use as the file that gets
# built when the library is built.
# In xsim the result is a library directory that is always built all at once, and is
# always removed entirely each time it is built.  It is so fast that there is no
# point in fussing over "incremental" mode.
# So there not a specific file name we can look for
HdlToolLibraryFile=$2

################################################################################
# Function required by toolset: given a list of targets for this tool set
# Reduce it to the set of library targets.
HdlToolLibraryTargets=xsim
################################################################################
# Variable required by toolset: HdlBin
# What suffix to give to the binary file result of building a core
# Note we can't build cores for further building, only simulatable "tops"
HdlBin=
################################################################################
# Variable required by toolset: HdlToolRealCore
# Set if the tool can build a real "core" file when building a core
# I.e. it builds a singular binary file that can be used in upper builds.
# If not set, it implies that only a library containing the implementation is
# possible
HdlToolRealCore=

# For this tool, it is not sufficient just to include the assembly and pfconfig
# at the container level. We must also include app workers, devices and the PW
HdlToolRequiresFullCoreHierarchy_xsim=yes
################################################################################
# Variable required by toolset: HdlToolNeedBB=yes
# Set if the tool set requires a black-box library to access a core
HdlToolNeedBB=

################################################################################
# Function required by toolset: $(call HdlToolCoreRef,corename)
# This is the name after core name in a path
# It might adjust (genericize?) the target
HdlToolCoreRef=$(call HdlRmRv,$1)
HdlToolCoreRef_xsim=$(call HdlRmRv,$1)

XsimFiles=\
  $(foreach f,$(HdlSources),\
     $(foreach x,$(call FindRelative,$(TargetDir),$(dir $(f)))/$(notdir $(f)),\
       $(infox XSF:$x)$x))
$(call OcpiDbgVar,XsimFiles)

XsimCoreLibraryChoices=$(strip \
  $(foreach c,$(call HdlRmRv,$1),$(call HdlCoreRef,$c,xsim)))

ifneq (,)
XsimLibs=\
  $(and $(filter assembly container,$(HdlMode)),\
  $(eval $(HdlSetWorkers)) \
  $(foreach w,$(HdlWorkers),\
    $(foreach f,$(firstword \
                  $(or $(foreach c,$(ComponentLibraries), \
                         $(foreach d,$(call HdlComponentLibrary,$c,xsim),\
	                   $(wildcard $d/$w))),\
                       $(error Worker $w not found in any component library.))),\
      -lib $w=$(call FindRelative,$(TargetDir),$f)))) \
  $(foreach l,\
    $(HdlLibrariesInternal) $(Cores),\
    -lib $(notdir $(l))=$(strip \
          $(call FindRelative,$(TargetDir),$(call HdlLibraryRefDir,$l,xsim,,xsim))))
else
XsimLibs=\
    $(foreach l,\
      $(HdlLibrariesInternal),\
      -lib $(notdir $l)=$(strip \
            $(call FindRelative,$(TargetDir),$(call HdlLibraryRefDir,$l,xsim,,xsim)))) \
    $(foreach c,$(call HdlCollectCorePaths),$(infox CCC:$c)\
      -lib $(call HdlRmRv,$(notdir $(c)))=$(infox fc:$c)$(call FindRelative,$(TargetDir),$(strip \
          $(firstword $(foreach l,$(call XsimCoreLibraryChoices,$c),$(call HdlExists,$l))))))

endif
ifneq (,)
MyIncs=\
  $(foreach d,$(VerilogDefines),-d $d) \
  $(foreach d,$(VerilogIncludeDirs),-i $(call FindRelative,$(TargetDir),$(d))) \
  $(foreach l,$(call HdlXmlComponentLibraries,$(ComponentLibraries)),-i $(call FindRelative,$(TargetDir),$l))
else
XsimVerilogIncs=\
  $(foreach d,$(VerilogDefines),-d $d) \
  $(foreach d,$(VerilogIncludeDirs),-i $(call FindRelative,$(TargetDir),$(d))) \
  $(foreach l,$(HdlXmlComponentLibraries),-i $(call FindRelative,$(TargetDir),$l))
endif

ifndef XsimTop
XsimTop=$(Worker).$(Worker)
endif


XsimArgs= -v 2 -work $(call ToLower,$(WorkLib))=$(WorkLib) $(XsimExtraArgs) 
# Set this option to pass additional arguments to xvhdl and xvlog.
# For example, if you are simulating IP, you may need to point to
# the XSIM IP init file:
# XsimExtraArgs=-initfile $(call OcpiXilinxVivadoDir,infox)/data/xsim/ip/xsim_ip.ini
#XsimExtraArgs=

XsimXelabArgs= -O3 $(XsimXelabExtraArgs)
# Set this option to pass additional arguments to xelab
#XsimXelabExtraArgs=
# -noieeewarnings

HdlToolCompile=\
  $(OcpiXilinxVivadoInit); \
  echo verilog work $(OcpiXilinxVivadoDir)/data/verilog/src/glbl.v \
    >> $(Worker).prj; \
  $(and $(filter %.vhd %.vhdl,$(XsimFiles)),\
    xvhdl $(XsimArgs) $(XsimLibs) $(filter %.vhd %.vhdl,$(XsimFiles)) -prj $(Worker).prj ; ) \
  $(and $(filter %.v,$(XsimFiles))$(findstring $(HdlMode),platform),\
    xvlog $(XsimVerilogIncs) $(XsimArgs) $(XsimLibs) $(filter %.v,$(XsimFiles)) \
      $(and $(findstring $(HdlMode),platform),\
        $(OcpiXilinxVivadoDir)/data/verilog/src/glbl.v) -prj $(Worker).prj ;) \
  $(if $(filter worker platform config assembly,$(HdlMode)),\
    $(if $(HdlNoSimElaboration),, \
      xelab $(WorkLib).$(WorkLib)$(and $(filter assembly config,$(HdlMode)),_rv) work.glbl -v 2 \
             -prj $(Worker).prj -L unisims_ver -s $(Worker).exe --timescale 10ns/1ps \
             --override_timeprecision --override_timeunit --timeprecision_vhdl 1ps \
             $(XsimXelabArgs) $(XsimXelabExtraArgs) -lib $(WorkLib)=$(WorkLib) $(XsimLibs)))

# Since there is not a singular output, make's builtin deletion will not work
HdlToolPost=\
  touch $(WorkLib);

BitFile_xsim=$1.tar

define HdlToolDoPlatform_xsim

# Generate bitstream
# xelab generates a "snapshot" underneath the xsim.dir directory.  So the results are all
# in that directory.
$1/$3.tar:
	$(AT)echo Building xsim simulation executable: "$$@" with details in $1/$3-xelab.out
	$(AT)echo verilog work $(OcpiXilinxVivadoDir)/data/verilog/src/glbl.v >$1/$3.prj
	$(AT)(set -e; cd $1; $(OcpiXilinxVivadoInit); \
	      xelab $3.$3 work.glbl -v 2 -debug typical -prj $3.prj \
              $(XsimXelabArgs) $(XsimXelabExtraArgs) -lib $3=$3 $$(XsimLibs) -L unisims_ver -s $3;\
	      tar cf $3.tar metadatarom.dat xsim.dir) > $1/$3-xelab.out 2>&1

endef
ifneq (,)
 -s $3.exe ;\
XsimPlatform:=xsim_pf
XsimAppName=$(call AppName,$(XsimPlatform))
ExeFile=$(XsimAppName).exe
BitFile=$(XsimAppName).bit
BitName=$(call PlatformDir,$(XsimPlatform))/$(BitFile)
XsimPlatformDir=$(HdlPlatformsDir)/$(XsimPlatform)
XsimTargetDir=$(call PlatformDir,$(XsimPlatform))
XsimFuseCmd=\
  $(VivadoXilinx); xelab $(XsimPlatform).main $(XsimPlatform).glbl -v 2 -debug typical \
		-lib $(XsimPlatform)=$(XsimPlatformDir)/target-xsim/$(XsimPlatform) \
		-lib mkOCApp4B=mkOCApp4B \
	        -lib $(Worker)=../target-xsim/$(Worker) \
	$$(XsimLibs) -L unisims_ver -s $(ExeFile) && \
	tar -c -f $(BitFile) xsim.dir metadatarom.data

define HdlToolDoPlatform
# Generate bitstream
$$(BitName): TargetDir=$(call PlatformDir,$(XsimPlatform))
$$(BitName): HdlToolCompile=$(XsimFuseCmd)
$$(BitName): HdlToolSet=xelab
$$(BitName): override HdlTarget=xsim
$$(BitName): $(XsimPlatformDir)/target-xsim/$(XsimPlatform) $(XsimTargetDir)/mkOCApp4B | $(XsimTargetDir)
	$(AT)echo Building xsim simulation executable: $$(BitName).  Details in $$(XsimAppName)-xelab.out
	$(AT)$$(HdlCompile)
endef
endif
endif
