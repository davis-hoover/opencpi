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
#
# Originally, this script began life as "scripts/install-platform.sh".  Then,
# the functionality of "scripts/deploy-opencpi.sh" was integrated.  Now, both
# of the original scripts have gone away because it made no sense to have one
# integrated script with three names.  Unlike the originals (which were never
# exported, but it was discovered they needed to be), this script must be run
# with the OpenCPI environment properly initialized.

set -e

if [ "x$OCPI_CDK_DIR" = x ]
then
  #
  # OpenCPI environment not initialized: fatal error.
  #
  echo "$0: ERROR: OCPI_CDK_DIR not set!" >&2
  echo "From the top-level \"opencpi\" directory, try \"source cdk/opencpi-setup.sh -s\"." >&2
  exit 1
fi

#
# Must be in the OpenCPI base directory, at least until a
# clean way of dealing with relative paths can be implemented.
#
cd $OCPI_ROOT_DIR

# Provides `setVarsFromMake`
source $OCPI_CDK_DIR/scripts/util.sh


function usage {
  if [ "$action" != install ]; then
    cat <<-EOF
To install a platform (by downloading it, if necessary, and building it):
  $(basename $0) install platform <platform> [-p PKG_ID [-u URL] [-g GIT_REV]]
To deploy a platform:
  $(basename $0) deploy platform <rcc_platform> <hdl_platform>
EOF
  else
    install_usage
  fi
  exit 1
}

function install_usage {
  cat <<-EOF
Usage: $(basename $0) install platform <platform> [-p PKG_ID [-u URL] [-g GIT_REV]]

Download, build, and register the built-in or remote OpenCPI RCC or HDL platform.

Required args:
  platform  Name of platform to install

Optional args:
  The -u and -g flags are only valid if the -p flag is specified as well. If
  the PKG_ID has already been downloaded and is detected, then PKG_ID can be
  omitted and just the PLATFORM name is required.

  -g GIT_REV, --git-revision GIT_REV
                        The branch, tag, or other valid git revision to checkout
                        after cloning the default git repo determined by PKG_ID.
                        GIT_REV defaults to the currently checked out OpenCPI
                        git revision.
  -p PKG_ID, --package-id PKG_ID
                        The OpenCPI Package ID that provides PLATFORM
  -u URL, --url URL     Use this URL when cloning the remote or local git repo
                        instead of the default url determined by PKG_ID
  --optimize            Use this option to install a software platform built with optimization,
                        at the expense of debugging.
  -u URL, --url URL     Use this URL when cloning the remote or local git repo
                        instead of the default url determined by PKG_ID
Examples:
  # xsim
  ocpiadmin install platform xsim

  # E31x
  ocpiadmin install platform e31x -p ocpi.osp.e3xx

  # PlutoSDR
  # PKG_ID not needed for second command as it has already been downloaded
  ocpiadmin install platform adi_plutosdr0_32 -p ocpi.osp.plutosdr
  ocpiadmin install platform plutosdr
EOF
  exit 1
}

function getvars {
  setVarsFromMake $OCPI_CDK_DIR/include/hdl/hdl-targets.mk ShellHdlTargetsVars=1
  setVarsFromMake $OCPI_CDK_DIR/include/rcc/rcc-targets.mk ShellRccTargetsVars=1
  if [ "$action" = deploy ]
  then
    export OCPI_ALL_RCC_PLATFORMS="$RccAllPlatforms" OCPI_ALL_HDL_PLATFORMS="$HdlAllPlatforms"
    return 0
  fi
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

function bad {
  echo -e "Error: $@" >&2
  exit 1
}


#
# Quick and dirty argument parsing:
# getopt(s) overhead not required.
#
PARAMS=""
while (( "$#" )); do
  case "$1" in
    -g|--git-revision)
      if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
        GIT_REV=$2
        shift 2
      else
        bad "Argument for \"$1\" is missing"
      fi
      ;;
    -p|--package-id)
      if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
        PKG_ID=$2
        shift 2
      else
        bad "Argument for \"$1\" is missing"
      fi
      ;;
    -u|--url)
      if [ -n "$2" ] && [ ${2:0:1} != "-" ]; then
        URL=$2
        shift 2
      else
        bad "Argument for \"$1\" is missing"
      fi
      ;;

    # Undocumented flags
    -d|--distro)
      export OCPI_DISTRO_BUILD=1
      shift
      ;;
    -v|--verbose)
      verbose=-v
      shift
      ;;
    --optimize)
      optimize=1
      shift
      ;;
    --dynamic)
      dynamic=1
      shift
      ;;
    --minimal)
      minimal=1 # use ${minimal:+whatever}
      shift
      ;;
    # Unsupported flags
    -*)
      HELP=1  # can't print usage yet as usage message is based on other args
      shift
      ;;

    # Preserve positional arguments
    *)
      PARAMS="$PARAMS \"$1\""
      shift
      ;;
  esac
