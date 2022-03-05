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
# This file defines the ubuntu20_04 software platform.
# It sets platform variables as necessary to override the defaults in
#   "tools/include/platform-defaults.mk".
# See that file for a description of valid variables and their defaults.

OcpiPlatformOs=linux
OcpiPlatformOsVersion=u20_04
OcpiPlatformArch=x86_64

#
# "OcpiKernelDir" must be set if it is appropriate to build
# the "opencpi.ko" driver module for this platform.
#
OcpiKernelDir:=$(call OcpiGetKernelDir,Ubuntu)
