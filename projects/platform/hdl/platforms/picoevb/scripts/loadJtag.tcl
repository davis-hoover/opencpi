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
set Path [lindex $argv 0]

open_hw_manager
connect_hw_server
open_hw_target -xvc_url localhost:2542

# Program and Refresh the xc7a50t Device
set Device [lindex [get_hw_devices] 0] 
current_hw_device [get_hw_devices xc7a50t_0]
refresh_hw_device -update_hw_probes false $Device
set_property PROGRAM.FILE $Path $Device
program_hw_devices $Device
refresh_hw_device $Device
