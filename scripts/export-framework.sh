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
# Populate the exports tree with the links for files that will be part of the CDK
#
# This script must be tolerant of things not existing, and it is called repeatedly as
# more things get built

# This script does not care or drive how these things get built.
#

set -e
if test "$*" = ""; then
  echo "Usage is: export-framework.sh [-v] <model> [<platform> <platform-dir>]"
  echo 'This script is typically used internally by "make exports"'
  echo 'It is designed to be run repeatedly, making links to whatever exists.'
  echo 'Thus it is run several times during the build process.'
  echo 'Model is a hyphen in bootstrap mode'
  echo 'If the first arg (model) is a hyphen we are just doing bootstrapping for no particular platform'
  exit 1
fi
if [ "$1" = "-v" -o "$OCPI_EXPORTS_VERBOSE" = 1 ]; then
  verbose=-v
  [ "$1" = "-v" ] && shift
fi
model=$1
platform=$2
platform_dir=$3
# We don't need a real CDK to perform exports, so just force out skeletal one
export OCPI_CDK_DIR=`pwd`/bootstrap
exports=Project.exports
[ -f Project.exports ] || exports=Framework.exports

source $OCPI_CDK_DIR/scripts/export-utils.sh

[ -f $exports ] || bad No Project.exports or Framework.exports file found for framework.

# If we have a platform, do its exports.
if [ $model = - ]; then
  platform=-  # this is for do_addition below
else
  $OCPI_CDK_DIR/scripts/export-platform-to-framework.sh $verbose $model $platform $platform_dir
fi
# If were not doing bootstrapping or rcc, we're done
[ $model = rcc ] || [ $model = - ] || exit 0

# For RCC platforms (or no platform), do the extra framework (not platform-specified) exports
[ -n "$verbose" ] && echo Collecting framework exports
readExport exclusions - $exports
readExport additions + $exports
readExport runtimes = $exports
[ -n "$verbose" ] && echo Processing framework development additions
mkdir -p exports
for a in $additions; do
  do_addition $a "" "$platform" "$platform_dir"
done
[ -n "$verbose" ] && echo Processing framework runtime additions
for a in $runtimes; do
  do_addition $a -  "$platform" "$platform_dir"
done
[ -n "$verbose" ] && echo Processing framework deployment additions
for a in $deployments; do
  do_addition $a --  "$platform" "$platform_dir"
done

# Create or replace the user editable environment setup file.
# Since this might enable tools, we do it early, even when we are not creating links for a target
# Note that this is analogous to the runtime system config file system.xml
userenv=user-env.sh
defaultuserenv=tools/scripts/default-user-env.sh
if [ -r $userenv ] && grep -q '^ *export' $userenv; then
  [ -n "$verbose" ] &&
      echo Preserving user environment script \"$userenv\" since it has user-specified exports in it.
  version=$(sed -n '/^ *# *VERSION */s///p' $userenv)
  defaultversion=$(sed -n '/^ *# *VERSION */s///p' $defaultuserenv)
  if [ "$version" != "$defaultversion" ]; then
    echo The user-edited environment setup file \"$userenv\", is out of date.
    echo It should be re-edited based on a copy of the updated default version in \"$defaultuserenv\".
 fi
elif [ -r $userenv ]; then
  if cmp -s $userenv $defaultuserenv; then
    [ -n "$verbose" ] && echo Preserving user environment script \"$userenv\" since it is the default one.
  else
    [ -n "$verbose" ] && echo "Replacing user environment script \"$userenv\" with current default, since it has no exports and is different from the (presumably newer) default one."
    cp $defaultuserenv $userenv
  fi
else
  cp $defaultuserenv $userenv
fi

shopt -u nullglob

# If we are building/running on the target platform, pre-compile python AV-4850
if [ "$OCPI_TOOL_DIR" = "$platform" ]; then
  # Force precompilation of python files right here, but only if we are doing a dev host
  py=python3
  command -v $py &> /dev/null || py=/opt/local/bin/$py
  dirs=
  for d in `find exports -name "*.py"|sed 's=/[^/]*$=='|sort -u`; do
    $py -m compileall -q $d
    $py -O -m compileall -q $d
  done
fi
