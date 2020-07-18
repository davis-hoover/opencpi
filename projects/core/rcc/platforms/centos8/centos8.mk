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

##########################################################################################
# This file defines the "centos8" software platform.
# It sets platform variables as necessary to override the defaults in
#   "tools/cdk/include/platform-defaults.mk".
# See that file for a description of valid variables and their defaults.

OcpiPlatformOs=linux
OcpiPlatformOsVersion=c8
OcpiPlatformArch=x86_64
OcpiExtraLibs+=yaml-cpp
#
# "OcpiKernelDir" must be set if it is appropriate to build
# the "opencpi.ko" driver module for this platform.
#
# There are less expensive ways to find a kernel headers directory if
# the stars align properly, but the method below is guaranteed to find
# one on "centosX" if one exists.
#
OcpiKernelDir:=\
$(strip $(foreach krel,$(shell uname -r),\
  $(foreach hver,$(word 1, $(shell rpm -q --qf=%{version}-%{release}.%{arch} kernel-headers)),\
    $(if $(filter $(krel),$(hver)),,$(info Warning: probable running kernel vs. installed kernel mismatch detected: the OpenCPI kernel driver will be built for kernel version $(hver).  The detected mismatch usually means the kernel has been updated recently, but the system has not been rebooted since the update.  Please reboot your system if you have not already done so.))\
    $(foreach kdir,/usr/src/kernels/$(hver),\
      $(or $(wildcard $(kdir)),$(info Warning: no kernel headers directory found))))))
