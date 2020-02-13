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

# This file has the HDL tool details for xst

################################################################################
# Name of the tool that needs to be installed to use this compilation flow
HdlToolName_xst=ISE

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

# When XST compiles VHDL files it creates <lib>.vdbl, <lib>.vdbx
# When XST compiles Verilog files it creates <lib>.sdbl, <lib>.sdbx
# Core platform and assembly modes only use Verilog
# Libraries and workers may also have VHDL
ifneq ($(findstring $(HdlMode),core platform assembly container),)
  HdlLibSuffix=sdbl
else
   ifneq ($(strip $(filter %.vhd,$(CompiledSourceFiles))),)
      HdlLibSuffix=vdbl
   else
      HdlLibSuffix=sdbl
   endif
endif

HdlToolLibraryFile=$2/$2.$(HdlLibSuffix)

# This was correct BEFORE we forced using the new parser in xst
#$(strip \
#  $2/$(if $(filter virtex6 spartan6 zynq,$(call HdlGetFamily,$1)),$2.$(HdlLibSuffix),hdllib.ref))

################################################################################
# Function required by toolset: given a list of targets for this tool set
# Reduce it to the set of library targets.
HdlToolLibraryTargets=$(call Unique,$(foreach t,$(1),$(call HdlGetFamilies,$(t))))
################################################################################
# Variable required by toolset: HdlBin
# What suffix to give to the binary file result of building a core
HdlBin=.ngc
HdlBin_xst=.ngc
################################################################################
# Variable required by toolset: HdlToolRealCore
# Set if the tool can build a real "core" file when building a core
# I.e. it builds a singular binary file that can be used in upper builds.
# If not set, it implies that only a library containing the implementation is
# possible
HdlToolRealCore:=yes
HdlToolRealCore_xst:=yes
################################################################################
# Variable required by toolset: HdlToolNeedBB=yes
# Set if the tool set requires a black-box library to access a core
HdlToolNeedBB:=yes
HdlToolNeedBB_xst:=yes
################################################################################
# Function required by toolset: $(call HdlToolCoreRef,coreref)
# Modify a stated core reference to be appropriate for the tool set
HdlToolCoreRef=$1
HdlToolCoreRef_xst=$1

################################################################################
# This is the name after library name in a path
# It might adjust (genericize?) the target
XstLibRef=$(or $3,$(call HdlGetFamily,$2))

################################################################################
# $(call XstLibraryFileTarget2(target,libname)
# Return the actual file to depend on when it is built
XstLibraryFileTarget=$(if $(filter virtex6 spartan6 zynq,$(call HdlGetFamily,$(infox x3:$1)$(1))),$(2).sdbl,hdllib.ref)
XstLibraryCleanTargets=$(strip \
  $(if $(filter virtex6 spartan6 zynq,$(call HdlFamily,$(1))),*.sdb?,hdllib.ref vlg??))
# When making a library, xst still wants a "top" since we can't precompile 
# separately from synthesis (e.g. it can't do what vlogcomp can with isim)
# Need to be conditional on libraries
ifeq ($(HdlMode),library)
ifeq ($(Core),)
Core=onewire
Top=onewire
endif
endif
#################################################################################
# NOTE:  XST only makes the verilog primitive libraries available if there are verilog sources
# in the project.  This means that, during elaboration, it will fail to elaborate lower level
# verilog modules in libraries if there are no verilog sources in the project file.
# Sooo, we ALWAYS stick the "onewire" verilog in all projects.
# If we are building a library, this serves as the "top" of the library, otherwise
# it is simply stuck in to the compilation to cause XST to make the verilog primitives available
CompiledSourceFiles+= $(OCPI_CDK_DIR)/include/hdl/onewire.v 
WorkLibrarySources+= $(OCPI_CDK_DIR)/include/hdl/onewire.v

XstInternalOptions=$(and $(wildcard $(TargetDir)/$(HdlPlatform).xcf),-uc ../$(HdlPlatform).xcf)
XstDefaultExtraOptions=
#XstDefaultContainerExtraOptions=-iobuf yes -bufg 32 -iob auto
XstDefaultContainerExtraOptions=-bufg 32 -iob auto
XstMyExtraOptions=$(strip \
  $(if $(filter $(HdlMode),container),\
      $(if $(filter undefined,$(origin XstContainerExtraOptions)),\
          $(XstDefaultContainerExtraOptions),\
          $(XstContainerExtraOptions)),\
      $(if $(filter undefined,$(origin XstExtraOptions)),\
          $(XstDefaultExtraOptions),\
          $(XstExtraOptions))))
