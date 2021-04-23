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

###############################################################################################
# This file is meant to be *sourced* to set up the environment for OpenCPI
# in the typical way that such scripts are called from the user's .profile.
# It not meant to be *executed* as a shell script, only sourced.
# It is sourced by its name in the top level of the desired CDK installation
# (possibly /opt/opencpi/cdk).  It may be sourced using a relative pathname.

# The actual location/name of this file in the source tree (opencpi-setup-internal)
# is purposely named differently from the documented file name for users (opencpi-setup)
# to prevent users from sourcing the file where they happened to find it in the
# source tree.  I.e. we export opencpi-setup-internal.sh as cdk/opencpi-setup.sh to avoid
# this undesireable user behavior.

# Thus its location (where it is sourced from) implies where OpenCPI is installed.
# This means that it should only be run (sourced) in its "exported" location, not in its
# location inside the source tree.  Most common usage from source tree is: source cdk/opencpi-setup.sh -s
# The CDK is where this is sourced from (its dirname) and so OCPI_CDK_DIR is set accordingly.
# Note that OCPI_ROOT_DIR, which indicates the overall location of the opencpi installation,
# is set to OCPI_CDK_DIR/.. as a default, but may be elsewhere.

# There are several different scenarios where this script will run:

# 1. From the global bash /etc/profile.d entry created when the RPM or equivalent is installed.
#    This means that this script is called for login shells, with the "-s" argument, which means
#    it will complain if it finds anything in the environment, which it should not.

# 2. When a user specifically sources this file in one of their bash login files.
#    This would be when the user is operating either without a global OpenCPI installation (thus
#    no /etc/profile.d files are present or invoked) *or* wants to override such settings and
#    indicate a different CDK or different options.  Executing this script in the user's
#    login script (.bash_profile or .bash_login or .profile) will do this.
#    Note that if it wants to override any global settings, it can use the "-r" option, whereas
#    if a global installation would be unexpected, it can use "-s" which will complain if any
#    global login settings are found.

# 3. Manually when the OpenCPI environment should be established or changed for a particular
#    shell.  In this case a variety of the options may be used.

# When sourced on a development platform, the platform is dynamically determined.
# This file is NOT intended to be sourced in an embedded environment.

