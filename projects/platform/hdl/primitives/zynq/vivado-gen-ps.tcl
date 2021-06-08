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
package require fileutil

set ip_name [lindex $argv 0]
set ip_part [lindex $argv 1]
set ip_module ${ip_name}_0

proc copy_file {file dest} {
    puts "COPYING $file to $dest"
    if {[file exists $file]} {
        puts "FILE $file exists"
	file copy $file $dest
        return 1
    }
    puts "FILE $file does not exist"
    return 0
}

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
set gen_dir managed_ip_project/managed_ip_project.gen/sources_1/ip/$ip_module
set ip_dir managed_ip_project/managed_ip_project.srcs/sources_1/ip/$ip_module
generate_target all [get_files $ip_dir/$ip_module.xci]
set ip_wrapper ${ip_name}_v${ip_version}_${ip_name}
puts "ip_version:$ip_version ip_wrapper:$ip_wrapper"
# This may be the file name (2020.2 at least)
set ip_maybe ${ip_name}_v${ip_version}
# Vivado 2020.2 has a different resulting directory structure when generating the IP
if {[version -short] >= "2020.2"} {
  set hdl_dir $gen_dir/hdl
} else {
  set hdl_dir $ip_dir/hdl
}
# This is pretty lame, but it is what is different between the PS7 IP and the PS8 ip
# and what is different across vivado versions
# Look both without the minor version and with the minor version
# And then look in three places:
# - in verilog subdir
# - not in verilog subdir with module name appended to file name
# - not in verilog subdir without module name appended to file name
if {[copy_file $hdl_dir/verilog/${ip_wrapper}.v ../]} { return }
if {[copy_file $hdl_dir/${ip_wrapper}.v ../]} { return }
if {[copy_file $hdl_dir/${ip_maybe}.v ../${ip_wrapper}.v]} { return }
# Try with minor version number appended
set ip_version ${ip_version}_${ip_minor}
set ip_wrapper ${ip_name}_v${ip_version}_${ip_name}
set ip_maybe ${ip_name}_v${ip_version}
if {[copy_file $hdl_dir/verilog/${ip_wrapper}.v ../]} { return }
if {[copy_file $hdl_dir/${ip_wrapper}.v ../]} { return }
if {[copy_file $hdl_dir/${ip_maybe}.v ../${ip_wrapper}.v]} { return }
puts "Could not file the IP wrapper file"
exit 1

}
