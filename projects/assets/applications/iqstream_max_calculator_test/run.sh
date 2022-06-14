#!/bin/bash

# Run in various modes

# Servers
set -e
SERVER1="192.168.2.1:12345:-p analog -b"
INTERFACE1=enp0s29f7u2
SERVER2=
INTERFACE2=
SIMULATOR1=xsim
SIMULATOR2=modelsim

# First run using hardware on server 1
unset OCPI_SERVER_ADDRESSES
unset OCPI_SOCKET_INTERFACE


if [ -n "$SIMULATOR1" ]; then
  export OCPI_HDL_FORCE_SIM_DMA_PULL=0
  export OCPI_ENABLE_HDL_SIMULATOR_DISCOVERY=1
  export OCPI_HDL_SIMULATOR=$SIMULATOR1
  ocpidev -v run
  export OCPI_HDL_FORCE_SIM_DMA_PULL=1
  ocpidev -v run
fi
if [ -n "$SIMULATOR2" ]; then
  export OCPI_HDL_FORCE_SIM_DMA_PULL=0
  export OCPI_ENABLE_HDL_SIMULATOR_DISCOVERY=1
  export OCPI_HDL_SIMULATOR=$SIMULATOR2
  ocpidev -v run
  export OCPI_HDL_FORCE_SIM_DMA_PULL=1
  ocpidev -v run
fi
export OCPI_HDL_SIMULATOR_DISCOVERY=0
if [ -n "$SERVER1" ]; then
  export OCPI_SERVER_ADDRESSES=$SERVER1
  export OCPI_SOCKET_INTERFACE=$INTERFACE1
  ocpidev -v run
fi
if [ -n "$SERVER2" ]; then
  export OCPI_SERVER_ADDRESSES=$SERVER2
  export OCPI_SOCKET_INTERFACE=$INTERFACE2
  ocpidev -v run
fi
