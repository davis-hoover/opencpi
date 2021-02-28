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
  
  # Run the generic script to setup the OpenCPI environment
  # Note the ocpidriver load command is innocuous if run redundantly
  export OCPI_CDK_DIR=$OCPI_LOCAL_DIR
  export OCPI_ROOT_DIR=$OCPI_LOCAL_DIR/..
  if test -d /etc/profile.d; then
    export PROFILE_FILE=/etc/profile.d/opencpi-persist.sh
  else
    export PROFILE_FILE=$HOME/.profile
  fi
  cat <<EOF > $PROFILE_FILE
    echo Executing $PROFILE_FILE\.
	export OCPI_CDK_DIR=$OCPI_CDK_DIR
  export OCPI_ROOT_DIR=$OCPI_ROOT_DIR
	cd $OCPI_ROOT_DIR/opencpi
	source $OCPI_CDK_DIR/zynq_setup_common.sh set_tool_platform
    export OCPI_TOOL_OS=linux
    # There is no multimode support when running standalone
    export OCPI_TOOL_DIR=$OCPI_TOOL_PLATFORM
    export OCPI_LIBRARY_PATH=$OCPI_CDK_DIR/\$OCPI_TOOL_DIR/artifacts:$OCPI_CDK_DIR/artifacts
    export PATH=$OCPI_CDK_DIR/\$OCPI_TOOL_DIR/bin:\$PATH
    # path to SDK libraries, not related to opencpi but missing from boot system
    export LD_LIBRARY_PATH=$OCPI_CDK_DIR/\$OCPI_TOOL_DIR/sdk/lib:\$LD_LIBRARY_PATH
    ocpidriver load
    export TZ=$2
    echo OpenCPI ready for zynq.
    if test -r $OCPI_ROOT_DIR/mysetup.sh; then
       source $OCPI_ROOT_DIR/mysetup.sh
    elif test -r $OCPI_CDK_DIR/mysetup.sh; then
       source $OCPI_CDK_DIR/mysetup.sh
    fi
	
	alias ls='ls --color=auto'	
EOF
  echo Running login script. 
  echo OCPI_CDK_DIR is now $OCPI_CDK_DIR
  echo OCPI_ROOT_DIR is now $OCPI_ROOT_DIR
  source $PROFILE_FILE

