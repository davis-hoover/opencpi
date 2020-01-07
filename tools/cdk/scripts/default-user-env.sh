# This file specifies user-specified environment variable settings for OpenCPI during development.
# It is sourced, not executed.
# There are no variables that are required to be set, since having them not set is always the default.
# When there are no uncommented export commands in this file, it is not used/sourced.
# When there are export commands in this file, it will be *sourced* when OpenCPI's own environment setup script
# is sourced to set the the user-specified non-default values for the development environment.
# This file must not depend on any variables being set to any particular values before it is sourced.

# This file is meant to provide non-default values for environment variables that are used
# during development.   A runtime-only environment would not use this file.

# The following line should be preserved and helps recognize when a user has edited this file based on
# an older version, and thus should be informed that it should be re-edited based on the newer one
# VERSION 1

####################################################################################################
####################################################################################################
# Xilinx tool-related variables.
# Normally the defaults are used since they represent the defaults used by the Xilinx tool installers.
# None of them are normally set unless the installation of Xilinx tools is complex, e.g. using a variety of
# versions where the desired one is not the latest one etc.
# The older tools are ISE (for simulation and synthesis) and EDK (for cross-compilers)
# The newer tools are Vivado (for simulation and synthesis) and SDK (for cross-compilers)
# Recently the tool called "Vitis" covers what was previously done by "SDK".
# The "labtools" package is considered a separate tool.  See below.

# OCPI_XILINX_DIR specifies the top level directory where Xilinx tools are installed.
# If not specified, both the /opt/Xilinx and /tools/Xilinx directories are looked for, in that order.
# These are the defaults offered by the Xilinx tool installers.  Even if the tools are installed elsewhere
# it is usually preferable to put a symbolic link in one of these default locations rather than setting this
# environment variable.
# export OCPI_XILINX_DIR=/opt/Xilinx

# OCPI_XILINX_LICENSE_FILE specifies the location of the license file for Xilinx tools
# If not specified, the file Xilinx-License.lic is used in the $OCPI_XILINX_DIR directory.
# Note that no license file is required if using recent WebPack versions of xilinx tools.
# license file can be: <port>@<server.ip.addr>
# export OCPI_XILINX_LICENSE_FILE=

# OCPI_XILINX_VERSION specifies the version of Xilinx tools to be used.
# If not specified, the most recent version found is used, for any tools that are used.
# export OCPI_XILINX_VERSION=

####################################################################################################
# Xilinx Vivado-specific variables, that more specifically override the variables above.
# Only used when Vivado is used with other tools and the locations or versions are different.

# OCPI_XILINX_VIVADO_DIR specifies where *all* versions of Xilinx Vivado are installed.
# If not specified, the directory $OCPI_XILINX_DIR/Vivado is used.
# export OCPI_XILINX_VIVADO_DIR=xxx

# OCPI_XILINX_VIVADO_VERSION specifies which version of Vivado should be used
# If not specified, OCPI_XILINX_VERSION is used (or the latest version if that is not set)
# export OCPI_XILINX_VIVADO_VERSION=xxx


# OCPI_XILINX_VIVADO_TOOLS_DIR specifies the location of a specific version of Xilinx Vivado that should be used
# If not specified, the directory $OCPI_XILINX_DIR/Vivado/$OCPI_XILINX_VERSION is used.
# export OCPI_XILINX_VIVADO_DIR=xxx

# OCPI_XILINX_VIVADO_LICENSE_FILE specifies the location of the Vivado license file
# If not specified, the file $OCPI_XILINX_VIVADO_DIR/Vivado/Xilinx-License.lic is used
# license file can be: <port>@<server.ip.addr>
# export OCPI_XILINX_VIVADO_DIR=xxx

####################################################################################################
# Xilinx SDK-specific variables, that more specifically override the variables above.
# Only used when the SDK from Vivado is used with other tools and the locations or versions are different.

# OCPI_XILINX_VIVADO_SDK_VERSION is used when the SDK version is different from the Vivado version.
# If not specified, the version of Vivado determines the version of the SDK


####################################################################################################
# Xilinx ISE-specific (older tools) variables, that more specifically override the OCPI_XILINX_DIR and
# OCPI_ variables above.
# Only used when ISE is used with other tools and the locations or versions are different.

# OCPI_XILINX_TOOLS_DIR specifies the location of the Xilinx ISE tools directory.
# If not specified, the $OCPI_XILINX_DIR/$OCPI_XILINX_VERSION/ISE_DS is used.
# export OCPI_XILINX_TOOLS_DIR=

# OCPI_XILINX_EDK_DIR specifies the location of the Xilinx ISE EDK tools directory.
# This is the cross-compiler tool set provided with ISE.
# If not specified, the $OCPI_XILINX_DIR/$OCPI_XILINX_VERSION/ISE_DS/EDK directory is used.
# export OCPI_XILINX_EDK_DIR=

####################################################################################################
# Xilinx LABTOOLS-specific variables, that more specifically override the OCPI_XILINX_DIR and
# OCPI_ variables above.  This tool is used by OpenCPI for loading bitstreams or initializing
# flash memories using JTAG.

# OCPI_XILINX_LAB_TOOLS_DIR specifies the location of the separately installed LABTOOLS package.
# If not specified, with $OCPI_XILINX_DIR/$OCPI_XILINX_VERSION as a starting point, the tools are
# first sought at $OCPI_XILINX_DIR/$OCPI_XILINX_VERSION/LabTools, and if not present,
# then $OCPI_XILINX_DIR/$OCPI_XILINX_VERSION/ISE_DS.
# export OCPI_XILINX_LAB_TOOLS_DIR=

####################################################################################################
####################################################################################################
# Intel/Altera tool-related variables.
# Normally the defaults are used since they represent the defaults used by the Xilinx tool installers.
# None of them are normally set unless the installation of Xilinx tools is complex, e.g. using a variety of
# versions where the desired one is not the latest one etc.



####################################################################################################
####################################################################################################
# MODELSIM tool-related variables.
# Normally the defaults are used since they represent the defaults used by the Xilinx tool installers.
# None of them are normally set unless the installation of Xilinx tools is complex, e.g. using a variety of
# versions where the desired one is not the latest one etc.

# OCPI_MODELSIM_DIR specifies the top level directory where modelsim installed.
# export OCPI_MODELSIM_DIR=xxx

# OCPI_MODELSIM_LICENSE_FILE specified the modelsim license file to be used
# license file can be: <port>@<server.ip.addr>
# export OCPI_MODELSIM_LICENSE_FILE=ssdf

return 0


OCPI_ALTERA_DIR
OCPI_ALTERA_VERSION
OCPI_ALTERA_LICENSE_FILE

# Project registry-related when you want separate sets of projects not globally registered
# I.e. not the installation
OCPI_PROJECT_REGISTRY_DIR
OCPI_PROJECT_PATH

# runtime
OCPI_SYSTEM_CONFIG --- runtime - but infrequently used to override installation default
OCPI_LIBRARY_PATH --- runtime - execution outside of projects outside the dev environment
OCPI_LOG_LEVEL


/opt/Xilinx/Xilinx-License.lic
• /opt/Xilinx/Vivado/Xilinx-License.lic
OCPI_REMOTE_TEST_SYSTEMS

