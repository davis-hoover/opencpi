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
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
  $(shell \
    ln -s ../../../../assets/hdl/devices/ad9361_dac_sub.hdl/ad9361_dac_sub-build.xml data_sink_qdac_csts_ad9361_sub-build.xml;)
endif


HdlExactPart=\
        $(or $(and $(filter zynq_ise,$(HdlTarget)),xc7z020_ise_alias-1-clg484), \
        $(and $(filter zynq,$(HdlTarget)),xc7z020-1-clg484), \
        $(and $(filter zynq_ultra,$(HdlTarget)),xczu7ev-2-ffvc1156e)) 

include $(OCPI_CDK_DIR)/include/worker.mk

clean::
	rm -f data_sink_qdac_csts_ad9361_sub-build.xml
