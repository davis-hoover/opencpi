#!/bin/bash --noprofile

# Usage is:  update-release.sh <release-tag>
# Release tag before any hyphen is assume to be numeric maj.min.patch

set -e
# Fix the common release subtitle and any URLs in fodt files
(cd doc/odt
 sed -i "s|\(OpenCPI Release \)[^<]*|\1$1|" shared/release.fodt
 for f in *.fodt; do
     sed -i 's|\( xlink:href="https://opencpi.gitlab.io/releases/\)[^/]*\(/docs/[^"]*"\)|\1'$1'\2|g' $f
     sed -i 's|\(>https://opencpi.gitlab.io/releases/\)[^/]*\(/docs/[^<]*<\)|\1'$1'\2|g' $f
 done
)
# Fix the common release subtitle for (some) tex docs
(cd doc/av/tex/snippets
 sed -i "s/\(ocpiversion{\)[^}]*/\1$1/" includes.tex
)
# Fix the builtin software release tag for compatibility checking
# Uses arg 2 which is a release tag without any suffixes etc.
(cd build/autotools
 base=$(echo ${1#v*} | sed 's/-.*//')
 major=$(echo $base | sed 's/^\([^.]*\).*$/\1/')
 minor=$(echo $base | sed 's/^[^.]*\.\([^.]*\).*$/\1/')
 patch=$(echo $base | sed 's/^[^.]*\.[^.]*\.\([^.]*\).*$/\1/')
 sed -e "s/\(AC_INIT(\[opencpi\],\[\)[^]]*/\1$base/" \
     -e "s/\(AC_DEFINE(\[VERSION_MAJOR\],\)[^,]*\(,.*\)$/\1$major\2/" \
     -e "s/\(AC_DEFINE(\[VERSION_MINOR\],\)[^,]*\(,.*\)$/\1$minor\2/" \
     -e "s/\(AC_DEFINE(\[VERSION_PATCHLEVEL\],\)[^,]*\(,.*\)$/\1$patch\2/" \
     -i configure.ac
)
