#!/bin/bash

# Take an fodt file with the CLI-vs-GUI scheme and generate two PDFs -cli.pdf and -gui.pdf
# Caller decides which files need this treatment.

# usage is:  $0 infile outdir

base=$(basename $1)
name=${base%.*}
suff=${base##*.}
cg=${name%-cg}
sed \
    -e 's|\(<text:variable-set text:name="AVGUI"[^/>]* text:formula="[^0-9]*\)[0-9]*|\11|' \
    -e 's|\(<text:variable-set text:name="AVGUI"[^/>]* office:value="\)[^"]*|\11|' \
    $1 > $2/${cg}_CLI.$suff
sed \
    -e 's|\(<text:variable-set text:name="AVGUI"[^/>]* text:formula="[^0-9]*\)[0-9]*|\12|' \
    -e 's|\(<text:variable-set text:name="AVGUI"[^/>]* office:value="\)[^"]*|\12|' \
    $1 > $2/${cg}_GUI.$suff
soffice --convert-to pdf --outdir $2 $2/${cg}_CLI.$suff
soffice --convert-to pdf --outdir $2 $2/${cg}_GUI.$suff
exit 0


