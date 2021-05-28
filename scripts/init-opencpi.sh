#!/bin/bash --noprofile
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

################################################################################################
# This script does the bare minimum in the source tree to enable other things to happen.
# It is usually internally called when anything big and generic happens like
# install-packages, install-prerequisites, build-opencpi, etc.
# But it might be called directly to enable other scripts to be run before/without doing
# any of the above.
# It is only callable from the top level of the source tree.
# This sourced script is for clean environments, only for use in the core source tree,
# although if CDK is available we let it go with a warning
if [ -n "$OCPI_ROOT_DIR" ] ; then
  [ -d "$OCPI_ROOT_DIR" ] || { echo The OCPI_ROOT_DIR environment variable is invalid && exit 1; }
  ocpi_old=$(cd "$OCPI_ROOT_DIR" && pwd -P)
  ocpi_new=$(pwd -P)
  [ "$ocpi_old" == "$ocpi_new" ] || {
      echo You cannot run this command with an existing OpenCPI environment set up elsewhere.
      echo Your environment currently has OCPI_ROOT_DIR as $OCPI_ROOT_DIR, and OCPI_CDK_DIR as $OCPI_CDK_DIR.
      echo Either use a fresh shell/terminal or perhaps do:
      echo "   source $OCPI_CDK_DIR/opencpi-setup.sh --clean"
      exit 1; }
fi
if test ! -d exports; then
  # We're being run in an uninitialized environment.
  if test ! -x ./scripts/export-framework.sh; then
    echo Error: it appears that this script is not being run at the top level of the OpenCPI source tree.
    exit 1
  fi
  # Ensure a skeletal exported CDK
  ./scripts/export-framework.sh -
fi
mkdir -p prerequisites

# This for bootstrapping.  When the environment is fully set up and the framework is exported,
# the python path will point into cdk/<platform>/lib, so that there is a platform-specific
# directory for the optimized (pyc, pycache) to go.
# But earlier in the installation process, before there is such a platform-specific directory
# we still want to expose and use some of our python modules.  This allows that.
# Note this isn't doing anything to the user's environment, just temporarily for the
# few callers of this script
export PYTHONPATH=$(pwd)/tools/python