done  # end parsing optional args and flags

# Set positional arguments in their proper place
eval set -- "$PARAMS"
unset PARAMS

# Parse and validate positional args.
action=$1

# Needs to be after $action is set as a different usage message is printed
# based on the action. Also, at least 3 positional arguments are required.
if [[ -n "$HELP" || $# -lt 3 ]]; then
  usage
fi

# $2 is always 'platform' for now
noun=$2
if [ "$noun" != platform ]; then
  bad "Unknown $action noun: '$noun'"
fi
if [ "$action" = install ]; then
  platform=${3%-*}
  platform_target_dir=$3
  if [ -z "$platform" ]; then
    bad 'Missing platform to install'
  fi
  # Check to ensure "PKG_ID" is non-null if either
  # "--url" or "--git-revision" were specified.
  if [[ ("$URL" || "$GIT_REV") && -z "$PKG_ID" ]]
  then
    bad 'PKG_ID is required if a URL or GIT_REV is specified'
  fi
elif [ "$action" = deploy ]; then
  rcc_platform=$3
  hdl_platform=$4
  if [ -z "$hdl_platform" ]; then
    bad 'Cannot deploy platform, missing required rcc and/or hdl platform'
  fi
else
  bad "Unknown action: '$action'"
fi

# End parsing and validation of positional args

#
# The "deploy" case is trivial: "deploy-platform.sh"
# does the heavy lifting.  Note undocumented "verbose"
# option: set to "-v" for debugging.
#
if [ "$action" = deploy ]
then
  getvars
  $OCPI_CDK_DIR/scripts/deploy-platform.sh $verbose $rcc_platform $hdl_platform
  exit $?
fi


if getvars; then
    echo The $model platform \"$platform\" is already defined in this installation, in $platform_dir.
    project_dir=$(echo $platform_dir | sed -e 's=/exports/=/=' -e "s=/.../platforms/$platform==" -e 's=/lib$==')
    if [ -n "$PKG_ID" ]; then
	echo The supplied project package-id for this platform, \"$PKG_ID\", will be ignored.
    fi
else
    echo The platform \"$platform\" is not defined in this installation yet.
    if [ -z "$PKG_ID" ]; then
	echo ERROR: no project package-id was specified, and
	echo platform \"$platform\" is not in a built-in project.
	echo Either the platform name is misspelled or you must supply a project package-id.
	exit 1
    fi
    project_dir=projects/osps/$PKG_ID
    if [ -d "$project_dir" ]; then
	echo There is already a directory at $project_dir, so it is assumed to contain the right project.
	echo It will be used and registered.  To force a new download of the project, unregister it and remove it.
        echo It will not be checked out for any particular tag or branch since it is assumed that it has
	echo either been done manually or previously by this script.
    else
	if [ -z "$URL" ]; then
	    URL=https://gitlab.com/opencpi/osp/$PKG_ID.git
	    echo No URL was specified, so it will default to the OpenCPI repo site: $URL
	fi
	echo "Downloading (git cloning) from $URL..."
	if git clone --no-checkout $URL $project_dir && test -d $project_dir; then
	    echo "Download/clone successful into $project_dir."
	else
	    echo "ERROR: download/clone of project \"$PKG_ID\" for platform \"$platform\" failed."
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
		echo "ERROR: no git branch found for tag $tag"
		exit 1
	    fi
	elif branch=$(git branch --contains); then
	    branch=${branch#* }
	    echo "The OpenCPI (framework) repo is on branch: $branch."
	else
	    echo "ERROR: cannot determine branch of OpenCPI repo"
	    exit 1
	fi
	if [ -n "$GIT_REV" ]; then
	    echo Checking out the OSP at $project_dir using the user-supplied branch/tag: $GIT_REV
	    if (cd $project_dir && git checkout $GIT_REV); then
		echo The OSP at $project_dir checked out for branch/tag: $GIT_REV
	    else
		echo ERROR: failed to checkout the OSP for branch/tag \"$GIT_REV\".
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
		    echo ERROR: failed to checkout the OSP for either tag \"$tag\" or branch \"$branch\".
		    exit 1
		fi
	    fi
	else
	    echo Checking out the OSP at $project_dir for branch $branch.
	    if (cd $project_dir && git checkout $branch); then
		echo The OSP at $project_dir checked out for branch: $branch
	    else
		echo ERROR: failed to checkout the OSP for branch \"$branch\".
		exit 1
	    fi
	fi
    fi
    # Check if the platform is now available, without registering it
    export OCPI_PROJECT_PATH=`pwd`/$project_dir
    if getvars; then
	echo The $model platform \"$platform\" found after using the new project \"$PKG_ID\".
    else
	echo ERROR: in the downloaded project \"$PKG_ID\", at $project_dir, platform \"$platform\" is not visible.
	echo If you want to download it again, you must remove that directory and its contents.
	exit 1
    fi
    unset OCPI_PROJECT_PATH
    if [ ! -d "project-registry/$PKG_ID" ]; then
	if ocpidev register project $project_dir; then
	    echo The OSP at $project_dir has now been registered.
	else
	    echo ERROR: the project \"$PKG_ID\", at $project_dir, cannot be registered.
	    echo If you want to download it again, you must remove that directory and its contents.
	    exit 1
	fi
    fi
fi
if [ "$model" = RCC ]; then
    if [ -n "$dynamic" -o -n "$optimize" ]; then
	if [[ $platform_target_dir == *-* ]]; then
	    echo "ERROR: you cannot use the --dynamic(-d) or the --optimize(-O) options when you have" >&2
	    echo "       included build options in the platform name, in this case: $platform_target_dir" >&2
	    exit 1
	fi
	platform_target_dir+=-
	[ -n "$dynamic" ] && platform_target_dir+=d
	[ -n "$optimize" ] && platform_target_dir+=o
    fi
    ./scripts/install-opencpi.sh ${minimal:+--minimal} $platform_target_dir || exit 1
else
    # Since the build-opencpi.sh does an "rcc" build per project, and that implicitly
    # does "declarehdl" on projects, that is sufficient for on-demand hdl worker builds
    if [ -n "$minimal" ]; then
      ocpidev -d projects/core build hdl primitives library --hdl-platform=$platform
      ocpidev -d projects/platform build hdl primitives library --hdl-platform=$platform
      # REMOVE THIS WHEN THE ASSETS PROJECT IS CLEANED UP
      # But ultimately we need to get the platform's project's dependencies from the platform's project
      # and build primitives for all of them
      ocpidev -d projects/assets build hdl primitives library --hdl-platform=$platform
      ocpidev -d projects/assets_ts build hdl primitives library --hdl-platform=$platform
    else
      ocpidev -d projects/core build --hdl --hdl-platform=$platform
      ocpidev -d projects/platform build --hdl --hdl-platform=$platform --no-assemblies
      ocpidev -d projects/assets build --hdl --hdl-platform=$platform --no-assemblies
      ocpidev -d projects/assets_ts build --hdl --hdl-platform=$platform --no-assemblies
      ocpidev -d projects/tutorial build --hdl --hdl-platform=$platform --no-assemblies

      # Make sure that tutorials can run after installation, note will do rcc too.
      [ "$platform" = xsim ] && ocpidev -d projects/tutorial build --hdl-platform=$platform
    fi
    # If project dir is not one of the core projects, build the platform
    if [[ -n "$platform_dir" && "$platform_dir" != *"/projects/core/"* \
          && "$platform_dir" != *"/projects/platform/"* \
          && "$platform_dir" != *"/projects/assets/"* ]]
    then
        if [ -n "$minimal" ]; then
          ocpidev -d $project_dir build hdl primitives library --hdl-platform=$platform
          # the rcc build ensures all workers are visible to build the platform
          # we don't have a verb to do that.
          ocpidev -d $project_dir build --rcc
          ocpidev -d $project_dir build hdl --workers-as-needed platform $platform
        else
          ocpidev -d $project_dir build --hdl --hdl-platform=$platform --no-assemblies
        fi
        echo "HDL platform \"$platform\" built for OSP in $project_dir."
    elif [ -n "$minimal" ]; then
      # Build the platform in its project
      ocpidev -d $project_dir build hdl --workers-as-needed platform $platform
    fi
    ocpidev -d projects/assets build --hdl-platform=$platform hdl ${minimal:+--workers-as-needed} assembly testbias
    echo "HDL platform \"$platform\" built, with one HDL assembly (testbias) built for testing."
    echo "Preparing exported files for using this platform."
    #
    # At this point, we have an issue applicable to OSPs that have not
    # been previously installed.  A previous "getvars" call (above) sets
    # "platform_dir" to
    #   "./projects/osps/$PKG_ID/hdl/platforms/<hdl_platform>"
    # because
    #   "./projects/osps/$PKG_ID/hdl/platforms/<hdl_platform>/lib"
    # does not exist until the above "ocpidev" commands have been run,
    # i.e., this is a bootstrapping issue.  "platform_dir" can be updated
    # here by calling "getvars" one more time (after everything is built),
    # or in the "export-platform-to-framework.sh" script.
    #
    # No need to check the return value from "getvars" at this point.
    #
    getvars
    $OCPI_CDK_DIR/scripts/export-platform-to-framework.sh -v hdl $platform_target_dir $platform_dir
fi
echo "Platform installation (download and build) for platform \"$platform\" succeeded."
exit 0
