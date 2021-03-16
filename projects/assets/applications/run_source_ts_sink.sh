#!/bin/bash

if [ -z "$1" ]; then
    echo "Usage is:  $0 <from-pf> <to-pf> <message-size> <from-buffer-count> <to_buffer_count> <suppress> <divisor>"
    exit 1
fi

div=$7
[ -z "$div" ] && div=1
OCPI_LIBRARY_PATH=../artifacts \
ocpirun -v -d -Ptest_source=$1 -Ptest_sink=$2 -ptest_source=valuestosend=25000000 -Ztimestamper_scdcd=out=$3 -Btimestamper_scdcd=out=$4 -Btest_sink=in=$5 -ptest_source=clockdivisor=$div -ptest_sink=suppressreads=$6 -H  -ptimestamper_scdcd=bypass=false -ptimestamper_scdcd=min_num_samples_per_timestamp=4096  test_source_ts_sink
