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

# This is the Makefile for the test directory which tests component "time_demux"

TestApplications = test_data_generator

include $(OCPI_CDK_DIR)/include/test.mk

# Our input generator depends on this file.
inputs: | gen/mytestdata

gen/mytestdata: | gen
	$(AT)echo Generating test data file: $@
	$(AT)rm -f gen/mytestdata && cp `which ocpirun` gen/mytestdata
