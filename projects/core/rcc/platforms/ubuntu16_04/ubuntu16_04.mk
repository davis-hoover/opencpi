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
# This file defines the ubuntu16_04 software platform.
# It sets platform variables as necessary to override the defaults in
#   "tools/cdk/include/platform-defaults.mk".
# See that file for a description of valid variables and their defaults.

OcpiPlatformOs=linux
OcpiPlatformOsVersion=u16_04
OcpiPlatformArch=x86_64
OcpiExtraLibs+=yaml-cpp
#
# "OcpiKernelDir" must be set if it is appropriate to build
# the "opencpi.ko" driver module for this platform.
#
# There are less expensive ways to find a kernel headers directory if
# the stars align properly, but the method below is guaranteed to find
# one on "ubuntu16_04" if one exists.
#
OcpiKernelDir:=\
$(strip $(foreach krel,$(shell uname -r),\
 $(foreach ktype,$(shell echo $(krel) | cut -f3 -d'-'),\
  $(foreach hver,$(or $(shell dpkg -l | grep 'linux-headers' | cut -f3 -d' ' | sort -t'-' -n -k 3,4 -k 4,5 | egrep '$(ktype)$$' | tail -1),NOPE),\
   $(if $(filter NOPE,$(hver)),\
    $(info Warning: no kernel headers for "$(ktype)" kernel installed),\
    $(if $(filter linux-headers-$(krel),$(hver)),,$(info Warning: probable running kernel vs. installed kernel mismatch detected: the OpenCPI kernel driver will be built for kernel version $(subst linux-headers-,,$(hver)).  The detected mismatch usually means the kernel has been updated recently, but the system has not been rebooted since the update.  Please reboot your system if you have not already done so.))\
    $(foreach kdir,/usr/src/$(hver),\
     $(or $(wildcard $(kdir)),$(info Warning: no kernel headers directory found))))))))
