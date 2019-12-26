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

#include "OcpiApi.hh"
#include <iostream> //std::cerr
#include <sstream> // std::ostringstream
#include "ezxml.h"

//to prevent hanging application
const int MAX_EXPECTED_RUN_TIME_USECS=1e6;

namespace OA = OCPI::API;

int main(/*int argc, char **argv*/) {

  int ret = 0;
  std::ostringstream oss;
  const char *platform, *freq_std_tty, *freq_counter_ip;

  try {
    //Extract test setup config from system.xml
    //First check if OCPI_SYSTEM_CONFIG sets location of system.xml
    const char *system_xml_filename = getenv("OCPI_SYSTEM_CONFIG");
    if(!system_xml_filename)
      //If not, check default location of /opt/opencpi/system.xml
      system_xml_filename = "/opt/opencpi/system.xml";
    FILE *system_xml_file = fopen(system_xml_filename, "r"); 
    if(system_xml_file){
      fclose(system_xml_file);
      ezxml_t system_xml = ezxml_parse_file(system_xml_filename);
      ezxml_t timetest_xml = ezxml_get(system_xml,
				     "container", 0,
				     "timetest", -1);
      platform = ezxml_cattr(timetest_xml, "platform");
      ezxml_t freqstd_xml = ezxml_child(timetest_xml, "freqstd");
      freq_std_tty = ezxml_cattr(freqstd_xml, "serialport");
      ezxml_t freqcounter_xml = ezxml_child(timetest_xml, "freqcounter");
      freq_counter_ip = ezxml_cattr(freqcounter_xml, "ipaddr");
    } else
      system_xml_filename = NULL;

    if(!system_xml_filename || !platform || !freq_std_tty || !freq_counter_ip){
      std::cerr << "WARNING: system.xml not setup correctly. Exiting but not failing.\n";
    } else {
      //Check as much as you can about the test setup

      //10 MHz reference
      std::string cmd = "./53230A_Counter_PPS_Stats.py " + std::string(freq_counter_ip) + " ref_check";
      if(system(cmd.c_str()) != 0){
	oss << "no valid 10 MHz reference to frequency counter" << "\n";
	throw oss.str();
      }
      //Check if Rb Standard has 1 PPS sync
      cmd = "./FS725_Freq_Std_Status.py " + std::string(freq_std_tty);
      if(system(cmd.c_str()) != 0){
	oss << "no valid PPS into frequency standard" << "\n";
	throw oss.str();
      }
      
      //Run nothing application
      std::string platform_string = "=" + std::string(platform);
      OA::PValue pvs[] = { OA::PVBool("verbose", false), OA::PVBool("dump", false), 
			   OA::PVString("platform", platform_string.c_str()), 
			   OA::PVBool("dumpPlatforms", true), OA::PVEnd };
      OA::Application app("../nothing.xml", pvs);
      app.initialize();
      app.start();
      app.wait(MAX_EXPECTED_RUN_TIME_USECS);
      app.stop();
      app.finish();

      //Frequency Error and Allan Variance Measurements
      cmd = "./53230A_Counter_PPS_Stats.py " + std::string(freq_counter_ip) + " frequency";
      if(system(cmd.c_str()) != 0){
	oss << "frequency measurement failure" << "\n";
	throw oss.str();
      }

      //Jitter Measurements
      cmd = "./53230A_Counter_PPS_Stats.py " + std::string(freq_counter_ip) + " single_period";
      if(system(cmd.c_str()) != 0){
	oss << "jitter measurement failure" << "\n";
	throw oss.str();
      }

      //Phase Accuracy Measurements
      cmd = "./53230A_Counter_PPS_Stats.py " + std::string(freq_counter_ip) + " time_interval_2-1";
      if(system(cmd.c_str()) != 0){
	oss << "phase accuracy measurement failure" << "\n";
	throw oss.str();
      }
    }
  } catch (std::string &e) {
    std::cerr << "ERROR: " << e << "\n";
    ret = 1;
  }
  return ret;
}
