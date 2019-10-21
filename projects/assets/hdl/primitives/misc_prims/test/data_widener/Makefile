.PHONY: all \
        cleantxt clean \
        uut testbench \
        FORCE

all: xsim.dir/sim/

FORCE:

cleantxt:
	rm -rf uut*.txt

clean: cleantxt
	rm -rf xsim.dir/ *.log *.pb *.jou *.str *.wdb .cache .Xil octave-workspace

../xsim.dir/misc_prims/misc_prims.vdb: ../Makefile \
  FORCE
	$(MAKE) -C ../ xsim.dir/misc_prims/misc_prims.vdb

../xsim.dir/misc_prims/data_widener.vdb: ../Makefile \
  FORCE
	$(MAKE) -C ../ xsim.dir/misc_prims/data_widener.vdb

../xsim.dir/misc_prims/counter.vdb: ../Makefile \
  FORCE
	$(MAKE) -C ../ xsim.dir/misc_prims/counter.vdb

../xsim.dir/misc_prims/lfsr.vdb: ../Makefile \
  FORCE
	$(MAKE) -C ../ xsim.dir/misc_prims/lfsr.vdb

../xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb: ../Makefile \
  FORCE
	$(MAKE) -C ../ xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb

../xsim.dir/misc_prims/latest_reg.vdb: ../Makefile \
  FORCE
	$(MAKE) -C ../ xsim.dir/misc_prims/latest_reg.vdb

../xsim.dir/misc_prims/adc_samp_drop_detector.vdb: ../Makefile \
  FORCE
	$(MAKE) -C ../ xsim.dir/misc_prims/adc_samp_drop_detector.vdb

xsim.dir/work/data_src.vdb: data_src.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    ../xsim.dir/misc_prims/adc_maximal_lfsr_data_src.vdb \
    ../xsim.dir/misc_prims/adc_samp_drop_detector.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

xsim.dir/work/file_writer.vdb: file_writer.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    ../xsim.dir/misc_prims/latest_reg.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

xsim.dir/work/subtest.vdb: subtest.vhd \
    ../xsim.dir/misc_prims/misc_prims.vdb \
    xsim.dir/work/data_src.vdb \
    ../xsim.dir/misc_prims/data_widener.vdb \
    xsim.dir/work/file_writer.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

xsim.dir/work/testbench.vdb: testbench.vhd \
    xsim.dir/work/subtest.vdb
	./myxvhdl.sh --lib misc_prims=../xsim.dir/misc_prims $<

xsim.dir/sim/: xsim.dir/work/testbench.vdb
	xelab -debug wave --lib unisim --lib misc_prims=../xsim.dir/misc_prims testbench -s sim

# for convenience
uut:       xsim.dir/misc_prims/data_widener.vdb
testbench: xsim.dir/work/testbench.vdb
