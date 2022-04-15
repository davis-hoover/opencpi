#!/bin/bash
set -e
source $(dirname $0)/ci_args.sh $@

if [[ -z $hdl_platform && -z $rcc_platform || -z $host ]] ; then
    echo Error: Must provide a host and an hdl-platform or rcc-platform
    exit 1
fi

if [[ -n $hdl_platform ]] ; then
    model=hdl
    platform=$hdl_platform
else
    model=rcc
    platform=$rcc_platform
fi

export OCPI_LIBRARY_PATH="$OCPI_ROOT_DIR/projects/assets/artifacts:\
$OCPI_ROOT_DIR/projects/platform/artifacts:\
$OCPI_ROOT_DIR/projects/core/artifacts"

cd $OCPI_ROOT_DIR/projects/assets/applications
if [[ -n $ip ]] ; then
    ocpiremote restart -b -i $ip -u $user -p $password
fi
ocpirun -v -d -m bias=$model -P file_read=$host -P file_write=$host -P bias=$platform testbias.xml -t 10