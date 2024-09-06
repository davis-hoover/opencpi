#!/bin/bash
find /home/user/opencpi/projects -type d -wholename */gen/inputs -exec rm -rf -- {} +
find /home/user/opencpi/projects -type d \( -name ".Xil" -o -name *.dir \) -exec rm -rf -- {} +
find /home/user/opencpi/projects -type f \( -name *.log -o -name *.out -o -name *.jou -o -name *.pb -o -name *.dcp -o -name *.rpx -o -name *.bit \) -exec rm -- {} +