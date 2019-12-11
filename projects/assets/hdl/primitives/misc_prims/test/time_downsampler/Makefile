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

../xsim.dir/misc_prims/time_downsampler.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/time_downsampler.vdb

../xsim.dir/misc_prims/counter.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/counter.vdb

../xsim.dir/misc_prims/lfsr.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/lfsr.vdb

../xsim.dir/misc_prims/maximal_lfsr_data_src.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/maximal_lfsr_data_src.vdb

../xsim.dir/misc_prims/latest_reg.vdb: ../Makefile
	$(MAKE) -C ../ xsim.dir/misc_prims/latest_reg.vdb

xsim.dir/work/data_src.vdb: data_src.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    ../xsim.dir/misc_prims/maximal_lfsr_data_src.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

xsim.dir/work/file_writer.vdb: file_writer.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    ../xsim.dir/misc_prims/counter.vdb \
    ../xsim.dir/misc_prims/latest_reg.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

xsim.dir/work/subtest.vdb: subtest.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/work/data_src.vdb \
    ../xsim.dir/misc_prims/time_downsampler.vdb \
    xsim.dir/work/file_writer.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

xsim.dir/work/testbench.vdb: testbench.vhd \
    xsim.dir/work/subtest.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

sim: testbench
	xelab -debug wave --lib unisim --lib misc_prims=../xsim.dir/misc_prims testbench -s sim
	touch sim

# for convenience
uut:       xsim.dir/misc_prims/time_downsampler.vdb
testbench: xsim.dir/work/testbench.vdb
