.PHONY: \
    all clean \
    prims clean_prims \
    run clean_run \
    result clean_results \
    clean_adc_samp_drop_detector \
    clean_data_widener \
    clean_dac_underrun_detector \
    clean_data_narrower \
    clean_time_corrector \
    clean_time_downsampler

all: run

clean: clean_run

################################################################################
# prims
################################################################################

xsim.dir/fixed_float/fixed_float_types.vdb: \
    ../../../../../core/hdl/primitives/fixed_float/fixed_float_types_pkg.vhd
	./myxvhdl.sh -work fixed_float $<

xsim.dir/fixed_float/fixed_pkg.vdb: \
    ../../../../../core/hdl/primitives/fixed_float/fixed_pkg.vhd \
    ../../../../../core/hdl/primitives/fixed_float/fixed_body.vhd
	./myxvhdl.sh -work fixed_float ../../../../../core/hdl/primitives/fixed_float/fixed_pkg.vhd ../../../../../core/hdl/primitives/fixed_float/fixed_body.vhd

xsim.dir/fixed_float/float_pkg.vdb: \
    ../../../../../core/hdl/primitives/fixed_float/float_pkg.vhd \
    ../../../../../core/hdl/primitives/fixed_float/float_body.vhd \
    xsim.dir/fixed_float/fixed_float_types.vdb \
    xsim.dir/fixed_float/fixed_pkg.vdb
	./myxvhdl.sh -work fixed_float ../../../../../core/hdl/primitives/fixed_float/float_pkg.vhd ../../../../../core/hdl/primitives/fixed_float/float_body.vhd

xsim.dir/ocpi/types.vdb: \
    xsim.dir/fixed_float/float_pkg.vdb \
    ../../../../../core/hdl/primitives/ocpi/types_pkg.vhd \
    ../../../../../core/hdl/primitives/ocpi/types_body.vhd
	./myxvhdl.sh -work ocpi ../../../../../core/hdl/primitives/ocpi/types_pkg.vhd ../../../../../core/hdl/primitives/ocpi/types_body.vhd

xsim.dir/ocpi/util.vdb: ../../../../../core/hdl/primitives/ocpi/util_pkg.vhd \
    ../../../../../core/hdl/primitives/ocpi/util_body.vhd \
    xsim.dir/ocpi/types.vdb
	./myxvhdl.sh -work ocpi ../../../../../core/hdl/primitives/ocpi/util_pkg.vhd ../../../../../core/hdl/primitives/ocpi/util_body.vhd

xsim.dir/ocpi/ocp.vdb: ../../../../../core/hdl/primitives/ocpi/ocp_pkg.vhd
	./myxvhdl.sh -work ocpi $<

xsim.dir/ocpi/wci.vdb: ../../../../../core/hdl/primitives/ocpi/wci_pkg.vhd \
    ../../../../../core/hdl/primitives/ocpi/wci_body.vhd \
    xsim.dir/ocpi/types.vdb \
    xsim.dir/ocpi/util.vdb \
    xsim.dir/ocpi/ocp.vdb
	./myxvhdl.sh -work ocpi ../../../../../core/hdl/primitives/ocpi/wci_pkg.vhd ../../../../../core/hdl/primitives/ocpi/wci_body.vhd

xsim.dir/util/types.vdb: ../../../../../core/hdl/primitives/util/types_pkg.vhd
	./myxvhdl.sh -work util $<

xsim.dir/util/util.vdb: ../../../../../core/hdl/primitives/util/util_pkg.vhd \
    xsim.dir/ocpi/types.vdb \
    xsim.dir/util/types.vdb \
    xsim.dir/ocpi/util.vdb \
    xsim.dir/ocpi/wci.vdb
	./myxvhdl.sh -work util $<

xsim.dir/util/counter.vdb : ../../../../../core/hdl/primitives/util/counter.vhd \
    xsim.dir/util/util.vdb
	./myxvhdl.sh -work util $<

xsim.dir/protocol/complex_short_with_metadata.vdb: ../../../../../core/hdl/primitives/protocol/complex_short_with_metadata/pkg.vhd \
    ../../../../../core/hdl/primitives/protocol/complex_short_with_metadata/body.vhd \
    xsim.dir/ocpi/types.vdb
	./myxvhdl.sh -work protocol ../../../../../core/hdl/primitives/protocol/complex_short_with_metadata/pkg.vhd ../../../../../core/hdl/primitives/protocol/complex_short_with_metadata/body.vhd

xsim.dir/misc_prims/misc_prims.vdb: ../misc_prims_pkg.vhd \
    xsim.dir/protocol/complex_short_with_metadata.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/cdc/cdc.vdb: ../../../../../core/hdl/primitives/cdc/cdc_pkg.vhd
	./myxvhdl.sh -work cdc $<

