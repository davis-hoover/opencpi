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

$(if $(realpath $(OCPI_CDK_DIR)),,\
  $(error The OCPI_CDK_DIR environment variable is not set correctly.))
# This is the HDL assembly Makefile for the "param_test_assy" assembly
# The file "param_test_assy.xml" defines the assembly.
# The default container for all assemblies is one that connects all external ports to
# the devices interconnect to communicate with software workers or other FPGAs.
#
# Limit this assembly to certain platforms or targets with Exclude/Only and Targets/Platforms ie:
# ExcludePlatforms=

OnlyTargets=xsim modelsim

include $(OCPI_CDK_DIR)/include/hdl/hdl-assembly.mk
