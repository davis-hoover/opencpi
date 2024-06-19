#!/bin/bash

do_linter_test() {
  sudo apt install pycodestyle
  # these are the only files that pass the linter, for now (TODO get all ocpidev2 files)
  files=("library2.py" "component2.py" "application2.py" "assembly2.py" "primitive2.py")
  for file in "${files[@]}"
  do
    pycodestyle tools/ocpidev2/assets/$file
  done
}

do_unit_test() {
  ocpidev2 unittest
}

do_build_test() {
  ocpidev2 clean -d projects/core
  ocpidev2 clean -d projects/asset
  ocpidev2 clean -d projects/asset_ts
  ocpidev2 clean -d projects/tutorial
  ocpidev2 clean -d projects/platform
  ocpidev2 build -j 4 -d projects/assets --hdl-platform zed
}

report_coverage() {
  python3 -m pip install coverage
  coverage run $(which ocpidev2) unittest
  coverage report -m
}

set -e
do_linter_test
do_unit_test
do_build_test
#report_coverage
