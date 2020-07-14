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
# This script should be customized to do what you want.
# It is used in two contexts:
# 1. The core setup has not been run, so run it with your specific parameters
#    (mount point on development host, etc.), and supply the IP address as arg
# 2. The core setup HAS been run and you are just setting up a shell or ssh session

# add any additional platform checks into this function
# For Dev Testing: export OCPI_TOOL_PLATFORM and OCPI_DIR for testing platforms 
# in the future without touching the set_tool_platform function or script in general

trap "trap - ERR; break" ERR; for i in 1; do

if test "$OCPI_CDK_DIR" = ""; then
  source ./zynq_setup_common.sh setup.sh time.nist.gov
  if test "$1" = ""; then
     echo It appears that the environment is not set up yet.
     echo You must supply the IP address of the OpenCPI server machine as an argument to this script.
     break
  fi
  # Uncomment this section and change the MAC address for an environment with multiple
  # ZedBoards on one network (only needed for xilinx13_3)
  # ifconfig eth0 down
  # ifconfig eth0 hw ether 00:0a:35:00:01:23
  # ifconfig eth0 up
  # udhcpc
  
  # add or remove mount points based on your needs
  mkdir -p /mnt/net
  mount -t nfs -o udp,nolock,soft,intr $1:$2 /mnt/net
  # mkdir -p /mnt/ocpi_core
  # mount -t nfs -o udp,nolock,soft,intr $1:/home/developer/opencpi/projects/core /mnt/ocpi_core
  # mkdir -p /mnt/ocpi_assets
  # mount -t nfs -o udp,nolock,soft,intr $1:/home/developer/opencpi/projects/assets /mnt/ocpi_assets
  # mkdir -p /mnt/ocpi_assets_ts
  # mount -t nfs -o udp,nolock,soft,intr $1:/home/developer/opencpi/projects/assets_ts /mnt/ocpi_assets_ts
  # Below this line other projects can be included
  # Here is a template of including a BSP project
  # mkdir -p /mnt/bsp_<bsp_name>
  # mount -t nfs -o udp,nolock,soft,intr $1:/home/user/ocpi_projects/bsp_<bsp_name> /mnt/bsp_<bsp_name>
  
  # Tell the kernel to make fake 32 bit inodes when 64 nodes come from the NFS server
  # This may change for 64 bit zynqs
  echo 0 > /sys/module/nfs/parameters/enable_ino64
  # Mount the opencpi development system as an NFS server, onto /mnt/net
  # CUSTOMIZE THIS LINE FOR YOUR ENVIRONMENT
  # Second arg is shared file system mount point on development system
  # Third argument is opencpi dir relative to mount point
  # Fourth argument is backup time server for the time protocol used by the ntp command
  # Fifth arg is timezone spec - see "man timezone" for the format.
  
  source ./zynq_net_setup.sh $1 /opt/opencpi cdk time.nist.gov EST5EDT,M3.2.0,M11.1.0
  
  # add any commands to be run only the first time this script is run

  break # this script will be rerun recursively by setup.sh
fi
# Below this (until "done") is optional user customizations
alias ll='ls -lt --color=auto'
# Tell the ocpihdl utility to always assume the FPGA device is the zynq PL.
export OCPI_DEFAULT_HDL_DEVICE=pl:0
#prevent looking for simulation tools such as xsim
export OCPI_ENABLE_HDL_SIMULATOR_DISCOVERY=0
# Only override this file if it is customized beyond what is the default for the platform
#export OCPI_SYSTEM_CONFIG=$OCPI_DIR/system.xml
# Get ready to run some test xml-based applications
PS1='% '
# add any commands to be run every time this script is run

# Print the available containers as a sanity check
echo Discovering available containers...
ocpirun -C
# Since we are sourcing this script we can't use "exit", so "done" is for "break" from "for"
done
trap - ERR
