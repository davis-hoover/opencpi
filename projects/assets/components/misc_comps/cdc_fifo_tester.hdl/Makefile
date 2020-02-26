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

# "xilinx" covers xsim, zynq, etc.
OnlyTargets=xilinx

# For vivado we use vivado stubs with netlists
# For xsim we use simulation netlists
SourceFiles=\
  gen_clk.vhd \
	mmcm_100_to_100_50_and_25_top.vhd \
	$(if $(filter vivado,$(HdlToolSet)),\
      ./xilinx_ip/mmcm_100_to_100_50_and_25.v,\
  $(if $(filter xsim,$(HdlToolSet)),\
      ./xilinx_ip/mmcm_100_to_100_50_and_25_sim_netlist.vhd,\
	$(if $(filter isim xst,$(HdlToolSet)),\
	  	./xilinx_ip/mmcm_100_to_100_50_and_25_ise.vhd)))

include $(OCPI_CDK_DIR)/include/worker.mk
