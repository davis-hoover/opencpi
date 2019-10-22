.PHONY: \
    all clean \
    prims clean_prims \
    run clean_run \
    clean_adc_samp_drop_detector \
    clean_data_widener

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

xsim.dir/cdc/bit.vdb: \
	../../../../../core/hdl/primitives/cdc/bit.vhd
	./myxvhdl.sh -work cdc $<

xsim.dir/cdc/fast_pulse_to_slow_sticky.vdb: ../../../../../core/hdl/primitives/cdc/fast_pulse_to_slow_sticky.vhd \
    xsim.dir/cdc/cdc.vdb \
    xsim.dir/cdc/bit.vdb
	./myxvhdl.sh -work cdc $<

xsim.dir/misc_prims/adc_samp_drop_detector.vdb: ../adc_samp_drop_detector.vhd \
    xsim.dir/misc_prims/misc_prims.vdb
	./myxvhdl.sh -work misc_prims $<

xsim.dir/misc_prims/data_widener.vdb: ../data_widener.vhd \
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

prims: \
    xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/cdc/cdc.vdb \
    xsim.dir/cdc/bit.vdb \
    xsim.dir/cdc/fast_pulse_to_slow_sticky.vdb \
    xsim.dir/misc_prims/adc_samp_drop_detector.vdb \
    xsim.dir/misc_prims/counter.vdb \
    xsim.dir/misc_prims/lfsr.vdb \
    xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb \
    xsim.dir/misc_prims/latest_reg.vdb \
    xsim.dir/misc_prims/latest_reg_signed.vdb

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

results_adc_samp_drop_detector.log: adc_samp_drop_detector \
    adc_samp_drop_detector/xsim.dir/sim
	./run_test.sh $< | tee results_$<.log

results_data_widener.log: data_widener \
    data_widener/xsim.dir/sim
	./run_test.sh $< | tee results_$<.log

run: prims \
    results_adc_samp_drop_detector.log \
    results_data_widener.log
	./run.sh

clean_adc_samp_drop_detector:
	$(MAKE) -C adc_samp_drop_detector clean

clean_data_widener:
	$(MAKE) -C data_widener clean

clean_run: \
    clean_prims \
    clean_adc_samp_drop_detector \
    clean_data_widener
	rm -rf results*log
	rm -rf octave-workspace

