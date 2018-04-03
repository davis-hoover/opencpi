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

# The default definitions for native RCC compilation
Gc_$(OCPI_TOOL_PLATFORM)=gcc -std=c99
Gc++_$(OCPI_TOOL_PLATFORM)=g++ -std=c++0x
Gc_LINK_$(OCPI_TOOL_PLATFORM)=gcc
Gc++_LINK_$(OCPI_TOOL_PLATFORM)=g++
Gc++_MAIN_LIBS_$(OCPI_TOOL_PLATFORM)=rt dl pthread
Gc++_MAIN_FLAGS_$(OCPI_TOOL_PLATFORM)=-Xlinker --export-dynamic
