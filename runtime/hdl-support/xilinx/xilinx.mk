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

ifndef _XILINX_MK
export SHELL=/bin/bash
_XILINX_MK=1
# Functions to retrieve and default pathnames for Xilinx tools
# FIXME: it may be worth caching these singular values
# The functions to retrieve dirs take an optional second argument which is used in place of
# "error" in error messages.  This is used when the caller wants an empty return rather than
# an error

OcpiXilinxDir=$(strip $(foreach t,$(or $(OCPI_XILINX_DIR),/opt/Xilinx),$(infox TT is $t)\
		 $(if $(shell test -d $t && echo 1),$t,\
		    $(call $(or $1,error), Directory "$t" for OCPI_XILINX_DIR not found))))

OcpiXilinxLicenseFile=$(strip $(foreach t,$(or $(OCPI_XILINX_LICENSE_FILE),\
                                               $(call OcpiXilinxDir,$1)/Xilinx-License.lic),\
			 $(if $(or $(findstring @,$t),$(findstring :,$t),$(shell test -f $t && echo 1)),$t,\
			    $(if $(OCPI_XILINX_LICENSE_FILE),\
                              $(call $(or $1,error), File "$t", for OCPI_XILINX_LICENSE_FILE, not found),\
			      $(warning, No license file specified in OCPI_XILINX_LICENSE_DIR and default one in $t is nonexistent.  Webpack installations may still work.)))))

