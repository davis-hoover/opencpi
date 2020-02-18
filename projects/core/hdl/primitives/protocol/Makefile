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

HdlLibraries=fixed_float ocpi util

# These need to be in order for most tools that aren't smart about figuring it out.
SourceFiles= \
  protocol_pkg.vhd \
  message_sizer.vhd \
  zlm_detector.vhd \
  complex_short_with_metadata/pkg.vhd \
  complex_short_with_metadata/body.vhd \
  complex_short_with_metadata/demarshaller.vhd \
  complex_short_with_metadata/marshaller.vhd \
  complex_short_with_metadata/marshaller_old.vhd \
  iqstream/pkg.vhd \
  iqstream/body.vhd \
  iqstream/marshaller.vhd
include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
