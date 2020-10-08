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

set -e
if [ -n "$HDL_TEST_PLATFORM" ]; then
   sims=$HDL_TEST_PLATFORM
else
   sims=(`ocpirun -C --only-platforms | grep '.*-.*xsim' | sed s/^.*-//`)
   [ -z "$sims" ] && {
       echo This test requires a simulator for building, and there are none so we are skipping it.
       exit 0
  }
  echo Available simulators are: ${sims[*]}, using $sims.
  export HDL_TEST_PLATFORM=$sims
fi
echo Using sim platform: $sims

fail() {
  echo "Did not receive an error running this test: this command should not work"
  exit 1
}

OCPIDEV="$OCPI_CDK_DIR/$OCPI_TOOL_DIR/bin/ocpidev"

# Clean everything if it detected a failure the the previous run
if [ -f adapter_insertion.log ]; then
  $OCPIDEV clean hdl assembly clock_from_worker_in_and_clock_from_woker_out_internal  -d ../../av-test/hdl/assemblies
  $OCPIDEV clean hdl assembly clock_from_worker_in_only_external  -d ../../av-test/hdl/assemblies
  $OCPIDEV clean hdl assembly clock_from_worker_in_only_internal  -d ../../av-test/hdl/assemblies
  $OCPIDEV clean hdl assembly clock_from_worker_out_only_external  -d ../../av-test/hdl/assemblies
  $OCPIDEV clean hdl assembly clock_from_worker_out_only_internal  -d ../../av-test/hdl/assemblies
  $OCPIDEV clean worker clock_from_worker_in_only.hdl -d ../../av-test
  $OCPIDEV clean worker clock_from_worker_out_only.hdl -d ../../av-test
  rm -rf clock_from_worker_in_and_clock_from_woker_out_internal.log clock_from_worker_in_only_external.log clock_from_worker_in_only_internal.log \
  clock_from_worker_out_only_external.log clock_from_worker_out_only_internal.log adapter_insertion.log
fi

$OCPIDEV build worker clock_from_worker_in_only.hdl -d ../../av-test --hdl-platform $HDL_TEST_PLATFORM
$OCPIDEV build worker clock_from_worker_out_only.hdl -d ../../av-test --hdl-platform $HDL_TEST_PLATFORM

OCPI_LOG_LEVEL=8 $OCPIDEV build hdl assembly clock_from_worker_in_and_clock_from_woker_out_internal  -d ../../av-test/hdl/assemblies --hdl-platform $HDL_TEST_PLATFORM > clock_from_worker_in_and_clock_from_woker_out_internal.log 2>&1
OCPI_LOG_LEVEL=8 $OCPIDEV build hdl assembly clock_from_worker_in_only_external  -d ../../av-test/hdl/assemblies --hdl-platform $HDL_TEST_PLATFORM > clock_from_worker_in_only_external.log 2>&1
OCPI_LOG_LEVEL=8 $OCPIDEV build hdl assembly clock_from_worker_in_only_internal  -d ../../av-test/hdl/assemblies --hdl-platform $HDL_TEST_PLATFORM > clock_from_worker_in_only_internal.log 2>&1
OCPI_LOG_LEVEL=8 $OCPIDEV build hdl assembly clock_from_worker_out_only_external  -d ../../av-test/hdl/assemblies --hdl-platform $HDL_TEST_PLATFORM > clock_from_worker_out_only_external.log 2>&1
OCPI_LOG_LEVEL=8 $OCPIDEV build hdl assembly clock_from_worker_out_only_internal  -d ../../av-test/hdl/assemblies --hdl-platform $HDL_TEST_PLATFORM > clock_from_worker_out_only_internal.log 2>&1

# Takes in assembly name and worker/instance names that the clock adapters are inserted between
function checkClockAdapterInsertion(){
  if grep -r -q "The clock adapter was inserted between workers: $2 and $3" ${1}.log; then
    echo "For the $1 assembly or container, the clock adapter was inserted in the correct location"
    $OCPIDEV clean hdl assembly $1 -d ../../av-test/hdl/assemblies
  else
    echo "For the $1 assembly or container, the clock adatper was not inserted between $2 and $3" | tee -a adapter_insertion.log
    echo "Check assembly or container -assy.v/-assy.vhd files to see where adapters were placed" >> adapter_insertion.log
  fi
}

checkClockAdapterInsertion clock_from_worker_in_and_clock_from_woker_out_internal clock_from_worker_out_only bias_vhdl
checkClockAdapterInsertion clock_from_worker_in_and_clock_from_woker_out_internal bias_vhdl clock_from_worker_in_only
checkClockAdapterInsertion clock_from_worker_in_only_external sdp_sdp_receive0_1 clock_from_worker_in_only_external
checkClockAdapterInsertion clock_from_worker_in_only_internal bias_vhdl clock_from_worker_in_only
checkClockAdapterInsertion clock_from_worker_out_only_external clock_from_worker_out_only_external sdp_sdp_send0_1
checkClockAdapterInsertion clock_from_worker_out_only_internal clock_from_worker_out_only file_write

if [ -f adapter_insertion.log ]; then
  echo "Failure"
  echo "The clock adapters were not inserted in the correct place for one or more assemblies (or containers)."
  echo "Check adapter_insertion.log for more details"
  exit 1
else
  echo "Success"
  echo "The clock adapters were inserted in the correct place for all the assemblies (or containers)"
  $OCPIDEV clean worker clock_from_worker_in_only.hdl -d ../../av-test
  $OCPIDEV clean worker clock_from_worker_out_only.hdl -d ../../av-test
  rm -rf clock_from_worker_in_and_clock_from_woker_out_internal.log clock_from_worker_in_only_external.log clock_from_worker_in_only_internal.log \
  clock_from_worker_out_only_external.log clock_from_worker_out_only_internal.log adapter_insertion.log
fi
