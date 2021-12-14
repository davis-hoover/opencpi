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

# This file is the generic Makefile for .comp directories in component libraries.
# Note that these directories can contain unit tests for the component when
# there is a <component>-test.xml file is present.

$(if $(wildcard $(OCPI_CDK_DIR)),,$(error OCPI_CDK_DIR environment variable not set properly.))

include $(OCPI_CDK_DIR)/include/util.mk

ifneq ($(Model),comp)
  $(error This directory, $(Cwd), does not end with the .comp suffix)
endif

# If there is a unit test suite in this component directory, then include the file for that
ifneq ($(wildcard $(CwdName)-test.xml),)
  include $(OCPI_CDK_DIR)/include/test.mk
else
  ifeq ($(filter clean%,$(MAKECMDGOALS)),)
    $(call OcpiIncludeAssetAndParent)
  endif
endif
ifeq ($(filter clean%,$(MAKECMDGOALS)),)
  # $(if $(call DoShell,make -C $(DirContainingLib) $(OcpiLibraryMakefile) speclinks,Value),$(warning $(Value)))
  # For now, make sure there is an rst file of some type.
  OcpiRstFiles:=$(wildcard *.rst)
  # generate an appropriate one if none exists
  ifndef OcpiRstFiles
    $(CwdName)-spec.rst:
	$(AT)cat > $@ <<-EOF \
		.. _$(CwdName):\
		The $(CwdName) component
    all: $(CwdName)-spec.rst
  endif
endif

clean::
	$(AT)rm -r -f $(GeneratedDir)
all:
	$(AT) ocpidoc build

ifneq (,)
ocpidoc needs to be supplied with the XML include paths per platform.cc.
That function needs variables set in the project in the makefiles (projectreldir)
So the python world of ocpidev does not have them.
So we need "make", when building, to get the right path and then call ocpidoc.

So the toctree stuff needs to use symlinks in gen subdirs?

The HTML has refs to the rst files.

So if we generate, e.g. componpents/gen/components.rst, then it will generate components/gen/components.html etc.

But all the existing files do stuff.
So for any given level, we have a prefix file (or not),
and then as add the toctree to it in the gen dir.
So it is our automation that generates the toc tree.
So each level does it:

projects:
   components/components
   hdl/primitives/primitives
   specs/specs
   CHANGELOG
components:
   */*-library
componentlibraries:
   *.comp/*-index
primitives:
   */*-library
primitivelibraries:
   */*-primitive


But we need a depth-first algorithm to build the intermediate things, in gen dirs.

endif
