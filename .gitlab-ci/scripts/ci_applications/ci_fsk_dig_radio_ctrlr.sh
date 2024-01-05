#!/bin/bash
set -e
source $(dirname $0)/ci_args.sh $@

if [[ -z $hdl_platform || -z $host ]] ; then
    echo Error: Must provide a host and an hdl-platform
    exit 1
fi

export OCPI_LIBRARY_PATH="$OCPI_ROOT_DIR/projects"
if [[ -z $application_dir ]] ; then
    application_dir=$OCPI_ROOT_DIR/projects/assets/applications
fi
cd $application_dir/fsk_dig_radio_ctrlr
if [[ -f fsk_modem_app.xml ]]; then
    app=fsk_modem_app.xml
elif [[ -f fsk_dig_radio_ctrlr.xml ]]; then
    app=fsk_dig_radio_ctrlr.xml
else
    echo 'Error: Unable to find application'
    exit 1
fi
if [[ -n $ip ]] ; then
    ocpiremote restart -b -i $ip -u $user -p $password
fi

ocpirun -d -v -t 30 -P drc=$host -P file_write=$host -P file_read=$host $app --only-platforms $hdl_platform