$(call OcpiDbgVar,Core)
$(call OcpiDbgVar,HdlMode)

# TODO: tempdir,xsthdpdir?, -p family vs part?, sim
# XST parameters controlled by the user should NOT include these:
# ifn:       because we generate the project file
# ofn:       because the output file is according to our conventions
# top:       because the top level module is named in metadata
# xsthdpini: because the library dependencies are in set in the Libraries variable
# p:         because targets are in the Targets variable for the whole library
#            or overriden in the hdl implementation directory (target device)
# ifmt:      because we generate the project file
# iobuf:     because this is a component built, not a chip build
# sd:        how is this different from libraries?
# this may be conditionalized based on xst version.  This is baselined on 11.3.

# target must already include the canonical xst target-device, which has hyphens...
# MAYBE USE PLUS SIGN AS TARGET SEPARATOR
# XST stuff
# From IncludeDirs
# -ofn, not -o
# -vlgincdir {a c b}
# -vlgpath to search for modules

# there is no such thing
#OBJ:=.xxx
# Options that the user should not specify
XstBadOptions=\
    -ifn -ofn -top -xsthdpini -ifmt -sd -vlgincdir -vlgpath -lso
# Options that the user may specify/override
XstGoodOptions=-bufg -opt_mode -opt_level -read_cores -iobuf \
-p \
-power \
-iuc \
-opt_mode Speed \
-opt_level \
-keep_hierarchy \
-netlist_hierarchy \
-rtlview \
-glob_opt \
-write_timing_constraints \
-cross_clock_analysis \
-hierarchy_separator \
-bus_delimiter \
-case \
-slice_utilization_ratio \
-bram_utilization_ratio \
-dsp_utilization_ratio \
-lc \
-reduce_control_sets \
-fsm_extract \
-fsm_encoding \
-safe_implementation \
-fsm_style \
-ram_extract \
-ram_style \
-rom_extract \
-shreg_extract \
-rom_style  \
-auto_bram_packing \
-resource_sharing \
-async_to_sync \
-shreg_min_size \
-use_dsp48 \
-max_fanout \
-register_duplication \
-register_balancing \
-optimize_primitives \
-use_clock_enable \
-use_sync_set \
-use_sync_reset \
-iob \
-equivalent_register_removal \
-slice_utilization_ratio_maxmargin

# Our default options, some of which may be overridden
# This is the set for building cores, not chips.
XstDefaultOptions=\
    -ifmt mixed -bufg 0 $(and $(filter-out container,$(HdlMode)),-iobuf no) -opt_mode speed -opt_level 2 -ofmt NGC \
    -keep_hierarchy soft -netlist_hierarchy rebuilt \
    -hierarchy_separator / \
    -read_cores $(if $(filter container,$(HdlMode)),yes,yes) \
    -use_new_parser yes \

# Extra default ones:\
 -xor_collapse TRUE -verilog2001 TRUE -slice_packing TRUE \
 -shift_extract TRUE -register_balancing No -priority_extract Yes \
 -mux_style Auto -mux_extract Yes -decoder_extract TRUE
# check the first option in the list and recurse
XstCheckOption=\
$(if $(filter -%,$(word 1,$(1))),\
    $(if $(filter $(XstGoodOptions),$(word 1,$(1))),\
        $(if $(word 2,$(1)),\
            $(call XstCheckOption,$(wordlist 3,$(words $(1)),$(1))),\
            $(error Missing value for XST option after "$(1)")),\
        $(error XST option "$(word 1,$(1))" unknown)),\
   $(and $(1),$(error Expected hyphen in XST option "$(1)")))

# Function to check whether options are bad, good, or unknown
XstCheckOptions=\
    $(foreach option,$(XstBadOptions),\
        $(if $(findstring $(option),$1),\
            $(error XST option "$(option)" not allowed here)))\
    $(call XstCheckOption,$1)

