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

# The zed_ise platform, mostly copied from zed

include $(OCPI_CDK_DIR)/include/util.mk

# Clone what we can from the zed platform
# Source code can be sym-linked
# Extract configurations *from zed_ise xml* and symlink to them in zed (except base)
# OWD cannot be symlinked - it has part numbers and platform names
# So OWD is original here and must be updated if zed.xml is updated.
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
  $(shell \
    test -e zed_ise.vhd || ln -s ../zed/zed.vhd zed_ise.vhd; \
    for c in $$(ocpixml -t hdlplatform -a '?configurations' parse zed_ise.xml); do \
    test -e zed_ise-build.xml || ln -s ../zed/zed-build.xml zed_ise-build.xml; \
    test -e zed_ise.xml || sed "s/value='zed'/value='zed_ise'/" ../zed/zed.xml > zed_ise.xml;\
      [ $$c = base ] || [ -e $$c.xml ] || ln -s ../zed/$$c.xml .;\
    done)
endif

include $(OCPI_CDK_DIR)/include/hdl/hdl-platform.mk

clean::
	rm -f zed_ise.vhd
	for x in *.xml; do [ $$x = zed_ise.xml ] || rm $$x; done
