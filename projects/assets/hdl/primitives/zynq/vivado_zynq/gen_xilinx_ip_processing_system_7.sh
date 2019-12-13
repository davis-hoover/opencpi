# In order to generate the processing_system7 top verilog file with Vivado,
# we need to run a series of TCL commands located in vivado/tcl
#
# Prerequisites: Vivado settings script must be sourced
#
# arg 1: Value to be passed to:
#        Vivado create_ip tcl command: version parameter (for
#        processing_system_7), e.g. 5.5
# arg 2: Value to be passed to:
#        Vivado create_ip tcl command: module_name parameter (for
#        processing_system_7)
# arg 3: Value to be passed to:
#        Vivado set_property tcl command:
#        -dict parameter's CONFIG.PCW_SPI0_PERIPHERAL_ENABLE name's value
ip_version=$1
ip_module_name=$2
pcw_spi0_peripheral_enable=$3
echo ip_version=$ip_version
echo ip_module_name=$ip_module_name
echo pcw_spi0_peripheral_enable=$pcw_spi0_peripheral_enable

rm -rf vivado_zynq/tmp
mkdir vivado_zynq/tmp
cd vivado_zynq/tmp
vivado -mode batch -source ../ps7.tcl -tclargs $ip_version $ip_module_name $pcw_spi0_peripheral_enable | tee ../ps7.log
cd ..
ip_dir=tmp/managed_ip_project/managed_ip_project.srcs/sources_1/ip/
rm -rf tmp
cd ..
