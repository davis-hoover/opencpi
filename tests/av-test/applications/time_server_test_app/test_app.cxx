/*
 * This file is protected by Copyright. Please refer to the COPYRIGHT file
 * distributed with this source distribution.
 *
 * This file is part of OpenCPI <http://www.opencpi.org>
 *
 * OpenCPI is free software: you can redistribute it and/or modify it under the
 * terms of the GNU Lesser General Public License as published by the Free
 * Software Foundation, either version 3 of the License, or (at your option) any
 * later version.
 *
 * OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
 * A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
 * details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

/*
 * The purpose of this application is to test the quality of time (valid) 
 * presented to workers on the WTI interface
 *
 * 4 configurations of the time_server are tested for all combinations of 
 * the enabled_time_now_updates_from_PPS and valid_requires_write_to_time_now
 * properties.
 *
 * When valid_requires_write_to_time_now is true, time_now is written to a known 
 * value during initialize. The first valid timestamp (seconds portion) observed 
 * by the time_server_tester should match the value written to time_now. The previous
 * timestamp (seconds portion) should be zero.
 *
 * When enable_time_now_updates_from_PPS, the first valid timestamp (fractional 
 * portion) should be less than PPS_tolerance % of the maximum fractional value. 
 * It will be less than the fractional portion because a PPS signal is generated upon 
 * starting the simulation and the internal counter used to determine PPS_ok starts 
 * shortly after. 
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "OcpiApi.hh"
#include <iostream>
#include <stdlib.h>

const int MAX_EXPECTED_SIM_TIME_USECS=120000000; //to prevent simulator hanging
const unsigned long TIME_NOW_VALUE_FOR_VERIFY=0x0123456700000000;

//PPS valid expected to occur > 0.999% of frac rollover (2^32=4294967296)
const double LOWER_FRAC_SEC_THRESHOLD=4294967296*.999;

//The current set of test cases are for all possible combinations of 
// {enable_time_now_updates_from_PPS, valid_requires_write_to_time_now} for the time server
const int NUM_TEST_CASES=4;
const bool testValues[NUM_TEST_CASES][2] = {{0,0},{0,1},{1,0},{1,1}}; 
namespace OA = OCPI::API;
using namespace std;
int programRet = 0; 

unsigned int verifyTestCase(bool enable_time_now_updates_from_PPS, bool valid_requires_write_to_time_now, unsigned long seconds[2], unsigned long fraction[2])
{
  int retVal = 0;
  //cout << "Seconds[0]: " << seconds[0] << " Fraction[0]: " << fraction[0] << endl;
  //cout << "Seconds[1]: " << seconds[1] << " Fraction[1]: " << fraction[1] << endl;
  if (valid_requires_write_to_time_now)
    {
      // Current second value should be TIME_NOW_VALUE_FOR_VERIFY when GPS enabled
      // and last second (which was captured before valid) should be 0
      if (seconds[0] != TIME_NOW_VALUE_FOR_VERIFY >> 32)
	  retVal=1;
      if (seconds[1] != 0)
	  retVal=2;
    }
  else
    {
      //Second value should be zero when valid_requires_write_to_time_now = false
      if (seconds[0] != 0)
	retVal=3;
    }

  if (retVal)
    return retVal;

  if (enable_time_now_updates_from_PPS)
    {
      //Fraction value should be > lower threshold when enable_time_now_updates_from_PPS = true
      if (fraction[0] < LOWER_FRAC_SEC_THRESHOLD)
	retVal=4;
    }
  //Currently, no way to deterministically verify fractional second count when
  //enable_time_now_updates_from_PPS = false  
  return retVal;
}

unsigned int runApp(bool enable_time_now_updates_from_PPS, bool valid_requires_write_to_time_now)
{
  int retVal = 0;
  unsigned long seconds[2];
  unsigned long fraction[2];

  cout << "Test Case: " << endl;
  cout << "enable_time_now_updates_from_PPS = " << enable_time_now_updates_from_PPS << endl;
  cout << "valid_requires_write_to_time_now = " << valid_requires_write_to_time_now << endl;

  OA::PValue pvs[] = { OA::PVBool("verbose", false), OA::PVBool("dump", false), OA::PVEnd };
  OA::Application app("test_app.xml", pvs);
  app.initialize();
  app.setPropertyValue("time_server", "enable_time_now_updates_from_PPS", enable_time_now_updates_from_PPS);
  app.setPropertyValue("time_server", "valid_requires_write_to_time_now", valid_requires_write_to_time_now);
  if (valid_requires_write_to_time_now)
    app.setPropertyValue("time_server", "time_now", TIME_NOW_VALUE_FOR_VERIFY);
  
  app.start();
  app.wait(MAX_EXPECTED_SIM_TIME_USECS);
  app.stop();

  app.getPropertyValue("time_server_tester", "timestamp_sec", seconds[0], {0});
  app.getPropertyValue("time_server_tester", "timestamp_frac", fraction[0], {0});
  app.getPropertyValue("time_server_tester", "timestamp_sec", seconds[1], {1});
  app.getPropertyValue("time_server_tester", "timestamp_frac", fraction[1], {1});

  app.finish();
  retVal= verifyTestCase(enable_time_now_updates_from_PPS, valid_requires_write_to_time_now, seconds, fraction);

  return retVal;
}

int main(/*int argc, char **argv*/) {
  programRet = 0; 
  bool hdl = false;
  unsigned n = 0;
  // When run in a build environment that is suppressing HDL platforms, respect that.
  // This guard should be removed when Issue #99 is resolved
  const char *env = getenv("HdlPlatforms");
  if (!env || env[0])
    for (OA::Container *c; (c = OA::ContainerManager::get(n)); n++) {
      if (c->model() == "hdl") {
        hdl = true;
        std::cout << "INIT: found HDL container " << c->name() << ", will run HDL tests" << std::endl;
      }
    }

  if (hdl){
    for(int a=0; a<NUM_TEST_CASES; a++){
      bool enable_time_now_updates_from_PPS = testValues[a][0];
      bool valid_requires_write_to_time_now = testValues[a][1];

      programRet = runApp(enable_time_now_updates_from_PPS, valid_requires_write_to_time_now);

      if (programRet)
	return programRet;
      else
	cout << "OK" << endl;
    }
  } else
    std::cout << "Application requires HDL container, but none found. Exiting." << std::endl;
  return programRet;
}