OcpiXilinxIseDir=$(strip\
$(foreach t,$(OcpiXilinxDir),\
  $(foreach i,\
    $(or $(OCPI_XILINX_TOOLS_DIR),\
      $(foreach v,\
        $(if $(filter-out undefined,$(origin OCPI_XILINX_VERSION)),\
          $(foreach e,$(OCPI_XILINX_VERSION),\
            $(if $(shell test -d $t/$e && echo 1),$e,\
              $(call $(or $1,error), Directory "$t/$e" for OCPI_XILINX_VERSION not found))),\
          $(or $(shell for i in \
                        `shopt -s nullglob && echo $t/*  | tr ' ' '\n' | sort -n -r`; \
                       do \
                         [ -d $$i -a -d $$i/ISE_DS ] && echo `basename $$i` && break; \
                       done),\
            $(call $(or $1,error), No version directory under $t/*/ISE_DS for Xilinx ISE))),\
        $(infox VV:$v)$(call OcpiXilinxDir,$1)/$v/ISE_DS)),\
    $(infox II:$i.)\
    $(if $(shell test -d $i && echo 1),$i,\
      $(call $(or $1,error), Directory "$i", in OCPI_XILINX_TOOLS_DIR for ISE, not found)))))

# We call this if all we really need is lab tools (e.g. impact)
# First look for lab tools, then look for ise
OcpiXilinxLabToolsDir=$(strip\
$(if $(OCPI_XILINX_LAB_TOOLS_DIR),\
  $(foreach d,$(OCPI_XILINX_LAB_TOOLS_DIR),\
    $(or $(shell test -d $d/LabTools && echo $d/LabTools),\
      $(call $(or $1,error),OCPI_XILINX_LAB_TOOLS_DIR, $d, missing or has no LabTools subdirectory))),\
  $(foreach t,$(call OcpiXilinxDir,$1),$(infox TOP:$t)\
      $(foreach v,\
        $(if $(filter-out undefined,$(origin OCPI_XILINX_VERSION)),\
          $(foreach e,$(OCPI_XILINX_VERSION),\
          $(or $(shell test -d $t/$e && echo $e),\
              $(call $(or $1,error), Directory "$t/$e", for OCPI_XILINX_VERSION, not found))),\
        $(or $(shell \
               for i in `shopt -s nullglob && echo $t/*  | tr ' ' '\n' | sort -n -r`; \
                       do \
                   [ -d "$$i/LabTools" -o -d "$$i/ISE_DS" ] && echo `basename $$i` && break; \
                       done),\
            $(call $(or $1,error), No version directory under $t for Xilinx ISE or LabTools))),\
      $(or $(wildcard $t/$v/LabTools/LabTools),$(wildcard $t/$v/ISE_DS/ISE),\
        $(call $(or $1,error), Directory $t/$v has no ISE or LabTools under it))))))

# This looks for the (ISE) edk dir. It does not consider Vivado installations
OcpiXilinxEdkDir=$(strip\
 $(foreach d,$(or $(OCPI_XILINX_EDK_DIR),$(call OcpiXilinxIseDir,$1)/EDK),\
   $(infox EDK:$d)$(if $(shell test -d $d && echo 1),$d,\
                     $(call $(or $1,error), Directory "$d", for OCPI_XILINX_EDK_DIR, not found))))

# This looks for the Vivado SDK dir OR the ISE EDK dir
OcpiXilinxEdkOrSdkDir=$(strip\
 $(foreach d,\
   $(or $(OCPI_XILINX_EDK_DIR),$(call OcpiXilinxSdkDir,warning),$(warning Checking for ISE EDK since Vivado SDK was not found)$(call OcpiXilinxIseEdkDir,$1)),\
   $(infox EDK:$d)$(if $(shell test -d $d && echo 1),$d,\
                     $(call $(or $1,error), Directory "$d", for OCPI_XILINX_EDK_DIR, not found))))

# The "set -e" is to force an error if the settings64.sh has problems
OcpiXilinxIseInit=\
  set -e ; \
  . $(OcpiXilinxIseDir)/settings64.sh $(and $1,> $1); \
  export LM_LICENSE_FILE=$(OcpiXilinxLicenseFile)

# Looks for the Vivado SDK dir
OcpiXilinxSdkDir=$(strip\
$(foreach t,$(OcpiXilinxDir)/SDK,$(shell > /dev/tty echo vt:$t:$(OCPI_XILINX_VIVADO_SDK_VERSION))\
  $(foreach i,\
      $(foreach v,\
        $(if $(filter-out undefined,$(origin OCPI_XILINX_VIVADO_SDK_VERSION)),\
          $(foreach e,$(OCPI_XILINX_VIVADO_SDK_VERSION),\
            $(if $(shell test -d $t/$e && echo 1),$e,\
              $(call $(or $1,error), Directory "$t/$e", for OCPI_XILINX_SDK_VIVADO_VERSION, not found))),\
          $(or $(shell for i in \
                        `shopt -s nullglob && echo $t/*  | tr ' ' '\n' | sort -n -r`; \
                       do \
                         [ -d $$i -a -r $$i/settings*.sh ] && echo `basename $$i` && break; \
                       done),\
            $(call $(or $1,error), No valid version directory under $t/* for Xilinx Vivado SDK))),\
        $(infox VV:$v)$(call OcpiXilinxDir,$1)/SDK/$v),\
    $(infox II:$i.)\
    $(if $(shell test -d $i && echo 1),$i,\
      $(call $(or $1,error), Directory "$i", in $$OCPI_XILINX_DIR/SDK, not found)))))


# Return the directory where Vivado lives, which as a default is usually /opt/Xilinx/Vivado
OcpiXilinxTryVivadoDir=$(strip $(foreach t,$(or $(OCPI_XILINX_VIVADO_DIR),$(foreach x,$(call OcpiXilinxDir,),$x/Vivado)),$(infox TT is $t)\
		 $(if $(shell test -d $t && echo 1),$t,\
		    $(call $(or $1,error), Directory "$t" for OCPI_VIVADO_XILINX_DIR or OCPI_XILINX_DIR not found))))

# When getting the VIVADO_VERSION, first check OCPI_XILINX_VIVADO_VERSION,
# then fall back on OCPI_XILINX_VERSION ONLY IF it does NOT start with '0' or '1' which are reserved for ISE.
OcpiXilinxVivadoDir=$(strip\
$(foreach t,$(OcpiXilinxTryVivadoDir),$(infox vt:$t)\
  $(foreach i,\
    $(or $(OCPI_XILINX_VIVADO_TOOLS_DIR),\
      $(foreach v,\
        $(if $(or $(filter-out undefined,$(origin OCPI_XILINX_VIVADO_VERSION)),$(and $(filter-out undefined,$(origin OCPI_XILINX_VERSION)),$(filter-out  0% 1%,$(OCPI_XILINX_VERSION)))),\
          $(foreach e,$(or $(OCPI_XILINX_VIVADO_VERSION),$(OCPI_XILINX_VERSION)),\
            $(if $(shell test -d $t/$e && echo 1),$e,\
              $(call $(or $1,error), Directory "$t/$e", for OCPI_XILINX_VIVADO_VERSION (or OCPI_XILINX_VERSION), not found))),\
          $(or $(shell for i in \
                        `shopt -s nullglob && echo $t/*  | tr ' ' '\n' | sort -n -r`; \
                       do \
                         [ -d $$i -a -r $$i/settings64.sh ] && echo `basename $$i` && break; \
                       done),\
            $(call $(or $1,error), No version directory under $t/* for Xilinx Vivado))),\
        $(infox VV:$v)$(call OcpiXilinxTryVivadoDir,$1)/$v)),\
    $(infox II:$i.)\
    $(if $(shell test -d $i && echo 1),$i,\
      $(call $(or $1,error), Directory "$i", in OCPI_XILINX_VIVADO_DIR, not found)))))

# Here we first check for an explicitly set license path.
# Then, we check for common/default location for a Vivado license
# Finally, we resort to checking for the plain/ISE Xilinx license
OcpiXilinxVivadoLicenseFile=$(strip\
  $(foreach t,$(or $(OCPI_XILINX_VIVADO_LICENSE_FILE),\
                $(wildcard $(call OcpiXilinxTryVivadoDir,$1)/Xilinx-License.lic),$(call OcpiXilinxLicenseFile,$1)),\
    $(if $(or $(findstring @,$t),$(findstring :,$t),$(shell test -f $t && echo 1)),$t,\
      $($(or $1,error) File "$t", for OCPI_XILINX_VIVADO_LICENSE_FILE, not found))))

OcpiXilinxVivadoInit=\
  set -e; \
  . $(OcpiXilinxVivadoDir)/.settings64-Vivado.sh $(and $1,> $1); \
  $(if $(OcpiXilinxVivadoLicenseFile),,\
    echo Warning: No Vivado license file specified or found, which is ok with recent WebPack versions/parts.;) \
  export LM_LICENSE_FILE=$(OcpiXilinxVivadoLicenseFile)


# emit shell assignments - allowing errors etc.
ifdef ShellIseVars

XilinxCheck=ignore
all:

$(info OcpiXilinxIseDir=$(call OcpiXilinxIseDir,$(XilinxCheck));\
       OcpiXilinxEdkOrSdkDir=$(call OcpiXilinxEdkOrSdkDir,$(XilinxCheck));\
       OcpiXilinxIseEdkDir=$(call OcpiXilinxIseEdkDir,$(XilinxCheck));\
       OcpiXilinxLabToolsDir=$(call OcpiXilinxLabToolsDir,$(XilinxCheck));\
       OcpiXilinxVivadoDir=$(call OcpiXilinxVivadoDir,$(XilinxCheck));\
       OcpiXilinxSdkDir=$(call OcpiXilinxSdkDir,$(XilinxCheck));\
       OcpiXilinxLicenseFile=$(call OcpiXilinxLicenseFile,$(XilinxCheck));\
       OcpiXilinxVivadoLicenseFile=$(call OcpiXilinxVivadoLicenseFile,$(XilinxCheck)))

endif

endif
