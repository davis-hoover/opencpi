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
#  (2) Must have previously downloaded the appropriate Xilinx
#      Unified Installer file from https://www.xilinx.com.
#  (3) Must have enough available disk space to handle both the
#      expansion of the Xilinx Unified Installer file and the items
#      downloaded during installation (into INSTALL_DIR/Downloads).
#      The installer normally checks for the latter.  The former is
#      not worth the overhead of checking for because expanding the
#      installer file happens early, and the error message produced
#      by the system is unambiguous as to the problem.  Expansion of
#      the installer file requires considerably less than a gigabyte
#      as of mid-2022 (approximately 700 MB).
#
# The OpenCPI Installation Guide is an appropriate reference to have
# handy when running this script.
#

function usage {
  cat <<EOF

Usage: $(basename $0) [OPTION]... XILINX_UNIFIED_INSTALLER_FILE

Mandatory arguments to long options are mandatory for short options too.
Long options may be abbreviated.

  -e, --extract-dir=DIR          extraction directory for the installer;
                                   not the same as the installation directory;
				   default is "20YY.X" in the directory where
				   the installer file exists
  -d, --destination=DIR          installation directory; default is "/opt/Xilinx"
  -p, --program-group-shortcuts  create program group shortcuts; default is "no"
  -s, --shortcuts-on-desktop     create desktop shortcuts; default is "no"
  -f, --file-association         create Xilinx tool file associations (file
                                   suffix recognition); default is "no"
  -h, --help                     print this message and exit

   Use of the next two options is STRONGLY DISCOURAGED.  Create
   "~/.Xilinx/.auth" containing the account credentials instead:
   first line is the account ID, second is the account password.

  -U, --User-id=X_ID             Xilinx account ID; no default
  -P, --Password=X_PW            Xilinx account password; no default
EOF
  exit 1
}

#
# "getopts" does not handle long-format options (--opt=blah, --opt blah)
# directly, so things get complex in a hurry.  Observed limitation of this
# approach and similar ones: a long-format option must begin with the same
# letter as its corresponding short option.  This means there can be only
# one long-format option associated with a given short option.
#
# One very cool plus to this implementation: abbreviated long-format
# options are handled correctly.  A very uncool minus: short-format
# options requiring an argument will end up with the next argument,
# whether an option or otherwise, as the value for that option.  A
# fix has been incorporated below.
#
# Credit where due: this was found on StackExchange.
#
# Options we know about:
# -e, --extract-dir=[extraction directory] (default: $XDIR)
# -d, --destination=[installation directory] (default: /opt/Xilinx)
# -p, --program-group-shortcuts (default: 0 == "no")
# -s, --shortcuts-on-desktop (default: 0 == "no")
# -f, --file-association (default: 0 == "no")
# -U, --User-id (no default: use strongly discouraged)
# -P, --Password (no default: use strongly discouraged)
# -h, --help
#
# Both short and long opts requiring an argument end with ':'.
#
short_opts=e:d:psfU:P:h
long_opts=extract-dir:/destination:/program-group-shortcuts/shortcuts-on-desktop/file-association/User-id:/Password:/help

# override via command line for testing purposes
# if [ "$#" -ge 2 ]; then
#   short_opts=$1; long_opts=$2; shift 2
# fi

while getopts ":$short_opts-:" o; do
    case $o in
    :) echo "Error: option -$OPTARG needs an argument." >&2 ; usage ;;
    '?') echo "Error: bad option -$OPTARG" >&2 ; usage ;;
    -)  o=${OPTARG%%=*}; OPTARG=${OPTARG#"$o"}; lo=/$long_opts/
        case $lo in
        *"/$o"[!/:]*"/$o"[!/:]*) echo "Error: ambiguous option --$o" >&2 ; usage ;;
        *"/$o"[:/]*) ;;
        *) o=$o${lo#*"/$o"}; o=${o%%[/:]*} ;;
        esac
        case $lo in
        *"/$o/"*) OPTARG= ;;
        *"/$o:/"*)
            case $OPTARG in
            '='*)   OPTARG=${OPTARG#=};;
            *)  eval "OPTARG=\$$OPTIND"
                if [ "$OPTIND" -le "$#" ] && [ "$OPTARG" != -- ]; then
                    OPTIND=$((OPTIND + 1))
                else
                    echo "Error: option --$o needs an argument." >&2 ; usage
                fi ;;
            esac ;;
        *) echo "Error: unknown option --$o" >&2 ; usage ;;
        esac
    esac

    #
    # Set shell variables we will need when editing the default batch
    # config file.  These variable names just happen to precisely match
    # the parameter names in the config file.  This is a good place to
    # see if $OPTARG begins with '-', meaning, a short-format option
    # requiring an argument got assigned another option as its value.
    #
    case $o in
    e|extract-dir)
        if [[ "$OPTARG" == "-"* ]]
        then
            echo "Error: '-e' needs an argument." >&2 && usage
        else
            XExDIR=$OPTARG
        fi ;;
    d|destination)
        if [[ "$OPTARG" == "-"* ]]
        then
            echo "Error: '-d' needs an argument." >&2 && usage
        else
            Destination=$OPTARG
        fi ;;
    p|program-group-shortcuts)
        CreateProgramGroupShortcuts=1 ;;
    s|shortcuts-on-desktop)
        CreateDesktopShortcuts=1 ;;
    f|file-association)
        CreateFileAssociation=1 ;;
    U|User-id)
        if [[ "$OPTARG" == "-"* ]]
        then
            echo "Error: '-U' needs an argument." >&2 && usage
        else
            X_ID=$OPTARG
        fi ;;
    P|Password)
        if [[ "$OPTARG" == "-"* ]]
        then
            echo "Error: '-P' needs an argument." >&2 && usage
        else
            X_PW=$OPTARG
        fi ;;
    h|help)
        usage ;;
    esac
