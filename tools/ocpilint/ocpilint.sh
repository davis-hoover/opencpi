#!/bin/bash
#
# Wrapper script for "ocpilint.py".
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
VENV_DIR="$OCPI_CDK_DIR/$OCPI_TOOL_DIR/lib/ocpilint/venv"

#
# If there is an existing python3 virtual environment for the linter,
# check to see if it was created on *this* system.  If
# not, remove it before continuing.
#
if [ -d "$VENV_DIR" ]
then
  C_VENV_DIR=$(grep -E '^VIRTUAL_ENV=' "$VENV_DIR/bin/activate" | cut -f2 -d'=' | tr -d '"')
  if [ "$VENV_DIR" != "$C_VENV_DIR" ]
  then
    echo "WARNING: python3 virtual environment is not where it was originally created: removing..."
    rm -rf "$VENV_DIR"
  fi
fi

#
# If the python3 virtual environment does not exist,
# create it and install the needed modules.
#
[ -d "$VENV_DIR" ] || {
  echo "WARNING: one-time setup of \"ocpilint\" execution environment in progress..."
  #
  # python3 version must be >= 3.6.0 for "ocpilint".
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

  $PYCMD -m venv "$VENV_DIR"
  source "$VENV_DIR/bin/activate"
  # wheel needs to be installed before the other required packages on Ubuntu 18.04
  #   and doesn't hurt the other OS's, specifically pyyaml requires it.
  pip3 install "wheel"
  pip3 install "lxml" "pydocstyle" "pycodestyle" "autopep8" "cpplint" "pyyaml" "jinja2"

  # Ubuntu 18.04 version of clang-format is missing dependencies
  #   that aren't in the version of pip3. Install clang-format on the OS
  #   for Ubuntu 18.04 and skip it in the venv
  if [ "$OCPI_TOOL_PLATFORM" != "ubuntu18_04" ]; then
    pip3 install "clang-format"
  fi
  # Empty line after installing for the cosmetics
  echo

  deactivate
}

source "$VENV_DIR/bin/activate"
"$OCPI_CDK_DIR/$OCPI_TOOL_DIR"/lib/ocpilint/ocpilint.py "$@"
