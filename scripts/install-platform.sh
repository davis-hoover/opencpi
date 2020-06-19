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

# Just check if it looks like we are in the source tree.
[ -d runtime -a -d build -a -d scripts -a -d tools ] || {
  echo "Error:  this script ($0) is not being run from the top level of the OpenCPI source tree."
  exit 1
}
set -e
if [ $# = 0 ]; then
    cat <<-EOF
	This script installs a platform by downloading it (if needed) and building it.
	Usage is:  ./scripts/install-platform.sh <platform> <project-package-id> <url> <checkout>
EOF
    exit 1
fi

# We do some bootstrapping here (that is also done in the scripts we call), in order to know
# whether the platform we are building

# Ensure exports (or cdk) exists and has scripts
source ./scripts/init-opencpi.sh
# Ensure CDK and TOOL variables
OCPI_BOOTSTRAP=`pwd`/cdk/scripts/ocpibootstrap.sh; source $OCPI_BOOTSTRAP

platform=$1
project=$2
url=$3
checkout=$4
source $OCPI_CDK_DIR/scripts/util.sh

function getvars {
  setVarsFromMake $OCPI_CDK_DIR/include/hdl/hdl-targets.mk ShellHdlTargetsVars=1
  setVarsFromMake $OCPI_CDK_DIR/include/rcc/rcc-targets.mk ShellRccTargetsVars=1
  platforms="$RccAllPlatforms $HdlAllPlatforms"
  if isPresent $platform $platforms; then
    if isPresent $platform $RccAllPlatforms; then
	model=RCC
	v=RccPlatDir_$platform
    else
	model=HDL
	v=HdlPlatformDir_$platform
    fi
    platform_dir=`echo ${!v} | sed 's=^.*/projects/=./projects/='`
    return 0
  fi
  return 1
}
if getvars; then
    echo The $model platform \"$platform\" is already defined in this installation, in $platform_dir.
    project_dir=$(echo $platform_dir | sed -e "s=/.../platforms/$platform==" -e 's=/lib$==')
    if [ -n "$project" ]; then
	echo The supplied project package-id for this platform, \"$project\", will be ignored.
    fi
else
    echo The platform \"$platform\" is not defined in this installation yet.
    if [ -z "$project" ]; then
	echo There is no project package-id supplied as the second argument, and
	echo platform \"$platform\" is not in a built-in project.
	echo Either the platform name is misspelled or you must supply a project package-id.
	exit 1
    fi
    project_dir=projects/osps/$project
    if [ -d $project_dir ]; then
	echo There is already a directory at $project_dir, so it is assumed to contain the right project.
	echo It will be used and registered.  To force a new download of the project, unregister it and remove it.
        echo It will not be checked out for any particular tag or branch since it is assumed that it has
	echo either been done manually or previously by this script.
    else
	if [ -z "$url" ]; then
	    url=https://gitlab.com/opencpi/osp/$project.git
	    echo No URL was supplied as the third argument, so it will be located at the OpenCPI repo site: $url
	fi
	echo "Downloading (git cloning) from $url..."
	if git clone --no-checkout $url $project_dir && test -d $project_dir; then
	    echo "Download/clone successful into $project_dir."
	else
	    echo "Download/clone of project \"$project\" for platforn \"$platform\" failed."
	    rm -r -f $project_dir
	    exit 1
	fi
	# Perform the checkout of the project repo
	# First assume we want the same tag/branch as the main repo.
	# If framework is on a tag, see if this repo is also.

	# Before registering it we will test whether it seems to be a working repo
	if tag=$(git describe --exact-match --tags 2>/dev/null); then
	    echo "The OpenCPI (framework) repo is on tag: $tag".
	    if branch=$(git branch --contains $(git rev-parse tags/$tag)); then
		echo "The branch for tag $tag is $branch";
	    else
		echo "Error: No git branch found for tag $tag"
		exit 1
	    fi
	elif branch=$(git branch --contains); then
	    branch=${branch#* }
	    echo "The OpenCPI (framework) repo is on branch: $branch."
	else
	    echo "Error: cannot determine branch of OpenCPI repo"
	    exit 1
	fi
	if [ -n "$checkout" ]; then
	    echo Checking out the OSP project at $project_dir using the user-supplied checkout: $checkout
	    if (cd $project_dir && git checkout $checkout); then
		echo The OSP at $project_dir checked out for branch/tag: $checkout
	    else
		echo Error: failed to checkout the OSP for branch/tag \"$checkout\".
		exit 1
	    fi
	elif [ -n "$tag" ]; then
	    if (cd $project_dir && git checkout $tag); then
		echo The OSP at $project_dir has been checked out to tag: $tag
	    else
		echo The OSP at $project_dir did not successfully checkout for tag: $tag.
		echo Checking out to branch $branch will be tried.
		if (cd $project_dir && git checkout $branch); then
		    echo The OSP at $project_dir checked out for branch: $branch
		else
		    echo Error: failed to checkout the OSP for either tag \"$tag\" or branch \"$branch\".
		    exit 1
		fi
	    fi
	else
	    echo Checking out the OSP project at $project_dir for branch $branch.
	    if (cd $project_dir && git checkout $branch); then
		echo The OSP at $project_dir checked out for branch: $branch
	    else
		echo Error: failed to checkout the OSP for branch \"$branch\".
		exit 1
	    fi
	fi
    fi
    # Check if the platform is now available, without registering it
    export OCPI_PROJECT_PATH=`pwd`/$project_dir
    if getvars; then
	echo The $model platform \"$platform\" found after using the new project \"$project\".
    else
	echo Error: in the downloaded project \"$project\", at $project_dir, platform \"$platform\" is not visible.
	echo If you want to download it again, you must remove that directory and its contents.
	exit 1
    fi
    if [ ! -d project-registry/$project ]; then
	if ocpidev register project $project_dir; then
	    echo The OSP at $project_dir has now been registered.
	else
	    echo Error: the project \"$project\", at $project_dir, cannot be registered.
	    echo If you want to download it again, you must remove that directory and its contents.
	    exit 1
	fi
    fi
fi
if [ $model = RCC ]; then
    ./scripts/install-opencpi.sh $platform || exit 1
else
    ocpidev -d projects/core build --hdl --hdl-platform=$platform
    ocpidev -d projects/platform build --hdl --hdl-platform=$platform --no-assemblies
    ocpidev -d projects/assets build --hdl --hdl-platform=$platform --no-assemblies
    ocpidev -d projects/assets_ts build --hdl --hdl-platform=$platform --no-assemblies
    # Make sure that tutorials can run after installation, note will do rcc too.
    [ "$platform" != xsim ] || ocpidev -d projects/tutorial build --hdl-platform=$platform
    # If project dir is not one of the core projects build platoform  
    if [[ "$platform_dir" != *"/projects/core/"* && "$platform_dir" != *"/projects/platform/"* && \
            "$platform_dir" != *"/projects/assets/"* ]]; then 
	ocpidev -d $project_dir build --hdl --hdl-platform=$platform --no-assemblies
	echo "HDL platform \"$platform\" built for OSP in $project_dir, including assemblies."
    fi
    ocpidev -d projects/assets build --hdl-platform=$platform hdl assembly testbias
    echo "HDL platform \"$platform\" built, with one HDL assembly (testbias) built for testing."
    echo "Preparing exported files for using this platform."
    ./scripts/makeExportLinks.sh -v - - $platform $platform_dir
fi
echo "Platform installation (download and build) for platform \"$platform\" succeeded."
exit 0