XstPruneOption=\
    $(if $(filter $(word 1,$(1)),$(XstMyExtraOptions)),,$(wordlist 1,2,$(1))) \
    $(if $(word 3,$(1)),\
        $(call XstPruneOption,$(wordlist 3,$(words $(1)),$(1))))

XstOptions=\
$(call XstCheckOptions,$(XstMyExtraOptions))\
$(call XstPruneOption,$(XstDefaultOptions)) $(XstMyExtraOptions) $(XstInternalOptions)

# Options and temp files if we have any libraries
# Note that "Libraries" is for precompiled libraries, whereas "OcpiLibraries" are for cores (in the -sd path),
# BUT! the empty module declarations must be in the lso list to get cores we need the bb in a library too.

XstCores=$(call HdlCollectCorePaths)
XstLsoFile=$(Core).lso
XstIniFile=$(Core).ini

XstLibraries=$(HdlLibrariesInternal)

XstNeedLso= $(strip $(XstCompLibs)$(HdlLibrariesInternal)$(XstCores))
XstNeedIni= $(strip $(XstCores)$(HdlLibrariesInternal))
#   $(and $(findstring worker,$(HdlMode)),echo $(call ToLower,$(Worker))=$(call ToLower,$(Worker));) 

# Choices as to where a bb might be
# 1. For pointing to a built target directory with the filename being the core name,
#    where the core, and bblib is built.  Core is $1.$(HdlBin) Lib is $(dir $1)/bb/$(notdir $1)
XstCoreLibraryChoices=$(infox XCLT:$1:$2)$(strip \
  $(and $(filter target-%,$(subst /, ,$1)),$(dir $1)/bb/$(notdir $1)) \
  $(and $(filter target-%,$(subst /, ,$1)),$(dir $1)/bb/$(patsubst %_rv,%,$(notdir $1))) \
  $(call HdlLibraryRefDir,$1_bb,$(if $(HdlTarget),$(call HdlGetFamily,$(HdlTarget)),NONE3),x,X1) \
  $(call HdlLibraryRefDir,$1,$(or $(HdlTarget),$(info NONE4)),x,X2) \
  $(call HdlLibraryRefDir,$1_rv,$(or $(HdlTarget),$(info NONE4)),x,X3) \
)

#   $(if $(PreBuiltCore)$(filter container assembly platform worker core,$(HdlMode)),,echo work;) $(if $(findstring work,$(LibName)),,echo $(LibName);) \
#####################################################
# The list of libraries is ordered:
# 1. Component libraries
# 2. Primitive libraries
# 3. Black box core libraries
# This must be consistent with the XstMakeIni
# The trick is to filter out component library BB libs from the cores.
XstCompLibs=$(ComponentLibraries) $(DeviceLibraries) $(CDKComponentLibraries) $(CDKDeviceLibraries)
# Remove the RV in the middle or at the end.
# This will get fixed when we put the RV at the end everywhere...
XstLibFromCore=$(foreach n,$(patsubst %_rv,%,$(basename $(notdir $1))),\
                 $(if $(findstring _rv_c,$n),$(subst _rv_c,_c,$n),$n))
XstPathFromCore=$(foreach n,$(call XstLibFromCore,$1),$(and $(findstring /,$1),$(dir $1))$n)

XstMakeLso=\
  (\
   $(foreach l,$(XstCompLibs),\
      $(infox CL:$l) \
      echo $(lastword $(subst -, ,$(notdir $l)));)\
   $(foreach l,$(HdlLibrariesInternal),\
      $(infox HL:$l) \
      echo $(lastword $(subst -, ,$(notdir $l)));)\
   $(foreach l,$(XstCores), \
      $(infox CC:$l) \
      echo $(call XstLibFromCore,$l);)\
  ) > $(XstLsoFile);

XstMakeIni=\
  (\
   $(foreach l,$(HdlLibrariesInternal),\
      echo $(lastword $(subst -, ,$(notdir $(l))))=$(strip \
        $(call FindRelative,$(TargetDir),$(strip \
           $(call HdlLibraryRefDir,$(l),$(HdlTarget),,X4))));) \
   $(foreach l,$(XstCores),$(infox XstCore:$l)\
      echo $(call XstLibFromCore,$l)=$(call FindRelative,$(TargetDir),$(strip \
          $(firstword $(foreach c,$(call XstCoreLibraryChoices,$(call XstPathFromCore,$l),a),$(infox CECEL:$c)$(call HdlExists,$c)))));) \
  ) > $(XstIniFile);

