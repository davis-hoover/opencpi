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

$(if $(realpath $(OCPI_CDK_DIR)),,$(error The OCPI_CDK_DIR environment variable is not set correctly.))
Containers= \
	cnt_0rx_1tx_thruasm_fmcomms_2_3_lpc_LVDS_ml605 \
	cnt_nopfcfg_0rx_1tx_fmcomms_2_3_lpc_thruasm_zed \
	cnt_0rx_1tx_thruasm_matchstiq_z1 \
	cnt_0rx_1tx_thruasm_zipper_hpc_ml605 \
	cnt_0rx_1tx_thruasm_zipper_hsmc_a_alst4 \
	cnt_0rx_1tx_thruasm_zipper_hsmc_b_alst4 \
	cnt_0rx_1tx_thruasm_zipper_lpc_ml605 \
	cnt_0rx_1tx_thruasm_zipper_lpc_zed
# ML605/FMCOMMS3-FMC_HPC combo is currently known to have TX data fidelity issues
#	cnt_0rx_1tx_thruasm_fmcomms_2_3_hpc_LVDS_ml605

# we want default containers for the file_read/file_write sub-assy application tests
# DefaultContainers=
ExcludePlatforms=isim modelsim xsim
Libraries+=misc_prims util_prims dsp_prims comms_prims
include $(OCPI_CDK_DIR)/include/hdl/hdl-assembly.mk
