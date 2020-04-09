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

# Build Ordering Rules:
# 1) Subdevices that support other devices must occur AFTER the devices they support.
# 2) Similarly, Emulators must occur after the devices they emulate.
Workers = \
	data_src_adc.hdl \
	data_src_adc_ad9361_sub.hdl \
	data_src_adc_em.hdl \
	data_sink_dac.hdl \
	data_sink_dac_ad9361_sub.hdl \
	data_sink_dac_em.hdl

include $(OCPI_CDK_DIR)/include/library.mk
