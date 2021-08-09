# This file is protected by Copyright. Please refer to the COPYRIGHT file
# # distributed with this source distribution.
# #
# # This file is part of OpenCPI <http://www.opencpi.org>
# #
# # OpenCPI is free software: you can redistribute it and/or modify it under the
# # terms of the GNU Lesser General Public License as published by the Free
# # Software Foundation, either version 3 of the License, or (at your option) any
# # later version.
# #
# # OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# # WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# # A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# # details.
# #
# # You should have received a copy of the GNU Lesser General Public License along
# # with this program. If not, see <http://www.gnu.org/licenses/>.
# ##
# Description - The generic_pcie primitive currently supports the following FPGA toolsets:
#   <- Vivado 2019.2 
#   <- Vivado 2020.2
#
#   Although each toolset may have different directory structures for the generated IP, this script
# takes these difference into account by querying the installed version and setting the search paths 
# accordingly.   
#
#   Vivado 2019.2 and 2020.2 have different directory structures when generating the PCIe IP:
#   * 2020.2 - The files are split between managed_ip_project.srcs, and manageded_ip_project.gen
#   * 2019.2 - All files are under managed_ip_project.srcs
#   
# ##
package require fileutil

set ip_name [lindex $argv 0]
set ip_part [lindex $argv 1]
set ip_module ${ip_name}_0
# Testing data width conversion (dwidth IP)
set dwidth_ip_name axi_dwidth_converter
set dwidth_ip_module ${dwidth_ip_name}_0

proc copy_sources {directory pattern} {
   # Find files in the specified directory
   set file_set [fileutil::findByPattern $directory -regexp $pattern]

   # Copy matching file set to gen directory
   file copy -force $file_set ../
}

# Create project for generating the IP
create_project  managed_ip_project managed_ip_project -ip -force -part $ip_part 
#Get latest version
create_ip -name $ip_name -vendor xilinx.com -library ip -module_name $ip_module
create_ip -name $dwidth_ip_name -vendor xilinx.com -library ip -module_name $dwidth_ip_module
set ip [get_ips $ip_module]
set ip_minor [get_property CORE_REVISION $ip]
set ip_major [regsub {\.} [regsub {.*:} [get_property IPDEF $ip] ""] "_"]
puts "ip_name:$ip_name ip_part:$ip_part ip_module:$ip_module ip_major:$ip_major ip_minor:$ip_minor"

set dwidth_ip [get_ips $dwidth_ip_module]
set dwidth_ip_minor [get_property CORE_REVISION $dwidth_ip]
set dwidth_ip_major [regsub {\.} [regsub {.*:} [get_property IPDEF $dwidth_ip] ""] "_"]
puts "ip_name:$dwidth_ip_name ip_part:$ip_part ip_module:$dwidth_ip_module ip_major:$dwidth_ip_major ip_minor:$dwidth_ip_minor"

set ip_version $ip_major
set ip_dir managed_ip_project/managed_ip_project.srcs/sources_1/ip/$ip_module
set gen_dir managed_ip_project/managed_ip_project.gen/sources_1/ip/$ip_module

set dwidth_ip_dir managed_ip_project/managed_ip_project.srcs/sources_1/ip/$dwidth_ip_module
set dwidth_gen_dir managed_ip_project/managed_ip_project.gen/sources_1/ip/$dwidth_ip_module

