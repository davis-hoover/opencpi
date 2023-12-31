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

FOUND_PLATFORMS=$(./target-$OCPI_TOOL_DIR/get_comma_separated_ocpi_platforms)
AT_LEAST_ONE_ML605_AVAILABLE=$(./target-$OCPI_TOOL_DIR/get_at_least_one_platform_is_available ml605)
if [ "$FOUND_PLATFORMS" == "" ]; then
  echo ERROR: no platforms found! check ocpirun -C
  echo "TEST FAILED"
  exit 1
elif [ "$FOUND_PLATFORMS" == "zed" ]; then
  # force test zed bitstream (and NOT zed_ise bitstream)
  ocpihdl -d PL:0 load ../../hdl/assemblies/ad9361_1r1t_test_asm/container-ad9361_1r1t_test_asm_zed_cfg_1rx_1tx_fmcomms_2_3_lpc_lvds_cnt_1rx_1tx_thruasm_txsrc_fmcomms_2_3_lpc_LVDS_zed/target-zynq/ad9361_1r1t_test_asm_zed_cfg_1rx_1tx_fmcomms_2_3_lpc_lvds_cnt_1rx_1tx_thruasm_txsrc_fmcomms_2_3_lpc_LVDS_zed.bitz
  XX=$?
  if [ "$XX" !=  "0" ]; then
    echo "TEST FAILED"
    exit $XX
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

mkdir -p odata

APP_XML=ad9361_test_1r1t_lvds_app.xml

if [ ! -f $APP_XML ]; then
  echo "app xml not found: $APP_XML"
  echo "(pwd is: $PWD)"
  exit 1
fi

DO_PRBS=1
if [ ! -z "$1" ]; then
  if [ "$1" == "disableprbs" ]; then # ONLY DO THIS TO SAVE TIME IF YOU KNOW
                                     # PRBS IS ALREADY WORKING
    DO_PRBS=0
  fi
fi

if [ "$DO_PRBS" == "1" ]; then
  echo "Running PRBS Built-In-Self-Test across range of sample rates for LVDS mode"
#'grep -v ...' added below to satisfy AV-5444. the test would report a failure because of the warning about readable otherwise
  OCPI_LOG_LEVEL=1 OCPI_LIBRARY_PATH=$OCPI_LIBRARY_PATH:./assemblies/ ./scripts/AD9361_BIST_PRBS.sh $APP_XML 2>&1 | tee odata/temp; grep -v "attribute is deprecated" odata/temp > odata/AD9361_BIST_PRBS.log; rm odata/temp; test ${PIPESTATUS[0]} -eq 0
  XX=$?
  if [ "$XX" !=  "0" ]; then
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
    diff odata/AD9361_BIST_PRBS.log scripts/AD9361_BIST_PRBS.zed.golden
    XX=$?
  elif [ "$AT_LEAST_ONE_ML605_AVAILABLE" == "true" ]; then
    diff odata/AD9361_BIST_PRBS.log scripts/AD9361_BIST_PRBS.lvds.delays_2_0_7_0.use_xo.golden
    XX=$?
  else
    printf "platform found which is not supported: "
    echo $FOUND_PLATFORMS
    echo "TEST FAILED"
    exit 1
  fi
  X=$XX

  if [ "$X" !=  "0" ]; then
    echo "TEST FAILED"
    exit 1
  fi
fi

FOUND_PLATFORMS=$(./target-$OCPI_TOOL_DIR/get_comma_separated_ocpi_platforms)
AT_LEAST_ONE_ML605_AVAILABLE=$(./target-$OCPI_TOOL_DIR/get_at_least_one_platform_is_available ml605)
if [ "$FOUND_PLATFORMS" == "" ]; then
  echo ERROR: no platforms found! check ocpirun -C
  echo "TEST FAILED"
  exit 1
elif [ "$FOUND_PLATFORMS" == "zed" ]; then
  # force test zed bitstream (and NOT zed_ise bitstream)
  ocpihdl -d PL:0 load ../../hdl/assemblies/ad9361_1r1t_test_asm/container-ad9361_1r1t_test_asm_zed_cfg_1rx_1tx_fmcomms_2_3_lpc_lvds_cnt_1rx_1tx_thruasm_txsrc_fmcomms_2_3_lpc_LVDS_zed/target-zynq/ad9361_1r1t_test_asm_zed_cfg_1rx_1tx_fmcomms_2_3_lpc_lvds_cnt_1rx_1tx_thruasm_txsrc_fmcomms_2_3_lpc_LVDS_zed.bitz
  XX=$?
  if [ "$XX" !=  "0" ]; then
    echo "TEST FAILED"
    exit $XX
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

echo "Running loopback Built-In-Self-Test across range of sample rates for LVDS mode"
#'grep -v ...' added below to satisfy AV-5444. the test would report a failure because of the warning about readable otherwise
OCPI_LOG_LEVEL=1 OCPI_LIBRARY_PATH=$OCPI_LIBRARY_PATH:./assemblies/ ./scripts/AD9361_BIST_loopback.sh $APP_XML 2>&1 | tee odata/temp_loopback; grep -v "attribute is deprecated" odata/temp_loopback > odata/AD9361_BIST_loopback.log; rm odata/temp_loopback;
if [ "$?" !=  "0" ]; then
  cat odata/AD9361_BIST_loopback.log
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
  diff odata/AD9361_BIST_loopback.log scripts/AD9361_BIST_loopback.zed.golden
  XX=$?
elif [ "$AT_LEAST_ONE_ML605_AVAILABLE" == "true" ]; then
  diff odata/AD9361_BIST_loopback.log scripts/AD9361_BIST_loopback.lvds.delays_2_0_7_0.use_xo.golden
  XX=$?
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

exit 0
