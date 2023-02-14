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

.PHONY: clean

# intentionally serial build/runs
all:
	$(MAKE) -C ../base/test -f .Makefile
	$(MAKE) -C ../ad9361/test -f .Makefile
	../base/test/build/test && ../ad9361/test/build/test

clean:
	$(MAKE) -C ../base/test -f .Makefile clean
	$(MAKE) -C ../ad9361/test -f .Makefile clean
