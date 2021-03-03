#!/bin/bash

set -e

function usage {
  cat <<USAGE
Take an fodt file with the CLI-vs-GUI scheme and generate two PDFs -cli.pdf
and -gui.pdf

usage: $(basename "$0") <infile> <outdir>

infile    Input fodt file to process
outdir    Output directory to place generated PDF files
USAGE
}

if [ $# -ne 2 ]; then
  usage
  exit 1
fi

INFILE="$1"
OUTDIR="$2"

if [ ! -r "$INFILE" ]; then
  echo "Could not find file '$INFILE' or you do not have read access to it"
  exit 1
fi
if [ ! -d "$OUTDIR" ]; then
  echo "Could not find directory '$OUTDIR' or you do not have read access to it"
  exit 1
fi

#### MAIN ####

BASE=$(basename "$INFILE")
NAME="${BASE%.*}"
SUFF="${BASE##*.}"
CG="${NAME%-cg}"

# There is a bug with unoconv where it doesn't work the first time it is
# ran so we kick start it here
# https://github.com/dagwieers/unoconv/issues/241
unoconv /dev/null > /dev/null 2>&1 || :

# Toggle CLI version of doc and convert to pdf
tmpfile="$OUTDIR/${CG}_CLI.$SUFF"
sed \
    -e 's|\(<text:variable-set text:name="AVGUI"[^/>]* text:formula="[^0-9]*\)[0-9]*|\11|' \
    -e 's|\(<text:variable-set text:name="AVGUI"[^/>]* office:value="\)[^"]*|\11|' \
    "$INFILE" > "$tmpfile"
unoconv --output "$OUTDIR/${CG}_CLI.pdf" "$tmpfile"
rm -f "$tmpfile"

# Toggle GUI version of doc and convert to pdf
tmpfile="$OUTDIR/${CG}_GUI.$SUFF"
sed \
    -e 's|\(<text:variable-set text:name="AVGUI"[^/>]* text:formula="[^0-9]*\)[0-9]*|\12|' \
    -e 's|\(<text:variable-set text:name="AVGUI"[^/>]* office:value="\)[^"]*|\12|' \
    "$INFILE" > "$tmpfile"
unoconv --output "$OUTDIR/${CG}_GUI.pdf" "$tmpfile"
rm -f "$tmpfile"

exit 0
