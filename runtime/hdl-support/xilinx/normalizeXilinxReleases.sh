#!/bin/bash

# Access all the xilinx release tarballs for this Xilinx release and put the files
# in a normalized form even though the Xilinx tarballs are not the same
# Two args:
# 1. This release version (e.g. 2019.1)
# 2. The location of the xilinx release downloads
# The script will create a directory that will have subdirs for each hdl platform
set -vx
version=$1
releases=$2
dir=$3
tmp=$(mktemp -d)
set -e
[ -z "$dir" ] && echo Error: no directory argument && exit 1
trap "rm -f -r $dir" ERR
mkdir -p $dir
for d in $releases/*.tar.xz; do
  f=$(basename $d)
  if [[ $f = ${version}* ]]; then
      tar -C $tmp -x -z -f $d
      if [ $d = ${version}-release.tar.xz ]; then
	  echo Old style release with embedded platforms: $d
      else
	  echo New per-platform release: $f
	  platform=$(echo $f | sed -e 's/[^-]*-\([^-]*\)-.*$/\1/')
	  echo PLATFORM=$platform
	  mkdir $dir/$platform
	  cp -Rp $tmp/*${platform}*/* $dir/$platform
      fi
  fi
done
exit 0

	echo Here is original boot dir:
	ls -l boot
	mkdir -p gen/patch_ub_image
	mv boot/image.ub gen/patch_ub_image
	set -evx; cd gen/patch_ub_image; \
	PATH=$(local_repo)/u-boot-xlnx/tools:$(local_repo)/linux-xlnx/scripts/dtc:$$PATH; \
	echo Dumping metadata for image.ub; \
	dumpimage -l image.ub; \
	dumpimage -T flat_dt -i image.ub -p 0 old-kernel; \
	dumpimage -T flat_dt -i image.ub -p 1 old-dtb; \
	dumpimage -T flat_dt -i image.ub -p 2 uramdisk.image.gz; \
	dumpimage -i $(kernel_image) -p 0 new-kernel; \
	cmp ../../boot/system.dtb old-dtb; \
	cp ../../test.its test.its; \
	mkimage -f test.its new_image.ub; \
	dumpimage -l new_image.ub; \
	cp new_image.ub ../../boot/image.ub
