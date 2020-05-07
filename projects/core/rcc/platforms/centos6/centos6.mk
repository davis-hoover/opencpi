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
# This file defines the CentOS6 software platform.
# It sets platform variables as necessary to override the defaults in
#   "tools/cdk/include/platform-defaults.mk".
# See that file for a description of valid variables and their defaults.

OcpiPlatformOs=linux
OcpiPlatformOsVersion=c6
OcpiPlatformArch=x86_64
# CLOCK_MONOTONIC_RAW, the preferred value, is broken on centos6.  The values returned
# by clock_gettime with CLOCK_MONOTONIC_RAW are garbage.
OcpiGetTimeClockId=CLOCK_MONOTONIC
OcpiRequiredCFlags:=$(patsubst -grecord-gcc-switches,-frecord-gcc-switches,$(OcpiRequiredCFlags))
OcpiRequiredCXXFlags:=$(patsubst -grecord-gcc-switches,-frecord-gcc-switches,$(OcpiRequiredCXXFlags))
# Could not find a way to make swig-1.X do what is required
# for python3, so using swig3 from Springdale Computational.
OcpiSWIG:=/usr/local/swig/3.0.12/bin/swig
#
# Must set the following variable for the "opencpi.ko" module
# build if we are running in a container, because there is no
# "/lib/modules/`uname -r`/build" symlink in that environment.
#
# TODO: figure out a way to set the variable conditionally if
# there is an easy way to determine whether we are running in
# a container.
#
# For debugging: $(info OcpiKernelDir is $(OcpiKernelDir))
#
OcpiKernelDir:=/usr/src/kernels/$(shell uname -r)
