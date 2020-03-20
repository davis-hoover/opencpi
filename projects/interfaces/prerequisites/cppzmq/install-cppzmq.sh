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

################################################################################
# 1. Download/clone and setup directories in the prereq area
################################################################################

GIT_REPO_URL=REDACTED/git/scm/mirror/cppzmq.git
GIT_REPO_TAG=v4.2.1
source $OCPI_CDK_DIR/scripts/setup-prerequisite.sh \
       "$1" \
       cppzmq \
       "ZeroMQ C++ Binding" \
       $GIT_REPO_URL \
       $GIT_REPO_TAG \
       cppzmq \
       1
base=$(basename `pwd`)
(cd ..; cp -R $(ls . | grep -v ocpi-build-) $base)

################################################################################
# 2. Patch
################################################################################

#################################################################################
# 3. Compile code into the library
################################################################################

################################################################################
# 4. Install the deliverables
################################################################################

II=$OcpiInstallDir/include
[ ! -d $II ] && mkdir $II
cp *.hpp $II/
