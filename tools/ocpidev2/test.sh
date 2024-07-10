#!/bin/bash

do_linter_test() {
  sudo apt install pycodestyle
  pycodestyle tools/ocpidev2/*py
  pycodestyle tools/ocpidev2/assets/*py
}

do_unit_test() {
  ocpidev2 unittest
}

do_show_test() {
  sudo apt install pycodestyle
  pycodestyle tools/ocpidev2/*py
  pycodestyle tools/ocpidev2/assets/*py
  ocpidev2 show -h
  ocpidev2 show --help
  ocpidev2 unittest
  ocpidev2 show component drc
  ocpidev2 show component drc -v
  ocpidev2 show component drc --verbose
  ocpidev2 show component platform
  ocpidev2 show component Consumer
}

report_coverage() {
  python3 -m pip install coverage
  coverage run $(which ocpidev2) unittest
  coverage report -m
}

set -e
do_linter_test
do_unit_test
do_show_test
#report_coverage
