.PHONY: all \
        cleantxt clean \
        uut testbench

all: xsim.dir/sim/

cleantxt:
	rm -rf uut*.txt

clean: cleantxt
	rm -rf xsim.dir/ *.log *.pb *.jou *.str *.wdb .cache .Xil octave-workspace

../xsim.dir/misc_prims/misc_prims.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/misc_prims.vdb

../xsim.dir/cdc/cdc.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/cdc/cdc.vdb

../xsim.dir/cdc/bit.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/cdc/bit.vdb

../xsim.dir/cdc/fast_pulse_to_slow_sticky.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/cdc/fast_pulse_to_slow_sticky.vdb

../xsim.dir/misc_prims/adc_samp_drop_generator.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/adc_samp_drop_generator.vdb

../xsim.dir/misc_prims/adc_samp_drop_generator_scdcd.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/adc_samp_drop_generator_scdcd.vdb

../xsim.dir/misc_prims/counter.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/counter.vdb

../xsim.dir/misc_prims/lfsr.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/lfsr.vdb

../xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb

../xsim.dir/misc_prims/latest_reg.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/latest_reg.vdb

xsim.dir/work/data_src.vdb: data_src.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    ../xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

xsim.dir/work/file_writer.vdb: file_writer.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    ../xsim.dir/misc_prims/latest_reg.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

xsim.dir/work/subtest.vdb: subtest.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/work/data_src.vdb \
    ../xsim.dir/misc_prims/adc_samp_drop_generator_scdcd.vdb \
    xsim.dir/work/file_writer.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib cdc=../xsim.dir/cdc $<

xsim.dir/work/testbench.vdb: testbench.vhd \
    xsim.dir/work/subtest.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib cdc=../xsim.dir/cdc $<

xsim.dir/sim/: xsim.dir/work/testbench.vdb
	xelab -debug wave --lib unisim --lib misc_prims=../xsim.dir/misc_prims --lib cdc=../xsim.dir/cdc testbench -s sim

# for convenience
uut:       xsim.dir/misc_prims/adc_samp_drop_generator_scdcd.vdb
testbench: xsim.dir/work/testbench.vdb
