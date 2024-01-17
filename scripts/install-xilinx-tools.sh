#!/bin/bash
#
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
#
# N.B: all Xilinx tool installation prerequisites must be satisfied.
# No error checking of any kind is performed by *this* script in that
# regard.  Among other prerequisites are these in particular:
#
#  (1) Must have a valid account at https://www.xilinx.com.
#  (2) Must have a working Java runtime installed.
#  (3) Must have enough available disk space to handle both the
#      expansion of the Xilinx Unified Installer file and the items
#      downloaded during installation (into INSTALL_DIR/Downloads).
#      The installer normally checks for the latter.
#
# Bottom line: the OpenCPI Installation Guide is an appropriate
# reference to have handy when running this script.
#
read -p 'Xilinx Unified Installer file: ' XIF
if [ ! -f "$XIF" ]
then
    echo "Error: specified installer file ($XIF) does not exist" >&2
    exit 1
fi

#
# Get the Xilinx tools version: it is part of the file name.
#
XVER=`basename $XIF | cut -f3 -d'_'`

#
# Versions of Xilinx prior to 2021.1 also require "WebTalkTerms".
#
if (( $(echo "$XVER < 2021.1" | bc -l) ))
then
    AGREE="XilinxEULA,3rdPartyEULA,WebTalkTerms"
else
    AGREE="XilinxEULA,3rdPartyEULA"
fi

XDIR=$(dirname $XIF)/$XVER
read -p "Extraction directory [$XDIR]: " XExDIR
bash $XIF --noexec --nox11 --target ${XExDIR:-$XDIR}
(
  cd ${XExDIR:-$XDIR}
  #
  # xsetup requires console access, i.e.,
  # it will NOT read the Xilinx account e-mail
  # address and password from a here document.
  #
  ./xsetup -b AuthTokenGen
  #
  # generate default batch config file
  #
  echo -e "\nNow generating the default batch config file for the installation."
  echo "Please answer a few questions as to which product you plan to install."
  echo "For 2019.2, specify \"Vivado\", and for later releases, specify \"Vitis\"."
  ./xsetup -b ConfigGen
  #
  # modify default config file to taste
  #
  echo -e "\nWhen EDITOR is invoked on the default batch config file that was"
  echo "just created, you will have an opportunity to set various installation"
  echo "parameters such as the installation directory, whether to create"
  echo "program groups, shortcuts, file associations, etc. -- this is exactly"
  echo "analogous to the checkboxes in the installation GUI as described in"
  echo "the OpenCPI Installation Guide.  Refer to the OIG if the comments in"
  echo "the config file prove insufficient.  Although the installation process"
  echo "will take considerably more time, \"EnableDiskUsageOptimization=1\""
  echo -e "is strongly encouraged.\n"
  read -p 'Preferred text editor [vi]: ' EDITOR
  ${EDITOR:-vi} ~/.Xilinx/install_config.txt
  ./xsetup --agree $AGREE --batch Install --config ~/.Xilinx/install_config.txt
)
echo "All done!"