XstOptions += $(and $(XstNeedLso),-lso $(XstLsoFile))
#endif
XstPrjFile=$(Core).prj
# old XstMakePrj=($(foreach f,$(HdlSources),echo verilog $(if $(filter $(WorkLibrarySources),$(f)),work,$(WorkLib)) '"$(call FindRelative,$(TargetDir),$(dir $(f)))/$(notdir $(f))"';)) > $(XstPrjFile);

VhdlSources    = ${strip ${filter %vhd, $(HdlSources)}}
VerilogSources = ${strip ${filter-out %vhd, $(HdlSources)}}
XstMakePrj=rm -f $(XstPrjFile); \
           $(if $(VerilogSources), ($(foreach f,$(VerilogSources), echo verilog $(if $(filter $(WorkLibrarySources),$(f)),work,$(WorkLib)) '"$(call FindRelative,$(TargetDir),$(dir $(f)))/$(notdir $(f))"';)) >>  $(XstPrjFile);, ) \
           $(if $(VhdlSources),    ($(foreach f,$(VhdlSources),    echo vhdl    $(if $(filter $(WorkLibrarySources),$(f)),work,$(WorkLib)) '"$(call FindRelative,$(TargetDir),$(dir $(f)))/$(notdir $(f))"';)) >> $(XstPrjFile);, )
XstScrFile=$(Core).scr

XstMakeScr=(echo set -xsthdpdir . $(and $(XstNeedIni),-xsthdpini $(XstIniFile));\
            echo run $(XstParams) $(strip $(XstOptions))) > $(XstScrFile);
# The options we directly specify
#$(info TARGETDIR: $(TargetDir))
# $(and $(findstring worker,$(HdlMode)),-work_lib work) 
# $(and $(findstring worker,$(HdlMode)),-work_lib $(call ToLower,$(Worker))) 
# -p $(strip \
      $(foreach t,$(or $(HdlExactPart),$(HdlTarget)),\
        $(if $(findstring $t,$(HdlAllFamilies)),\
           $(firstword $(HdlTargets_$(t))),$t))) \

# -ifn $(XstPrjFile) -ofn $(Core).ngc -top $(Top)

# Here we remove '_ise' from target names (e.g. zynq_ise)
# We also remove '_ise_alias' from target parts (e.g. xc7z020_ise_alias).
# These suffixes are used to redirect zynq/xc7z020 to the XST tool, but they
# need to be stripped off now so that the 'Real' target/part can be passed 
# to the tool.
HdlTargetReal=$(firstword $(subst _ise,,$(HdlTarget)))
HdlExactPartReal=$(subst _ise_alias,,$(HdlExactPart))

XstCoreSearchList=\
  $(call Unique, \
     $(foreach l,$(CDKComponentLibraries),$(strip \
       $(call FindRelative,$(TargetDir),\
         $(l)/hdl/$(call XstLibRef,$(LibName),$(HdlTarget)))))\
     $(foreach l,$(CDKDeviceLibraries),$(strip \
       $(call FindRelative,$(TargetDir),\
         $(l)/hdl/$(call XstLibRef,$(LibName),$(HdlTarget)))))\
     $(and $(filter $(HdlMode),assembly config container),\
     $(foreach l,$(call HdlTargetComponentLibraries,$(HdlTarget),XST),$(strip \
       $(call FindRelative,$(TargetDir),$l)))) \
     $(foreach l,$(DeviceLibraries),$(strip \
       $(call FindRelative,$(TargetDir),\
         $(l)/lib/hdl/$(call XstLibRef,$(LibName),$(HdlTarget)))))\
     $(foreach c,$(XstCores),$(infox XST:$c)$(call FindRelative,$(TargetDir),$(dir $(call HdlCoreRef,$c,$(HdlTarget)))))\
     $(and $(findstring platform,$(HdlMode)),..) \
  )

