OcpiXilinxLinuxRepoTag:=xilinx-v2019.2.01

include $(OCPI_CDK_DIR)/include/xilinx/xilinx-rcc-platform-definition.mk
OcpiPlatformOs:=linux
OcpiPlatformOsVersion:=19_2
OcpiPlatformArch:=aarch32
OcpiRequiredCXXFlags:=$(OcpiRequiredCXXFlags) -Wno-psabi
