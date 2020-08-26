#!/bin/bash --noprofile

set -e

function usage {
  cat <<USAGE
Usage: $(basename "$0") [--autotools-only] <release-tag>

Updates OpenCPI version that is defined in various places. This script is only
used when creating releases.

Required arguments:
  release-tag  An OpenCPI semver compatible release tag.
               Ex. v1.6.0, v1.7.0-beta.1, v1.7.0-rc.1

Optional arguments:
  --autotools-only  Only update version defined in configure.ac. This is done
                    after a new minor release has been made.
USAGE
  exit 1
}

function parse_release {
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

if [ -z "$1" ]; then
  usage
  exit 1
fi

# Parse args
RELEASE=         # set by parse_release
AUTOTOOLS_ONLY=
while [ -n "$1" ]; do
  case "$1" in
    --help|-h)         usage ;;
    --autotools-only)  AUTOTOOLS_ONLY=1 ;;
    *)                 parse_release "$1" || exit 1 ;;
  esac
  shift
done

# RELEASE should be defined by now...
[ -n "$RELEASE" ] || usage

# Fix the builtin software release tag for compatibility checking
if [ "$RELEASE" != develop ]; then
  (cd build/autotools
   base="${RELEASE#v*}"  # remove leading v
   base="${base//-*/}"   # remove hypen and everything after
   read -r -a parts <<< "${base//./ }"  # split on '.'
   major="${parts[0]}"
   minor="${parts[1]}"
   patch="${parts[2]}"
   echo "Updating autotools for release $RELEASE (base=$base major=$major minor=$minor patch=$patch)"
   sed -e "s/\(AC_INIT(\[opencpi\],\[\)[^]]*/\1$base/" \
       -e "s/\(AC_DEFINE(\[VERSION_MAJOR\],\)[^,]*\(,.*\)$/\1$major\2/" \
       -e "s/\(AC_DEFINE(\[VERSION_MINOR\],\)[^,]*\(,.*\)$/\1$minor\2/" \
       -e "s/\(AC_DEFINE(\[VERSION_PATCHLEVEL\],\)[^,]*\(,.*\)$/\1$patch\2/" \
       -i configure.ac
  )
else
  echo "Not updating autotools, 'develop' specified as release"
fi

# Are we only doing autotools?
[ -z "$AUTOTOOLS_ONLY" ] || exit 0

# Fix the common release subtitle and any URLs in fodt files
echo "Updating odt docs for release $RELEASE"
for f in $(find doc/ -type f -name '*.fodt'); do
  sed -i "s|\(OpenCPI Release:\)[^<]*|\1  $RELEASE|" "$f"
  sed -i 's|\( xlink:href="https://opencpi.gitlab.io/releases/\)[^/]*\(/docs/[^"]*"\)|\1'"$RELEASE"'\2|g' "$f"
  sed -i 's|\(>https://opencpi.gitlab.io/releases/\)[^/]*\(/docs/[^<]*<\)|\1'"$RELEASE"'\2|g' "$f"
done

# Fix the common release subtitle for (some) tex docs
echo "Updating tex docs for release $RELEASE"
sed -i "s/\(ocpiversion{\)[^}]*/\1$RELEASE/" doc/av/tex/snippets/LaTeX_Header.tex

exit 0
