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
# If there is a "mysetup.sh" script in this directory it will run it after the
# other setup items, and arrange for it to be run in any login scripts later
# e.g. ssh logins
#
# Set time using ntpd
# If ntpd fails because it could not find ntp.conf fall back on time server
# passed in as the first parameter

if test $# != 2; then
  echo You must supply 2 arguments to this script.
  echo Usage is: zynq_setup.sh '<ntp-server> <timezone>'
  echo A good example timezone is: EST5EDT,M3.2.0,M11.1.0
  echo If the ntp-server is '"-"', no ntpclient will be started.
else
  export OCPI_CDK_DIR=$OCPI_DIR
  # In case dhcp failed on eth0, try it on eth1
  
  # Make sure the hostname is in the host table
  myhostname=`hostname`
  if ! grep -q $myhostname /etc/hosts; then echo 127.0.0.1 $myhostname >> /etc/hosts; fi
  # Run the generic script to setup the OpenCPI environment
  # Note the ocpidriver load command is innocuous if run redundantly
  OCPI_CDK_DIR=$OCPI_DIR
  cat <<EOF > $HOME/.profile
    echo Executing $HOME/.profile.
    export OCPI_CDK_DIR=$OCPI_CDK_DIR
    export OCPI_TOOL_PLATFORM=$OCPI_TOOL_PLATFORM
    export OCPI_TOOL_OS=linux
	cd $OCPI_CDK_DIR
    # There is no multimode support when running standalone
    export OCPI_TOOL_DIR=\$OCPI_TOOL_PLATFORM
    export OCPI_LIBRARY_PATH=$OCPI_CDK_DIR/\$OCPI_TOOL_DIR/artifacts
    export PATH=$OCPI_CDK_DIR/\$OCPI_TOOL_DIR/bin:\$PATH
    export LD_LIBRARY_PATH=$OCPI_CDK_DIR/\$OCPI_TOOL_DIR/sdk/lib:\$LD_LIBRARY_PATH
    ocpidriver load
    export TZ=$2
    echo OpenCPI ready for zynq.
    if test -r $OCPI_CDK_DIR/mysetup.sh; then
       source $OCPI_CDK_DIR/mysetup.sh
    fi
EOF
  echo Running login script. OCPI_CDK_DIR is now $OCPI_CDK_DIR.
  source $HOME/.profile
fi

