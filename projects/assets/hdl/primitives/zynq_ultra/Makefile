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

# This Makefile is for the primitive library: zynq_ultra

# Remember two rules for OpenCPI primitive libraries, in order to be usable with all tools:
# 1. Any entity (VHDL) or module (verilog) must have a VHDL component declaration in zynq_ultra_pkg.vhd
# 2. Entities or modules to be used from outside the library must have the file name
#    be the same as the entity/module name, and one entity/module per file.

################################################################################
# See the READMEfor more information regarding the source files listed below
include $(OCPI_CDK_DIR)/include/hdl/xilinx.mk # for OcpiXilinxVivadoInit
include $(OCPI_CDK_DIR)/include/util.mk       # for DoShell below
OnlyTargets=zynq_ultra xsim
HdlLibraries=fixed_float ocpi axi sdp platform

SourceFiles=zynq_ultra_pkg.vhd gen/$(WrapperModule).v zynq_ultra_ps.cpp_vhd
OcpiCPPDefines=PS8_WRAPPER_MODULE=$(WrapperModule)

# The TCL script that gets the wrapper verilog code also determines the version and module name.
# Since this determines the file name of the wrapper code, we do it here on the first pass of make
# so the "SourceFiles" to build includes the module whose name is determined by the tcl.
# It actually depends on the tcl script (which is in ../zynq) and of course the particular
# version of Vivado installed. If either of those changes a clean build here is required.
ifeq ($(filter clean%,$(MAKECMDGOALS)),) # if not cleaning
  ifeq ($(wildcard gen/wrapper-module),) # if wrapper-module not determined yet
    $(info Generating the verilog wrapper for the Zynq Ultra PS (PS8 primitive).)
    $(and $(call DoShell,\
             mkdir -p gen && cd gen && rm -r -f tmp && mkdir tmp && \
             (cd tmp && \
               $(call OcpiXilinxVivadoInit) && \
               vivado -mode batch -source ../../../zynq/vivado-gen-ps.tcl \
                      -tclargs zynq_ultra_ps_e xczu7ev-ffvc1156-2-e \
             ) > vivado-gen-ps8.log && \
             rm -r -f tmp,MyError),\
      $(shell rm -f gen/wrapper-module)$(error $(MyError)))
  endif # if need to get the wrapper
  WrapperModule:=$(shell cat gen/wrapper-module)
  $(info The Zynq Ultra PS wrapper module name is: $(WrapperModule))
endif # if not cleaning

$(info SOURCE:$(SourceFiles))
include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
