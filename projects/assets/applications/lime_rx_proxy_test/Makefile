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

RccOnlyPlatforms+=centos7 xilinx13_3

include $(OCPI_CDK_DIR)/include/application.mk

.SILENT: show
.PHONY: clean show

clean::
	rm -rf odata/*
	rm -rf target-*

show:
	echo "$$showhelp"

define showhelp
----------------------------------------------------------------------------
----------------------------------------------------------------------------
The instructions below are used to execute an application on a remote
platform like the Matchstiq-Z1 or Zedboard/Zipper.

There are four steps for executing an application:
1) Build ACI and/or input test data (development system)
2) Setup the OCPI_LIBRARY_PATH (remote system)
3) Execution of application (remote system)
4) Verification of output data (development system)
----------------------------------------------------------------------------
1) Build ACI and/or input test data: (development system)
NOTE: Required only if test data has never been built.
ocpidev build --rcc-platform xilinx13_3
or
ocpidev build --rcc-platform xilinx13_4
----------------------------------------------------------------------------
2) Setup the OCPI_LIBRARY_PATH: (remote system)

NOTE: Reminder to setup the run-time OCPI environment on remote system.
. /mnt/card/opencpi/mynetsetup.sh {DEVELOPMENT HOST IPADDRESS}

NOTE: Convenience cmd to quickly switch to application directory.
cd /mnt/ocpi_assets/applications/lime_rx_proxy_test

a) REQUIRED - Reconfigure to default.
Copy/paste string to terminal of remote system:
export OCPI_LIBRARY_PATH=/mnt/ocpi_assets/hdl/assemblies/empty/container-empty_matchstiq_z1_matchstiq_z1_rx_cnt_1rx_0tx_bypassasm_matchstiq_z1

b) REQUIRED - Configure for operation.
Copy/paste string to terminal of remote system:
export OCPI_LIBRARY_PATH+=:$$OCPI_CDK_DIR/$$OCPI_TOOL_PLATFORM/artifacts:/mnt/ocpi_assets/artifacts
NOTE: When copy/paste of the above 'export' from the Makefile source file, the redundant '$' must be manually removed.
----------------------------------------------------------------------------
3) Execution of application is specific to platform: (remote system)
./target-xilinx13_3/lime_rx_proxy_test
----------------------------------------------------------------------------
4) Verification of output data: (development system)
(Matchstiq-Z1): 
./scripts/plotAndFft.py odata/lime_rx_proxy_test_app.out complex 300000 0.1 &
(Zedboard): 
./scripts/plotAndFft.py odata/lime_rx_proxy_test_app.out complex 1500000 0.5 &
----------------------------------------------------------------------------
----------------------------------------------------------------------------
endef
export showhelp