done

#
# Set default values for config parameters if not set by user.
#
Destination=${Destination:-/opt/Xilinx}
CreateProgramGroupShortcuts=${CreateProgramGroupShortcuts:-0}
CreateDesktopShortcuts=${CreateDesktopShortcuts:-0}
CreateFileAssociation=${CreateFileAssociation:-0}

#echo "XExDir: ${XExDIR:-(will be computed)}"
#echo "Destination: $Destination"
#echo "CreateProgramGroupShortcuts: $CreateProgramGroupShortcuts"
#echo "CreateDesktopShortcuts: $CreateDesktopShortcuts"
#echo "CreateFileAssociation: $CreateFileAssociation"
#echo "X_ID: ${X_ID:-(not specified)}"
#echo "X_PW: ${X_PW:-(not specified)}"

#
# Remaining args are positional parameters.  There should
# be only one -- the Xilinx Unified Installer file.
#
shift "$((OPTIND - 1))"
if [ $# -ne 1 ]
then
    usage
else
    XIF=$1
fi
#echo "XIF: $XIF"

#
# Early error checking: no sense going any further if the
# necessary Xilinx account credentials are not available.
#
if [ -n "$X_ID" -a -z "$X_PW" ]
then
    echo "Error: Xilinx account password not specified." >&2
    exit 1
elif [ -z "$X_ID" -a -n "$X_PW" ]
then
    echo "Error: Xilinx account ID not specified." >&2
    exit 1
elif [ -z "$X_ID" -a -z "$X_PW" -a ! -f ~/.Xilinx/.auth ]
then
    echo "Error: missing Xilinx account authentication credentials." >&2
    exit 1
fi

#
# More early error checking: if the destination (installation)
# directory does not exist or is not writable, bail.
#
if [ ! -d $Destination -o ! -w $Destination ]
then
    echo "Error: specified installation directory ($Destination)" >&2
    echo "       either does not exist or is not writable." >&2
    exit 1
fi

#
# Helper scripts will be in the same directory as this script.
#
SDIR=$(dirname $(readlink -f $0))

if [ ! -f "$XIF" ]
then
    echo "Error: specified installer file ($XIF) does not exist." >&2
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
bash $XIF --noexec --nox11 --target ${XExDIR:-$XDIR}
(
  cd ${XExDIR:-$XDIR}
  #
  # The following depends on the existence of "~/.Xilinx/.auth"
  # which should contain two lines: the first line is the Xilinx
  # account email address, and the second is the password.
  #
  if [ -z "$X_ID" ]
  then
    exec {FD}<~/.Xilinx/.auth
    read -u $FD X_ID
    read -u $FD X_PW
    exec {FD}<&-
  fi

  echo -e "\nGenerating authentication token...\n"
  $SDIR/gen_auth_token.exp $X_ID $X_PW

  echo -e "\nGenerating default batch config file...\n"

  #
  # It used to be the case that Vivado was the correct
  # choice of product to install for the 2019.2 release.
  # Xilinx evidently repackaged at least *that* older
  # release to be consistent with how newer releases
  # are packaged.  For now, disable the product version
  # check and always select Vitis.
  #
  #if [ $XVER == "2019.2" ]
  #then
  #  # 2 == Vivado
  #  $SDIR/xilinx_conf_gen.exp 2
  #else
    # 1 == Vitis
    $SDIR/xilinx_conf_gen.exp 1
  #fi

  #
  # Patch the default config file based on user-specified parameters.
  #
  echo -e "\nAdjusting batch config file parameters...\n"
  CONF=~/.Xilinx/install_config.txt
  sed -e "s,^\(Destination=\).*,\\1$Destination,g" \
      -e "s,^\(CreateProgramGroupShortcuts=\).*,\\1$CreateProgramGroupShortcuts,g" \
      -e "s,^\(CreateDesktopShortcuts=\).*,\\1$CreateDesktopShortcuts,g" \
      -e "s,^\(CreateFileAssociation=\).*,\\1$CreateFileAssociation,g" $CONF > $CONF.new 
  mv $CONF.new $CONF

  #
  # Run the installer.
  #
  echo -e "\nBeginning installation of $XVER Xilinx tools into \"$Destination\"...\n"
  ./xsetup --agree $AGREE --batch Install --config ~/.Xilinx/install_config.txt
)
echo -e "\nThe $XVER Xilinx tools have been installed in \"$Destination\"."
echo "If needed to help diagnose installation issues, a log is available"
echo "in the \"~/.Xilinx/xinstall\" directory."
