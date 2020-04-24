#!/bin/bash --noprofile
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
if [ -z "$OCPI_CDK_DIR" ]; then
  echo "The environment (specifically OCPI_CDK_DIR) is not set up."
  echo "You probably need to do \"source <wherever-the-cdk-is>/opencpi-setup.sh -s\"."
  exit 1
fi

usage () {
    cat <<-EOF
  Usage: ocpiav -h|--help|desktop|remove|run

    -h|--help   Show this message.

    desktop     Adds desktop environment "Applications" menu shortcut
                for running the AV GUI tool (creates "ocpiav.desktop"
                file in "~/.local/share/applications").

    remove      Removes the desktop environment menu shortcut
                (deletes "~/.local/share/applications/ocpiav.desktop").

    run         Runs the AV GUI tool.
EOF
    exit 1
}

[ -z "$1" -o "$1" = "-h" -o "$1" = "--help" ] && usage

file=~/.local/share/applications/ocpiav.desktop
case $1 in
  desktop)
    echo "Adding desktop environment menu item under \"Applications\" for running ocpiav tool."
    echo "This creates \"$file\"."
    mkdir -p ~/.local/share/applications
    sed "s-OCPI_CDK_DIR-$OCPI_CDK_DIR-" $OCPI_CDK_DIR/scripts/ocpiav.desktop > $file
    ;;
  remove)
    rm $file
    ;;
  run)
    if [ ! -x $OCPI_CDK_DIR/../av/eclipse/eclipse ]; then
	echo The OpenCPI AV GUI does not appear to be installed.
	exit 1
    fi
    exec $OCPI_CDK_DIR/../av/eclipse/eclipse> $OCPI_CDK_DIR/../av/av.log 2>&1 
    ;;
  *)
    echo "Illegal argument: $1" && usage
    ;;
esac