# This script modifies the environment in these ways:
# 1. setting OCPI_CDK_DIR environment variable to an absolute pathname - the dirname of this script
#    where it is executed as exported
# 2. setting the OCPI_TOOL_* environment variables as a cache of this platform determination
# 3. adding the binaries directory for the running platform to the PATH environment variable
# 4. adding the lib directory for the running platform to the PYTHONPATH environment variable
# 5. setting the OCPI_PREREQUISITES_DIR environment variable
#    either $OCPI_ROOT_DIR/prerequisites if present or /opt/opencpi/prerequisites
# 6. enable bash command line completion for OpenCPI commands with completion
#
# It internally sets shell variables starting with "ocpi_"
# It insists on bash.  Someday someone can write it for csh or zsh :-)
# You can give an optional "-v" argument to get it to be verbose.
ocpi_name=opencpi-setup.sh
ocpi_me=$BASH_SOURCE
ocpi_cdk_dir=cdk
ocpi_root_dir=root
# The egrep of the beginning of variables to clean out, e.g. derived rather than user specified
ocpi_cleaned_vars="OCPI_(PREREQUISITES_DIR|TARGET_|TOOL_|CDK_|ROOT_)"
[ -z "$BASH_VERSION" -o -z "$ocpi_me" ] && {
  echo Error:  You can only use the $ocpi_name script with the bash shell. >&2
  return 1
}
[ "$ocpi_me" == $0 ] && {
    cat <<-EOF >&2
	Error: This OpenCPI $ocpi_name file must be read using the \"source\" command.
	       It appears that you are executing this script rather than sourcing it.
	EOF
    exit 1 # note exit and not return since we are not being sourced
}
case "$ocpi_me" in
    */*);;
    *)
      cat <<-EOF >&2
	Error: You are attempting to source $ocpi_me and should instead
	       source <installation-directory-of-opencpi>/cdk/$ocpi_name
	EOF
      return 1
    ;;
esac
[ "$ocpi_name" != "$(basename $ocpi_me)" ] && {
  cat <<-EOF >&2
	Error: You are attempting to source $ocpi_me and should instead
	       source <installation-directory-of-opencpi>/cdk/$ocpi_name
	EOF
  return 1
}
[ "$1" = --help -o "$1" = -h -o -z "$1" ] && {
  # use when documented:--dynamic:   enable the currently running host platform to use dynamic linking
  cat <<-EOF >&2
	This script modifies the OpenCPI environment variables and the PATH/PYTHONPATH/MANPATH variables.
	Options to this $ocpi_name file when *sourced* are:
	 --help or -h:      print this message
	 --reset or -r:     reset any previous OpenCPI environment before setting up a new one
	 --clean or -c:     unset all OpenCPI environment variables and nothing more.
	 --list or -l:      list current settings - will not setup or modify any settings
	 --verbose or -v:   be verbose about what is happening
	 --ensure or -e:    do nothing if OpenCPI is already set up, otherwise like --set
	 --set or -s:       setup the environment for OpenCPI when it is not yet set up
	 --optimize:        enable the currently running host platform to use optimized code
	When --set or --reset is used, the OpenCPI CDK location is inferred from the location
	of this file, where sourced.  E.g. issuing the command "source a/b/c/opencpi-setup.sh -s"
	will setup the CDK as found in a/b/c.
	When in the root directory of the OpenCPI source tree, the typical usage is:
	   source cdk/opencpi-setup.sh -s
	Note that neither --dynamic nor --optimize affect what is built.  Just what is used.
	EOF
  return 1
}

# Guard against somebody sourcing us with nullglob set (otherwise "unset ocpi_options[0]" could be blank below)
if shopt -q nullglob; then echo 'Note: Turning off nullglob; was active!'; shopt -u nullglob; fi

# Parse opts
ocpi_dynamic= ocpi_optimize= ocpi_reset= ocpi_verbose= ocpi_clean= ocpi_list= ocpi_ensure= ocpi_bootstrap=
ocpi_options=($*)
while [ -n "$ocpi_options" ] ; do
  case $ocpi_options in
    --dynamic) ocpi_dynamic=1;;
    --optimized|--optimize) ocpi_optimize=1;;
    -r|--reset) ocpi_reset=1;;
    -v|--verbose) ocpi_verbose=1;;
    -c|--clean) ocpi_clean=1;;
    -l|--list) ocpi_list=1;;
    -e|--ensure) ocpi_ensure=1;;
    -b|--bootstrap) ocpi_bootstrap=1;;  # Undocumented option for internal use only
    -|-s|--set);; # perhaps the single required variable
    *)
      echo Unknown option \"$ocpi_options\" when sourcing the $ocpi_name file. Try --help. >&2
      return 1;;
  esac
  unset ocpi_options[0]
  ocpi_options=(${ocpi_options[*]})
done

# Make sure this script is being sourced in the correct location, except when
# bootstrapping
if [ -z "$ocpi_bootstrap" ]; then
  # Get file location w/o following symlinks since 'realpath -s' not in cos6
  ocpi_file_location=$(cd $(dirname $ocpi_me); pwd)/$(basename $ocpi_me)
  # Get the parent directory of the file being called and make sure it's cdk
  ocpi_file_parent_dir=$(basename $(dirname $ocpi_file_location))
  if [ "$ocpi_file_parent_dir" != "$ocpi_cdk_dir" ]; then
    cat <<-EOF >&2
	Error: You are attempting to source the wrong $ocpi_name file
	       and should instead source <installation-directory-of-opencpi>/cdk/$ocpi_name
	EOF
    return 1
  fi
fi
unset ocpi_bootstrap

[ -n "$ocpi_clean" ] && {
  [ -n "$OCPI_CDK_DIR" ] && {
    ocpi_cleaned=$(echo "$PATH" | sed "s=$OCPI_CDK_DIR/[^:/]*/bin[^:]*:==g")
    [ "$ocpi_cleaned" != "$PATH" ] && {
      [ -n "$ocpi_verbose" ] && echo Removing OpenCPI bin directory from PATH.
      PATH="$ocpi_cleaned"
    }
    # Note we might be the only thing in this path, with no colon
    ocpi_cleaned=$(echo "$PYTHONPATH" | sed "s=$OCPI_CDK_DIR/[^:/]*/lib[^:]*:*==g")
    [ "$ocpi_cleaned" != "$PYTHONPATH" ] && {
      [ -n "$ocpi_verbose" ] && echo Removing OpenCPI lib directory from PYTHONPATH.
      PYTHONPATH="$ocpi_cleaned"
    }
    # Note we might be the only thing in this path, with no colon
    ocpi_cleaned=$(echo "$MANPATH" | sed "s=$OCPI_CDK_DIR/doc/man[^:]*:*==g")
    [ "$ocpi_cleaned" != "$MANPATH" ] && {
      [ -n "$ocpi_verbose" ] && echo Removing OpenCPI doc/man directory from MANPATH.
      MANPATH="$ocpi_cleaned"
    }
  }
  [ -n "$ocpi_verbose" ] && echo Unsetting all OpenCPI environment variables.
  for ocpi_v in $(env | egrep "^$ocpi_cleaned_vars" | sort | cut -f1 -d=)
  do
    unset $ocpi_v
  done
  return 0
}
[ -n "$ocpi_list" ] && {
  [ -n "$ocpi_verbose" ] && echo Listing OpenCPI environment and the PATH variables.
  env | grep OCPI >&2
  env | grep '^PATH='
  env | grep '^PYTHONPATH='
  env | grep '^MANPATH='
  return 0
}

