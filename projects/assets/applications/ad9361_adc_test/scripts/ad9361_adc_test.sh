#!/bin/bash
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

if [ -z "$OCPI_TOOL_DIR" ]; then
  echo OCPI_TOOL_DIR env variable must be specified before running BIST_PRBS_rates.sh
  exit 1
fi
if [ ! -d target-$OCPI_TOOL_DIR ]; then
  echo "missing binary directory: (target-$OCPI_TOOL_DIR does not exist)"
  exit 1
fi

# handle case where zedboard doesn't have a bitstream loaded
FOUND_PLATFORMS=$(./target-$OCPI_TOOL_DIR/get_comma_separated_ocpi_platforms)
AT_LEAST_ONE_ML605_AVAILABLE=$(./target-$OCPI_TOOL_DIR/get_at_least_one_platform_is_available ml605)
if [ "$FOUND_PLATFORMS" == "" ]; then
  ocpihdl -d PL:0 load ../../hdl/assemblies/ad9361_1r1t_test_adc_asm/container-ad9361_1r1t_test_adc_asm_zed_cfg_1rx_0tx_fmcomms_2_3_lpc_lvds_cnt_1rx_0tx_thruasm_fmcomms_2_3_lpc_LVDS_zed/target-zynq/ad9361_1r1t_test_adc_asm_zed_cfg_1rx_0tx_fmcomms_2_3_lpc_lvds_cnt_1rx_0tx_thruasm_fmcomms_2_3_lpc_LVDS_zed.bitz
fi
FOUND_PLATFORMS=$(./target-$OCPI_TOOL_DIR/get_comma_separated_ocpi_platforms)
AT_LEAST_ONE_ML605_AVAILABLE=$(./target-$OCPI_TOOL_DIR/get_at_least_one_platform_is_available ml605)

if [ "$FOUND_PLATFORMS" == "" ]; then
  echo ERROR: no platforms found! check ocpirun -C
  echo "TEST FAILED"
  exit 1
elif [ "$FOUND_PLATFORMS" == "zed" ]; then
  # force test zed bitstream (and NOT zed_ise bitstream)
  ocpihdl -d PL:0 load ../../hdl/assemblies/ad9361_1r1t_test_adc_asm/container-ad9361_1r1t_test_adc_asm_zed_cfg_1rx_0tx_fmcomms_2_3_lpc_lvds_cnt_1rx_0tx_thruasm_fmcomms_2_3_lpc_LVDS_zed/target-zynq/ad9361_1r1t_test_adc_asm_zed_cfg_1rx_0tx_fmcomms_2_3_lpc_lvds_cnt_1rx_0tx_thruasm_fmcomms_2_3_lpc_LVDS_zed.bitz
  if [ "$?" !=  "0" ]; then
    echo "TEST FAILED"
    echo "exit 1"
    exit 1
  fi
elif [ "$AT_LEAST_ONE_ML605_AVAILABLE" == "true" ]; then
  if [ "$run" == "2" ]; then
    continue
  fi
else
  printf "platform found which is not supported: "
  echo $FOUND_PLATFORMS
  echo "TEST FAILED"
  exit 1
fi

touch toberemoved.log
rm *log > /dev/null 2>&1

if [ -d odata ]; then
  rm -rf odata
  XX=$?
  if [ "$XX" !=  "0" ]; then
    echo "TEST FAILED: could not remove odata"
    exit 1
  fi
fi

mkdir odata

APP_XML=ad9361_adc_test_1r1t_lvds_app.xml
if [ ! -z "$1" ]; then
  APP_XML=$1
fi

if [ ! -f $APP_XML ]; then
  echo "app xml not found: $APP_XML"
  echo "(pwd is: $PWD)"
  exit 1
fi

echo "Running PRBS Built-In-Self-Test across range of sample rates for 1R1T LVDS mode"
#'grep -v ...' added below to satisfy AV-5440. the test would report a failure because of the warning about readable otherwise
set -o pipefail; OCPI_LOG_LEVEL=1 OCPI_LIBRARY_PATH=$OCPI_LIBRARY_PATH:./assemblies/ ./scripts/AD9361_BIST_PRBS.sh $APP_XML 2>&1 | tee odata/temp; grep -v "the \"readable\" attribute is deprecated: all properties are considered readable" odata/temp > odata/AD9361_BIST_PRBS.log; rm odata/temp; 
if [ "$?" !=  "0" ]; then
  echo "TEST FAILED"
  exit 1
fi

FOUND_PLATFORMS=$(./target-$OCPI_TOOL_DIR/get_comma_separated_ocpi_platforms)
AT_LEAST_ONE_ML605_AVAILABLE=$(./target-$OCPI_TOOL_DIR/get_at_least_one_platform_is_available ml605)
XX="1"
if [ "$FOUND_PLATFORMS" == "" ]; then
  echo ERROR: no platforms found! check ocpirun -C
  echo "TEST FAILED"
  exit 1
elif [ "$FOUND_PLATFORMS" == "zed" ]; then
  diff odata/AD9361_BIST_PRBS.log scripts/AD9361_BIST_PRBS.zed.golden >/dev/null
  XX=$?
  diff odata/AD9361_BIST_PRBS.log scripts/AD9361_BIST_PRBS.zed.golden | head -n 20
elif [ "$AT_LEAST_ONE_ML605_AVAILABLE" == "true" ]; then
  diff odata/AD9361_BIST_PRBS.log scripts/AD9361_BIST_PRBS.lvds.delays_2_0_7_0.use_xo.golden >/dev/null
  XX=$?
  diff odata/AD9361_BIST_PRBS.log scripts/AD9361_BIST_PRBS.lvds.delays_2_0_7_0.use_xo.golden | head -n 20
else
  printf "platform found which is not supported: "
  echo $FOUND_PLATFORMS
  echo "TEST FAILED"
  exit 1
fi
X=$XX

if [ "$X" ==  "0" ]; then
  echo "TEST PASSED"
else
  echo "TEST FAILED"
  exit 1
fi

#echo "Running additional reports: (PRBS Built-In-Self-Test across range of clock and data delays)"
#./scripts/AD9361_BIST_PRBS_delays.sh $APP_XML > odata/AD9361_BIST_PRBS_delays.log
exit 0
