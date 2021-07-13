#!/bin/bash
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

# Edit soc_system.qip
sed -i '1s/^/set_global_assignment \-name SEARCH_PATH "..\/..\/..\/primitives\/lib\/cyclone5\/cyclone5\/"\n/' soc_system.qip
sed -i '1s/^/set_global_assignment \-name SEARCH_PATH "..\/..\/..\/..\/"\n# Assignments for adding libraries to search path\n/' soc_system.qip
sed -i '1s/^/set_global_assignment \-name SEARCH_PATH ".."\nset_global_assignment \-name SEARCH_PATH "..\/..\/"\nset_global_assignment \-name SEARCH_PATH "..\/..\/..\/"\n/' soc_system.qip
sed -i 's/^.*soc_system.sopcinfo.*$/set_global_assignment \-library "soc_system" \-name SOPCINFO_FILE "soc_system.sopcinfo"/' soc_system.qip
sed -i 's/^.*soc_system.qsys.*$/set_global_assignment \-library "soc_system" \-name MISC_FILE "soc_system.qsys"/' soc_system.qip
sed -i 's/^.*soc_system.vhd.*$/#set_global_assignment \-library "soc_system" \-name VHDL_FILE "soc_system.vhd"/' soc_system.qip
sed -i 's/^.*soc_system_hps_0.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "soc_system_hps_0.v"/' soc_system.qip
sed -i 's/^.*soc_system_hps_0_hps_io.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "soc_system_hps_0_hps_io.v"/' soc_system.qip
sed -i 's/^.*hps_sdram.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_pll.sv.*$/set_global_assignment \-library "soc_system" \-name SYSTEMVERILOG_FILE "hps_sdram_pll.sv"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_clock_pair_generator.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_clock_pair_generator.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_acv_hard_addr_cmd_pads.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_acv_hard_addr_cmd_pads.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_acv_hard_memphy.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_acv_hard_memphy.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_acv_ldc.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_acv_ldc.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_acv_hard_io_pads.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_acv_hard_io_pads.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_generic_ddio.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_generic_ddio.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_reset.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_reset.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_reset_sync.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_reset_sync.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_phy_csr.sv.*$/set_global_assignment \-library "soc_system" \-name SYSTEMVERILOG_FILE "hps_sdram_p0_phy_csr.sv"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_iss_probe.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_iss_probe.v"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0.sv.*$/set_global_assignment \-library "soc_system" \-name SYSTEMVERILOG_FILE "hps_sdram_p0.sv"/' soc_system.qip
sed -i 's/^.*hps_sdram_p0_altdqdqs.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "hps_sdram_p0_altdqdqs.v"/' soc_system.qip
sed -i 's/^.*altdq_dqs2_acv_connect_to_hard_phy_cyclonev.sv.*$/set_global_assignment \-library "soc_system" \-name SYSTEMVERILOG_FILE "altdq_dqs2_acv_connect_to_hard_phy_cyclonev.sv"/' soc_system.qip
sed -i 's/^.*altera_mem_if_hhp_qseq_synth_top.v.*$/set_global_assignment \-library "soc_system" \-name VERILOG_FILE "altera_mem_if_hhp_qseq_synth_top.v"/' soc_system.qip
sed -i 's/^.*hps_AC_ROM.hex.*$/set_global_assignment \-library "soc_system" \-name SOURCE_FILE "hps_AC_ROM.hex"/' soc_system.qip
sed -i 's/^.*hps_inst_ROM.hex.*$/set_global_assignment \-library "soc_system" \-name SOURCE_FILE "hps_inst_ROM.hex"/' soc_system.qip
sed -i 's/^.*altera_mem_if_hard_memory_controller_top_cyclonev.sv.*$/set_global_assignment \-library "soc_system" \-name SYSTEMVERILOG_FILE "altera_mem_if_hard_memory_controller_top_cyclonev.sv"/' soc_system.qip
sed -i 's/^.*altera_mem_if_oct_cyclonev.sv.*$/set_global_assignment \-library "soc_system" \-name SYSTEMVERILOG_FILE "altera_mem_if_oct_cyclonev.sv"/' soc_system.qip
sed -i 's/^.*altera_mem_if_dll_cyclonev.sv.*$/set_global_assignment \-library "soc_system" \-name SYSTEMVERILOG_FILE "altera_mem_if_dll_cyclonev.sv"/' soc_system.qip
sed -i 's/^.*soc_system_hps_0_hps_io_border.sv.*$/set_global_assignment \-library "soc_system" \-name SYSTEMVERILOG_FILE "soc_system_hps_0_hps_io_border.sv"/' soc_system.qip
sed -i 's/^.*soc_system_hps_0_fpga_interfaces.sv.*$/set_global_assignment \-library "soc_system" \-name SYSTEMVERILOG_FILE "soc_system_hps_0_fpga_interfaces.sv"/' soc_system.qip

# Edit soc_system.qsf
sed -i 's/^.*5CSXFC6D6F31C6.*$/set_global_assignment \-name DEVICE 5CSXFC6D6F31C8ES/' soc_system.qsf
sed -i 's/^.*TOP_LEVEL_ENTITY ghrd_top.*$/#set_global_assignment \-name TOP_LEVEL_ENTITY ghrd_top/' soc_system.qsf
sed -i 's/^.*soc_system.qip.*$/set_global_assignment \-name QIP_FILE soc_system.qip/' soc_system.qsf
sed -i 's/^.*hps_reset.qip.*$/#set_global_assignment \-name QIP_FILE ip\/altsource_probe\/hps_reset.qip/' soc_system.qsf
sed -i 's/^.*altera_edge_detector.v.*$/#set_global_assignment \-name VERILOG_FILE ip\/edge_detect\/altera_edge_detector.v/' soc_system.qsf
sed -i 's/^.*debounce.v.*$/#set_global_assignment \-name VERILOG_FILE ip\/edge_detect\/altera_edge_detector.v/' soc_system.qsf
sed -i 's/^.*ghrd_top.v.*$/#set_global_assignment \-name VERILOG_FILE ip\/edge_detect\/altera_edge_detector.v/' soc_system.qsf
sed -i 's/^.*soc_system_timing.sdc.*$/set_global_assignment \-name SDC_FILE ..\/cyclone5_sockit.sdc/' soc_system.qsf
sed -i 's/^.*USE_SIGNALTAP_FILE cti_tapping.stp.*$/#set_global_assignment \-name USE_SIGNALTAP_FILE cti_tapping.stp/' soc_system.qsf
sed -i 's/^.*SIGNALTAP_FILE cti_tapping.stp.*$/#set_global_assignment \-name SIGNALTAP_FILE cti_tapping.stp/' soc_system.qsf

# Edit soc_system.sopcinfo
sed -i -e 's:5CSXFC6D6F31C6:5CSXFC6D6F31C8ES:g' soc_system.sopcinfo
sed -i -e 's:6_H6:8_H6:g' soc_system.sopcinfo