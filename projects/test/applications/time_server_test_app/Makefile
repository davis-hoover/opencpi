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
# This is the application Makefile for the "time_server_test_app" application
# If there is a time_server_test_app.cc (or time_server_test_app.cxx) file, it will be assumed to be a C++ main program to build and run
# If there is a time_server_test_app.xml file, it will be assumed to be an XML app that can be run with ocpirun.
# The RunArgs variable can be set to a standard set of arguments to use when executing either.

#Check for time_server_test_assy bitfiles before executing
#This guard should be removed when Issue #99 is resolved
ifeq ($(wildcard ../../artifacts/*time_server_test_assy*),)
 $(info No time_server_test_assy assembly built in this project. Skipping application run.)
 OcpiAppNoRun=1
 run:
endif

APP=test_app

include $(OCPI_CDK_DIR)/include/application.mk

clean::
	rm -rf simulations
