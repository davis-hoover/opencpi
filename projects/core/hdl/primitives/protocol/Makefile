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
  complex_short_with_metadata_pkg.vhd \
  complex_short_with_metadata_body.vhd \
  complex_short_with_metadata_demarshaller.vhd \
  complex_short_with_metadata_marshaller.vhd \
  complex_short_with_metadata_marshaller_old.vhd \
  out_port_cswm_samples_and_sync.vhd \
  iqstream_pkg.vhd \
  iqstream_body.vhd \
  iqstream_demarshaller.vhd \
  iqstream_marshaller.vhd \
  tx_event_pkg.vhd \
  tx_event_body.vhd \
  tx_event_demarshaller.vhd
include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
