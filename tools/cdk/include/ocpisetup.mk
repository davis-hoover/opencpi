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

# This make file fragment establishes gnumake variables for user Makefiles outside of projects,
# all based on OCPI_CDK_DIR, which must be set already and the environment set up.
# This means that a user makefile simply includes this file in their Makefile.
# FIXME: there should be a 
# Note you need two blank lines below
define OCPI_NL


endef
$(eval $(subst ;,$(OCPI_NL),\
  $(shell source $(OCPI_CDK_DIR)/opencpi-setup.sh -r; make -n -r -s -f $(OCPI_CDK_DIR)/include/setup-target-platform.mk ShellExternalVars=1)))
