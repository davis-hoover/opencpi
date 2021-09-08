#!/bin/sh

date

# Program FPGA
sudo $OCPI_ROOT_DIR/runtime/hdl-support/xilinx/cfgFiles_openocd/openocd -f $OCPI_ROOT_DIR/runtime/hdl-support/xilinx/cfgFiles_openocd/fpga.cfg

#Done
date

