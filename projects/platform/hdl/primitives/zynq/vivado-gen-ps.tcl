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

# This TCL script generates the verilog wrapper for the PS7 primitive, under Vivado.
# The ip_name is passed into this script as an argument.
# The generated Verilog "processor instantiator" is a highly parameterized wrapper
# instantiating the underlying PS7 primitive.  This wrapper does a variety of
# signal adaptations based on the parameters.
# The result of the script is that the wrapper verilog is copied to ".."
# And a file named wrapper-module is placed there with the name of the wrapper module
# which includes the version.


set ip_name [lindex $argv 0]
set ip_part [lindex $argv 1]
set ip_module ${ip_name}_0
# puts [llength [get_parts -regexp {xcz.*}]]
# puts [get_parts -regexp {xc7z.*}]
create_project managed_ip_project managed_ip_project -ip -force -part $ip_part
# Get latest version
create_ip -name $ip_name -vendor xilinx.com -library ip -module_name $ip_module
set ip [get_ips $ip_module]
set ip_minor [get_property CORE_REVISION $ip]
set ip_major [regsub {\.} [regsub {.*:} [get_property IPDEF $ip] ""] "_"]
puts "ip_name:$ip_name ip_part:$ip_part ip_module:$ip_module ip_major:$ip_major ip_minor:$ip_minor"
set ip_version $ip_major
set ip_dir managed_ip_project/managed_ip_project.srcs/sources_1/ip/$ip_module
generate_target all [get_files $ip_dir/$ip_module.xci]
set ip_wrapper ${ip_name}_v${ip_version}_${ip_name}
# This is pretty lame, but it is what is different between the PS7 IP and the PS8 ip...
# Look in two places (in verilog subdir or not), and look in two ways (with minor or not)
if {[file exists $ip_dir/hdl/verilog/${ip_wrapper}.v]} {
  file copy $ip_dir/hdl/verilog/${ip_wrapper}.v ..
} elseif {[file exists $ip_dir/hdl/${ip_wrapper}.v]} {
  file copy $ip_dir/hdl/${ip_name}_v${ip_version}.v ../${ip_wrapper}.v
} else {
  set ip_version ${ip_version}_${ip_minor}
  set ip_wrapper ${ip_name}_v${ip_version}_${ip_name}
  if {[file exists $ip_dir/hdl/verilog/${ip_wrapper}.v]} {
    file copy $ip_dir/hdl/verilog/${ip_wrapper}.v ..
  } else {
    # This will fail if we can't find it anywhere
    file copy $ip_dir/hdl/${ip_name}_v${ip_version}.v ../${ip_wrapper}.v
  }
}
