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

$(if $(realpath $(OCPI_CDK_DIR)),,$(error The OCPI_CDK_DIR environment variable is not set correctly.))

.SILENT: show
.PHONY: clean show

# build unit test input data
all:
	./scripts/gen_rrcos_taps.py 128 0.95 `echo "1/64000" | bc -l` 3200000 4096 idata/tx_rrcos_taps.dat
	./scripts/gen_rrcos_taps.py 128 0.95 `echo "1/64000" | bc -l` 3200000 4096 idata/rx_rrcos_taps.dat

clean::
	rm -rf odata/* scripts/*.pyc

show:
	echo "$$showhelp"

define showhelp
----------------------------------------------------------------------------
Instructions for setup/execution on remote platforms '(i.e. Matchstiq-Z1, Zedboard)'
These steps may be repeated to test each available HDL assembly
----------------------------------------------------------------------------
----------------------------------------------------------------------------
Setup:
----------------------------------------------------------------------------
Development Computer - generate filter coefficients
'make'
----------------------------------------------------------------------------
Zynq-Based Platform - setup environment
. /mnt/card/opencpi/mynetsetup.sh {IPADDRESS}
cd /mnt/ocpi_assets/applications/zp_16i16o_fir_real_fir_real

HDL:
export OCPI_LIBRARY_PATH=$$OCPI_ROOT_DIR/projects/core/exports/lib/components/rcc:$$(pwd)/../../hdl/assemblies/$${PWD##*/}:$$(pwd)/../../exports/lib

#NOTE: If copy/paste of the above exports, the redundant '$' must be removed.
----------------------------------------------------------------------------
----------------------------------------------------------------------------
Execution:
----------------------------------------------------------------------------
Zynq-Based Platform - execute
HDL: 'ocpirun -v -d app_zp_16i16o_fir_real_fir_real_filerw.xml'
HDL: 'ocpirun -v -d app_zp_16i16o_fir_real_fir_real_baudtrack_filerw.xml'
HDL: 'ocpirun -v -d app_zp_16i16o_fir_real_fir_real_baudtrack_digitizer_filerw.xml'
----------------------------------------------------------------------------
Development Computer - verify output data
'./scripts/plotAndFft.py odata/out_app_zp_16i16o_fir_real_fir_real_filerw.bin real 8192 1 &'
'./scripts/plotAndFft.py odata/out_app_zp_16i16o_fir_real_fir_real_baudtrack_filerw.bin real 8192 1 &'
'./scripts/plotAndFft.py odata/out_app_zp_16i16o_fir_real_fir_real_baudtrack_digitizer_filerw.bin real 4096 1 &'
----------------------------------------------------------------------------
endef
export showhelp

include $(OCPI_CDK_DIR)/include/application.mk
