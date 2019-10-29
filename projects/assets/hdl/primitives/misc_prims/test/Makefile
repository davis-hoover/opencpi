.PHONY: \
    all clean \
    prims clean_prims \
    run clean_run \
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

xsim.dir/misc_prims/: xsim.dir/misc_prims/misc_prims.vdb

xsim.dir/misc_prims/misc_prims.vdb: ../misc_prims_pkg.vhd ../misc_prims_body.vhd
	./myxvhdl.sh -work misc_prims $<
	./myxvhdl.sh -work misc_prims ../misc_prims_body.vhd

xsim.dir/cdc/cdc.vdb: ../../../../../core/hdl/primitives/cdc/cdc_pkg.vhd
	./myxvhdl.sh -work cdc $<

xsim.dir/cdc/single_bit.vdb: \
	../../../../../core/hdl/primitives/cdc/single_bit.vhd
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

xsim.dir/misc_prims/counter.vdb: ../counter.vhd
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/lfsr.vdb: ../lfsr/src/lfsr.vhd
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb: ../adc_maximal_lfsr_data_src.vhd \
    xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/misc_prims/counter.vdb \
    xsim.dir/misc_prims/lfsr.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/maximal_lfsr_data_src.vdb: ../maximal_lfsr_data_src.vhd \
    xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/misc_prims/counter.vdb \
    xsim.dir/misc_prims/lfsr.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/latest_reg.vdb: ../latest_reg.vhd
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/latest_reg_signed.vdb: ../latest_reg_signed.vhd
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/time_corrector.vdb: ../time_corrector.vhd \
    xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/misc_prims/latest_reg_signed.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/time_downsampler.vdb: ../time_downsampler.vhd \
    xsim.dir/misc_prims/misc_prims.vdb
	./myxvhdl.sh -work misc_prims $<

prims: \
    xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/cdc/cdc.vdb \
    xsim.dir/cdc/single_bit.vdb \
    xsim.dir/cdc/fast_pulse_to_slow_sticky.vdb \
    xsim.dir/misc_prims/adc_samp_drop_detector.vdb \
    xsim.dir/misc_prims/counter.vdb \
    xsim.dir/misc_prims/lfsr.vdb \
    xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb \
    xsim.dir/misc_prims/latest_reg.vdb \
    xsim.dir/misc_prims/latest_reg_signed.vdb \
    xsim.dir/misc_prims/dac_underrun_detector.vdb \
    xsim.dir/misc_prims/time_corrector.vdb \
    xsim.dir/misc_prims/time_downsampler.vdb

clean_prims:
	rm -rf xsim.dir *.pb

################################################################################
# run
################################################################################

adc_samp_drop_detector/xsim.dir/sim: adc_samp_drop_detector \
    prims
	$(MAKE) -C $<

data_widener/xsim.dir/sim: data_widener \
    prims
	$(MAKE) -C $<

dac_underrun_detector/xsim.dir/sim: dac_underrun_detector \
    prims
	$(MAKE) -C $<

data_narrower/xsim.dir/sim: data_narrower \
    prims
	$(MAKE) -C $<

time_corrector/xsim.dir/sim: time_corrector \
    prims
	$(MAKE) -C $<

time_downsampler/xsim.dir/sim: time_downsampler \
    prims
	$(MAKE) -C $<

results_adc_samp_drop_detector.log: adc_samp_drop_detector \
    adc_samp_drop_detector/xsim.dir/sim
	./run_test.sh $< | tee results_$<.log

results_data_widener.log: data_widener \
    data_widener/xsim.dir/sim
	./run_test.sh $< | tee results_$<.log

results_dac_underrun_detector.log: dac_underrun_detector \
    dac_underrun_detector/xsim.dir/sim
	./run_test.sh $< | tee results_$<.log

results_data_narrower.log: data_narrower \
    data_narrower/xsim.dir/sim
	./run_test.sh $< | tee results_$<.log

results_time_corrector.log: time_corrector \
    time_corrector/xsim.dir/sim
	./run_test.sh $< | tee results_$<.log

results_time_downsampler.log: time_downsampler \
    time_downsampler/xsim.dir/sim
	./run_test.sh $< | tee results_$<.log

run: prims \
    results_adc_samp_drop_detector.log \
    results_data_widener.log \
    results_dac_underrun_detector.log \
    results_data_narrower.log \
    results_time_corrector.log \
    results_time_downsampler.log
	./run.sh

clean_adc_samp_drop_detector: adc_samp_drop_detector
	$(MAKE) -C $< clean

clean_data_widener: data_widener
	$(MAKE) -C $< clean

clean_time_corrector: time_corrector
	$(MAKE) -C $< clean

clean_time_downsampler: time_downsampler
	$(MAKE) -C $< clean

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

