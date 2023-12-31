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

//TODO: These are internal headers which should not be included directly
//      Anything from them exposed to the ACI should be in Ocpi*Api.h files
//      https://gitlab.com/opencpi/opencpi/issues/887
#include "BasePluginManager.hh"
#include "UtilEzxml.hh"

const char *APP_NAME = "ocpi.platform.timekeeping_clock_characterization";
//to prevent hanging application
const int MAX_EXPECTED_RUN_TIME_USECS=1e6;

namespace OA = OCPI::API;
namespace OX = OCPI::Util::EzXml;

int main(/*int argc, char **argv*/) {

  int ret = 0;
  std::ostringstream oss;
  const char *container, *freq_std_tty, *freq_counter_ip, *gps_freq_ref_ip;

  try {

    //Check if system is setup to run test
    OCPI::Base::Plugin::ManagerManager::getManagerManager().configure();
    ezxml_t system_xml = OCPI::Base::Plugin::ManagerManager::getManagerManager().getXML();
    ezxml_t applications_xml = ezxml_child(system_xml, "applications");
    ezxml_t application_xml = OX::findChildWithAttr(applications_xml, "application", "name", APP_NAME); 
    ezxml_t freqstd_xml, freqcounter_xml, gpsfreqref_xml;
    if(application_xml){
      freqstd_xml = ezxml_child(application_xml, "freqstd");
      freq_std_tty = ezxml_cattr(freqstd_xml, "serialport");
      freqcounter_xml = ezxml_child(application_xml, "freqcounter");
      freq_counter_ip = ezxml_cattr(freqcounter_xml, "ipaddr");
      gpsfreqref_xml = ezxml_child(application_xml, "gpsfreqref");
      gps_freq_ref_ip = ezxml_cattr(gpsfreqref_xml, "ipaddr");
    }

    if(!application_xml || !freq_std_tty || !freq_counter_ip || !gps_freq_ref_ip)
      std::cerr << "WARNING: system.xml not setup correctly. Exiting but not failing.\n";
    else {

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
      //Check GPS Receiver status
      cmd = "./FS740_GPS_Freq_Ref_Status.py " + std::string(gps_freq_ref_ip);
      if(system(cmd.c_str()) != 0){
	oss << "Unexpected GPS receiver status register" << "\n";
	throw oss.str();
      }

      //Run nothing application for containers listed in system.xml
      ezxml_t containers_xml = ezxml_child(application_xml, "containers");
      for (ezxml_t x = OX::ezxml_firstChild(containers_xml); x; x = OX::ezxml_nextChild(x)) {	
	container = ezxml_cattr(x, "name");
	std::string container_string = "=" + std::string(container);
	OA::PValue pvs[] = { OA::PVBool("verbose", false), OA::PVBool("dump", false), 
			     OA::PVString("container", container_string.c_str()), 
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
    }
  } catch (std::string &e) {
    std::cerr << "ERROR: " << e << "\n";
    ret = 1;
  }
  return ret;
}
