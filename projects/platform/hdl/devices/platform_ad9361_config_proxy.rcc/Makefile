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

#RccStaticPrereqLibs=ad9361

# Our "platform" functions that the ADI library calls
#SourceFiles=ad9361_platform.cc

RccIncludeDirs+=./supporting/include/OCPIProjects/
RccIncludeDirs+=./supporting/src/OCPIProjects/

include $(OCPI_CDK_DIR)/include/worker.mk

# if someone happened to run doxygen, this will clean it up
clean::
	$(AT)rm -rf supporting/html/ supporting/latex/
