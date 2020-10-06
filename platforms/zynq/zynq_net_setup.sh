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
# If there is a "mynetsetup.sh" script in this directory it will run it after the
# other setup items, and arrange for it to be run in any login scripts later
# e.g. ssh logins

  if test -n "$3"; then
    echo OCPI_HDL_PLATFORM set to $3.
    export OCPI_HDL_PLATFORM=$3
  fi
  
  # Run the generic script to setup the OpenCPI environment
  # Note the ocpidriver load command is innocuous if run redundantly
  # Some Zynq-based SD cards are ephemeral and lose $HOME on reboots. Others don't.
  # This tries to handle both cases sanely.
  if test -d /etc/profile.d; then
    export PROFILE_FILE=/etc/profile.d/opencpi-persist.sh
  else
    export PROFILE_FILE=$HOME/.profile
  fi
  export OCPI_CDK_DIR=/mnt/net/$2
  cat <<EOF > $PROFILE_FILE
  if test -e /mnt/net/$2; then
    echo Executing $PROFILE_FILE
    export OCPI_CDK_DIR=$OCPI_CDK_DIR
	export OCPI_DIR=$OCPI_DIR
    cd $OCPI_DIR
	source $OCPI_DIR/zynq_setup_common.sh set_tool_platform
    export OCPI_TOOL_OS=linux
    export OCPI_TOOL_DIR=$OCPI_TOOL_PLATFORM
	export OCPI_HDL_PLATFORM=$OCPI_HDL_PLATFORM
	cd $OCPI_DIR
    # As a default, access all built artifacts in the core project as well as
    # the bare-bones set of prebuilt runtime artifacts for this SW platform
    export OCPI_LIBRARY_PATH=$OCPI_CDK_DIR/../project-registry/ocpi.core/exports/artifacts:$OCPI_CDK_DIR/$OCPI_TOOL_PLATFORM/artifacts:$OCPI_CDK_DIR/../projects/assets/artifacts:$OCPI_DIR/\$OCPI_TOOL_DIR/artifacts
    # Priorities for finding system.xml:
    # 1. If is it on the local system it is considered customized for this system - use it.
    if test -r $OCPI_DIR/system.xml; then
      OCPI_SYSTEM_CONFIG=$OCPI_DIR/system.xml
    # 2. If is it at the top level of the mounted CDK, it is considered customized for all the
    #    systems that use this CDK installation (not shipped/installed by the CDK)
    elif test -r $OCPI_CDK_DIR/system.xml; then
      OCPI_SYSTEM_CONFIG=$OCPI_CDK_DIR/system.xml
    # 3. If there is one for this HDL platform, it is considered more specific than one that is
    #    specific to the RCC platform, so it should be used in preference to the RCC platform one.
    elif test -n "$OCPI_HDL_PLATFORM" -a -r $OCPI_CDK_DIR/$OCPI_HDL_PLATFORM/system.xml; then
      OCPI_SYSTEM_CONFIG=$OCPI_CDK_DIR/$OCPI_HDL_PLATFORM/system.xml
    # 4. If there is one for this RCC platform, it is more specific than the default one.
    elif test -r $OCPI_CDK_DIR/\$OCPI_TOOL_PLATFORM/system.xml; then
      OCPI_SYSTEM_CONFIG=$OCPI_CDK_DIR/\$OCPI_TOOL_PLATFORM/system.xml
    # 5. Finally use the default one that is very generic.
    else
      OCPI_SYSTEM_CONFIG=$OCPI_CDK_DIR/default-system.xml
    fi
    export OCPI_SYSTEM_CONFIG
    export PATH=$OCPI_CDK_DIR/\$OCPI_TOOL_DIR/bin:\$PATH
    # path to SDK libraries, not related to opencpi but missing from boot system
    export LD_LIBRARY_PATH=$OCPI_CDK_DIR/\$OCPI_TOOL_DIR/sdk/lib:\$LD_LIBRARY_PATH
    ocpidriver load
    export TZ=$5
    echo OpenCPI ready for zynq.
    if test -r $OCPI_DIR/mynetsetup.sh; then
       source $OCPI_DIR/mynetsetup.sh
    else
       echo Error: enable to find $OCPI_DIR/mynetsetup.sh
    fi
  else
    echo NFS mounts not yet set up. Please mount the OpenCPI CDK into /mnt/net/.
  fi
  
  alias ls='ls --color=auto'
EOF
  echo Running login script. OCPI_CDK_DIR is now $OCPI_CDK_DIR.
  source $PROFILE_FILE
