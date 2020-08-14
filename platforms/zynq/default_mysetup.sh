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

# add any additional platform checks into this function
# For Dev Testing: export OCPI_TOOL_PLATFORM and OCPI_DIR for testing platforms 
# in the future without touching the set_tool_platform function or script in general

if [[ "$BASH_SOURCE" = "$0" ]]; then  # script has to be sourced in order to run applications
  echo "Script is NOT sourced. Expected form 'source ./mysetup.sh'"
  exit 1  # note exit and not return since we are not being sourced
fi

trap "trap - ERR; break" ERR

for i in 1; do
  if test "$OCPI_CDK_DIR" = ""; then
    source ./zynq_setup_common.sh
	  set_tool_platform
	  set_time time.nist.gov
    # Uncomment this section and change the MAC address for an environment with multiple
    # ZedBoards on one network (only needed on xilinx13_3)
    # ifconfig eth0 down
    # ifconfig eth0 hw ether 00:0a:35:00:01:23
    # ifconfig eth0 up
    # udhcpc
  
    # CUSTOMIZE THIS LINE FOR YOUR ENVIRONMENT
    # First argument is backup time server for the time protocol used by the ntp command
    # Second argument is timezone spec - see "man timezone" for the format.
    source ./zynq_setup.sh time.nist.gov EST5EDT,M3.2.0,M11.1.0
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

  echo Loading hdl bitstream
  if ocpihdl load -d $OCPI_DEFAULT_HDL_DEVICE $OCPI_DIR/artifacts/testbias_$HDL_PLATFORM\_base.bitz; then
    echo Bitstream successfully loaded
  else
    echo Bitstream load error
  fi
  
  # Print the available containers as a sanity check
  echo Discovering available containers...
  ocpirun -C
  # Since we are sourcing this script we can't use "exit", do "done" is for "break"
done
trap - ERR
