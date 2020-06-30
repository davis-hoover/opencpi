# This Makefile is for the primitive library: cyclone5

# Set this variable to any other primitive libraries that this library depends on.
# If they are remote from this project, use slashes in the name (relative or absolute)
# If they are in this project, they must be compiled first, and this requires that the
# PrimitiveLibraries variable be set in the hdl/primitives/Makefile such that the
# libraries are in dependency order.
#Libraries=



# Set this variable to the list of source files in dependency order
# If it is not set, all .vhd and .v files will be compiled in wildcard/random order,
# except that any *_pkg.vhd files will be compiled first
#SourceFiles=


# Remember two rules for OpenCPI primitive libraries, in order to be usable with all tools:
# 1. Any entity (VHDL) or module (verilog) must have a VHDL component declaration in cyclone5_pkg.vhd
# 2. Entities or modules to be used from outside the library must have the file name
#    be the same as the entity/module name, and one entity/module per file.
HdlLibraries=fixed_float ocpi axi sdp platform
OnlyTargets=cyclone5

SourceFiles=cyclone5_pkg.vhd $(wildcard src_files/*) cyclone5_hps.vhd

include $(OCPI_CDK_DIR)/include/hdl/hdl-library.mk