[ -n "$OCPI_CDK_DIR" -a -n "$OCPI_ROOT_DIR" ] && {
  [ -n "$ocpi_ensure" ] && {
    # The environment appears already setup so we can leave things as they are, but check for
    # a half-baked setup and complain
    [ -z "$OCPI_PREREQUISITES_DIR" -o -z "$OCPI_TOOL_OS" -o -z "$OCPI_TOOL_DIR" ] && {
      echo Error: The environment is partially set up, which is bad.  Perhaps use --reset. >&2
      return 1
    }
    return 0;
  }
  [ -z "$ocpi_reset" -a -z "$ocpi_clean" ] && {
    cat<<-EOF >&2
	Warning:  The OpenCPI $ocpi_name file should be sourced when OCPI_CDK_DIR is not set,
	          when not cleaning or resetting it.
	          OCPI_CDK_DIR was already set to: $OCPI_CDK_DIR, so nothing is changed.
	          Use the --reset argument to reset OpenCPI environment variables before setup
	          Use the --clean argument to unset all OpenCPI environment variables and return
	EOF
    return 1
  }
  [ -n "$ocpi_verbose" ] &&
      echo Clearing all OpenCPI environment variables before setting anything >&2
  for ocpi_v in $(env | egrep "^$ocpi_cleaned_vars" | sort | cut -f1 -d=)
  do
    unset $ocpi_v
  done
}
# Make the file name of this script absolute if it isn't already
# But leave it user friendly (don't do readlink etc.)
[[ "$ocpi_me" = /* ]] || ocpi_me=`pwd`/$ocpi_me
ocpi_dir=`dirname $ocpi_me`
[ -d $ocpi_dir -a -x $ocpi_dir ] || {
  echo $ocpi_name:' ' Unexpected error:' ' directory $ocpi_dir not a directory or inaccessible. >&2
  return 1
}
ocpi_cdk_dir=$(cd $ocpi_dir && pwd)
ocpi_root_dir=$(cd $ocpi_dir/.. && pwd)
[ "$ocpi_verbose" = 1 ] && cat <<-EOF >&2
	This $ocpi_name script is located at:
	  $ocpi_me
	OCPI_CDK_DIR is being set to be $ocpi_cdk_dir.
	Determining the OpenCPI platform we are running on...
	EOF
if [ -n "$OCPI_ROOT_DIR" ]; then
  echo "OCPI_ROOT_DIR already set to $OCPI_ROOT_DIR, so we will use that value"
  ocpi_root_dir=$OCPI_ROOT_DIR
fi
ocpi_gp=$ocpi_cdk_dir/scripts/getPlatform.sh
if [ ! -f $ocpi_gp ]; then
  # Poor mans get-platform in a runtime installation, that also sets TARGET variables
  # !!We commit the global variables here so under failure, the envronment is polluted.
  # FIXME:  what "runtime" scenario is this really supposed to work in?
  export OCPI_CDK_DIR=$ocpi_cdk_dir
  export OCPI_ROOT_DIR=$ocpi_root_dir
  for p in $ocpi_cdk_dir/*; do
    ocpi_check=$p/$(basename $p)-check.sh
    [ -e $ocpi_check ] && bash $ocpi_check && {
       source $p/$(basename $p)-init.sh
       break
    }
  done
  [ -z "$OCPI_TOOL_PLATFORM" ] && {
    echo "Cannot determine the runtime platform from $ocpi_cdk_dir/*/*-check.sh" >&2
    return 1
  }
else
  # We have not committed any variable settings yet
  [ -x $ocpi_gp ] || {
    echo $ocpi_name: cannot run the internal getPlatforms.sh script at $ocpi_gp. >&2
    echo $ocpi_name: this indicates a corrupted or incomplete installation >&2
    return 1
  }
  read v0 v1 v2 v3 v4 v5 <<< `$ocpi_gp "" $ocpi_cdk_dir $ocpi_root_dir`
  if [ "$v4" == "" -o $? != 0 ]; then
    echo $ocpi_name: failed to determine runtime platform. >&2
    return 1
  fi
  ocpi_tool_dir=$v4
  [ -n "$ocpi_dynamic" -o -n "$ocpi_optimize" ] && {
      ocpi_tool_dir+=-
      [ -n "$ocpi_dynamic" ] && ocpi_tool_dir+=d
      [ -n "$ocpi_optimize" ] && ocpi_tool_dir+=o
      ocpi_bin_dir=$ocpi_cdk_dir/$ocpi_tool_dir/bin
      [ ! -d "$ocpi_bin_dir" ] && {
	  echo "$ocpi_name:  Error: the --dynamic or --optimize options were specified, " >&2
	  echo "$ocpi_name:  but the host platform has not yet been built with these options." >&2
	  echo "$ocpi_name:  You need to build for these options before using them." >&2
	  echo "$ocpi_name:  with the command:" >z&2
	  echo "$ocpi_name:    ocpiadmin install platform [--dynamic|--optimize]* $4" >&2
	  return 1
      }
  }
  # Now we commit the settings of the variables and thus the "pollution" of the user's envronment
  export OCPI_CDK_DIR=$ocpi_cdk_dir
  export OCPI_ROOT_DIR=$ocpi_root_dir
  export OCPI_TOOL_DIR=$ocpi_tool_dir
  export OCPI_TOOL_OS=$v0
  export OCPI_TOOL_OS_VERSION=$v1
  export OCPI_TOOL_ARCH=$v2
  export OCPI_TOOL_PLATFORM=$v4
  export OCPI_TOOL_PLATFORM_DIR=$v5
  # This is (temporarily) redundant with ocpibootstrap.sh
  [ -z "$OCPI_PREREQUISITES_DIR" ] && {
    export OCPI_PREREQUISITES_DIR=$OCPI_ROOT_DIR/prerequisites
    if [ -d $OCPI_PREREQUISITES_DIR ]; then
      export OCPI_PREREQUISITES_DIR=$(cd $OCPI_PREREQUISITES_DIR; pwd)
    else
      echo "$ocpi_name:  warning:  $OCPI_PREREQUISITES_DIR does not exist.  The installation/build of OpenCPI is incomplete." >&2
    fi
  }
  [ "$ocpi_verbose" = 1 ] &&
    echo "Software prerequisites are located at $OCPI_PREREQUISITES_DIR" >&2
fi

# Clean out any previous instances in the path
ocpi_cleaned=$(echo "$PATH" | sed "s=$OCPI_CDK_DIR/[^:/]*/bin[^:]*:==g")
[ -n "$ocpi_verbose" -a "$PATH" != "$ocpi_cleaned" ] && echo Removing OpenCPI bin directory from PATH >&2
export PATH="$OCPI_CDK_DIR/$OCPI_TOOL_DIR/bin:$ocpi_cleaned"
ocpi_cleaned=$(echo "$PYTHONPATH" | sed "s=$OCPI_CDK_DIR/[^:/]*/lib[^:]*:*==g")
[ -n "$ocpi_verbose" -a "$PYTHONPATH" != "$ocpi_cleaned" ] && echo Removing OpenCPI lib directory from PYTHONPATH >&2
export PYTHONPATH="$OCPI_CDK_DIR/$OCPI_TOOL_DIR/lib${ocpi_cleaned:+:}$ocpi_cleaned:"
ocpi_cleaned=$(echo "$MANPATH" | sed "s=$OCPI_CDK_DIR/doc/man[^:]*:*==g")
[ -n "$ocpi_verbose" -a "$MANPATH" != "$ocpi_cleaned" ] && echo Removing OpenCPI doc/man directory from MANPATH >&2
export MANPATH="$OCPI_CDK_DIR/doc/man${ocpi_cleaned:+:}$ocpi_cleaned"
ocpi_comp=$OCPI_CDK_DIR/scripts/ocpidev_bash_complete
[ -f $ocpi_comp ] && source $ocpi_comp
[ "$ocpi_verbose" = 1 ] && cat <<-EOF >&2
	The OpenCPI platform we are running on is "$OCPI_TOOL_PLATFORM" (placed in OCPI_TOOL_PLATFORM).
	The OpenCPI target directory set for this environment is "$OCPI_TOOL_DIR".
	PATH now set to $PATH
	PYTHONPATH now set to $PYTHONPATH
	MANPATH now set to $MANPATH
	Now determining where prerequisite software is installed.
	EOF
ocpi_user_env=$OCPI_ROOT_DIR/user-env.sh
[ -r "$ocpi_user_env" ] && {
  if grep -q '^ *export' $ocpi_user_env; then
    [ "$ocpi_verbose" = 1 ] &&
	echo "Sourcing $ocpi_user_env for user settings of OpenCPI environment variables." >&2
    source $ocpi_user_env
  elif [ -r $ocpi_user_env ]; then
    [ "$ocpi_verbose" = 1 ] &&
	echo The user environment setting script \"$ocpi_user_env\" contains no export commands so it is ignored. >&2
  fi
}
[ "$ocpi_verbose" = 1 ] && {
  echo "Below are all OCPI_* environment variables now set:" >&2
  env | grep OCPI | sort >&2
}

# Clear bash hash in case there are any paths stored in it
hash -r

return 0
