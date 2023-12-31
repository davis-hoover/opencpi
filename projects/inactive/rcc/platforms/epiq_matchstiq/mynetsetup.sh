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

################################
# Must set the system hostname to 'zynq', default is '(none)'
hostname zynq
# Create /etc/hosts (Failed to access this file, as it didn't exsist upon boot).
touch /etc/hosts
# Create & populate /etc/ocpi-release and /etc/opencpi-release 
echo 3.9.0-xilinx-trd > /etc/ocpi-release
echo epiq_matchstiq linux-zynq-arm_cs 3.9.0-xilinx-trd > /etc/opencpi-release

trap "trap - ERR; break" ERR; for i in 1; do
if test "$OCPI_CDK_DIR" = ""; then
  if test "$1" = ""; then
     echo It appears that the environment is not set up yet.
     echo You must supply the IP address of the OpenCPI server machine as an argument to this script.
     break
  fi
  # CUSTOMIZE THIS LINE FOR YOUR ENVIRONMENT
  # Second arg is shared file system mount point on development system
  # Third argument is opencpi dir relative to mount point
  # Fourth argument is time server for the (old) time protocol used by the rdate command
  # Fifth arg is timezone spec - see "man timezone" for the format.
  export OCPI_TOOL_MODE=
  export OCPI_TARGET_MODE=

  source /root/opencpi/zynq_net_setup.sh $1 /opt/opencpi cdk time.nist.gov EST5EDT,M3.2.0,M11.1.0
  # add any commands to be run only the first time this script is run
  # mkdir -p /root/opencpi/mnt/ocpi_core
  # mount -t nfs -o udp,nolock,soft,intr $1:/home/user/core /root/opencpi/mnt/ocpi_core
  # mkdir -p /root/opencpi/mnt/ocpi_assets
  # mount -t nfs -o udp,nolock,soft,intr $1:/home/user/assets /root/opencpi/mnt/ocpi_assets
  # mkdir -p /root/opencpi/mnt/ocpi_assets_ts
  # mount -t nfs -o udp,nolock,soft,intr $1:/home/user/assets /root/opencpi/mnt/ocpi_assets_ts

  break # this script will be rerun recursively by setup.sh
fi
# Below this (until "done") is optional user customizations
alias ll='ls -lt --color=auto'
# Tell the ocpihdl utility to always assume the FPGA device is the zynq PL.
export OCPI_DEFAULT_HDL_DEVICE=pl:0
# Only override this file if it is customized beyond what is the default for the platform
# export OCPI_SYSTEM_CONFIG=/root/opencpi/system.xml
# Get ready to run some test xml-based applications
PS1='% '
# add any commands to be run every time this script is run

# Print the available containers as a sanity check
echo Discovering available containers...
ocpirun -C
# Since we are sourcing this script we can't use "exit", so "done" is for "break" from "for"
done
trap - ERR
