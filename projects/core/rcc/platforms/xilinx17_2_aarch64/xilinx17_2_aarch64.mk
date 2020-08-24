

include $(OCPI_CDK_DIR)/include/xilinx/xilinx-rcc-platform-definition.mk
OcpiCXXFlags+=-fno-builtin-memset -fno-builtin-memcpy
OcpiCFlags+=-fno-builtin-memset -fno-builtin-memcpy
OcpiPlatformOs:=linux
OcpiPlatformOsVersion:=17_2
OcpiPlatformArch:=aarch64
