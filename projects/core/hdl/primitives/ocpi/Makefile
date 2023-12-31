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

# This primitive library contains VHDL primitive modules that are used
# by all workers

# the generated entities for each property type
Types=bool char double float short long uchar ulong ushort longlong ulonglong string
TypeEntities=$(foreach t,$(Types),$t_property $t_array_property $t_read_property $t_read_array_property)
TypeFiles=$(TypeEntities:%=gen/%.vhd)

# These need to be in order for most tools that aren't smart about figuring it out.
SourceFiles=ocp_pkg.vhd types_pkg.vhd util_pkg.vhd wci_pkg.vhd wsi_pkg.vhd ocpi_worker.vhd \
            util_body.vhd types_body.vhd wci_body.vhd wsi_body.vhd \
            property_decoder.vhd decoder.vhd readback.vhd no_props_decoder.vhd \
            gen/props_pkg.vhd \
	    master.vhd slave.vhd  \
	    part_master.vhd part_slave.vhd  \
	    message_bounds.vhd clock_limiter.vhd zlm_detector.vhd \
	    raw_arb.vhd delayline.vhd\
	    $(TypeFiles)

include $(OCPI_CDK_DIR)/include/hdl/hdl-lib.mk # we are a primitive library

CPP_TO_VHD=\
 gcc -E -P -std=c99 -xc $< | tr '$$' '\n' | tr '@' ' ' | tr '~' "'" | sed '/^ *$$/d' > $@

gen/proptypes.gen: proptypes.cpp_gen
	$(AT)$(CPP_TO_VHD)

$(TypeFiles): gen/proptypes.gen
	$(AT)sed -e '1,/^-- FILE: $(@:gen/%.vhd=%)/d' -e '/^-- END:/,$$d' $< > $@

CPPFiles=$(wildcard *.cpp_vhd)
GenFiles=$(CPPFiles:%.cpp_vhd=gen/%.vhd)
$(GenFiles): gen/%.vhd : %.cpp_vhd | gen
	$(AT)echo Preprocessing $< into $@:
	$(AT)$(CPP_TO_VHD)
