#!/bin/bash --noprofile

# Usage is:  update-release.sh <release-tag>
# Release tag before any hyphen is assume to be numeric maj.min.patch

set -e

function usage {
  cat <<USAGE
Usage: $(basename "$0") <release-tag>

release-tag    An OpenCPI semver compatible release tag.
               Ex. v1.6.0, v1.7.0-beta.1, v1.7.0-rc.1
USAGE
  exit 1
}

function parse_release {
  local release="$1"

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

# Parse args
RELEASE=
if [[ -z "$1" || "$1" = -* ]]; then
  usage
elif [ "$1" == develop ]; then
  RELEASE=$1
elif ! parse_release "$1" ; then
  exit 1
fi

# Fix the common release subtitle and any URLs in fodt files
(cd doc/odt
 echo "Updating odt docs for release $RELEASE"
 sed -i "s|\(OpenCPI Release:  \)[^<]*|\1$RELEASE|" shared/release.fodt
 for f in *.fodt; do
   sed -i "s|\(OpenCPI Release:  \)[^<]*|\1$RELEASE|" "$f"
   sed -i 's|\( xlink:href="https://opencpi.gitlab.io/releases/\)[^/]*\(/docs/[^"]*"\)|\1'"$RELEASE"'\2|g' "$f"
   sed -i 's|\(>https://opencpi.gitlab.io/releases/\)[^/]*\(/docs/[^<]*<\)|\1'"$RELEASE"'\2|g' "$f"
 done
)

# Fix the common release subtitle for (some) tex docs
(cd doc/av/tex/snippets
 echo "Updating tex docs for release $RELEASE"
 sed -i "s/\(ocpiversion{\)[^}]*/\1$RELEASE/" includes.tex
)

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
