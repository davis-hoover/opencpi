#!/bin/bash
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

# See the "usage" message below
# "make" will run in parallel unless you set MAKE_PARALLEL to blank or null string (but defined)
# We set the default to 4 since using "-j" by itself blows up (infinite forks) on some systems.

################################################################################
# Retrieve items from the SDK that may be needed for deployment
# First arg is OcpiCrossCompile
# Second arg is dest dir
set -e
cross=$1
dest=$2
top=$(dirname $cross)/../$(basename $cross|sed 's/-$//')
places="libc/lib libc/usr/lib lib"
function getfile {
  if [ -L $1 ]; then
    link=$(readlink $1)
    if [[ $link == */* ]]; then
      file=${link//\//=} # change slashes to =
      dir=$(dirname $1)
      if [ -e $2/$file ]; then
	if ! cmp -s $dir/$file $2/$dir; then
          echo "Error: cannot overwrite symlinked non-local file '$1' => '$link'" && exit 1
        fi
      else
        cp -P $(dirname $1)/$link $2/$file
      fi
      ln -s $file $dest/lib/$(basename $1)
      return 0
    fi
  fi
  cp -P $1 $dest/lib
}

function getlib {
  for i in $places; do
    files=$(shopt -s nullglob; echo $top/$i/$1)
    if [ -n "$files" ]; then
      # Normally we could just copy all the files preserving symlinks, but there are
      # cases where the links point elsewhere out of the dir where we need to get that file too.
      for f in $files; do
        getfile $f $dest/lib
      done
      return 0
    fi
  done
  echo "WARNING: Cannot locate $1 in $top in any of these dirs below: $places"
}
rm -r -f $dest/lib
mkdir -p $dest/lib
getlib "libstdc++.so*"
getlib "libgcc_s.so*"
getlib "ld-*.so*"

