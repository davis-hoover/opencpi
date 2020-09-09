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
# This script should be customized to do what you want.
# It is used in two contexts:
# 1. The core setup has not been run, so run it with your specific parameters
#    (mount point on development host, etc.), and supply the IP address as arg
# 2. The core setup HAS been run and you are just setting up a shell or ssh session
#
# add any additional platform checks into this function
# For Dev Testing: export OCPI_TOOL_PLATFORM and OCPI_DIR for testing future platforms 
# without having to modify any of the code
#
# Customization options:
# - time server that is accessed during the set_time function in zynq_setup_common
# - MAC address if running multiple ZedBoards
# - Hostname if needed
# - OCPI_DEFAULT_HDL_DEVICE if needed to be anything other than default pl:0

# source check to ensure environment is set properly
if [[ "$(basename -- "$0")" == "mysetup.sh" ]]; then
  echo "Script is NOT sourced. Expected form 'source ./mysetup.sh'"
  exit 1  # note exit and not return since we are not being sourced
fi

trap "trap - ERR; break" ERR > /dev/null 2>&1  # part on end added to suppress 'error: signal not found' messages on platforms that don't support the ERR signal

for i in 1; do
    
  if test "$OCPI_CDK_DIR" = ""; then  
    # Uncomment this section and change the MAC address for an environment with multiple
    # ZedBoards on one network (only needed on xilinx13_3)
	# In case dhcp failed on eth0, try it on eth1
    #
	# ifconfig eth0 down
    # ifconfig eth0 hw ether 00:0a:35:00:01:23
    # ifconfig eth0 up
    # udhcpc
	# Make sure the hostname is in the host table
	myhostname=`hostname`
    if ! grep -q $myhostname /etc/hosts; then 
	echo 127.0.0.1 $myhostname >> /etc/hosts;
	fi
    source ./zynq_setup_common.sh set_tool_platform set_time time.nist.gov  # script takes which functions to run as arguments, expecting set_tool_platform as the first and set_time as well as the time server as its second and third respectively
    source ./zynq_setup.sh
    # add any commands to be run only the first time this script is run
    break # this script will be rerun recursively by setup.sh
  fi
	
  # Tell the ocpihdl utility to always assume the FPGA device is the zynq PL.
  export OCPI_DEFAULT_HDL_DEVICE=pl:0
  # The system config file sets the default SMB size
  export OCPI_SYSTEM_CONFIG=$OCPI_CDK_DIR/system.xml

  # Shorten the default shell prompt
  PS1='% '
  # add any commands to be run every time this script is run

  echo Loading bitstream
  if   ocpihdl load -d $OCPI_DEFAULT_HDL_DEVICE $OCPI_CDK_DIR/artifacts/testbias_$HDL_PLATFORM\_base.bitz; then
    echo Bitstream loaded successfully
  else
    echo Bitstream load error
    break
  fi 
  
  # Print the available containers as a sanity check
  echo Discovering available containers...
  ocpirun -C
  # Since we are sourcing this script we can't use "exit", do "done" is for "break"
done
trap - ERR > /dev/null 2>&1