xsim.dir/cdc/single_bit.vdb: ../../../../../core/hdl/primitives/cdc/single_bit.vhd
	./myxvhdl.sh -work cdc $<

xsim.dir/cdc/fast_pulse_to_slow_sticky.vdb: ../../../../../core/hdl/primitives/cdc/fast_pulse_to_slow_sticky.vhd \
    xsim.dir/cdc/cdc.vdb \
    xsim.dir/cdc/single_bit.vdb
	./myxvhdl.sh -work cdc $<

xsim.dir/misc_prims/adc_samp_drop_detector.vdb: ../adc_samp_drop_detector.vhd \
    xsim.dir/misc_prims/misc_prims.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/data_widener.vdb: ../data_widener.vhd \
    xsim.dir/misc_prims/misc_prims.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/data_narrower.vdb: ../data_narrower.vhd \
    xsim.dir/misc_prims/misc_prims.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/dac_underrun_detector.vdb: ../dac_underrun_detector.vhd \
    xsim.dir/misc_prims/misc_prims.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/lfsr.vdb: ../lfsr/src/lfsr.vhd
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb: ../adc_maximal_lfsr_data_src.vhd \
    xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/util/util.vdb \
    xsim.dir/util/counter.vdb \
    xsim.dir/misc_prims/lfsr.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/maximal_lfsr_data_src.vdb: ../maximal_lfsr_data_src.vhd \
    xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/util/counter.vdb \
    xsim.dir/misc_prims/lfsr.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/time_corrector.vdb: ../time_corrector.vhd \
    xsim.dir/misc_prims/misc_prims.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/time_downsampler.vdb: ../time_downsampler.vhd \
    xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/util/counter.vdb
	./myxvhdl.sh -work misc_prims $<

prims: prims_cdc prims_misc_prims

prims_cdc:
	$(MAKE) xsim.dir/cdc/cdc.vdb
	$(MAKE) xsim.dir/cdc/single_bit.vdb
	$(MAKE) xsim.dir/cdc/fast_pulse_to_slow_sticky.vdb

prims_misc_prims:
	$(MAKE) xsim.dir/misc_prims/misc_prims.vdb
	$(MAKE) xsim.dir/misc_prims/adc_samp_drop_detector.vdb
	$(MAKE) xsim.dir/misc_prims/lfsr.vdb
	$(MAKE) xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb
	$(MAKE) xsim.dir/misc_prims/dac_underrun_detector.vdb
	$(MAKE) xsim.dir/misc_prims/time_corrector.vdb
	$(MAKE) xsim.dir/misc_prims/time_downsampler.vdb
	$(MAKE) xsim.dir/misc_prims/data_narrower.vdb
	$(MAKE) xsim.dir/misc_prims/dac_underrun_detector.vdb

clean_prims:
	rm -rf xsim.dir *.pb

################################################################################
# run
################################################################################

results_adc_samp_drop_detector.log:
	$(MAKE) prims
	$(MAKE) -C adc_samp_drop_detector sim
	./run_test.sh adc_samp_drop_detector | tee results_adc_samp_drop_detector.log

results_data_widener.log:
	$(MAKE) prims
	$(MAKE) -C data_widener sim
	./run_test.sh data_widener | tee $@

results_dac_underrun_detector.log:
	$(MAKE) prims
	$(MAKE) -C dac_underrun_detector sim
	./run_test.sh dac_underrun_detector | tee $@

results_data_narrower.log:
	$(MAKE) prims
	$(MAKE) -C data_narrower sim
	./run_test.sh data_narrower | tee $@

results_time_corrector.log:
	$(MAKE) prims
	$(MAKE) -C time_corrector sim
	./run_test.sh time_corrector | tee $@

results_time_downsampler.log:
	$(MAKE) prims
	$(MAKE) -C time_downsampler sim
	./run_test.sh time_downsampler | tee $@

run:
	$(MAKE) prims
	$(MAKE) results

results: \
    results_adc_samp_drop_detector.log \
    results_data_widener.log \
    results_dac_underrun_detector.log \
    results_data_narrower.log \
    results_time_corrector.log \
    results_time_downsampler.log
	./run.sh

clean_adc_samp_drop_detector:
	$(MAKE) -C adc_samp_drop_detector clean

clean_data_widener:
	$(MAKE) -C data_widener clean

clean_time_corrector:
	$(MAKE) -C time_corrector clean

clean_time_downsampler:
	$(MAKE) -C time_downsampler clean

clean_dac_underrun_detector:
	$(MAKE) -C dac_underrun_detector clean

clean_data_narrower:
	$(MAKE) -C data_narrower clean

clean_run: \
    clean_prims \
    clean_adc_samp_drop_detector \
    clean_data_widener \
    clean_dac_underrun_detector \
    clean_data_narrower \
    clean_time_corrector \
    clean_time_downsampler
	rm -rf results*log
	rm -rf octave-workspace

clean_results:
	rm -rf results*

