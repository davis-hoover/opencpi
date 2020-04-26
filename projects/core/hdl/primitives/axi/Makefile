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

# We depend on sdp because we need to build the converter here due to parameterization
Libraries=ocpi platform fixed_float sdp
SourceFiles=axi_pkg.vhd
#SourceFiles=axi_pkg.vhd axi2cp.vhd axinull.vhd unoc2axi_rd.vhd unoc2axi_wd.vhd unoc2axi.vhd

################################################################################
# Generate per-interface VHDL packages and per-interface AXI modules
AxiInterfaces=$(patsubst axi_interface_%.h,%,$(wildcard axi_interface_*.h))
#  Assume all non-pkg VHDL files here need to be parameterized per interface
AxiModules=axi2cp sdp2axi_rd sdp2axi_wd sdp2axi axinull
AxiInterfacePackages=$(AxiInterfaces:%=gen/%_pkg.vhd)
AxiInterfaceModules=$(foreach i,$(AxiInterfaces),$(AxiModules:%=gen/%_$i.vhd))
$(infox AI:$(AxiInterfaces) AM:$(AxiModules) AIM: $(AxiInterfaceModules))
SourceFiles+= $(AxiInterfacePackages) $(AxiInterfaceModules)

# Create the module per interface by simply prepending the package reference
# $(call doInterfaceModule,module,interface)
all:


define doInterfacePackage
gen/$1_pkg.vhd: axi_interface_$1.h axi_interface.h | gen
	$$(AT)cpp -DNAME=$1 --include axi_interface_$1.h -std=c99 -xc -P  axi_interface.h | \
             sed '/^ *$$$$/d' > $$@
SourceFiles+=gen/$1_pkg.vhd
endef

define doInterfaceModule
$(infox DIM:$1:$2)
gen/$1_$2.vhd: gen/$2_pkg.vhd $1.vhd | gen
	$$(AT)tr "'" "~" < $1.vhd | cpp -P --include axi_interface_$2.h \
                  - | sed -e "s/AXI_INTERFACE/$2/" -e "s/~/'/g" > $$@
SourceFiles+=gen/$1_$2.vhd
endef

$(foreach i,$(AxiInterfaces),\
  $(eval $(call doInterfacePackage,$i))\
  $(foreach m,$(AxiModules),$(eval $(call doInterfaceModule,$m,$i))))
all: $(SourceFiles)
$(infox S:$(SourceFiles))

include $(OCPI_CDK_DIR)/include/hdl/hdl-lib.mk
