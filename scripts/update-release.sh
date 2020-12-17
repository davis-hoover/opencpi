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

set -e

function usage {
  cat <<USAGE
Usage: $(basename "$0") [--autotools-only]

Updates OpenCPI version that is defined in various places. This script is only
used when creating releases and relies on properties in the VERSION file being
set correctly.

Optional arguments:
  --autotools-only  Only update version defined in configure.ac. This is done
                    after a new minor release has been made.
USAGE
  exit 1
}

function validate_release {
  local release="$1"

  if [ "$release" = develop ]; then
    RELEASE=develop
    return 0
  fi

  # Clean up release tag
  [[ "$release" != v* ]]  && release="v$release"

  # Validate proper format. Format after the hyphen is not enforced, but
  # might be in the future.
  if [[ ! "${release%%-*}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Invalid release tag '$1'"
    return 1
  fi

  RELEASE="$release"
  return 0
}


##### Main #####

# Workaround for realpath not available on all OS
OCPI_ROOT=$(cd "$(dirname $0)"; cd ..; pwd)

# Parse args
RELEASE=         # set by parse_release
AUTOTOOLS_ONLY=
while [ -n "$1" ]; do
  case "$1" in
    --autotools-only)  AUTOTOOLS_ONLY=1 ;;
    *)                 usage ;;
  esac
  shift
done

if [ ! -f "$OCPI_ROOT/VERSION" ]; then
  echo '\
Cannot find required VERSION file. This file must reside at the root of the
OpenCPI source tree'
  exit 1
fi
source "$OCPI_ROOT/VERSION"

if [ "$OCPI_VERSION_EXTRA" = develop ]; then
  RELEASE=develop
else
  validate_release "$OCPI_RELEASE"
fi

# RELEASE should be defined by now...
if [ -z "$RELEASE" ]; then
  echo "Something went wrong processing the release string '$OCPI_RELEASE'"
  exit 1
fi

# Fix the builtin software release tag for compatibility checking
if [ "$RELEASE" != develop ]; then
  (cd build/autotools
   echo "Updating autotools for release $RELEASE (base=$OCPI_VERSION " \
        "major=$OCPI_VERSION_MAJOR minor=$OCPI_VERSION_MINOR " \
        "patch=$OCPI_VERSION_PATCH)"
   sed -e "s/\(AC_INIT(\[opencpi\],\[\)[^]]*/\1$OCPI_VERSION/" \
       -e "s/\(AC_DEFINE(\[VERSION_MAJOR\],\)[^,]*\(,.*\)$/\1$OCPI_VERSION_MAJOR\2/" \
       -e "s/\(AC_DEFINE(\[VERSION_MINOR\],\)[^,]*\(,.*\)$/\1$OCPI_VERSION_MINOR\2/" \
       -e "s/\(AC_DEFINE(\[VERSION_PATCHLEVEL\],\)[^,]*\(,.*\)$/\1$OCPI_VERSION_PATCH\2/" \
       -i configure.ac
  )
else
  echo "Not updating autotools, 'develop' specified as release"
fi

# Are we only doing autotools?
[ -n "$AUTOTOOLS_ONLY" ] && exit 0

# Fix the common release subtitle and any URLs in fodt files
echo "Updating odt docs for release $RELEASE"
for f in $(find doc/ -type f -name '*.fodt'); do
  sed -i "s|\(OpenCPI Release:\)[^<]*|\1  $RELEASE|" "$f"
  sed -i 's|\( xlink:href="https://opencpi.gitlab.io/releases/\)[^/]*\(/docs/[^"]*"\)|\1'"$RELEASE"'\2|g' "$f"
  sed -i 's|\(>https://opencpi.gitlab.io/releases/\)[^/]*\(/docs/[^<]*<\)|\1'"$RELEASE"'\2|g' "$f"
done

# Fix the common release subtitle for tex docs
echo "Updating tex docs for release $RELEASE"
sed -i "s/\(ocpiversion{\)[^}]*/\1$RELEASE/" doc/av/tex/snippets/LaTeX_Header.tex

exit 0
