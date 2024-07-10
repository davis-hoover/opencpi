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
  ocpidev2 unittest -v
  ocpidev2 unittest --verbose
  ocpidev2 show application FSK
  ocpidev2 show application FSK -v
  ocpidev2 show application FSK --verbose
  ocpidev2 show applications
  ocpidev2 show applications -v
  ocpidev2 show applications --verbose
  ocpidev2 show applications -d assets
  ocpidev2 show -d assets applications
  ocpidev2 -d assets show applications
  ocpidev2 show applications -d assets -d core -v
  ocpidev2 show component drc
  ocpidev2 show component drc -v
  ocpidev2 show component drc --verbose
  ocpidev2 show component platform
  ocpidev2 show component Consumer
  ocpidev2 show components
  ocpidev2 show components -v
  ocpidev2 show components --verbose
  ocpidev2 show components -d assets
  ocpidev2 show -d assets components
  ocpidev2 -d assets show components
  ocpidev2 show components -d assets -d core -v
  ocpidev2 show hdl library dsp_comps
  ocpidev2 show hdl library dsp_comps -v
  ocpidev2 show hdl library dsp_comps --verbose
  ocpidev2 show hdl libraries 
  ocpidev2 show hdl libraries -v
  ocpidev2 show hdl libraries --verbose
  ocpidev2 show hdl libraries -d assets
  ocpidev2 show -d assets hdl libraries
  ocpidev2 -d assets show hdl libraries
  ocpidev2 show hdl libraries -d assets -d core -v

  ocpidev2 show hdl platform zed
  ocpidev2 show hdl platform zed -v
  ocpidev2 show hdl platform zed --verbose
  ocpidev2 show hdl platforms
  ocpidev2 show hdl platforms -v
  ocpidev2 show hdl platforms --verbose
  ocpidev2 show hdl target zynq
  ocpidev2 show hdl target zynq -v
  ocpidev2 show hdl target zynq --verbose
  ocpidev2 show hdl targets
  ocpidev2 show hdl targets --verbose
  ocpidev2 show hdl targets -v
  ocpidev2 show hdl worker complex_mixer.hdl
  ocpidev2 show hdl worker complex_mixer.hdl -v
  ocpidev2 show hdl worker complex_mixer.hdl --verbose
  ocpidev2 show library dsp_comps
  ocpidev2 show library dsp_comps -v
  ocpidev2 show library dsp_comps --verbose
  ocpidev2 show libraries 
  ocpidev2 show libraries -v
  ocpidev2 show libraries --verbose
  ocpidev2 show platform zed
  ocpidev2 show platform zed -v
  ocpidev2 show platform zed --verbose
  ocpidev2 show platforms
  ocpidev2 show platforms -v
  ocpidev2 show platforms --verbose
  ocpidev2 show rcc platform ubuntu20_04
  ocpidev2 show rcc platform ubuntu20_04 -v
  ocpidev2 show rcc platform ubuntu20_04 --verbose
  ocpidev2 show rcc worker complex_mixer.rcc
  ocpidev2 show rcc worker complex_mixer.rcc -v
  ocpidev2 show rcc worker complex_mixer.rcc --verbose
  ocpidev2 show project assets
  ocpidev2 show project assets -v
  ocpidev2 show project assets --verbose
  ocpidev2 show projects
  ocpidev2 show projects -v
  ocpidev2 show projects --verbose
  ocpidev2 show registry
  ocpidev2 show registry -v
  ocpidev2 show registry --verbose
  ocpidev2 show target zynq
  ocpidev2 show target zynq -v
  ocpidev2 show target zynq --verbose
  ocpidev2 show targets
  ocpidev2 show targets --verbose
  ocpidev2 show targets -v
  ocpidev2 show test bias.test
  ocpidev2 show test bias.test -v
  ocpidev2 show test bias.test --verbose
  ocpidev2 show tests
  ocpidev2 show tests -v
  ocpidev2 show tests --verbose
  ocpidev2 show worker cic_dec.hdl
  ocpidev2 show worker cic_dec.hdl -v
  ocpidev2 show worker cic_dec.hdl --verbose
  ocpidev2 show workers
  ocpidev2 show workers -v
  ocpidev2 show workers --verbose
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
