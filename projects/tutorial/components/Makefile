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

# This is the components library

# All workers created here in *.<model> will be built automatically
# All tests created here in *.test directories will be built/run automatically
# To limit the workers that actually get built, set the Workers= variable
# To limit the tests that actually get built/run, set the Tests= variable

# Any variable definitions that should apply for each individual worker/test
# in this library belong in Library.mk

#ExcludeWorkers=counter.hdl
#ExcludeTests=counter.test
# These exclusions were needed due to a naming collision between the
# "counter" worker and a "counter" primitive in the core project.
# When an assembly is built, the search path puts primitive libraries
# before other workers, and so when building the test assemblies for
# the "counter" worker, the assembly file (verilog) tried to instantiate
# the "counter" worker but got the "counter" primitive instead.  Renamed
# "counter" to "tcounter" to avoid the namespace collision.
include $(OCPI_CDK_DIR)/include/library.mk
