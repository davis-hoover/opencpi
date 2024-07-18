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
  mkdir -p projects2
  cd projects2
  ocpidev2 create project core --package-id ocpi.core
  ocpidev2 create library components -d core
  ocpidev2 create library cards -d core/hdl --component-library devices --xml-include '../../components/specs ../devices/lib/hdl ../devices/specs'
  ocpidev2 create library devices -d core/hdl --package-id ocpi.core.devices
  ocpidev2 create library adapters -d core/hdl --package-id ocpi.core.adapters
  ocpidev2 create protocol ComplexShortWithMetadata -d core/specs
  ocpidev2 create protocol TimeStamped_IQ -d core/specs
  ocpidev2 create protocol bool_timed_sample -d core/specs
  ocpidev2 create protocol char_timed_sample -d core/specs
  ocpidev2 create protocol complex_char_timed_sample -d core/specs
  ocpidev2 create protocol complex_double_timed_sample -d core/specs
  ocpidev2 create protocol complex_float_timed_sample -d core/specs
  ocpidev2 create protocol complex_long_timed_sample -d core/specs
  ocpidev2 create protocol complex_longlong_timed_sample -d core/specs
  ocpidev2 create protocol complex_short_timed_sample -d core/specs
  ocpidev2 create protocol double_timed_sample -d core/specs
  ocpidev2 create protocol event -d core/specs
  ocpidev2 create protocol float_timed_sample -d core/specs
  ocpidev2 create protocol gpio -d core/specs
  ocpidev2 create protocol iqstream -d core/specs
  ocpidev2 create protocol iqstream_with_sync -d core/specs
  ocpidev2 create protocol long_timed_sample -d core/specs
  ocpidev2 create protocol longlong_timed_sample -d core/specs
  ocpidev2 create protocol rstream -d core/specs
  ocpidev2 create protocol short_timed_sample -d core/specs
  ocpidev2 create protocol stream32 -d core/specs
  ocpidev2 create protocol stream -d core/specs
  ocpidev2 create protocol tx_event -d core/specs
  ocpidev2 create protocol uchar_timed_sample -d core/specs
  ocpidev2 create protocol ulong_timed_sample -d core/specs
  ocpidev2 create protocol ulonglong_timed_sample -d core/specs
  ocpidev2 create protocol ushort_timed_sample -d core/specs
  ocpidev2 create component backpressure -d core/components/specs
  ocpidev2 create component file_read -d core/components/specs
  ocpidev2 create component file_write -d core/components/specs
  ocpidev2 create component hellow_world -d core/components/specs
  ocpidev2 create component metadata_stressor -d core/components/specs
  ocpidev2 create component zccons -d core/components/specs
  ocpidev2 create component zcloop -d core/components/specs
  ocpidev2 create component zcprod -d core/components/specs
  ocpidev2 create component emulator -d core/components
  ocpidev2 create component bias -d core/components
  ocpidev2 create component clock_gen -d core/specs
  ocpidev2 create component gp_in -d core/specs
  ocpidev2 create component gp_out -d core/specs
  ocpidev2 create component platform -d core/specs
  ocpidev2 create component rx -d core/specs
  ocpidev2 create component tx -d core/specs
  ocpidev2 create worker backpressure.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker backpressure.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker bias.hdl -d core/components --language Verilog --version 2
  ocpidev2 create worker bias.rcc -d core/components --language c --version 2
  ocpidev2 create worker biasFGM_cc.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker bias_cc.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker bias_clock.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker bias_param.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker bias_param.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker bias_spcm.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker bias_spcm.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker bias_ver.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker bias_vhdl.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker bias_wide.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker dgrdma_config_dev.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker dgrdma_config_proxy.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker file_read.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker file_read.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker file_write.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker file_write.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker hello_world.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker hello_world_cc.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker metadata_stressor.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker metadata_stressor.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker nothing.hdl -d core/components --language vhdl --version 2
  ocpidev2 create worker nothing.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker proxy.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker proxy_hdl.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker Consumer.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker Loopback.rcc -d core/components --language c++ --version 2
  ocpidev2 create worker Producer.rcc -d core/components --language c++ --version 2
  ocpidev2 create test backpressure.test -d core/components
  ocpidev2 create test bias.test -d core/components
  ocpidev2 create test metadata_stressor.test -d core/components
  ocpidev2 create hdl card fmc_hpc -d core/hdl/cards/specs
  ocpidev2 create hdl card fmc_lpc -d core/hdl/cards/specs
  ocpidev2 create hdl card hsmc -d core/hdl/cards/specs
  ocpidev2 create hdl card hsmc_alst4 -d core/hdl/cards/specs
  ocpidev2 create hdl primitive axi -d core/hdl/primitives
  ocpidev2 create hdl primitive bsv -d core/hdl/primitives
  ocpidev2 create hdl primitive clocking -d core/hdl/primitives
  ocpidev2 create hdl primitive dgrdma -d core/hdl/primitives
  ocpidev2 create hdl primitive fixed_float -d core/hdl/primitives
  ocpidev2 create hdl primitive ocpi -d core/hdl/primitives
  ocpidev2 create hdl primitive platform -d core/hdl/primitives
  ocpidev2 create hdl primitive protocol -d core/hdl/primitives
  ocpidev2 create hdl primitive sdp -d core/hdl/primitives
  ocpidev2 create hdl primitive sync -d core/hdl/primitives
  ocpidev2 create hdl primitive timed_sample_prot -d core/hdl/primitives
  ocpidev2 create hdl primitive util -d core/hdl/primitives
  ocpidev2 create hdl adapter wsi_from_zero_adapter.hdl -d core/hdl/adapters
  ocpidev2 create hdl adapter wsi_from_zero_clock_adapter.hdl -d core/hdl/adapters
  ocpidev2 create hdl adapter wsi_to_zero_adapter.hdl -d core/hdl/adapters
  ocpidev2 create hdl adapter wsi_to_zero_clock_adapter.hdl -d core/hdl/adapters
  ocpidev2 create hdl adapter wsi_width_adapter.hdl -d core/hdl/adapters
  ocpidev2 create hdl adapter wsi_width_clock_adapter.hdl -d core/hdl/adapters
  ocpidev2 create hdl device ocdp.hdl -d core/hdl/devices
  ocpidev2 create hdl device sdp2cp.hdl -d core/hdl/devices
  ocpidev2 create hdl device sdp_node.hdl -d core/hdl/devices
  ocpidev2 create hdl device sdp_pipeline.hdl -d core/hdl/devices
  ocpidev2 create hdl device sdp_receive.hdl -d core/hdl/devices
  ocpidev2 create hdl device sdp_send.hdl -d core/hdl/devices
  ocpidev2 create hdl device sdp_term.hdl -d core/hdl/devices
  ocpidev2 create hdl device sma.hdl -d core/hdl/devices
  ocpidev2 create hdl device time_server.hdl -d core/hdl/devices
  ocpidev2 create hdl device unoc2cp.hdl -d core/hdl/devices
  ocpidev2 create hdl device unoc_term.hdl -d core/hdl/devices
  ocpidev2 create hdl platform isim -d core/hdl/platforms
  ocpidev2 create hdl platform modelsim -d core/hdl/platforms
  ocpidev2 create hdl platform riviera -d core/hdl/platforms
  ocpidev2 create hdl platform x4sim -d core/hdl/platforms
  ocpidev2 create hdl platform xsim -d core/hdl/platforms
  ocpidev2 create project assets --package-id ocpi.assets --depends ocpi.platform --component-library util_comps --component-library base_comps --component-library misc_comps --component-library dsp_comps --component-library comms_comps --component-library devices
  ocpidev2 create library base_comps -d assets/components
  ocpidev2 create library comms_comps -d assets/components
  ocpidev2 create library dsp_comps -d assets/components
  ocpidev2 create library util_comps -d assets/components
  ocpidev2 create library cards -d assets/hdl
  ocpidev2 create library devices -d assets/hdl
  ocpidev2 create library adapters -d assets/hdl
  cd -
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
