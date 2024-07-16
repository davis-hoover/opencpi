#!/bin/bash

do_linter_test() {
  sudo apt install pycodestyle
  pycodestyle tools/ocpidev2/*py
  pycodestyle tools/ocpidev2/assets/*py
}

do_unit_test() {
  ocpidev2 unittest
}

do_create_test() {
  sudo apt install pycodestyle
  pycodestyle ../tools/ocpidev2/*py
  pycodestyle ../tools/ocpidev2/assets/*py
  ocpidev2 show -h
  ocpidev2 show --help
  ocpidev2 unittest
  ocpidev2 unittest -v
  ocpidev2 unittest --verbose
  rm -rf myproj/
  ocpidev2 create project myproj
  rm -rf myproj/
  ocpidev2 create project myproj -D ocpi.assets
  rm -rf myproj/
  ocpidev2 create project myproj -F ocpi
  rm -rf myproj/
  ocpidev2 create project myproj -K com.geontech
  rm -rf myproj/
  ocpidev2 create project myproj -N geontech
  rm -rf myproj/
  ocpidev2 create project myproj -A mydir
  rm -rf myproj/
  ocpidev2 create project myproj -I mydiri
  rm -rf myproj/
  ocpidev2 create project myproj -Y dsp_prims
  rm -rf myproj/
  ocpidev2 create project myproj -y dsp_comps
}

do_show_test() {
  sudo apt install pycodestyle
  pycodestyle ../tools/ocpidev2/*py
  pycodestyle ../tools/ocpidev2/assets/*py
  ocpidev2 show -h
  ocpidev2 show --help
  ocpidev2 unittest
  ocpidev2 unittest -v
  ocpidev2 unittest --verbose
  ocpidev2 show application FSK
  ocpidev2 show application FSK -v
  ocpidev2 show application FSK --verbose
  ocpidev2 show application FSK -d assets
  ocpidev2 show applications
  ocpidev2 show applications -v
  ocpidev2 show applications --verbose
  ocpidev2 show applications -d assets
  ocpidev2 show -d assets applications
  ocpidev2 -d assets show applications
  ocpidev2 -d assets show -d core applications -d platform -v
  ocpidev2 -d assets show -d core applications -d platform -v -l 8
  ocpidev2 -d assets show -d core applications -d platform -v --log-level 8
  ocpidev2 -d assets show -d core applications -d platform -v -l 10
  ocpidev2 show component drc
  ocpidev2 show component drc -v
  ocpidev2 show component drc --verbose
  ocpidev2 show component drc assets
  ocpidev2 show component platform
  ocpidev2 show component Consumer
  ocpidev2 show components
  ocpidev2 show components -v
  ocpidev2 show components --verbose
  ocpidev2 show components -d assets
  ocpidev2 show -d assets components
  ocpidev2 -d assets show components
  ocpidev2 -d assets show -d core components -d platform -v
  ocpidev2 -d assets show -d core components -d platform -v -l 8
  ocpidev2 -d assets show -d core components -d platform -v --log-level 8
  ocpidev2 -d assets show -d core components -d platform -v -l 10
  ocpidev2 show hdl assembly fsk_modem
  ocpidev2 show hdl assembly fsk_modem -v
  ocpidev2 show hdl assembly fsk_modem --verbose
  ocpidev2 show hdl assembly fsk_modem -d assets
  ocpidev2 show hdl assemblies 
  ocpidev2 show hdl assemblies -v
  ocpidev2 show hdl assemblies --verbose
  ocpidev2 show hdl assemblies -d assets
  ocpidev2 show -d assets hdl assemblies
  ocpidev2 -d assets show hdl assemblies
  ocpidev2 -d assets show -d core hdl assemblies -d platform -v
  ocpidev2 -d assets show -d core hdl assemblies -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl assemblies -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl assemblies -d platform -v -l 10
  ocpidev2 show hdl card fmcomms_2_3_lpc
  ocpidev2 show hdl card fmcomms_2_3_lpc -v
  ocpidev2 show hdl card fmcomms_2_3_lpc --verbose
  ocpidev2 show hdl card fmcomms_2_3_lpc -d assets
  ocpidev2 show hdl cards 
  ocpidev2 show hdl cards -v
  ocpidev2 show hdl cards --verbose
  ocpidev2 show hdl cards -d assets
  ocpidev2 show -d assets hdl cards
  ocpidev2 -d assets show hdl cards
  ocpidev2 -d assets show -d core hdl cards -d platform -v
  ocpidev2 -d assets show -d core hdl cards -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl cards -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl cards -d platform -v -l 10
  ocpidev2 show hdl device dsp_prims
  ocpidev2 show hdl device dsp_prims -v
  ocpidev2 show hdl device dsp_prims --verbose
  ocpidev2 show hdl device dsp_prims -d assets
  ocpidev2 show hdl devices 
  ocpidev2 show hdl devices -v
  ocpidev2 show hdl devices --verbose
  ocpidev2 show hdl devices -d assets
  ocpidev2 show -d assets hdl devices
  ocpidev2 -d assets show hdl devices
  ocpidev2 -d assets show -d core hdl devices -d platform -v
  ocpidev2 -d assets show -d core hdl devices -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl devices -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl devices -d platform -v -l 10
  ocpidev2 show hdl library dsp_prims
  ocpidev2 show hdl library dsp_prims -v
  ocpidev2 show hdl library dsp_prims --verbose
  ocpidev2 show hdl library dsp_prims -d assets
  ocpidev2 show hdl libraries 
  ocpidev2 show hdl libraries -v
  ocpidev2 show hdl libraries --verbose
  ocpidev2 show hdl libraries -d assets
  ocpidev2 show -d assets hdl libraries
  ocpidev2 -d assets show hdl libraries
  ocpidev2 -d assets show -d core hdl libraries -d platform -v
  ocpidev2 -d assets show -d core hdl libraries -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl libraries -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl libraries -d platform -v -l 10
  ocpidev2 show hdl platform zed 
  ocpidev2 show hdl platform zed -v
  ocpidev2 show hdl platform zed --verbose
  ocpidev2 show hdl platform zed -d assets
  ocpidev2 show hdl platforms 
  ocpidev2 show hdl platforms -v
  ocpidev2 show hdl platforms --verbose
  ocpidev2 show hdl platforms -d assets
  ocpidev2 show -d assets hdl platforms
  ocpidev2 -d assets show hdl platforms
  ocpidev2 -d assets show -d core hdl platforms -d platform -v
  ocpidev2 -d assets show -d core hdl platforms -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl platforms -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl platforms -d platform -v -l 10
  ocpidev2 show hdl primitive zynq
  ocpidev2 show hdl primitive zynq -v
  ocpidev2 show hdl primitive zynq --verbose
  ocpidev2 show hdl primitive zynq -d assets
  ocpidev2 show hdl primitives 
  ocpidev2 show hdl primitives -v
  ocpidev2 show hdl primitives --verbose
  ocpidev2 show hdl primitives -d assets
  ocpidev2 show -d assets hdl primitives
  ocpidev2 -d assets show hdl primitives
  ocpidev2 -d assets show -d core hdl primitives -d platform -v
  ocpidev2 -d assets show -d core hdl primitives -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl primitives -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl primitives -d platform -v -l 10
  ocpidev2 show hdl primitive core zed 
  ocpidev2 show hdl primitive core zed -v
  ocpidev2 show hdl primitive core zed --verbose
  ocpidev2 show hdl primitive core zed -d assets
  ocpidev2 show hdl primitive cores 
  ocpidev2 show hdl primitive cores -v
  ocpidev2 show hdl primitive cores --verbose
  ocpidev2 show hdl primitive cores -d assets
  ocpidev2 show -d assets hdl primitive cores
  ocpidev2 -d assets show hdl primitive cores
  ocpidev2 -d assets show -d core hdl primitive cores -d platform -v
  ocpidev2 -d assets show -d core hdl primitive cores -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl primitive cores -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl primitive cores -d platform -v -l 10
  ocpidev2 show hdl primitive library dsp_prims 
  ocpidev2 show hdl primitive library dsp_prims -v
  ocpidev2 show hdl primitive library dsp_prims --verbose
  ocpidev2 show hdl primitive library dsp_prims -d assets
  ocpidev2 show hdl primitive libraries 
  ocpidev2 show hdl primitive libraries -v
  ocpidev2 show hdl primitive libraries --verbose
  ocpidev2 show hdl primitive libraries -d assets
  ocpidev2 show -d assets hdl primitive libraries
  ocpidev2 -d assets show hdl primitive libraries
  ocpidev2 -d assets show -d core hdl primitive libraries -d platform -v
  ocpidev2 -d assets show -d core hdl primitive libraries -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl primitive libraries -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl primitive libraries -d platform -v -l 10
  ocpidev2 show hdl slot fmc_lpc
  ocpidev2 show hdl slot fmc_lpc -v
  ocpidev2 show hdl slot fmc_lpc --verbose
  ocpidev2 show hdl slot fmc_lpc -d assets
  ocpidev2 show hdl slots 
  ocpidev2 show hdl slots -v
  ocpidev2 show hdl slots --verbose
  ocpidev2 show hdl slots -d assets
  ocpidev2 show -d assets hdl slots
  ocpidev2 -d assets show hdl slots
  ocpidev2 -d assets show -d core hdl slots -d platform -v
  ocpidev2 -d assets show -d core hdl slots -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl slots -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl slots -d platform -v -l 10
  ocpidev2 show hdl target zynq 
  ocpidev2 show hdl target zynq -v
  ocpidev2 show hdl target zynq --verbose
  ocpidev2 show hdl target zynq -d assets
  ocpidev2 show hdl targets 
  ocpidev2 show hdl targets -v
  ocpidev2 show hdl targets --verbose
  ocpidev2 show hdl targets -d assets
  ocpidev2 show -d assets hdl targets
  ocpidev2 -d assets show hdl targets
  ocpidev2 -d assets show -d core hdl targets -d platform -v
  ocpidev2 -d assets show -d core hdl targets -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl targets -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl targets -d platform -v -l 10
  ocpidev2 show hdl worker complex_mixer.hdl
  ocpidev2 show hdl worker complex_mixer.hdl -v
  ocpidev2 show hdl worker complex_mixer.hdl --verbose
  ocpidev2 show hdl worker complex_mixer.hdl -d assets
  ocpidev2 show hdl workers 
  ocpidev2 show hdl workers -v
  ocpidev2 show hdl workers --verbose
  ocpidev2 show hdl workers -d assets
  ocpidev2 show -d assets hdl workers
  ocpidev2 -d assets show hdl workers
  ocpidev2 -d assets show -d core hdl workers -d platform -v
  ocpidev2 -d assets show -d core hdl workers -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl workers -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl workers -d platform -v -l 10
  ocpidev2 show library dsp_comps
  ocpidev2 show library dsp_comps -v
  ocpidev2 show library dsp_comps --verbose
  ocpidev2 show library dsp_comps -d assets
  ocpidev2 show hdl libraries 
  ocpidev2 show hdl libraries -v
  ocpidev2 show hdl libraries --verbose
  ocpidev2 show hdl libraries -d assets
  ocpidev2 show -d assets hdl libraries
  ocpidev2 -d assets show hdl libraries
  ocpidev2 -d assets show -d core hdl libraries -d platform -v -l 8
  ocpidev2 -d assets show -d core hdl libraries -d platform -v --log-level 8
  ocpidev2 -d assets show -d core hdl libraries -d platform -v -l 10
  ocpidev2 show platform zed
  ocpidev2 show platform zed -v
  ocpidev2 show platform zed --verbose
  ocpidev2 show platform zed -d assets
  ocpidev2 show platforms 
  ocpidev2 show platforms -v
  ocpidev2 show platforms --verbose
  ocpidev2 show platforms -d assets
  ocpidev2 show -d assets platforms
  ocpidev2 -d assets show platforms
  ocpidev2 -d assets show -d core platforms -d platform -v
  ocpidev2 -d assets show -d core platforms -d platform -v -l 8
  ocpidev2 -d assets show -d core platforms -d platform -v --log-level 8
  ocpidev2 -d assets show -d core platforms -d platform -v -l 10
  ocpidev2 show project assets
  ocpidev2 show project assets -v
  ocpidev2 show project assets --verbose
  ocpidev2 show project assets -d assets
  ocpidev2 show projects 
  ocpidev2 show projects -v
  ocpidev2 show projects --verbose
  ocpidev2 show projects -d assets
  ocpidev2 show -d assets projects
  ocpidev2 -d assets show projects
  ocpidev2 -d assets show -d core projects -d platform -v
  ocpidev2 -d assets show -d core projects -d platform -v -l 8
  ocpidev2 -d assets show -d core projects -d platform -v --log-level 8
  ocpidev2 -d assets show -d core projects -d platform -v -l 10
  ocpidev2 show protocol assets
  ocpidev2 show protocol assets -v
  ocpidev2 show protocol assets --verbose
  ocpidev2 show protocol assets -d assets
  ocpidev2 show protocols
  ocpidev2 show protocols -v
  ocpidev2 show protocols --verbose
  ocpidev2 show protocols -d assets
  ocpidev2 show -d assets protocols  
  ocpidev2 -d assets show protocols
  ocpidev2 -d assets show -d core protocols -d platform -v
  ocpidev2 -d assets show -d core protocols -d platform -v -l 8
  ocpidev2 -d assets show -d core protocols -d platform -v --log-level 8
  ocpidev2 -d assets show -d core protocols -d platform -v -l 10
  ocpidev2 show rcc platform ubuntu20_04
  ocpidev2 show rcc platform ubuntu20_04 -v
  ocpidev2 show rcc platform ubuntu20_04 --verbose
  ocpidev2 show rcc platform ubuntu20_04 -d assets
  ocpidev2 show rcc platforms 
  ocpidev2 show rcc platforms -v
  ocpidev2 show rcc platforms --verbose
  ocpidev2 show rcc platforms -d assets
  ocpidev2 show -d assets rcc platforms
  ocpidev2 -d assets show rcc platforms
  ocpidev2 -d assets show -d core rcc platforms -d platform -v
  ocpidev2 -d assets show -d core rcc platforms -d platform -v -l 8
  ocpidev2 -d assets show -d core rcc platforms -d platform -v --log-level 8
  ocpidev2 -d assets show -d core rcc platforms -d platform -v -l 10
  ocpidev2 show registry
  ocpidev2 show registry -v
  ocpidev2 show registry --verbose
  ocpidev2 show target zynq 
  ocpidev2 show target zynq -v
  ocpidev2 show target zynq --verbose
  ocpidev2 show target zynq -d assets
  ocpidev2 show targets 
  ocpidev2 show targets -v
  ocpidev2 show targets --verbose
  ocpidev2 show targets -d assets
  ocpidev2 show -d assets targets
  ocpidev2 -d assets show targets
  ocpidev2 -d assets show -d core targets -d platform -v
  ocpidev2 -d assets show -d core targets -d platform -v -l 8
  ocpidev2 -d assets show -d core targets -d platform -v --log-level 8
  ocpidev2 -d assets show -d core targets -d platform -v -l 10
  ocpidev2 show test bias.test
  ocpidev2 show test bias.test -v
  ocpidev2 show test bias.test --verbose
  ocpidev2 show test bias.test -d assets
  ocpidev2 show tests 
  ocpidev2 show tests -v
  ocpidev2 show tests --verbose
  ocpidev2 show tests -d assets
  ocpidev2 show -d assets tests
  ocpidev2 -d assets show tests
  ocpidev2 -d assets show -d core tests -d platform -v
  ocpidev2 -d assets show -d core tests -d platform -v -l 8
  ocpidev2 -d assets show -d core tests -d platform -v --log-level 8
  ocpidev2 -d assets show -d core tests -d platform -v -l 10
  ocpidev2 show worker cic_dec.hdl 
  ocpidev2 show worker cic_dec.hdl -v
  ocpidev2 show worker cic_dec.hdl --verbose
  ocpidev2 show worker cic_dec.hdl -d assets
  ocpidev2 show workers 
  ocpidev2 show workers -v
  ocpidev2 show workers --verbose
  ocpidev2 show workers -d assets
  ocpidev2 show -d assets workers
  ocpidev2 -d assets show workers
  ocpidev2 -d assets show -d core workers -d platform -v
  ocpidev2 -d assets show -d core workers -d platform -v -l 8
  ocpidev2 -d assets show -d core workers -d platform -v --log-level 8
  ocpidev2 -d assets show -d core workers -d platform -v -l 10
  ocpidev2 show components --simple
  ocpidev2 show components --table
  ocpidev2 show components --json
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
