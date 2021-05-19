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

################################################################################
# Access the xilinx release tarball(s) for a Xilinx release and put the files
# in a normalized form even though the Xilinx tarballs are not the same structure for different releases
# Three args:
# 1. This release version (e.g. 2019.1)
# 2. The location of the xilinx release downloads/tarballs (downloaded separately using click-through manual query)
# 3. The name of the dir to put it all in
# 4. The location of the built xilinx git kernel and u-boot repo
#
# The script will remove and thencreate a directory that will have subdirs for each hdl platform, and within
# each subdir there will be "root" and "boot" subdirectory.

version=$1
releases=$2
dir=$3
local_repo=$4
set -e
[ -z "$dir" ] && echo Error: no directory argument && exit 1
tmp=$(mktemp -d)
trap "rm -f -r $dir $tmp" ERR
trap "rm -f -r $tmp" EXIT
rm -r -f $dir
mkdir -p $dir
function copy_files {
    local i;
    for i in $1/*; do
	if [ ! -d $i ]; then
	    cp -p $i $2;
	fi
    done
}
function do_platform {
    echo Found platform subdir: $plat
    sub=$dir/$plat
    mkdir -p $sub
    sub+=/boot
    cp -Rp $1 $sub
}
for d in $releases/$version/*.tar.xz; do
  f=$(basename $d)
  [[ $f != ${version}* ]] && echo File in $d without release prexif ignored: $d && continue
  found=1
  tar -C $tmp -x -f $d # note that some files are actually gzip, not xz
  if [ $(basename $d) = ${version}-release.tar.xz ]; then
      echo Old style release with embedded platforms: $d
      for i in $tmp/*; do
	  if [ -d $i ]; then
	      plat=$(basename $i)
	      if [ $plat = zc70x ]; then
		  for p in $i/*; do
		      if [ -d $p ]; then
			  plat=$(basename $p)
			  do_platform $p
			  copy_files $tmp $sub
			  copy_files $i $sub
		      fi
		  done
	      else
		  do_platform $i
		  copy_files $tmp $sub
	      fi
	  fi
      done
  else
      plat=$(echo $f | sed -e 's/[^-]*-\([^-]*\)-.*$/\1/')
      echo New per-platform release: $f for platform $plat.
      do_platform $tmp/*${plat}*
  fi
done
[ -z "$found" ] && echo Could not find any Xilinx $version release tarballs in $releases. && exit 1
#
# Prepend "local_repo" directories to avoid problems with
# locally-installed commands that would otherwise conflict.
#
PATH=$local_repo/u-boot-xlnx/tools:$local_repo/linux-xlnx/scripts/dtc:$PATH
echo PATH is: $PATH
for d in $dir/*; do
    plat=$(basename $d)
    echo Extracting root FS for release ${version} platform $plat in $d "(for gdbserver and set sysroot)";
    source=$dir/$plat/boot/uramdisk.image.gz
    if [ -f $source ]; then
	if command -v dumpimage > /dev/null; then
	    dumpimage -i $source $tmp/rootfs.cpio.gz
	else
	    echo "!!No dumpimage tool is available, we'll assume $source is an old/simple image file"
	    dd if=$source bs=64 skip=1 of=$tmp/rootfs.cpio.gz
	fi
	gunzip $tmp/rootfs.cpio.gz
    else
	source=$dir/$plat/boot/image.ub
	if [ -f $source ]; then
	    echo Extracting uramdisk from image.ub
	    dumpimage -T flat_dt -i $source -p 2 $tmp/rootfs.cpio.gz
	    gunzip $tmp/rootfs.cpio.gz
	else
	    source=$dir/$plat/boot/$plat-*.cpio
	    if [ -f $source ]; then
		cp $source $tmp/rootfs.cpio
	    else
		echo Could not find an initial root - uramdisk.image.gz or image.ub && exit 1
	    fi
	fi
    fi
    mkdir -p $dir/$plat/root
    # This extraction of the cpio archive is for the purpose of providing a sysroot for remote
    # debugging with gdb.  I.e. for the "set sysroot" command to gdb when debugging using gdbserver
    # We remove "var/*" for to reasons:
    # 1. Just to make it smaller since it is not needed (we could certainly prune further)
    # 2. In some releases the dnf yumdb is in /var and it uses 100s of hard links in a way that causes
    #    NFS failures on some systems (it might be BSD/MacOS NFS servers?)
    (cd $dir/$plat/root;
     fakeroot cpio -i --quiet -d -H newc -F $tmp/rootfs.cpio --no-absolute-filenames -f "var/*")
    rm $tmp/rootfs.cpio
done
