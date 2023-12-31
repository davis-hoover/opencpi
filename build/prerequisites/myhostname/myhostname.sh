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

myhostnamelib="$OCPI_PREREQUISITES_DIR/myhostname/$OCPI_TOOL_DIR/lib/\${LIB}myhostname.so"
MYHOSTNAME_SPOOF=LD_PRELOAD="$myhostnamelib${LD_PRELOAD:+:}$LD_PRELOAD"
MYHOSTNAME_MNAME=$(uname -m)
if [ -n "$NODE_NAME" ]; then
  MYHOSTNAME=${NODE_NAME}_${MYHOSTNAME_MNAME}.jenkins
else
  MYHOSTNAME=buildhost_$MYHOSTNAME_MNAME
fi
export MYHOSTNAME+=.fakehostname



