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
package require fileutil

set ip_name [lindex $argv 0]
set clock_prim [string toupper [lindex $argv 1]]
set ip_module [lindex $argv 2]
set ip_part [lindex $argv 3]

proc is_ip_file_hw {current_file} {
    global ip_module
    return [string match ${ip_module}_clk_wiz.v $current_file]
}

create_project managed_ip_project managed_ip_project -ip -force -part $ip_part
# Get latest version
create_ip -name $ip_name -vendor xilinx.com -library ip -module_name $ip_module
set ip_dir managed_ip_project/managed_ip_project.srcs/sources_1/ip/$ip_module
set_property -dict [list CONFIG.PRIMITIVE $clock_prim] [get_ips $ip_module]
generate_target all [get_files $ip_dir/$ip_module.xci]
create_ip_run [get_files -of_objects [get_fileset sources_1] $ip_dir/$ip_module.xci]

# Find the generated IP
set ip_hw  [fileutil::find [pwd] is_ip_file_hw]
set ip_src_dir [string trim $ip_hw ${ip_module}_clk_wiz.v]

file copy -force $ip_hw ../${ip_module}.v
