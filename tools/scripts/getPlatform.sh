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

##########################################################################################
# This script determines the runtime platform and target variables
# The six variables are: OS OSVersion Processor Triple Platform PlatformDir
# The triple (os-osversion-processor) is redundant and legacy.
# If it returns nothing (""), that is an error

# Given the directory of the platform we want to return
returnPlatform() {
  local d=$1
  local vars=($(egrep '^ *OcpiPlatform(Os|Arch|OsVersion) *:*= *' $d/$2.mk |
              sed 's/OcpiPlatform\([^ :=]*\) *:*= *\([^a-zA-Z0-9_]*\)/\1 \2/'|sort))
  [ ${#vars[@]} = 6 ] || {
    echo "Error:  Platform file $d/$2.mk is invalid and cannot be used.${vars[*]}" >&2
    echo "Error:  OcpiPlatform(Os|OsVersion|Arch) variables are not valid." >&2
    exit 1
  }
  echo ${vars[3]} ${vars[5]} ${vars[1]} ${vars[3]}-${vars[5]}-${vars[1]} $2 $d
  exit 0
}
isCurPlatform() {
  [ -f $1-check.sh ] && bash $1-check.sh $HostSystem $HostProcessor > /dev/null && return 0
  return 1
}
tryDir() {
  local platforms_dir=$1
  if [ -n "$2" ]; then # looking for a specific platform (not the current one)
    local d=$platforms_dir/$2
    [ -d $d/lib -a -f $d/lib/$2.mk ] && returnPlatform $d/lib $2
    [ -d $d -a -f $d/$2.mk ] && returnPlatform $d $2
  else # not looking for a particular platform, but looking for the one we're running on
    for i in $platforms_dir/*; do
      local p=$(basename $i)
      test -d $i -a -f $i/$p.mk &&
        isCurPlatform $i/$p && returnPlatform $i $p
    done
  fi
  return 0 # if it returns, it didn't find anything
}
# These are universally available so far so we do this once and pass then to all probes.
HostSystem=`uname -s | tr A-Z a-z`
HostProcessor=`uname -m | tr A-Z a-z`

# Collect all known projects. Append with the default read-only core project
# in case this is a limited runtime-only system with no project registry
if [ -n "$OCPI_CDK_DIR" -a -e "$OCPI_CDK_DIR/scripts/util.sh" ]; then
  source $OCPI_CDK_DIR/scripts/util.sh
  projects="`getProjectPathAndRegistered`"
  # A fresh RPM install won't even have a registered core yet, so fallback
  [ -d $OCPI_CDK_DIR/../projects/core ] && projects="$projects $OCPI_CDK_DIR/../projects/core"
elif [ -n "$OCPI_PROJECT_PATH" ]; then
  # If the CDK is not set or util.sh does not exist, fall back on OCPI_PROJECT_PATH
  echo Unexpected internal error: OCPI_CDK_DIR IS NOT SET1 >&2 && exit 1
  projects="${OCPI_PROJECT_PATH//:/ }"
elif [ -d projects ]; then
  echo Unexpected internal error: OCPI_CDK_DIR IS NOT SET2 >&2 && exit 1
  # Probably running in a clean source tree.  Find projects and absolutize pathnames
  projects="$(for p in projects/*; do echo `pwd`/$p; done)"
fi
if [ -z "$projects" ]; then
  echo "Unexpected error:  Cannot find any projects for RCC platforms." >&2
  exit 1
fi
# loop through all projects to find the platform
shopt -s nullglob
for j in $projects; do
  # First, assume it is an exported project and check lib/rcc...
  # Next, assume this is a source project that is exported and check exports/lib/rcc,
  # Finally, just search the source rcc/platforms...
  for  d in $j/exports/rcc/platforms $j/rcc/platforms; do
    [ -d $d ] && tryDir $d $1
  done
done # done with the project

if [ -n "$1" ]; then
  echo Cannot find a platform named $1. >&2
else
  echo Cannot determine platform we are running on.  >&2
fi
exit 1
