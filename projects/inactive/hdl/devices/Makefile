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

# This is the hdl/devices library

# All workers created here in *.<model> will be built automatically
# All tests created here in *.test directories will be built/run automatically
# To limit the workers that actually get built, set the Workers= variable
# To limit the tests that actually get built/run, set the Tests= variable

# Any variable definitions that should apply for each individual worker/test
# in this library belong in Library.mk

## These two require support for embedded IOBUFs which is currently turned off
#	dram_v5.hdl \
#	dram_v6.hdl \

Workers=\
	adcx.hdl \
        dac.hdl \
	gbe.hdl \
	icap.hdl \
	lime_spi_em.hdl \
	lime_tx_em.hdl \
        data_sink_qdac_cswm.hdl \
        data_sink_qdac_cswm_ad9361_sub.hdl \
        data_sink_qdac_cswm_em.hdl \
        data_src_qadc_cswm.hdl \
        data_src_qadc_cswm_ad9361_sub.hdl \
        data_src_qadc_cswm_em.hdl \


Tests=

include $(OCPI_CDK_DIR)/include/library.mk