XstOptions +=\
 -ifn $(XstPrjFile) -ofn $(Core).ngc -work_lib $(WorkLib) -top $(Top) \
 -p $(or $(and $(HdlExactPart),$(foreach p,$(HdlExactPartReal),$(word 1,$(subst -, ,$p))-$(word 3,$(subst -, ,$p))-$(word 2,$(subst -, ,$p)))),$(HdlTargetReal))\
 $(and $(VerilogIncludeDirs),$(strip\
   -vlgincdir { \
     $(foreach d,$(VerilogIncludeDirs),$(call FindRelative,$(TargetDir),$(d))) \
    })) \
  $(and $(CDKComponentLibraries)$(CDKDeviceLibraries)$(ComponentLibraries)$(DeviceLibraries)$(XstCores)$(PlatformCores),-sd { $(XstCoreSearchList) })

XstNgdOptions=$(foreach c,$(XstCoreSearchList),-sd $c )

#     $(foreach c,$(XstCores),$(infox XNO:$c)-sd $(call FindRelative,$(TargetDir),$(dir $(call HdlCoreRef,$c,$(HdlTarget)))))

ifneq (,)
# ???
  $(foreach l,$(CDKComponentLibraries), -sd \
    $(call FindRelative,$(TargetDir),$(l)/hdl/$(or $(HdlPart),$(HdlTarget))))\
  $(foreach l,$(CDKDeviceLibraries), -sd \
    $(call FindRelative,$(TargetDir),$(l)/hdl/$(or $(HdlPart),$(HdlTarget))))\
  $(foreach l,$(ComponentLibraries), -sd \
    $(call FindRelative,$(TargetDir),$(l)/hdl/$(or $(HdlPart),$(HdlTarget))))\
  $(foreach l,$(DeviceLibraries), -sd \
    $(call FindRelative,$(TargetDir),$(l)/lib/hdl/$(or $(HdlPart),$(HdlTarget))))\
  $(foreach c,$(XstCores), -sd \
    $(call FindRelative,$(TargetDir),$(dir $(call HdlCoreRef,$c,$(HdlTarget)))))
endif
#$(info lib=$(HdlLibrariesInternal)= cores=$(XstCores)= Comps=$(ComponentLibraries)= td=$(TargetDir)= @=$(@))

HdlToolCompile=\
  $(foreach l,$(XstLibraries),\
     $(if $(wildcard $(call HdlLibraryRefDir,$(l),$(HdlTarget),,X5)),,\
          $(error Error: Specified library: "$l", in the "HdlLibraries" variable, was not found for $(call HdlGetFamily,$(HdlTarget)).))) \
  $(foreach l,$(XstCores),$(infox AC:$l)\
    $(if $(foreach x,$(call XstCoreLibraryChoices,$l,b),$(call HdlExists,$x)),,\
	$(info Error: Specified core library for "$l", in the "Cores" variable, was not found.) \
        $(error Error:   after looking in $(call HdlExists,$(call XstCoreLibraryChoices,$l,c))))) \
  $(infox ALLCORE1) \
  echo '  'Creating $@ with top == $(Top)\; details in $(TargetDir)/xst-$(Core).out.;\
  rm -f $(notdir $@);\
  $(XstMakeGenerics)\
  $(XstMakePrj)\
  $(and $(XstNeedLso),$(XstMakeLso))\
  $(and $(XstNeedIni),$(XstMakeIni))\
  $(XstMakeScr)\
  $(call OcpiXilinxIseInit); xst -ifn $(XstScrFile) && touch $(WorkLib)\
  $(and $(PlatformCores), && mv $(Core).ngc temp.ngc && ngcbuild -sd .. temp.ngc $(Core).ngc)

#  $(call OcpiXilinxIseInit); xst -ifn $(XstScrFile) && touch $(LibName) \
# optional creation of these doesn't work...
#    $(XstMakeLso) $(XstMakeIni))\

# We can't trust xst's exit code so we conservatively check for zero errors
# Plus we create the edif all the time...
HdlToolPost=\
  if grep -q 'Number of errors   :    0 ' $(HdlLog); then \
    ($(call OcpiXilinxIseInit); ngc2edif -log ngc2edif-$(Core).log -w $(Core).ngc) >> $(HdlLog) 2>&1 ; \
    HdlExit=0; \
  else \
    HdlExit=1; \
  fi;

