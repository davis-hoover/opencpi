.PHONY: all \
        cleantxt clean \
        uut testbench

all: sim

cleantxt:
	rm -rf uut*.txt

clean: cleantxt
	rm -rf xsim.dir/ *.log *.pb *.jou *.str *.wdb .cache .Xil octave-workspace sim

../xsim.dir/misc_prims/misc_prims.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/misc_prims.vdb

../xsim.dir/util/util.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/util/util.vdb

../xsim.dir/util/counter.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/util/counter.vdb

../xsim.dir/misc_prims/data_widener.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/data_widener.vdb

../xsim.dir/misc_prims/counter.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/counter.vdb

../xsim.dir/misc_prims/lfsr.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/lfsr.vdb

../xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb

../xsim.dir/misc_prims/adc_samp_drop_detector.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/adc_samp_drop_detector.vdb

xsim.dir/work/data_src.vdb: data_src.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    ../xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb \
    ../xsim.dir/misc_prims/adc_samp_drop_detector.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib fixed_float=../xsim.dir/fixed_float $<

xsim.dir/work/file_writer.vdb: ../file_writer.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    ../xsim.dir/util/util.vdb \
    ../xsim.dir/util/counter.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib util=../xsim.dir/util --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib fixed_float=../xsim.dir/fixed_float $<

xsim.dir/work/subtest.vdb: subtest.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/work/data_src.vdb \
    ../xsim.dir/misc_prims/data_widener.vdb \
    xsim.dir/work/file_writer.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib util=../xsim.dir/util --lib fixed_float=../xsim.dir/fixed_float $<

xsim.dir/work/testbench.vdb: testbench.vhd \
    xsim.dir/work/subtest.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib util=../xsim.dir/util --lib fixed_float=../xsim.dir/fixed_float $<

sim: testbench
	xelab -debug wave --lib unisim --lib misc_prims=../xsim.dir/misc_prims testbench --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib util=../xsim.dir/util --lib fixed_float=../xsim.dir/fixed_float -s sim
	touch sim

# for convenience
uut:       ../xsim.dir/misc_prims/data_widener.vdb
testbench: xsim.dir/work/testbench.vdb
