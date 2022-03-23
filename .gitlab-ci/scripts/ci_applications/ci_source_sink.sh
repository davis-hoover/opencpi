#!/bin/bash
[ $# -lt 2 ] && echo "Usage: $0 [--hdl-platform platform] [--rcc-platform platform] [--host platform] [-i ip] [-u user] [-p password]" && exit 1
set -e
while [ $# -gt 0 ]; do
    case "$1" in
        --hdl-platform)
            hdl_platform="$2"
            shift 2
            ;;
        --rcc-platform)
            rcc_platform="$2"
            shift 2
            ;;
        --host)
            host="$2"
            shift 2
            ;;
        -i|--ip)
            ip="$2"
            shift 2
            ;;
        -u|--user)
            user="$2"
            shift 2
            ;;
        -p|--password)
            password="$2"
            shift 2
            ;;
        *)
            echo "Unknown option '$1'"
            exit 1
            ;;
    esac
done

[[ -z $hdl_platform && -z $rcc_platform && -z $host ]] && {
    echo Error: Must provide at least one of hdl-platform, rcc-platform, or host
    exit 1
}

cd $OCPI_ROOT_DIR/projects/assets/applications/
message_sizes="8k 16k 32k"
cache_modes="0 1"
divisors="1 2 5"

for cache_mode in $cache_modes
do
    printf "Testing cache mode $cache_mode\n"
    [[ -n $ip ]] && {
        ocpiremote restart -b -m 0x400000 -e OCPI_DMA_CACHE_MODE=$cache_mode -i $ip -u $user -p $password
    }
    for message_size in $message_sizes
    do
        printf "Testing message size $message_size\n"
        for divisor in $divisors
        do
            printf "Testing divisor $divisor\n"
            if [[ -n $hdl_platform ]] ; then
                if [[ -n $rcc_platform ]] ; then
                    ./run_source_sink $hdl_platform $rcc_platform $message_size 2 2 0 $cache_mode $divisor
                    ./run_source_sink $hdl_platform $rcc_platform $message_size 2 10 0 $cache_mode $divisor
                    if $message_size != "32k" ]] ; then 
                        ./run_source_sink $rcc_platform $hdl_platform $message_size 2 2 0 $cache_mode $divisor
                        ./run_source_sink $rcc_platform $hdl_platform $message_size 10 2 0 $cache_mode $divisor
                    fi
                fi
                if [[ -n $host ]] ; then
                    ./run_source_sink $hdl_platform $host $message_size 2 2 0 $cache_mode $divisor
                    ./run_source_sink $hdl_platform $host $message_size 2 10 0 $cache_mode $divisor
                    if [[ $message_size != "32k" ]] ; then
                        ./run_source_sink $host $hdl_platform $message_size 2 2 0 $cache_mode $divisor
                        ./run_source_sink $host $hdl_platform $message_size 10 2 0 $cache_mode $divisor
                    fi
                fi
            else
                if [[ -n $rcc_platform ]] ; then
                    ./run_source_sink $rcc_platform $rcc_platform $message_size 2 2 0 $cache_mode $divisor
                    ./run_source_sink $rcc_platform $rcc_platform $message_size 10 10 0 $cache_mode $divisor
                elif [[ -n $host ]] ; then
                    ./run_source_sink $host $host $message_size 2 2 0 $cache_mode $divisor
                    ./run_source_sink $host $host $message_size 10 10 0 $cache_mode $divisor
                fi
                if [[ -n $rcc_platform && -n $host ]] ; then
                    ./run_source_sink $host $rcc_platform $message_size 2 2 0 $cache_mode $divisor
                    ./run_source_sink $host $rcc_platform $message_size 10 10 0 $cache_mode $divisor
                    ./run_source_sink $rcc_platform $host $message_size 2 2 0 $cache_mode $divisor
                    ./run_source_sink $rcc_platform $host $message_size 10 10 0 $cache_mode $divisor
                fi
            fi
        done
    done
done