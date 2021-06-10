#!/bin/bash
#
# Wrapper script for "ocpidoc.py".
#
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
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
[ -n "$OCPI_CDK_DIR" ] || { echo "Error: OCPI_CDK_DIR not set" && exit 1; }

#
# If the python3 virtual environment does not exist,
# create it and install the needed "sphinx" modules.
#
[ -d "$OCPI_CDK_DIR/$OCPI_TOOL_DIR/lib/ocpidoc/venv" ] || {
  echo "WARNING: one-time setup of \"ocpidoc\" execution environment in progress..."
  #
  # python3 version must be >= 3.6.0 for "ocpidoc".
  # If "python3" does not meet this requirement, "python3.6"
  # must exist, and if so, patch the python scripts to use
  # that instead of "python3".
  #
  PYCMD=python3
  echo "Checking python3 version"
  if python3 -c "import sys; sys.exit(0 if sys.hexversion < 0x030600f0 else 1)"; then
    echo "System python3 version is < 3.6.0"
    echo "Checking for python3.6"
    if ! command -v python3.6 &>/dev/null; then
      echo "ERROR: required python3 >= 3.6.0 not found"
      exit 1
    fi
    PYCMD=python3.6
  fi

  $PYCMD -m venv $OCPI_CDK_DIR/$OCPI_TOOL_DIR/lib/ocpidoc/venv
  source $OCPI_CDK_DIR/$OCPI_TOOL_DIR/lib/ocpidoc/venv/bin/activate
  pip3 install sphinx sphinx_rtd_theme sphinxcontrib_spelling
  deactivate ;
}

source $OCPI_CDK_DIR/$OCPI_TOOL_DIR/lib/ocpidoc/venv/bin/activate
$OCPI_CDK_DIR/$OCPI_TOOL_DIR/lib/ocpidoc/ocpidoc.py $@
