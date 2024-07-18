# recommmended use: cd projects/osps; OCPI_LOG_LEVEL=3 ../../tools/ocpidev2/test_project_creation.sh
set -e
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
ocpidev2 create hdl adapter wsi_from_zero_adapter.hdl -d core/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_from_zero_clock_adapter.hdl -d core/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_to_zero_adapter.hdl -d core/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_to_zero_clock_adapter.hdl -d core/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_width_adapter.hdl -d core/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl adapter wsi_width_clock_adapter.hdl -d core/hdl/adapters --language vhdl --version 2
ocpidev2 create hdl device ocdp.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp2cp.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_node.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_pipeline.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_receive.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_send.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sdp_term.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device sma.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device time_server.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device unoc2cp.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl device unoc_term.hdl -d core/hdl/devices --language vhdl --version 2
ocpidev2 create hdl platform isim -d core/hdl/platforms --language vhdl --spec platform
ocpidev2 create hdl platform modelsim -d core/hdl/platforms --language vhdl --spec platform --libraries sdp
ocpidev2 create hdl platform riviera -d core/hdl/platforms --language vhdl --spec platform --libraries sdp
ocpidev2 create hdl platform x4sim -d core/hdl/platforms --language vhdl --spec platform --libraries 'sdp util' --version 2
ocpidev2 create hdl platform xsim -d core/hdl/platforms --language vhdl --spec platform --libraries sdp --configurations 'base cfg_pps_sim_test'
ocpidev2 create project assets --package-id ocpi.assets --depends ocpi.platform --component-library util_comps --component-library base_comps --component-library misc_comps --component-library dsp_comps --component-library comms_comps --component-library devices
ocpidev2 create library base_comps -d assets/components
ocpidev2 create library comms_comps -d assets/components
ocpidev2 create library dsp_comps -d assets/components
ocpidev2 create library util_comps -d assets/components
ocpidev2 create library cards -d assets/hdl
ocpidev2 create library devices -d assets/hdl
ocpidev2 create library adapters -d assets/hdl
