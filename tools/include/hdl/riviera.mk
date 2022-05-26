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

# This file has the HDL tool details for riviera

################################################################################
# Name of the tool that needs to be installed to use this compilation flow
HdlToolName_riviera=Riviera

# This variable is needed when including this file
# for the sole purpose of extracting variable information
# E.g. if you want to know some information about a supported tool,
# you should not need the corresponding toolchain installed
ifndef __ONLY_TOOL_VARS__

################################################################################
# $(call HdlToolLibraryFile,target,libname)
# Function required by toolset: return the file to use as the file that gets
# built when the library is built.
# In riviera the result is a library directory that is always built all at once, and is
# always removed entirely each time it is built.  It is so fast that there is no
# point in fussing over "incremental" mode.
# So there not a specific file name we can look for
HdlToolLibraryFile=$2
################################################################################
# Function required by toolset: given a list of targets for this tool set
# Reduce it to the set of library targets.
HdlToolLibraryTargets=riviera
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
#
# For this tool, it is not sufficient just to include the assembly and pfconfig
# at the container level. We must also include app workers, devices and the PW
HdlToolRequiresFullCoreHierarchy_riviera=yes
################################################################################
# Variable required by toolset: HdlToolNeedBB=yes
# Set if the tool set requires a black-box library to access a core
HdlToolNeedBB=

################################################################################
# Function required by toolset: $(call HdlToolCoreRef,coreref)
# Modify a stated core reference to be appropriate for the tool set
HdlToolCoreRef=$(call HdlRmRv,$1)
HdlToolCoreRef_riviera=$(call HdlRmRv,$1)
HdlRecurseLibraries_riviera=yes

RivieraFiles=\
  $(foreach f,$(HdlSources),\
     $(call FindRelative,$(TargetDir),$(dir $(f)))/$(notdir $(f)))
$(call OcpiDbgVar,RivieraFiles)

# Riviera-PRO
RivieraExecDir=$(OCPI_RIVIERA_DIR)/bin
RivieraExec=$(OCPI_RIVIERA_DIR)/bin/$1


RivieraVlogLibs=

# FIXME: make . in the include path for primitives as well as workers
RivieraVlogIncs=\
  $(foreach d,$(VerilogDefines),+define+$d) +incdir+.. \
  $(foreach d,$(VerilogIncludeDirs),+incdir+$(call FindRelative,$(TargetDir),$d))

# Riviera-PRO args
RivieraArgs= -dbg -work $(WorkLib)
# VHDL Compiler arguments (additional to RivieraArgs) - issue #2912
RivieraVhdlArgs = -norangecheck
# RivieraVhdlArgs =

# $(RivieraExecDir)/vmap -re $(lib_name) $(lib_path)/$(lib_name).lib ; \

