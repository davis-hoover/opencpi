#include $(OCPI_CDK_DIR)/include/xilinx/xilinx-rcc-platform-definition.mk

mkfile_dir:=$(dir $(realpath $(lastword $(MAKEFILE_LIST))))
yocto_sdk_dir:=$(mkfile_dir)/gen/sdk

tooldir:=$(yocto_sdk_dir)/../opencpi-bin
OcpiCrossCompile=$(tooldir)/aarch64-xilinx-linux-

OcpiKernelCrossCompile=aarch64-xilinx-linux-
OcpiKernelDir=$(yocto_sdk_dir)/sysroots/cortexa72-cortexa53-xilinx-linux/usr/src/kernel
OcpiKernelEnv=$(yocto_sdk_dir)/environment-setup-cortexa72-cortexa53-xilinx-linux

OcpiPlatformOs:=linux
OcpiPlatformOsVersion:=21_1
OcpiPlatformArch:=aarch64
