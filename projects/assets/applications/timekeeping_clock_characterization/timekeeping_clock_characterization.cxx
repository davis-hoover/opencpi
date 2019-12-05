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

//#include <stdio.h>
//#include <stdlib.h>
//#include <unistd.h>
//#include <string.h>
#include "OcpiApi.hh"
#include <iostream> //std::cerr
#include <sstream> // std::ostringstream

//to prevent hanging application
const int MAX_EXPECTED_RUN_TIME_USECS=1e6;

namespace OA = OCPI::API;
using namespace std;

int main(int argc, char **argv) {

  int ret = 0;

  try {

    if(argc != 4) {
      std::ostringstream oss;
      oss << "wrong number of arguments" << "\n";
      oss << "Usage is: " << argv[0] << " <freq counter ip> <freq std tty> <platform>\n";
      throw oss.str();
    }

    //Check as much as you can about the test setup

    //10 MHz reference
    std::string freq_cnt_ip = argv[1];
    std::string cmd = "./53230A_Counter_PPS_Stats.py " + freq_cnt_ip + " ref_check";
    if(system(cmd.c_str()) != 0)
      return 1;

    //Check if Rb Standard has 1 PPS sync
    std::string freq_std_tty = argv[2];
    cmd = "./FS725_Freq_Std_Status.py " + freq_std_tty;
    if(system(cmd.c_str()) != 0)
      return 2;

    //Run nothing application
    std::string platform = "=" + std::string(argv[3]);
    OA::PValue pvs[] = { OA::PVBool("verbose", false), OA::PVBool("dump", false), 
			 OA::PVString("platform", platform.c_str()), 
			 OA::PVBool("dumpPlatforms", true), OA::PVEnd };
    OA::Application app("../nothing.xml", pvs);
    app.initialize();
    app.start();
    app.wait(MAX_EXPECTED_RUN_TIME_USECS);
    app.stop();
    app.finish();

    //Frequency Error and Allan Variance Measurements
    cmd = "./53230A_Counter_PPS_Stats.py " + freq_cnt_ip + " frequency";
    if(system(cmd.c_str()) != 0)
      return 3;

    //Jitter Measurements
    cmd = "./53230A_Counter_PPS_Stats.py " + freq_cnt_ip + " single_period";
    if(system(cmd.c_str()) != 0)
      return 4;

    //Phase Accuracy Measurements
    cmd = "./53230A_Counter_PPS_Stats.py " + freq_cnt_ip + " time_interval_2-1";
    if(system(cmd.c_str()) != 0)
      return 5;

  } catch (std::string &e) {
    std::cerr << "ERROR: " << e << "\n";
    ret = 1;
  }

  return ret;
}