#    mv $(Core).ngc temp.ngc; \
#    echo doing: ngcbuild -verbose $(XstNgcOptions) temp.ngc $(Core).ngc >> xst-$(Core).out; \
#    ngcbuild -verbose $(XstNgcOptions) temp.ngc $(Core).ngc >> xst-$(Core).out; \

# in case we need to run ngcbuild after xst
#    echo ngcbuild $(XstNgcOptions) temp.ngc $(Core).ngc; \
#    echo ngcbuild -verbose $(XstNgcOptions) temp.ngc $(Core).ngc; \
#
################################################################################
# Generate the per-platform files into platform-specific target dirs
XilinxAfter=set +e;grep -i error $1.out|grep -v '^WARNING:'|grep -i -v '[_a-z]error'; \
	     if grep -q $2 $1.out; then \
	       echo Time: `cat $1.time` at `date +%T`; \
	       exit 0; \
	     else \
	       exit 1; \
	     fi
# $(call DoXilinx,<tool>,<target-dir>,<
# Use default pattern to find error string in tool output
DoXilinx=$(call DoXilinxPat,$1,$2,$3,'Number of error.*s: *0')
DoXilinxPat=\
	echo " "Details in $1.out; cd $2; $(call OcpiXilinxIseInit,$1.out);\
	echo Command: $1 $3 >> $1.out; \
	/usr/bin/time -f %E -o $1.time bash -c "$1 $3; RC=\$$$$?; $(ECHO) Exit status: \$$$$RC; $(ECHO) \$$$$RC > $1.status" >> $1.out 2>&1;\
	(echo -n Elapsed time:; tr -d '\n' <$1.time; echo -n ', completed at '; date +%T) >> $1.out; \
	$(call XilinxAfter,$1,$4)
#AppBaseName=$(PlatformDir)/$(Worker)-$(HdlPlatform)
PromName=$1/$2.mcs
BitName=$1/$2$(and $(filter-out 0,$3),_$3).bit
BitFile_xst=$1.bit
# FIXME: allow for multiple container mappings, possible platform-specific, possibly not
NgdName=$1/$2.ngd
NgcName=$1/$2.ngc
MapName=$1/$2-map.ncd
ParName=$1/$2-par.ncd
TrceName=$1/$2.twr
ChipScopeName=$1/$2-csi.ngc
PcfName=$1/$2.pcf
#TopNgcName=$(HdlPlatformsDir)/$1/target-$(call HdlGetPart,$1)/$1.ngc

# We strip off '_ise_alias' from target parts (e.g. xc7z020_ise_alias-1-clg484).
# This suffix is used to redirect xc7z020 to the XST tool, but they
# need to be stripped off now so that the 'Real' part can be passed 
# to the tool.
HdlPartReal=$(subst _ise_alias,,$(HdlPart_$1))

OcpiXstTrceOptions=-v 200 -fastpaths
export OcpiXstMapOptionsDefault=-detail -w -logic_opt on -xe c -mt 4 -register_duplication on -global_opt off -ir off -pr off -lc off -power off
export OcpiXstParOptionsDefault=-mt 4 -w -xe n
# $(call HdlToolDoPlatform,1:<target-dir>,2:<app-name>,3:<app-core-name>,4:<pfconfig>,5:<platform-name>,6: paramconfig)

# The constraint file(s) to use, first/only arg is platform
HdlConstraintsSuffix_xst=.ucf
XstConstraints_default=$(HdlPlatformDir_$1)/$1$(HdlConstraintsSuffix_xst)
XstConstraints=$(or $(HdlConstraints),$(XstConstraints_default))

define HdlToolDoPlatform_xst

