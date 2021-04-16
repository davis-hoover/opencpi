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

#TODO: These are internal headers which should not be included directly
#      Anything from them exposed to the ACI should be in Ocpi*Api.h files
#      https://gitlab.com/opencpi/opencpi/issues/887
IncludeDirs+=\
	../../../../runtime/util/driver/include/ \
	../../../../runtime/util/ezxml/include/ \
	../../../../runtime/util/misc/include/ \
	../../../../runtime/util/parentChild/include/ \
	../../../../runtime/util/property/include/ \
	../../../../runtime/util/vfs/include/ \
	../../../../os/interfaces/include/

include $(OCPI_CDK_DIR)/include/application.mk
