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

# AV-4141
# This dropin test catches the bug found in AV-4141
# This confirms that a manually set set registry will only
# only be removed by 'make clean' if it matches the current
# global default. Otherwise it should remain untouched.
source $OCPI_CDK_DIR/scripts/util.sh # needed for getProjectRegistryDir
set -e

proj="set-reg-clean"
reg="$proj-project-registry"
rm -r -f $proj $reg

ocpidev create registry $reg
ocpidev create project $proj

pushd $proj

# Test that soft cleaning will not remove non-default imports
ocpidev set registry ../$reg
# soft clean - should leave imports alone
ocpidev clean
test "$(readlink imports)" == "../$reg"

# Test that soft cleaning will not remove the default imports
ocpidev set registry
default_reg=$(getProjectRegistryDir)
test "$(ocpiReadLinkE imports)" == "$(ocpiReadLinkE $default_reg)"
# soft clean - should leave imports alone
ocpidev clean
test -e imports

# Test that soft cleaning will remove the registry even if set in the environment
OCPI_PROJECT_REGISTRY_DIR=../$reg ocpidev set registry
OCPI_PROJECT_REGISTRY_DIR=../$reg ocpidev clean
test -e imports

popd
ocpidev delete -f project $proj
test -z "$(ls $proj 2>/dev/null)"

ocpidev delete -f registry $reg
test -z "$(ls $reg 2>/dev/null)"
