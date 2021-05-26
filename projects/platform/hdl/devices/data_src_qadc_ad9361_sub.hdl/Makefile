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

# During the build process, swap HdlTarget with 'actual' target part of the target platform
# We do this to build for a part with the correct number of resources, such as hardware
# multipliers, rather than the default smallest part in the family
# zynq => xc7z020 (ZedBoard, Matchstiq-Z1, Picoflexor-T6A)
# virtex6 => xc6vlx240t (ml605 development board)
# alst4 => ep4sgx230k (Stratix4 development board)
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
  $(shell \
    ln -s ../data_sink_qdac_ad9361_sub.hdl/clock_divider.vhd clock_divider.vhd; \
    ln -s ../data_sink_qdac_ad9361_sub.hdl/clock_manager.vhd clock_manager.vhd; \
    ln -s ../data_sink_qdac_ad9361_sub.hdl/clock_selector_with_async_select.vhd clock_selector_with_async_select.vhd; \
    ln -s ../../../../assets/hdl/devices/ad9361_adc_sub.hdl/ad9361_adc_sub-build.xml data_src_qadc_ad9361_sub-build.xml;)
endif



HdlExactPart=\
        $(or $(and $(filter zynq_ise,$(HdlTarget)),xc7z020_ise_alias-1-clg484), \
        $(and $(filter zynq,$(HdlTarget)),xc7z020-1-clg484), \
        $(and $(filter zynq_ultra,$(HdlTarget)),xczu7ev-2-ffvc1156e), \
        $(and $(filter virtex6,$(HdlTarget)),xc6vlx240t-1-ff1156), \
        $(and $(filter stratix4,$(HdlTarget)),ep4sgx230k-c2-f40))

include $(OCPI_CDK_DIR)/include/worker.mk


clean::
	rm -f clock_divider.vhd # -> ../data_sink_qdac_ad9361_sub.hdl/clock_divider.vhd
	rm -f clock_manager.vhd # -> ../data_sink_qdac_ad9361_sub.hdl/clock_manager.vhd
	rm -f clock_selector_with_async_select.vhd # -> ../data_sink_qdac_ad9361_sub.hdl/clock_selector_with_async_select.vhd
	rm -f data_src_qadc_ad9361_sub-build.xml # -> ../../../../assets/hdl/devices/ad9361_adc_sub.hdl/ad9361_adc_sub-build.xml
