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

OnlyTargets=zynq xsim isim zynq_ise modelsim

# Param_CLK_IN_FREQUENCY_MHz=100.0
# Param_CLK_OUT_FREQUENCY_MHz=100.0
# Param_Clock_Primitive=mmcme2
# Param_Clock_Primitive=plle2
# Param_M=$(shell [ ! -f M.txt ] && ./calc_pll_factors.py $(Param_CLK_IN_FREQUENCY_MHz) $(Param_CLK_OUT_FREQUENCY_MHz) $(HdlTarget) $(Param_Clock_Primitive); cat M.txt)
# Param_N=$(shell cat N.txt)
# Param_O=$(shell cat O.txt)

include $(OCPI_CDK_DIR)/include/worker.mk

# .SILENT: display_info
# .PHONY: display_info
#
# clean::
# 	rm -rf info.txt M.txt N.txt O.txt
#
# display_info:
# 	cat info.txt
