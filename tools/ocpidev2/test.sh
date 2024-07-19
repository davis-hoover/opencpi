#!/bin/bash
################################################################################
# THIS IS THE ALL-ENCOMPASING TEST FOR OCPIDEV2
################################################################################
# RECOMMENDED USAGE (note that q must be typed to bypass help screens):
#  cd projects; rm -rf c*2 a*2 *ev2*; OCPI_LOG_LEVEL=3 ../tools/ocpidev2/test.sh
################################################################################
set -e
sudo apt install pycodestyle
pycodestyle ../tools/ocpidev2/*py
pycodestyle ../tools/ocpidev2/assets/*py
#ocpidev2 -h
#ocpidev2 -help
ocpidev2 show -h
ocpidev2 show --help
#ocpidev2 create -h
#ocpidev2 create --help
ocpidev2 unittest
ocpidev2 unittest -v
ocpidev2 unittest --verbose
ocpidev2 create project core2 --package-id ocpi.core2
ocpidev2 create library components -d core2
ocpidev2 create library cards -d core2/hdl --component-library devices --xml-include '../../components/specs ../devices/lib/hdl ../devices/specs'
ocpidev2 create library devices -d core2/hdl --package-id ocpi.core.devices
ocpidev2 create library adapters -d core2/hdl --package-id ocpi.core.adapters
ocpidev2 create protocol ComplexShortWithMetadata -d core2/specs
ocpidev2 create protocol TimeStamped_IQ -d core2/specs
ocpidev2 create protocol bool_timed_sample -d core2/specs
ocpidev2 create protocol char_timed_sample -d core2/specs
ocpidev2 create protocol complex_char_timed_sample -d core2/specs
ocpidev2 create protocol complex_double_timed_sample -d core2/specs
ocpidev2 create protocol complex_float_timed_sample -d core2/specs
ocpidev2 create protocol complex_long_timed_sample -d core2/specs
ocpidev2 create protocol complex_longlong_timed_sample -d core2/specs
ocpidev2 create protocol complex_short_timed_sample -d core2/specs
ocpidev2 create protocol double_timed_sample -d core2/specs
ocpidev2 create protocol event -d core2/specs
ocpidev2 create protocol float_timed_sample -d core2/specs
ocpidev2 create protocol gpio -d core2/specs
ocpidev2 create protocol iqstream -d core2/specs
ocpidev2 create protocol iqstream_with_sync -d core2/specs
ocpidev2 create protocol long_timed_sample -d core2/specs
ocpidev2 create protocol longlong_timed_sample -d core2/specs
ocpidev2 create protocol rstream -d core2/specs
ocpidev2 create protocol short_timed_sample -d core2/specs
ocpidev2 create protocol stream32 -d core2/specs
ocpidev2 create protocol stream -d core2/specs
ocpidev2 create protocol tx_event -d core2/specs
ocpidev2 create protocol uchar_timed_sample -d core2/specs
ocpidev2 create protocol ulong_timed_sample -d core2/specs
ocpidev2 create protocol ulonglong_timed_sample -d core2/specs
ocpidev2 create protocol ushort_timed_sample -d core2/specs
ocpidev2 create component backpressure -d core2/components/specs
ocpidev2 create component file_read -d core2/components/specs
ocpidev2 create component file_write -d core2/components/specs
ocpidev2 create component hellow_world -d core2/components/specs
ocpidev2 create component metadata_stressor -d core2/components/specs
ocpidev2 create component zccons -d core2/components/specs
ocpidev2 create component zcloop -d core2/components/specs
ocpidev2 create component zcprod -d core2/components/specs
ocpidev2 create component emulator -d core2/components
ocpidev2 create component bias -d core2/components
ocpidev2 create component clock_gen -d core2/specs
ocpidev2 create component gp_in -d core2/specs
ocpidev2 create component gp_out -d core2/specs
ocpidev2 create component platform -d core2/specs
ocpidev2 create component rx -d core2/specs
ocpidev2 create component tx -d core2/specs
ocpidev2 create worker backpressure.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker backpressure.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker bias.hdl -d core2/components --language Verilog --version 2
ocpidev2 create worker bias.rcc -d core2/components --language c --version 2
ocpidev2 create worker biasFGM_cc.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker bias_cc.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker bias_clock.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker bias_param.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker bias_param.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker bias_spcm.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker bias_spcm.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker bias_ver.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker bias_vhdl.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker bias_wide.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker dgrdma_config_dev.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker dgrdma_config_proxy.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker file_read.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker file_read.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker file_write.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker file_write.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker hello_world.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker hello_world_cc.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker metadata_stressor.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker metadata_stressor.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker nothing.hdl -d core2/components --language vhdl --version 2
ocpidev2 create worker nothing.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker proxy.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker proxy_hdl.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker Consumer.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker Loopback.rcc -d core2/components --language c++ --version 2
ocpidev2 create worker Producer.rcc -d core2/components --language c++ --version 2
ocpidev2 create test backpressure -d core2/components
ocpidev2 create test bias -d core2/components
ocpidev2 create test metadata_stressor -d core2/components
ocpidev2 create hdl slot fmc_hpc -d core2/hdl/cards/specs
ocpidev2 create hdl slot fmc_lpc -d core2/hdl/cards/specs
ocpidev2 create hdl slot hsmc -d core2/hdl/cards/specs
ocpidev2 create hdl slot hsmc_alst4 -d core2/hdl/cards/specs
ocpidev2 create hdl primitive axi -d core2/hdl/primitives
ocpidev2 create hdl primitive bsv -d core2/hdl/primitives
ocpidev2 create hdl primitive clocking -d core2/hdl/primitives
ocpidev2 create hdl primitive dgrdma -d core2/hdl/primitives
ocpidev2 create hdl primitive fixed_float -d core2/hdl/primitives
ocpidev2 create hdl primitive ocpi -d core2/hdl/primitives
ocpidev2 create hdl primitive platform -d core2/hdl/primitives
ocpidev2 create hdl primitive protocol -d core2/hdl/primitives
ocpidev2 create hdl primitive sdp -d core2/hdl/primitives
ocpidev2 create hdl primitive sync -d core2/hdl/primitives
ocpidev2 create hdl primitive timed_sample_prot -d core2/hdl/primitives
ocpidev2 create hdl primitive util -d core2/hdl/primitives
ocpidev2 create hdl adapter wsi_from_zero_adapter.hdl -d core2/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_from_zero_clock_adapter.hdl -d core2/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_to_zero_adapter.hdl -d core2/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_to_zero_clock_adapter.hdl -d core2/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_width_adapter.hdl -d core2/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_width_clock_adapter.hdl -d core2/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl device ocdp.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp2cp.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_node.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_pipeline.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_receive.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_send.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_term.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sma.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device time_server.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device unoc2cp.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device unoc_term.hdl -d core2/hdl/devices --language vhdl --version 2
ocpidev2 create hdl platform isim -d core2/hdl/platforms --language vhdl --spec platform
ocpidev2 create hdl platform modelsim -d core2/hdl/platforms --language vhdl --spec platform --libraries sdp
ocpidev2 create hdl platform riviera -d core2/hdl/platforms --language vhdl --spec platform --libraries sdp
ocpidev2 create hdl platform x4sim -d core2/hdl/platforms --language vhdl --spec platform --libraries 'sdp util' --version 2
ocpidev2 create hdl platform xsim -d core2/hdl/platforms --language vhdl --spec platform --libraries sdp --configurations 'base cfg_pps_sim_test'
ocpidev2 create rcc platform centos7 -d core2/rcc/platforms
ocpidev2 create rcc platform centos8 -d core2/rcc/platforms
ocpidev2 create rcc platform macos10_13 -d core2/rcc/platforms
ocpidev2 create rcc platform macos10_14 -d core2/rcc/platforms
ocpidev2 create rcc platform macos10_15 -d core2/rcc/platforms
ocpidev2 create rcc platform macos11_1 -d core2/rcc/platforms
ocpidev2 create rcc platform macos11_2 -d core2/rcc/platforms
ocpidev2 create rcc platform macos11_3 -d core2/rcc/platforms
ocpidev2 create rcc platform macos11_4 -d core2/rcc/platforms
ocpidev2 create rcc platform macos11_5 -d core2/rcc/platforms
ocpidev2 create rcc platform macos11_6 -d core2/rcc/platforms
ocpidev2 create rcc platform macos12_0 -d core2/rcc/platforms
ocpidev2 create rcc platform macos12_1 -d core2/rcc/platforms
ocpidev2 create rcc platform macos12_2 -d core2/rcc/platforms
ocpidev2 create rcc platform macos12_3 -d core2/rcc/platforms
ocpidev2 create rcc platform macos12_4 -d core2/rcc/platforms
ocpidev2 create rcc platform macos12_5 -d core2/rcc/platforms
ocpidev2 create rcc platform macos12_6 -d core2/rcc/platforms
ocpidev2 create rcc platform macos13_0 -d core2/rcc/platforms
ocpidev2 create rcc platform macos13_1 -d core2/rcc/platforms
ocpidev2 create rcc platform mint21_1 -d core2/rcc/platforms
ocpidev2 create rcc platform rocky8 -d core2/rcc/platforms
ocpidev2 create rcc platform ubuntu18_04 -d core2/rcc/platforms
ocpidev2 create rcc platform ubuntu20_04 -d core2/rcc/platforms
ocpidev2 create rcc platform ubuntu22_04 -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx13_3 -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx13_4 -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx13_4_arm -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx17_1_aarch32 -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx17_1_aarch64 -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx17_2_aarch32 -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx17_2_aarch64 -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx18_3_aarch64 -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx19_2_aarch32 -d core2/rcc/platforms
ocpidev2 create rcc platform xilinx19_2_aarch64 -d core2/rcc/platforms
ocpidev2 create project assets2 --package-id ocpi.assets2 --depends ocpi.platform --component-library util_comps --component-library base_comps --component-library misc_comps --component-library dsp_comps --component-library comms_comps --component-library devices
ocpidev2 create library base_comps -d assets2/components
ocpidev2 create library comms_comps -d assets2/components
ocpidev2 create library dsp_comps -d assets2/components
ocpidev2 create library util_comps -d assets2/components
ocpidev2 create library cards -d assets2/hdl
ocpidev2 create library devices -d assets2/hdl
ocpidev2 create library adapters -d assets2/hdl
ocpidev2 create hdl card fmcomms_2_3_hpc -d assets2/hdl/cards/specs
ocpidev2 create project ocpidev2_test_project
ocpidev2 create protocol myprot1 -d ocpidev2_test_project/specs
ocpidev2 create protocol myprot2 -d ocpidev2_test_project --project
ocpidev2 create protocol myprot3 -d ocpidev2_test_project/specs --project
ocpidev2 create library cards -d ocpidev2_test_project/hdl
ocpidev2 create protocol myprot4 -d ocpidev2_test_project --library cards
ocpidev2 create protocol myprot5 -d ocpidev2_test_project --hdl-library cards
pushd ocpidev2_test_project && ocpidev2 create protocol myprot6 --library cards && popd
pushd ocpidev2_test_project && ocpidev2 create protocol myprot7 --hdl-library cards && popd
mkdir ocpidev2_test_project/baddir && pushd ocpidev2_test_project/baddir && ocpidev2 create protocol myprot8 --project && popd
#rm -rf core2
#rm -rf assets2
#ocpidev2 create project core2 --package-id ocpi.core2
#pushd core2 && ocpidev2 create library components && popd
#pushd core2 && ocpidev2 create library cards -d hdl --component-library devices --xml-include '../../components/specs ../devices/lib/hdl ../devices/specs' && popd
#pushd core2/hdl && ocpidev2 create library devices --package-id ocpi.core.devices && popd
#pushd core2/hdl && ocpidev2 create library adapters --package-id ocpi.core.adapters && popd
#pushd core2 && ocpidev2 create protocol ComplexShortWithMetadata -d specs && popd
#pushd core2/specs && ocpidev2 create protocol TimeStamped_IQ && popd
#pushd core2/specs && ocpidev2 create protocol bool_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol char_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol complex_char_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol complex_double_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol complex_float_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol complex_long_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol complex_longlong_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol complex_short_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol double_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol event && popd
#pushd core2/specs && ocpidev2 create protocol float_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol gpio && popd
#pushd core2/specs && ocpidev2 create protocol iqstream && popd
#pushd core2/specs && ocpidev2 create protocol iqstream_with_sync && popd
#pushd core2/specs && ocpidev2 create protocol long_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol longlong_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol rstream && popd
#pushd core2/specs && ocpidev2 create protocol short_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol stream32 && popd
#pushd core2/specs && ocpidev2 create protocol stream && popd
#pushd core2/specs && ocpidev2 create protocol tx_event && popd
#pushd core2/specs && ocpidev2 create protocol uchar_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol ulong_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol ulonglong_timed_sample && popd
#pushd core2/specs && ocpidev2 create protocol ushort_timed_sample && popd
#pushd core2 && ocpidev2 create component backpressure -d core2/components/specs && popd
#pushd core2/components/specs && ocpidev2 create component file_read && popd
#pushd core2/components/specs && ocpidev2 create component file_write && popd
#pushd core2/components/specs && ocpidev2 create component hellow_world && popd
#pushd core2/components/specs && ocpidev2 create component metadata_stressor && popd
#pushd core2/components/specs && ocpidev2 create component zccons && popd
#pushd core2/components/specs && ocpidev2 create component zcloop && popd
#pushd core2/components/specs && ocpidev2 create component zcprod && popd
#pushd core2/components && ocpidev2 create component emulator && popd
#pushd core2/components && ocpidev2 create component bias && popd
#pushd core2/specs && ocpidev2 create component clock_gen && popd
#pushd core2/specs && ocpidev2 create component gp_in && popd
#pushd core2/specs && ocpidev2 create component gp_out && popd
#pushd core2/specs && ocpidev2 create component platform && popd
#pushd core2/specs && ocpidev2 create component rx && popd
#pushd core2/specs && ocpidev2 create component tx && popd
#pushd core2/components && ocpidev2 create worker backpressure.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker backpressure.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias.hdl --language Verilog --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias.rcc --language c --version 2 && popd
#pushd core2/components && ocpidev2 create worker biasFGM_cc.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias_cc.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias_clock.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias_param.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias_param.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias_spcm.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias_spcm.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias_ver.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias_vhdl.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker bias_wide.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker dgrdma_config_dev.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker dgrdma_config_proxy.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker file_read.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker file_read.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker file_write.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker file_write.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker hello_world.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker hello_world_cc.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker metadata_stressor.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker metadata_stressor.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker nothing.hdl --language vhdl --version 2 && popd
#pushd core2/components && ocpidev2 create worker nothing.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker proxy.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker proxy_hdl.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker Consumer.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker Loopback.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create worker Producer.rcc --language c++ --version 2 && popd
#pushd core2/components && ocpidev2 create test backpressure && popd
#pushd core2/components && ocpidev2 create test bias && popd
#pushd core2/components && ocpidev2 create test metadata_stressor && popd
#pushd core2 && ocpidev2 create hdl slot fmc_hpc -d hdl/cards/specs && popd
#pushd core2/hdl/cards/specs && ocpidev2 create hdl slot fmc_lpc && popd
#pushd core2/hdl/cards/specs && ocpidev2 create hdl slot hsmc && popd
#pushd core2/hdl/cards/specs && ocpidev2 create hdl slot hsmc_alst4 && popd
#pushd core2 && ocpidev2 create hdl primitive axi -d hdl/primitives && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive bsv && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive clocking && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive dgrdma && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive fixed_float && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive ocpi && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive platform && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive protocol && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive sdp && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive sync && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive timed_sample_prot && popd
#pushd core2/hdl/primitives && ocpidev2 create hdl primitive util && popd
#pushd core2 && ocpidev2 create hdl adapter wsi_from_zero_adapter.hdl -d hdl/adapters --language vhdl --version 2 && popd
#pushd core2/hdl/adapters && ocpidev2 create hdl adapter wsi_from_zero_clock_adapter.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/adapters && ocpidev2 create hdl adapter wsi_to_zero_adapter.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/adapters && ocpidev2 create hdl adapter wsi_to_zero_clock_adapter.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/adapters && ocpidev2 create hdl adapter wsi_width_adapter.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/adapters && ocpidev2 create hdl adapter wsi_width_clock_adapter.hdl --language vhdl --version 2 && popd
#pushd core2 && ocpidev2 create hdl device ocdp.hdl -d hdl/devices --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device sdp2cp.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device sdp_node.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device sdp_pipeline.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device sdp_receive.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device sdp_send.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device sdp_term.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device sma.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device time_server.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device unoc2cp.hdl --language vhdl --version 2 && popd
#pushd core2/hdl/devices && ocpidev2 create hdl device unoc_term.hdl --language vhdl --version 2 && popd
#pushd core2 && ocpidev2 create hdl platform isim -d hdl/platforms --language vhdl --spec platform && popd
#pushd core2/hdl/platforms && ocpidev2 create hdl platform modelsim --language vhdl --spec platform --libraries sdp && popd
#pushd core2/hdl/platforms && ocpidev2 create hdl platform riviera --language vhdl --spec platform --libraries sdp && popd
#pushd core2/hdl/platforms && ocpidev2 create hdl platform x4sim --language vhdl --spec platform --libraries 'sdp util' --version 2 && popd
#pushd core2/hdl/platforms && ocpidev2 create hdl platform xsim --language vhdl --spec platform --libraries sdp --configurations 'base cfg_pps_sim_test' && popd
#pushd core2 && ocpidev2 create rcc platform centos7 -d rcc/platforms && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform centos8 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos10_13 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos10_14 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos10_15 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos11_1 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos11_2 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos11_3 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos11_4 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos11_5 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos11_6 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos12_0 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos12_1 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos12_2 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos12_3 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos12_4 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos12_5 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos12_6 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos13_0 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform macos13_1 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform mint21_1 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform rocky8 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform ubuntu18_04 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform ubuntu20_04 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform ubuntu22_04 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx13_3 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx13_4 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx13_4_arm && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx17_1_aarch32 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx17_1_aarch64 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx17_2_aarch32 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx17_2_aarch64 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx18_3_aarch64 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx19_2_aarch32 && popd
#pushd core2/rcc/platforms && ocpidev2 create rcc platform xilinx19_2_aarch64 && popd
#ocpidev2 create project assets2 --package-id ocpi.assets2 --depends ocpi.platform --component-library util_comps --component-library base_comps --component-library misc_comps --component-library dsp_comps --component-library comms_comps --component-library devices
#pushd assets2 && ocpidev2 create library base_comps -d assets2/components && popd
#pushd assets2 && ocpidev2 create library comms_comps -d assets2/components && popd
#pushd assets2 && ocpidev2 create library dsp_comps -d assets2/components && popd
#pushd assets2 && ocpidev2 create library util_comps -d assets2/components && popd
#pushd assets2 && ocpidev2 create library cards -d assets2/hdl && popd
#pushd assets2 && ocpidev2 create library devices -d assets2/hdl && popd
#pushd assets2 && ocpidev2 create library adapters -d assets2/hdl && popd
#pushd assets2 && ocpidev2 create hdl card fmcomms_2_3_hpc -d assets2/hdl/cards/specs && popd
#ocpidev2 show application FSK
#ocpidev2 show application FSK -v
#ocpidev2 show application FSK --verbose
#ocpidev2 show application FSK -d assets
#ocpidev2 show applications
#ocpidev2 show applications -v
#ocpidev2 show applications --verbose
#ocpidev2 show applications -d assets
#ocpidev2 show -d assets applications
#ocpidev2 -d assets show applications
#ocpidev2 -d assets show -d core applications -d platform -v
#ocpidev2 -d assets show -d core applications -d platform -v -l 8
#ocpidev2 -d assets show -d core applications -d platform -v --log-level 8
#ocpidev2 -d assets show -d core applications -d platform -v -l 10
#ocpidev2 show component drc
#ocpidev2 show component drc -v
#ocpidev2 show component drc --verbose
#ocpidev2 show component drc assets
#ocpidev2 show component platform
#ocpidev2 show component Consumer
#ocpidev2 show components
#ocpidev2 show components -v
#ocpidev2 show components --verbose
#ocpidev2 show components -d assets
#ocpidev2 show -d assets components
#ocpidev2 -d assets show components
#ocpidev2 -d assets show -d core components -d platform -v
#ocpidev2 -d assets show -d core components -d platform -v -l 8
#ocpidev2 -d assets show -d core components -d platform -v --log-level 8
#ocpidev2 -d assets show -d core components -d platform -v -l 10
#ocpidev2 show hdl assembly fsk_modem
#ocpidev2 show hdl assembly fsk_modem -v
#ocpidev2 show hdl assembly fsk_modem --verbose
#ocpidev2 show hdl assembly fsk_modem -d assets
#ocpidev2 show hdl assemblies 
#ocpidev2 show hdl assemblies -v
#ocpidev2 show hdl assemblies --verbose
#ocpidev2 show hdl assemblies -d assets
#ocpidev2 show -d assets hdl assemblies
#ocpidev2 -d assets show hdl assemblies
#ocpidev2 -d assets show -d core hdl assemblies -d platform -v
#ocpidev2 -d assets show -d core hdl assemblies -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl assemblies -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl assemblies -d platform -v -l 10
#ocpidev2 show hdl card fmcomms_2_3_lpc
#ocpidev2 show hdl card fmcomms_2_3_lpc -v
#ocpidev2 show hdl card fmcomms_2_3_lpc --verbose
#ocpidev2 show hdl card fmcomms_2_3_lpc -d assets
#ocpidev2 show hdl cards 
#ocpidev2 show hdl cards -v
#ocpidev2 show hdl cards --verbose
#ocpidev2 show hdl cards -d assets
#ocpidev2 show -d assets hdl cards
#ocpidev2 -d assets show hdl cards
#ocpidev2 -d assets show -d core hdl cards -d platform -v
#ocpidev2 -d assets show -d core hdl cards -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl cards -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl cards -d platform -v -l 10
#ocpidev2 show hdl device dsp_prims
#ocpidev2 show hdl device dsp_prims -v
#ocpidev2 show hdl device dsp_prims --verbose
#ocpidev2 show hdl device dsp_prims -d assets
#ocpidev2 show hdl devices 
#ocpidev2 show hdl devices -v
#ocpidev2 show hdl devices --verbose
#ocpidev2 show hdl devices -d assets
#ocpidev2 show -d assets hdl devices
#ocpidev2 -d assets show hdl devices
#ocpidev2 -d assets show -d core hdl devices -d platform -v
#ocpidev2 -d assets show -d core hdl devices -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl devices -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl devices -d platform -v -l 10
#ocpidev2 show hdl library dsp_prims
#ocpidev2 show hdl library dsp_prims -v
#ocpidev2 show hdl library dsp_prims --verbose
#ocpidev2 show hdl library dsp_prims -d assets
#ocpidev2 show hdl libraries 
#ocpidev2 show hdl libraries -v
#ocpidev2 show hdl libraries --verbose
#ocpidev2 show hdl libraries -d assets
#ocpidev2 show -d assets hdl libraries
#ocpidev2 -d assets show hdl libraries
#ocpidev2 -d assets show -d core hdl libraries -d platform -v
#ocpidev2 -d assets show -d core hdl libraries -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl libraries -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl libraries -d platform -v -l 10
#ocpidev2 show hdl platform zed 
#ocpidev2 show hdl platform zed -v
#ocpidev2 show hdl platform zed --verbose
#ocpidev2 show hdl platform zed -d assets
#ocpidev2 show hdl platforms 
#ocpidev2 show hdl platforms -v
#ocpidev2 show hdl platforms --verbose
#ocpidev2 show hdl platforms -d assets
#ocpidev2 show -d assets hdl platforms
#ocpidev2 -d assets show hdl platforms
#ocpidev2 -d assets show -d core hdl platforms -d platform -v
#ocpidev2 -d assets show -d core hdl platforms -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl platforms -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl platforms -d platform -v -l 10
#ocpidev2 show hdl primitive zynq
#ocpidev2 show hdl primitive zynq -v
#ocpidev2 show hdl primitive zynq --verbose
#ocpidev2 show hdl primitive zynq -d assets
#ocpidev2 show hdl primitives 
#ocpidev2 show hdl primitives -v
#ocpidev2 show hdl primitives --verbose
#ocpidev2 show hdl primitives -d assets
#ocpidev2 show -d assets hdl primitives
#ocpidev2 -d assets show hdl primitives
#ocpidev2 -d assets show -d core hdl primitives -d platform -v
#ocpidev2 -d assets show -d core hdl primitives -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl primitives -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl primitives -d platform -v -l 10
#ocpidev2 show hdl primitive core zed 
#ocpidev2 show hdl primitive core zed -v
#ocpidev2 show hdl primitive core zed --verbose
#ocpidev2 show hdl primitive core zed -d assets
#ocpidev2 show hdl primitive cores 
#ocpidev2 show hdl primitive cores -v
#ocpidev2 show hdl primitive cores --verbose
#ocpidev2 show hdl primitive cores -d assets
#ocpidev2 show -d assets hdl primitive cores
#ocpidev2 -d assets show hdl primitive cores
#ocpidev2 -d assets show -d core hdl primitive cores -d platform -v
#ocpidev2 -d assets show -d core hdl primitive cores -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl primitive cores -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl primitive cores -d platform -v -l 10
#ocpidev2 show hdl primitive library dsp_prims 
#ocpidev2 show hdl primitive library dsp_prims -v
#ocpidev2 show hdl primitive library dsp_prims --verbose
#ocpidev2 show hdl primitive library dsp_prims -d assets
#ocpidev2 show hdl primitive libraries 
#ocpidev2 show hdl primitive libraries -v
#ocpidev2 show hdl primitive libraries --verbose
#ocpidev2 show hdl primitive libraries -d assets
#ocpidev2 show -d assets hdl primitive libraries
#ocpidev2 -d assets show hdl primitive libraries
#ocpidev2 -d assets show -d core hdl primitive libraries -d platform -v
#ocpidev2 -d assets show -d core hdl primitive libraries -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl primitive libraries -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl primitive libraries -d platform -v -l 10
#ocpidev2 show hdl slot fmc_lpc
#ocpidev2 show hdl slot fmc_lpc -v
#ocpidev2 show hdl slot fmc_lpc --verbose
#ocpidev2 show hdl slot fmc_lpc -d assets
#ocpidev2 show hdl slots 
#ocpidev2 show hdl slots -v
#ocpidev2 show hdl slots --verbose
#ocpidev2 show hdl slots -d assets
#ocpidev2 show -d assets hdl slots
#ocpidev2 -d assets show hdl slots
#ocpidev2 -d assets show -d core hdl slots -d platform -v
#ocpidev2 -d assets show -d core hdl slots -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl slots -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl slots -d platform -v -l 10
#ocpidev2 show hdl target zynq 
#ocpidev2 show hdl target zynq -v
#ocpidev2 show hdl target zynq --verbose
#ocpidev2 show hdl target zynq -d assets
#ocpidev2 show hdl targets 
#ocpidev2 show hdl targets -v
#ocpidev2 show hdl targets --verbose
#ocpidev2 show hdl targets -d assets
#ocpidev2 show -d assets hdl targets
#ocpidev2 -d assets show hdl targets
#ocpidev2 -d assets show -d core hdl targets -d platform -v
#ocpidev2 -d assets show -d core hdl targets -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl targets -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl targets -d platform -v -l 10
#ocpidev2 show hdl worker complex_mixer.hdl
#ocpidev2 show hdl worker complex_mixer.hdl -v
#ocpidev2 show hdl worker complex_mixer.hdl --verbose
#ocpidev2 show hdl worker complex_mixer.hdl -d assets
#ocpidev2 show hdl workers 
#ocpidev2 show hdl workers -v
#ocpidev2 show hdl workers --verbose
#ocpidev2 show hdl workers -d assets
#ocpidev2 show -d assets hdl workers
#ocpidev2 -d assets show hdl workers
#ocpidev2 -d assets show -d core hdl workers -d platform -v
#ocpidev2 -d assets show -d core hdl workers -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl workers -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl workers -d platform -v -l 10
#ocpidev2 show library dsp_comps
#ocpidev2 show library dsp_comps -v
#ocpidev2 show library dsp_comps --verbose
#ocpidev2 show library dsp_comps -d assets
#ocpidev2 show hdl libraries 
#ocpidev2 show hdl libraries -v
#ocpidev2 show hdl libraries --verbose
#ocpidev2 show hdl libraries -d assets
#ocpidev2 show -d assets hdl libraries
#ocpidev2 -d assets show hdl libraries
#ocpidev2 -d assets show -d core hdl libraries -d platform -v -l 8
#ocpidev2 -d assets show -d core hdl libraries -d platform -v --log-level 8
#ocpidev2 -d assets show -d core hdl libraries -d platform -v -l 10
#ocpidev2 show platform zed
#ocpidev2 show platform zed -v
#ocpidev2 show platform zed --verbose
#ocpidev2 show platform zed -d assets
#ocpidev2 show platforms 
#ocpidev2 show platforms -v
#ocpidev2 show platforms --verbose
#ocpidev2 show platforms -d assets
#ocpidev2 show -d assets platforms
#ocpidev2 -d assets show platforms
#ocpidev2 -d assets show -d core platforms -d platform -v
#ocpidev2 -d assets show -d core platforms -d platform -v -l 8
#ocpidev2 -d assets show -d core platforms -d platform -v --log-level 8
#ocpidev2 -d assets show -d core platforms -d platform -v -l 10
#ocpidev2 show project assets
#ocpidev2 show project assets -v
#ocpidev2 show project assets --verbose
#ocpidev2 show project assets -d assets
#ocpidev2 show projects 
#ocpidev2 show projects -v
#ocpidev2 show projects --verbose
#ocpidev2 show projects -d assets
#ocpidev2 show -d assets projects
#ocpidev2 -d assets show projects
#ocpidev2 -d assets show -d core projects -d platform -v
#ocpidev2 -d assets show -d core projects -d platform -v -l 8
#ocpidev2 -d assets show -d core projects -d platform -v --log-level 8
#ocpidev2 -d assets show -d core projects -d platform -v -l 10
#ocpidev2 show protocol assets
#ocpidev2 show protocol assets -v
#ocpidev2 show protocol assets --verbose
#ocpidev2 show protocol assets -d assets
#ocpidev2 show protocols
#ocpidev2 show protocols -v
#ocpidev2 show protocols --verbose
#ocpidev2 show protocols -d assets
#ocpidev2 show -d assets protocols  
#ocpidev2 -d assets show protocols
#ocpidev2 -d assets show -d core protocols -d platform -v
#ocpidev2 -d assets show -d core protocols -d platform -v -l 8
#ocpidev2 -d assets show -d core protocols -d platform -v --log-level 8
#ocpidev2 -d assets show -d core protocols -d platform -v -l 10
#ocpidev2 show rcc platform ubuntu20_04
#ocpidev2 show rcc platform ubuntu20_04 -v
#ocpidev2 show rcc platform ubuntu20_04 --verbose
#ocpidev2 show rcc platform ubuntu20_04 -d assets
#ocpidev2 show rcc platforms 
#ocpidev2 show rcc platforms -v
#ocpidev2 show rcc platforms --verbose
#ocpidev2 show rcc platforms -d assets
#ocpidev2 show -d assets rcc platforms
#ocpidev2 -d assets show rcc platforms
#ocpidev2 -d assets show -d core rcc platforms -d platform -v
#ocpidev2 -d assets show -d core rcc platforms -d platform -v -l 8
#ocpidev2 -d assets show -d core rcc platforms -d platform -v --log-level 8
#ocpidev2 -d assets show -d core rcc platforms -d platform -v -l 10
#ocpidev2 show registry
#ocpidev2 show registry -v
#ocpidev2 show registry --verbose
#ocpidev2 show target zynq 
#ocpidev2 show target zynq -v
#ocpidev2 show target zynq --verbose
#ocpidev2 show target zynq -d assets
#ocpidev2 show targets 
#ocpidev2 show targets -v
#ocpidev2 show targets --verbose
#ocpidev2 show targets -d assets
#ocpidev2 show -d assets targets
#ocpidev2 -d assets show targets
#ocpidev2 -d assets show -d core targets -d platform -v
#ocpidev2 -d assets show -d core targets -d platform -v -l 8
#ocpidev2 -d assets show -d core targets -d platform -v --log-level 8
#ocpidev2 -d assets show -d core targets -d platform -v -l 10
#ocpidev2 show test bias.test
#ocpidev2 show test bias.test -v
#ocpidev2 show test bias.test --verbose
#ocpidev2 show test bias.test -d assets
#ocpidev2 show tests 
#ocpidev2 show tests -v
#ocpidev2 show tests --verbose
#ocpidev2 show tests -d assets
#ocpidev2 show -d assets tests
#ocpidev2 -d assets show tests
#ocpidev2 -d assets show -d core tests -d platform -v
#ocpidev2 -d assets show -d core tests -d platform -v -l 8
#ocpidev2 -d assets show -d core tests -d platform -v --log-level 8
#ocpidev2 -d assets show -d core tests -d platform -v -l 10
#ocpidev2 show worker cic_dec.hdl 
#ocpidev2 show worker cic_dec.hdl -v
#ocpidev2 show worker cic_dec.hdl --verbose
#ocpidev2 show worker cic_dec.hdl -d assets
#ocpidev2 show workers 
#ocpidev2 show workers -v
#ocpidev2 show workers --verbose
#ocpidev2 show workers -d assets
#ocpidev2 show -d assets workers
#ocpidev2 -d assets show workers
#ocpidev2 -d assets show -d core workers -d platform -v
#ocpidev2 -d assets show -d core workers -d platform -v -l 8
#ocpidev2 -d assets show -d core workers -d platform -v --log-level 8
#ocpidev2 -d assets show -d core workers -d platform -v -l 10
#ocpidev2 show components --simple
#ocpidev2 show components --table
#ocpidev2 show components --json
## python3 -m pip install coverage
## coverage run $(which ocpidev2) unittest
## coverage report -m
