pPHONY: all \
        cleantxt clean \
        uut testbench

all: sim

cleantxt:
	rm -rf uut*.txt

clean: cleantxt
	rm -rf xsim.dir/ *.log *.pb *.jou *.str *.wdb .cache .Xil octave-workspace sim

../xsim.dir/util/util.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/util/util.vdb

../xsim.dir/misc_prims/misc_prims.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/misc_prims.vdb

../xsim.dir/misc_prims/data_narrower.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/data_narrower.vdb

../xsim.dir/misc_prims/lfsr.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/lfsr.vdb

../xsim.dir/misc_prims/dac_underrun_detector.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/dac_underrun_detector.vdb

xsim.dir/work/data_src.vdb: data_src.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    ../xsim.dir/misc_prims/dac_underrun_detector.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib fixed_float=../xsim.dir/fixed_float --lib util=../xsim.dir/util $<

xsim.dir/work/file_writer.vdb: file_writer.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib fixed_float=../xsim.dir/fixed_float --lib util=../xsim.dir/util $<

xsim.dir/work/subtest.vdb: subtest.vhd \
    ../xsim.dir/util/util.vdb \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/work/data_src.vdb \
    ../xsim.dir/misc_prims/data_narrower.vdb \
    xsim.dir/work/file_writer.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib fixed_float=../xsim.dir/fixed_float --lib util=../xsim.dir/util $<

xsim.dir/work/testbench.vdb: testbench.vhd \
    xsim.dir/work/subtest.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib fixed_float=../xsim.dir/fixed_float --lib util=../xsim.dir/util $<

sim: testbench
	xelab -debug wave --lib unisim --lib misc_prims=../xsim.dir/misc_prims testbench --lib ocpi=../xsim.dir/ocpi --lib protocol=../xsim.dir/protocol --lib util=../xsim.dir/util --lib fixed_float=../xsim.dir/fixed_float -s sim
	touch sim

# for convenience
uut:       ../xsim.dir/misc_prims/data_narrower.vdb
testbench: xsim.dir/work/testbench.vdb
