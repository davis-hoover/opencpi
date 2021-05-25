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
HdlLibraries=fixed_float ocpi axi sdp platform
OnlyTargets=cyclone5

include $(OCPI_CDK_DIR)/include/hdl/altera.mk
include $(OCPI_CDK_DIR)/include/hdl/hdl-make.mk

# Todo: Perhaps should change OcpiAlteraQuartusDir should change to OcpiAlteraProgrammerDir?
ifeq ($(filter clean%,$(MAKECMDGOALS)),)   # if not cleaning
  ifeq ($(wildcard gen/timestamp-gen_hps_src_files),) # if it hasn't been generated
    $(info ==============================================)
    $(info  Generating HPS source files)
    $(info ==============================================)
    $(if $(call DoShell, ./call_embedded_command_shell.sh $(OcpiAlteraQuartusDir)/../embedded $(OcpiAlteraLicenseFile), MyError),$(error $(MyError)))
    $(info Generation of source files Succeeded.)
  endif
endif

SourceFiles=cyclone5_pkg.vhd $(wildcard gen/*.sv) $(wildcard gen/*.v) cyclone5_hps.vhd

include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
