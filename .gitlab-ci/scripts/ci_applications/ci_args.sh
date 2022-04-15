#!/bin/bash
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
