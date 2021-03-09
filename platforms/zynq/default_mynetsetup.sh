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
# 
# add any additional platform checks into this function
# For Dev Testing: export OCPI_TOOL_PLATFORM and OCPI_LOCAL_DIR for testing platforms 
# in the future without touching the set_tool_platform function or script in general
#
# Customization options:
# - time server that is accessed during the set_time function in zynq_setup_common
# - MAC address if running multiple ZedBoards
# - Hostname if needed
# - OCPI_DEFAULT_HDL_DEVICE if needed to be anything other than default pl:0
# - add a third argument to zynq_net_setup to set OCPI_HDL_PLATFORM

# source check to ensure environment is set properly during this script
if [[ "$(basename -- "$0")" == "mynetsetup.sh" ]]; then  # script has to be sourced in order to run applications
  echo "Script is NOT sourced. Expected form 'source ./mynetsetup.sh <IP-Address of server machine> < Server directory to mount>'"
  exit 1  # note exit and not return since we are not being sourced
fi
  
trap "trap - ERR; break" ERR > /dev/null 2>&1  # part on end added to suppress 'error: signal not found' messages on platforms that don't support the ERR signal

for i in 1; do 

  if test "$OCPI_CDK_DIR" = ""; then
    if test "$2" = ""; then
      echo "You must supply the IP address of the OpenCPI server machine as an argument to this script as well as the directory you would like to mount to"
      echo "Expected form 'source ./mynetsetup.sh <IP-Address of server machine> < Server directory to mount>'"
      break
    fi

     # Uncomment this section and change the MAC address for an environment with multiple
     # ZedBoards on one network (only needed for xilinx13_3)
     # ifconfig eth0 down
     # ifconfig eth0 hw ether 00:0a:35:00:01:23
     # ifconfig eth0 up
     # udhcpc
  
    if ifconfig | grep -v 127.0.0.1 | grep 'inet addr:' > /dev/null; then
      echo An IP address was detected.
    else
      echo No IP address was detected! No network or no DHCP.
      break;
    fi
    # Make sure the hostname is in the host table
    myipaddr=`ifconfig | grep -v 127.0.0.1 | sed -n '/inet addr:/s/^.*inet addr: *\([^ ]*\).*$/\1/p'`
    myhostname=`hostname`
    echo My IP address is: $myipaddr, and my hostname is: $myhostname
    if ! grep -q $myhostname /etc/hosts; then echo $myipaddr $myhostname >> /etc/hosts; fi
    
	# Mount the opencpi development system as an NFS server, onto /mnt/net
	# add or remove mount points based on your needs
    export OCPI_NET_DIR=/mnt/net
    mkdir -p $OCPI_NET_DIR
    mount -t nfs -o udp,nolock,soft,intr $1:$2 $OCPI_NET_DIR  # second argument should be location of opencpi directory
    # mkdir -p /mnt/ocpi_core
    # mount -t nfs -o udp,nolock,soft,intr $1:/home/user/ocpi_projects/core /mnt/ocpi_core
  
    # Tell the kernel to make fake 32 bit inodes when 64 nodes come from the NFS server
    # This may change for 64 bit zynqs
    echo 0 > /sys/module/nfs/parameters/enable_ino64
	
    source ./zynq_setup_common.sh set_tool_platform set_time time.nist.gov  # specify other time server if needed
    source ./zynq_net_setup.sh $1 cdk  # Usage is: zynq_net_setup.sh <nfs-ip-address> <opencpi-cdk-dir> <OCPI_HDL_PLATFORM> third argument is optional and dependant on use case
  
    # add any commands to be run only the first time this script is run

    break # this script will be rerun recursively by zynq_net_setup.sh
  fi
  # Below this (until "done") is optional user customizations
  
  # Tell the ocpihdl utility to always assume the FPGA device is the zynq PL.
  export OCPI_DEFAULT_HDL_DEVICE=pl:0
  #prevent looking for simulation tools such as xsim
  export OCPI_ENABLE_HDL_SIMULATOR_DISCOVERY=0

  # **customize system.xml or ensure it is correctly configured**
  # Get ready to run some test xml-based applications
  PS1='% '
  # add any commands to be run every time this script is run

  echo Loading bitstream
  if ocpihdl load -d $OCPI_DEFAULT_HDL_DEVICE $OCPI_CDK_DIR/$HDL_PLATFORM/*.bitz; then
    echo Bitstream successfully loaded
  else
    echo Bitstream load error
    break
  fi 
 
  # Print the available containers as a sanity check
  echo Discovering available containers...
  ocpirun -C
  # Since we are sourcing this script we can't use "exit", so "done" is for "break" from "for"
done
trap - ERR > /dev/null 2>&1
