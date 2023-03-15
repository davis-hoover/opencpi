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

include $(OCPI_CDK_DIR)/include/hdl/xilinx.mk
HdlLibraries=ocpi axi cdc
OnlyTargets=zynq_ultra
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk
XilinxCoreName=usp_rf_data_converter
ifeq ($(filter clean%,$(MAKECMDGOALS))$(if $(HdlTargets),,z),)  # if not cleaning and building hdl target
  $(info Generating the verilog wrapper for the Xilinx RF Data Converter.)
  $(if $(call DoShell,\
      mkdir -p gen && cd gen && rm -r -f tmp && mkdir tmp && \
      (cd tmp && \
      $(call OcpiXilinxVivadoInit) && \
      vivado -mode batch -source ../../vivado-gen-rfdc.tcl \
      -tclargs $(XilinxCoreName) xczu48dr-ffvg1517-2-e \
      ) > vivado-gen-rfdc.log && \
      rm -r -f tmp,MyError),\
      $(error $(MyError)))
endif # if not cleaning
SourceFiles=rfdc_pkg.vhd rfdc.vhd $(wildcard gen/*.edf)
include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
