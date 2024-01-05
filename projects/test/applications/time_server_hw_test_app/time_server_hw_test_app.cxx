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

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "OcpiApi.hh"
#include <iostream>
#include <fstream>
#include <iomanip>
#include <stdlib.h>
#include <time.h>

const int MAX_EXPECTED_TIME_USECS = 1000000; //to prevent simulator hanging

//PPS valid expected to occur > 0.999% of frac rollover (2^32=4294967296)
const double LOWER_FRAC_SEC_THRESHOLD = 4294967296 * .999;
//const unsigned long TIME_NOW_VALUE_FOR_VERIFY = 0x0123456700000000;
//const unsigned long TIME_NOW_VALUE_FOR_VERIFY = 0x0111111100000000;
const unsigned long TIME_NOW_VALUE_FOR_VERIFY = 0x0000000000000000;
const int NUM_TEST_CASES = 5;

//The current set of test cases are for the following combinations of 
// {
//  time_server.enable_time_now_updates_from_PPS, 
//  time_server.valid_requires_write_to_time_now, 
//  time_server_tester.mode
// }
// which is every combination of enable_time_now_updates_from_PPS and
// valid_requires_write_to_time_now in "valid" mode, which tests the 
// time_in.valid signal to workers. There is also one test for "rollover"
// mode, which tests that the rollover of the fractional seconds value is 
// aligned which in the increment of the integer seconds value  
const bool testValues[NUM_TEST_CASES][3] = {{0, 0, 0},
					    {0, 1, 0},
					    {1, 0, 0},
					    {1, 1, 0},
					    {0, 0, 1}}; 
namespace OA = OCPI::API;
using namespace std;
int programRet = 0; 

#define PRINT_ERROR(err) cerr << "ERROR: " << err << "\n";
unsigned int runApp(bool enable_time_now_updates_from_PPS, 
		    bool valid_requires_write_to_time_now,
		    bool time_server_tester_mode)
{
  int retVal = 0;
  unsigned long seconds[2];
  unsigned long fraction[2];
  bool pps_lock;

  cout << "Test Case: " << endl;
  cout << "enable_time_now_updates_from_PPS = " << enable_time_now_updates_from_PPS << endl;
  cout << "valid_requires_write_to_time_now = " << valid_requires_write_to_time_now << endl;
  cout << "time_server_tester_mode = " << time_server_tester_mode << endl;

  OA::PValue pvs[] = { OA::PVBool("verbose", false), OA::PVBool("dump", false), OA::PVEnd };
  
  OA::Application app("test_app.xml", pvs);
  app.initialize();

  std::string name, value;
  bool isParameter, hex = false;

  fprintf(stderr, "Dump of all final property values:\n");
  for (unsigned n = 0; app.getProperty(n, name, value, hex, &isParameter); n++)
    {
      if (!isParameter)
        {
          fprintf(stderr, "Property %2u: %s = \"%s\"\n", n, name.c_str(), value.c_str());
        }
      else
        {
          fprintf(stderr, "Parameter %2u: %s = \"%s\"\n", n, name.c_str(), value.c_str());
        }
    }

  time_t now;
  struct tm * timeinfo;

  time( &now );
  timeinfo = localtime( &now );
  printf("Start time: %02d:%02d:%02d\n", timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);

  app.start();


  ofstream outfile;
  outfile.open("pps_lock_status.out", std::ios_base::app);
  int WAIT_TIME = 300000;  // (seconds)
  int track_lock[WAIT_TIME];

  track_lock[0] = 0;

  for (int i = 1; i < WAIT_TIME; i++){
    
    app.getPropertyValue("time_server_hw_tester", "timestamp_sec", seconds[0], {0});
    app.getPropertyValue("time_server_hw_tester", "timestamp_frac", fraction[0], {0});
    app.getPropertyValue("time_server_hw_tester", "timestamp_valid", pps_lock); 
    track_lock[i] = pps_lock;

    if( track_lock[i] != track_lock[i-1]){
	 time( &now );
          timeinfo = localtime( &now );
	    if (pps_lock == 1){
	    	    printf("PPS LOCKED: ");
		    outfile << "[PPS LOCKED] -   ";
		}
	    else{
	    	    printf("PPS UNLOCKED: ");
		    outfile << "[PPS UNLOCKED] - ";
		}
	    printf("%d/%d (%02d:%02d:%02d)\n", timeinfo->tm_mon + 1, timeinfo->tm_mday, timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);
	    outfile << "(" << timeinfo->tm_mon + 1 << "/" << timeinfo->tm_mday << ") " << std::setfill('0')  << setw(2) << timeinfo->tm_hour << ":"<< std::setfill('0')  << setw(2) << timeinfo->tm_min << ":" << std::setfill('0')  << setw(2) << timeinfo->tm_sec << endl;
    } 
	
    //printf("[%d]",i);
    //cout << " Seconds: " << seconds[0] << " Fractional: " << fraction[0] << " Lock status: " << pps_lock << endl;
    app.wait(MAX_EXPECTED_TIME_USECS);
  }
  
  app.wait(MAX_EXPECTED_TIME_USECS);
 
  app.stop();

  time( &now );
  timeinfo = localtime( &now );
  printf("Finish time: %02d:%02d:%02d\n", timeinfo->tm_hour, timeinfo->tm_min, timeinfo->tm_sec);

  app.finish();

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

      int a = 2;
      bool enable_time_now_updates_from_PPS = testValues[a][0];
      bool valid_requires_write_to_time_now = testValues[a][1];
      bool time_server_tester_mode = testValues[a][2];

      printf("calling runApp\n");
      programRet = runApp(enable_time_now_updates_from_PPS, 
			  valid_requires_write_to_time_now,
			  time_server_tester_mode);

      if (programRet)
	return programRet;
      else
	cout << "OK" << endl;
  } else
    std::cout << "Application requires HDL container, but none found. Exiting." << std::endl;
  return programRet;
}