# Set the properties associated with the generated core
# NOTE: These parameters are deliberately set static to match the PicoEVB (artix7) test HDL platform.  Additional work will be done to either:
# 1) Have the set of parameters come in as arguments?
# 2) Use some sort of lookup table and derive the appropriate parameters based on the target/platform/etc?
# 3) Some other brilliant idea TBD?
set_property -dict [list CONFIG.DEVICE_ID {0x7021} \
                        CONFIG.REV_ID {0x00} \
                        CONFIG.VENDOR_ID {0x1DF7} \
                        CONFIG.SUBSYSTEM_VENDOR_ID {0x1DF7} \
                        CONFIG.SUBSYSTEM_ID {0x0040} \
                        CONFIG.CLASS_CODE {0x0B4000} \
                        CONFIG.BAR1_ENABLED {true} \
                        CONFIG.MAX_LINK_SPEED {5.0_GT/s} \
                        CONFIG.BASEADDR {0x0} \
                        CONFIG.HIGHADDR {0xFFFFFFFF} \
                        CONFIG.BAR0_SIZE {64} \
                        CONFIG.BAR1_SIZE {256} \
                        CONFIG.BAR0_SCALE {Megabytes} \
                        CONFIG.BAR1_SCALE {Kilobytes} \
                        CONFIG.BAR_64BIT {false} \
                        CONFIG.S_AXI_ID_WIDTH {6} \
                        CONFIG.AXIBAR_NUM {2} \
                        CONFIG.AXIBAR_AS_0 {false} \
                        CONFIG.AXIBAR_0 {0x0} \
                        CONFIG.AXIBAR2PCIEBAR_0 {0xF0000000} \
                        CONFIG.AXIBAR_HIGHADDR_0 {0xF3FFFFFF} \
                        CONFIG.AXIBAR_AS_1 {false} \
                        CONFIG.AXIBAR_1 {0x0} \
                        CONFIG.AXIBAR2PCIEBAR_1 {0xF4000000} \
                        CONFIG.AXIBAR_HIGHADDR_1 {0xF403FFFF}] \
                        [get_ips $ip_module]

set_property -dict [list CONFIG.SI_DATA_WIDTH {64} \
                        CONFIG.MI_DATA_WIDTH {32} \
                        CONFIG.SI_ID_WIDTH {6} \
                        CONFIG.FIFO_MODE {0} \
                        CONFIG.ACLK_RATIO {1:2} \
                        CONFIG.ACLK_ASYNC {0}] \
                        [get_ips $dwidth_ip_module]

# Create IP variation
generate_target all [get_files $ip_dir/$ip_module.xci ] 
generate_target all [get_files $dwidth_ip_dir/$dwidth_ip_module.xci ] 

create_ip_run [get_files -of_objects [get_fileset sources_1] $ip_dir/$ip_module.xci]
launch_runs ${ip_module}_synth_1 -jobs 8
wait_on_run ${ip_module}_synth_1

create_ip_run [get_files -of_objects [get_fileset sources_1] $dwidth_ip_dir/$dwidth_ip_module.xci]
launch_runs ${dwidth_ip_module}_synth_1 -jobs 8
wait_on_run ${dwidth_ip_module}_synth_1

# #############################################################
# Synthesis must be run at this step to enable netlist generation   
open_run ${ip_module}_synth_1 -name ${ip_module}_synth_1

if {[version -short] >= "2020.2"} {

   # Copy timing constraints file
   copy_sources $gen_dir/${ip_module}/source xdc

   # Copy IP variation stub
   copy_sources $gen_dir stub.vhdl

   # Copy IP variation file
   copy_sources $ip_dir xci

} else {

   # Copy timing constraints file
   copy_sources $ip_dir/${ip_module}/source xdc

   # Copy IP variation stub
   copy_sources $ip_dir stub.vhdl

   # Copy IP variation file
   copy_sources $ip_dir xci

}

# Write IP stub netlist
write_edif -security_mode all ../$ip_module.edf
write_vhdl -mode synth_stub $ip_dir/${ip_module}_stub.vhdl -force

# #############################################################
# Synthesis must be run at this step to enable netlist generation   
open_run ${dwidth_ip_module}_synth_1 -name ${dwidth_ip_module}_synth_1

if {[version -short] >= "2020.2"} {

   # Copy IP variation stub
   copy_sources $dwidth_gen_dir stub.vhdl

   # Copy IP variation file
   copy_sources $dwidth_ip_dir xci

} else {

   # Copy IP variation stub
   copy_sources $dwidth_ip_dir stub.vhdl

   # Copy IP variation file
   copy_sources $dwidth_ip_dir xci

}

# Write IP stub netlist
write_edif -security_mode all ../$dwidth_ip_module.edf
write_vhdl -mode synth_stub $dwidth_ip_dir/${ip_module}_stub.vhdl -force