# This dependency is required, since without it, ngdbuild can fail
# I.e. the input container ngc depends on it in some obscure way.
$(call NgcName,$1,$3): $(call XstConstraints,$5)
# Convert ngc to ngd (we don't do merging here)
$(call NgdName,$1,$3): $(call NgcName,$1,$3) $(call XstConstraints,$5)
	$(AT)echo -n For $2 on $5 using config $4: creating merged NGC file using '"ngcbuild"'.
	$(AT)$(call DoXilinx,ngcbuild,$1,\
	        -verbose \
		$$(XstNgdOptions) $3.ngc $3-b.ngc)
	$(AT)echo -n "    " Creating EDF textual netlist file using ngc2edif." "
	$(AT)$(call DoXilinxPat,ngc2edif,$1,-w $3-b.ngc,'ngc2edif: Total memory usage is')
	$(AT)echo -n For $2 on $5 using config $4: creating NGD '(Xilinx Native Generic Database)' file using '"ngdbuild"'.
	$(AT)rm -f $$@
	$(AT)$(call DoXilinx,ngdbuild,$1,\
	        -verbose $(foreach u,$(call XstConstraints,$5),-uc $(call AdjustRelative,$u)) \
                -p $(call HdlPartReal,$5) \
		$$(XstNgdOptions) $3-b.ngc $3.ngd)

# Map to physical elements
$(call MapName,$1,$3): $(call NgdName,$1,$3)
	$(AT)echo -n For $2 on $5 using config $4: creating mapped NCD '(Native Circuit Description)' file using '"map"'.
	$(AT)$(call DoXilinx,map,$1,-p $(call HdlPartReal,$5) $(if $(filter undefined,$(origin OcpiXstMapOptions)),$(OcpiXstMapOptionsDefault),$(OcpiXstMapOptions)) -t $(or $(OCPI_PAR_SEED),1) -o $(notdir $(call MapName,$1,$3)) \
	                         $(notdir $(call NgdName,$1,$3)) $(notdir $(call PcfName,$1,$3)))

# Place-and-route, and generate timing report
$(call ParName,$1,$3): $(call MapName,$1,$3) $(call PcfName,$1,$3)
	$(AT)echo -n For $2 on $5 using config $4: creating PAR\'d NCD file using '"par"'.
	$(AT)$(call DoXilinx,par,$1,$(if $(filter undefined,$(origin OcpiXstParOptions)),$(OcpiXstParOptionsDefault),$(OcpiXstParOptions)) $(notdir $(call MapName,$1,$3)) \
		$(notdir $(call ParName,$1,$3)) $(notdir $(call PcfName,$1,$3)))

$(call TrceName,$1,$3): $(call ParName,$1,$3)
	$(AT)echo -n Generating timing report '(TWR)' for $2 on $5 using $4 using '"trce"'.
	$(AT)-$(call DoXilinx,trce,$1,$(OcpiXstTrceOptions) -xml fpgaTop.twx \
		-o $$(notdir $$@) \
		$(notdir $(call ParName,$1,$3)) $(notdir $(call PcfName,$1,$3)))

# Generate bitstream
# using: '-intstyle ise" makes a nice option table, but also causes the return code to be "1",
# rather than zero.

$(call BitName,$1,$3,$6): $(call ParName,$1,$3) $(call PcfName,$1,$3) $(call TrceName,$1,$3)
	$(AT)echo -n For $2 on $5 using config $4: Generating Xilinx bitstream file $$@.
	$(AT)$(if $(wildcard $(HdlPlatformDir_$5)/$5.ut),,\
                $(error File $(HdlPlatformDir_$5)/$5.ut is required, but missing.))\
	     $(call DoXilinxPat,bitgen,$1,\
		-f $$(call FindRelative,$1,$(HdlPlatformDir_$5)/$5.ut) \
                $(notdir $(call ParName,$1,$3)) $(notdir $(call BitName,$1,$3,$6)) \
		$(notdir $(call PcfName,$1,$3)), 'DRC detected 0 errors')

ifdef HdlPromArgs_$5
$(call PromName,$1,$3): $(call BitName,$1,$3,$6)
	$(AT)echo -n For $2 on $5 using config $4: Generating PROM file $$@.
	$(AT)$(call DoXilinxPat,promgen,$1, -w -p mcs -c FF $$(HdlPromArgs_$5) $(notdir $(call BitName,$1,$3,$6)),'.*')

all: $(call PromName,$1,$3)
endif
endef
ifneq (,)

Notes:
Indirect cores do not need BB libraries, only direct cores.
But -sd do need all cores.
So even though the cores are not "merged", they are remembered enough to not require bb libs.
When we build an assembly, we can use the component library's stub library and single directory to find the cores.  Thus we never need to point at individual cores.

endif
endif
