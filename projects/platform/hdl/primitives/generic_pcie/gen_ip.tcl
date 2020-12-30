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

set ip_name [lindex $argv 0]
set ip_part [lindex $argv 1]
set ip_module ${ip_name}_0

# Create project for generating the IP
create_project  managed_ip_project managed_ip_project -ip -force -part $ip_part 
#Get latest version
create_ip -name $ip_name -vendor xilinx.com -library ip -module_name $ip_module
set ip [get_ips $ip_module]
set ip_minor [get_property CORE_REVISION $ip]
set ip_major [regsub {\.} [regsub {.*:} [get_property IPDEF $ip] ""] "_"]
puts "ip_name:$ip_name ip_part:$ip_part ip_module:$ip_module ip_major:$ip_major ip_minor:$ip_minor"
set ip_version $ip_major
set ip_dir managed_ip_project/managed_ip_project.srcs/sources_1/ip/$ip_module
# Set the properties associated with the generated core
# NOTE: These parameters are deliberately set static to match the PicoEVB (artix7) test HDL platform.  Additional work will be done to either:
# 1) Have the set of parameters come in as arguments?
# 2) Use some sort of lookup table and derive the appropriate parameters based on the target/platform/etc?
# 3) Some other brilliant idea TBD?
set_property -dict [list CONFIG.DEVICE_ID {0x4243} \
			CONFIG.REV_ID {0x02} \
			CONFIG.CLASS_CODE {0x050000} \
			CONFIG.BAR1_ENABLED {true} \
			CONFIG.BAR0_SCALE {Megabytes} \
			CONFIG.BAR1_SCALE {Megabytes} \
			CONFIG.BAR_64BIT {true} \
			CONFIG.AXIBAR_NUM {2} \
			CONFIG.AXIBAR_AS_0 {true} \
			CONFIG.AXIBAR_AS_1 {true} \
			CONFIG.BAR1_TYPE {Memory} \
			CONFIG.BAR0_SIZE {1} \
			CONFIG.BAR1_SIZE {1}] \
			[get_ips axi_pcie_0]
# With IP properties, generate the IP:
generate_target all [get_files $ip_dir/$ip_module.xci] 

# Generate the IP
create_ip_run [get_files -of_objects [get_fileset sources_1] $ip_dir/$ip_module.xci]
launch_runs ${ip_module}_synth_1
wait_on_run ${ip_module}_synth_1

# Copy the generated files to the appropriate directory location.  
# Note Copy will fail if the directory was not empty prior.
file copy -force $ip_dir ../

puts "Successfully generated and copied files!"