HdlToolCompile=\
	(echo 'This file is generated for building this '$(LibName)' library.'; \
	echo 'echo Building library: '$(LibName) > comp.do; \
	$(eval RivieraLibs:=$(call HdlCollectLibraries,riviera)) \
	$(foreach l,$(RivieraLibs),$(infox LLL:$l) \
		echo $(lastword $(subst :, ,$l))=$(strip \
        $(call FindRelative,$(TargetDir),$(strip \
		$(call HdlLibraryRefDir,$l,$(HdlTarget),,riviera))));) \
	echo '; above is primitive libraries, below is cores';\
	$(foreach c,$(call HdlCollectCorePaths),$(infox CCC:$c)\
    	$(- for each core, specify any libraries it needs)\
      	$(eval RivieraCoreLibs:=$(call HdlCollectCoreLibraries,$c,$(RivieraLibs)))\
      	$(foreach l,$(RivieraCoreLibs),$(infox LLL1:$l)\
        echo $(lastword $(subst :, ,$l))=$(strip\
			$(call AdjustRelative,$(call HdlLibraryRefDir,$l,$(HdlTarget),,riviera)));)\
		$(eval ModesimLibs+=$(RivieraCoreLibs))$(strip \
		echo ';core $c' && echo $(call HdlRmRv,$(notdir $(c)))=$(call FindRelative,$(TargetDir),$(strip \
		$(call HdlCoreRef,$(call HdlRmRv,$c),riviera)));)) \
	) > libs.dep ; \
	export LM_LICENSE_FILE=$(OCPI_RIVIERA_LICENSE_FILE); \
	rm -r -f $(WorkLib); \
	$(foreach c, $(call HdlCollectCorePaths), \
		$(eval RivieraCoreLibs:=$(call HdlCollectCoreLibraries, $c, $(RivieraLibs)))\
		$(foreach l, $(RivieraCoreLibs), \
			$(eval lib_entry:=$(subst :, ,$l)) \
			$(eval lib_name:=$(call HdlRmRv,$(notdir $(lastword $(lib_entry))))) \
			$(eval lib_path:=$(call FindRelative,$(TargetDir),$(strip $(call HdlCoreRef,$(call HdlRmRv,$(firstword $(lib_entry))),riviera)))) \
			$(RivieraExecDir)/vmap -re $(lib_name) $(lib_path)/$(lib_name).lib ; \
			echo vmap -re $(lib_name) $(lib_path)/$(lib_name).lib >> comp.do; \
		) \
		$(eval lib_name:=$(call HdlRmRv,$(notdir $(c)))) \
		$(eval lib_path:=$(call FindRelative,$(TargetDir),$(strip $(call HdlCoreRef,$(call HdlRmRv,$c),riviera)))) \
		$(RivieraExecDir)/vmap -re $(lib_name) $(lib_path)/$(lib_name).lib ; \
		echo vmap -re $(lib_name) $(lib_path)/$(lib_name).lib >> comp.do; \
	) \
	$(eval RivieraLibs:=$(call HdlCollectLibraries,riviera)) \
	$(foreach l, $(RivieraLibs), \
    	$(eval lib_entry:=$(subst :, ,$l)) \
    	$(eval lib_path:=$(firstword $(lib_entry))) \
    	$(eval lib_name:=$(lastword $(lib_entry))) \
    	$(eval lib_path_rel:=$(call FindRelative,$(TargetDir),$(strip \
        	$(call HdlLibraryRefDir,$l,$(HdlTarget)))))\
    	$(RivieraExecDir)/vmap -re $(lib_name) $(lib_path_rel)/$(lib_name).lib ; \
		echo vmap -re $(lib_name) $(lib_path_rel)/$(lib_name).lib >> comp.do; \
	) \
	( set -o pipefail && (\
    $(if $(filter work,$(LibName)),,\
        $(RivieraExecDir)/vlib $(WorkLib) && \
        $(RivieraExecDir)/vdel -lib $(WorkLib) -all && \
    ) \
    $(if $(filter work,$(LibName)),,\
        echo vlib $(WorkLib) >> comp.do && \
        echo adel -lib $(WorkLib) -all >> comp.do && \
    ) \
    $(and $(filter %.v,$(RivieraFiles)),\
        $(RivieraExecDir)/vlog $(RivieraVlogIncs) $(VlogLibs) $(RivieraArgs)\
            $(filter %.v, $(RivieraFiles)) &&)\
    $(if $(filter %.v,$(RivieraFiles)),\
        echo vlog $(RivieraVlogIncs) $(VlogLibs) $(RivieraArgs) $(filter %.v, $(RivieraFiles)) >> comp.do && \
	) \
	$(if $(filter %.vhd,$(RivieraFiles)),\
	    echo vcom $(if $(HdlNoSimElaboration),,$(ignore -bindAtCompile))\
            $(RivieraArgs) $(RivieraVhdlArgs) $(filter %.vhd,$(RivieraFiles)) >> comp.do && \
	) \
    $(and $(filter %.vhd,$(RivieraFiles)),\
          $(RivieraExecDir)/vcom $(if $(HdlNoSimElaboration),,$(ignore -bindAtCompile))\
          $(RivieraArgs) $(RivieraVhdlArgs) $(filter %.vhd,$(RivieraFiles)) &&)\
    :) 2>&1 ) || \
    (rm -r -f $(WorkLib) && exit 1)


# Since there is not a singular output, make's builtin deletion will not work
HdlToolPost=\
  touch $(WorkLib);

BitFile_riviera=$1.tar

define HdlToolDoPlatform_riviera

# Generate bitstream
$1/$3.tar:
	$(AT)echo Building riviera simulation executable: "$$@" with details in $1/$3-riviera.out
	$(AT)(set -e ; cd $1 && \
	     echo -L $3 $$$$(grep = libs.dep | grep -v others= | sed 's/=.*//' | sed 's/^/-L /') > vsim.args && \
	     export ALDEC_LICENSE_FILE=$(OCPI_RIVIERA_LICENSE_FILE) && \
		 echo 'Writing macro file: sim_diag.do for $3' && \
		 echo 'onerror {' > sim_diag.do && \
		 echo '    quit -force -code 1' >> sim_diag.do && \
		 echo '}' >> sim_diag.do && \
		 echo 'vsim -dbg -ieee_nowarn -t 1ps $3.$3 -f vsim.args' >> sim_diag.do && \
	     echo 'log -verbose /*' >> sim_diag.do && \
		 echo 'run -all' >> sim_diag.do && \
		 echo 'quit -force' >> sim_diag.do && \
	     $(call RivieraExec,vsimsa) -do sim_diag.do && \
            echo vsim exited successfully, now creating archive: $$@ && \
	        echo $$(notdir $$@) && \
			tar -cf $$(notdir $$@) -h dataset.asdb vsim.args metadatarom.dat )
endef
endif
