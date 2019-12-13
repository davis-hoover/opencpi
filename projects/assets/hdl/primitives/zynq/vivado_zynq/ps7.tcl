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
#
# arg 0: Value to be passed to:
#        Vivado create_ip tcl command: version parameter (for
#        processing_system_7), e.g. 5.5
# arg 1: Value to be passed to:
#        Vivado create_ip tcl command: module_name parameter (for
#        processing_system_7)
# arg 2: Value to be passed to:
#        Vivado set_property tcl command:
#        -dict parameter's CONFIG.PCW_SPI0_PERIPHERAL_ENABLE name's value
#
# Example usage:
# vivado -mode batch -source ps7.tcl -tclargs 5.5 processing_system7_0 0
set ip_version [lindex $argv 0]
set ip_module_name [lindex $argv 1]
set pcw_spi0_peripheral_enable [lindex $argv 2]
set ip_name processing_system7

puts "Generating wrapper verilog file for IP w/ name: $ip_name, version: $ip_version, module_name: $ip_module_name"
create_project managed_ip_project managed_ip_project -part xc7z020-clg484-1 -ip -force

create_ip -name $ip_name -vendor xilinx.com -library ip -version $ip_version -module_name $ip_module_name

puts "[get_ips $ip_module_name]"
set_property -dict [list CONFIG.PCW_SPI0_PERIPHERAL_ENABLE $pcw_spi0_peripheral_enable] [get_ips $ip_module_name]

generate_target all [get_files  managed_ip_project/managed_ip_project.srcs/sources_1/ip/$ip_module_name/$ip_module_name.xci]
