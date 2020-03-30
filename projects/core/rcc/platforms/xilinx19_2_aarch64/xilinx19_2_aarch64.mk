OcpiXilinxLinuxRepoTag:=xilinx-v2019.2.01

include $(OCPI_CDK_DIR)/include/xilinx/xilinx-rcc-platform-definition.mk
OcpiCXXFlags+=-fno-builtin-memset -fno-builtin-memcpy
OcpiCFlags+=-fno-builtin-memset
OcpiPlatformOs:=linux
OcpiPlatformOsVersion:=19_2
OcpiPlatformArch:=aarch64
