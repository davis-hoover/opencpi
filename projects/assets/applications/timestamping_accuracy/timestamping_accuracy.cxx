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
 * The purpose of this application is to collect statistics related to the 
 * accuracy of timestamps presented to workers which request time.
 * 
 * The application consists of a device worker with a single input signal. The
 * worker collects the timestamp from its WTI at every rising edge of the input
 * signal and is done when the number of timestamps collected =
 * num_time_tags_to_collect
 * 
 * The expected input signal is a 1 PPS signal from a high precision GPS receiver
 * (e.g FS740). Because the rising edge of this input signal is expected on each
 * second boundary of GPS time, the delta from the nearest second boundary can be
 * used to compute accuracy measurements. The average, minimum, maximum, and
 * standard deviation of the delta for the timestamps captured are reported. 
 *
 * The application is run twice. The first time the average delta from the nearest
 * second boundary is computed and fed into the application as a calibration
 * constant to the signal_time_tagger worker.
 */

#include "OcpiApi.hh"
#include <iostream>  // cout,cerr
#include <cmath>     // std::pow()
#include <algorithm> // std::min_element, std::max_element
#include <sstream>   // std::ostringstream

//TODO: These are internal headers which should not be included directly
//      Anything from them exposed to the ACI should be in Ocpi*Api.h files
//      https://gitlab.com/opencpi/opencpi/issues/887
#include "OcpiDriverManager.h"
#include "OcpiUtilEzxml.h"

const char *APP_NAME = "ocpi.assets.timestamping_accuracy";
//Seconds buffer for application timeout
const int MAX_NUM_TIME_TAGS_TO_COLLECT = 128;
const int EXTRA_TIME_BUFFER = 5;
const double NUM_MICROSECONDS_PER_FRAC_SEC = .000233;

namespace OA = OCPI::API;
namespace OX = OCPI::Util::EzXml;

int64_t computeStatistics(uint64_t* collected_time_tags, 
		       uint32_t num_time_tags_to_collect,
		       int64_t cal_value){
  uint32_t frac_sec;
  int64_t avg_delta;
  int64_t delta_from_nearest_sec[num_time_tags_to_collect];

  //Compute avg from nearest second value
  for (unsigned int a = 0; a < num_time_tags_to_collect; a++){
    frac_sec = collected_time_tags[a];
    if(frac_sec <= std::pow(2.,32.)/2)
      delta_from_nearest_sec[a] = frac_sec;
    else
      delta_from_nearest_sec[a] = -(std::pow(2.,32.) - frac_sec);
    avg_delta += (int64_t)(delta_from_nearest_sec[a] - avg_delta) / (a + 1);
  }

  std::cout << "Average Delta from nearest second          " << 
    avg_delta * NUM_MICROSECONDS_PER_FRAC_SEC << " us" << std::endl;

  //Compute min, max, std_dev from nearest second value when cal value supplied
  if(cal_value){
    double  var, std_dev = 0;

    for (unsigned int a = 0; a < num_time_tags_to_collect; a++)
      var += (int64_t)(delta_from_nearest_sec[a] - avg_delta) * 
	(int64_t)(delta_from_nearest_sec[a] - avg_delta);
    var /= num_time_tags_to_collect;
    std_dev = sqrt(var);

    std::cout << "Min Delta from nearest second              " << 
      *std::min_element(delta_from_nearest_sec, delta_from_nearest_sec + num_time_tags_to_collect - 1) *
      NUM_MICROSECONDS_PER_FRAC_SEC << " us" << std::endl;
    std::cout << "Max Delta from nearest second              " << 
      *std::max_element(delta_from_nearest_sec, delta_from_nearest_sec + num_time_tags_to_collect - 1) *
      NUM_MICROSECONDS_PER_FRAC_SEC << " us" << std::endl;
    std::cout << "Standard Deviation from nearest second     " << 
      std_dev * NUM_MICROSECONDS_PER_FRAC_SEC << " us" << std::endl;
  }
  return avg_delta;
}

int64_t runApp(const char *platform,
	       uint32_t num_time_tags_to_collect,
	       int64_t cal_value,
	       uint64_t* collected_time_tags){

  try {

    const char *freq_std_tty, *gps_freq_ref_ip;
    //to prevent hanging application
    uint32_t max_expected_run_time_usecs = (num_time_tags_to_collect + EXTRA_TIME_BUFFER) * 1e6;
    std::string platform_string = "=" + std::string(platform);
    OA::PValue pvs[] = { OA::PVBool("verbose", false), OA::PVBool("dump", false), 
			 OA::PVString("platform", platform_string.c_str()), OA::PVEnd };
    OA::Application app("timestamping_accuracy.xml", pvs);
    
    //Check if system is setup to run test
    ezxml_t system_xml = OCPI::Driver::ManagerManager::getManagerManager().getXML();
    ezxml_t applications_xml = ezxml_child(system_xml, "applications");
    ezxml_t application_xml = OX::findChildWithAttr(applications_xml, "application", "name", APP_NAME); 
    ezxml_t platform_xml, freqstd_xml, gpsfreqref_xml;
    if(application_xml){
      ezxml_t platforms_xml = ezxml_child(application_xml, "platforms");
      platform_xml = OX::findChildWithAttr(platforms_xml, "platform", "name", platform);
      if(platform_xml){
	freqstd_xml = ezxml_child(application_xml, "freqstd");
	freq_std_tty = ezxml_cattr(freqstd_xml, "serialport");
	gpsfreqref_xml = ezxml_child(application_xml, "gpsfreqref");
	gps_freq_ref_ip = ezxml_cattr(gpsfreqref_xml, "ipaddr");
      }
    }
    
    if(!application_xml || !platform_xml || !freq_std_tty || !gps_freq_ref_ip)
      std::cerr << "WARNING: system.xml not setup correctly. Exiting but not failing.\n";
    else {
      //Check as much as you can about the test setup
      std::ostringstream oss;

      //Check if Rb Standard has 1 PPS sync
      std::string cmd = "./FS725_Freq_Std_Status.py " + std::string(freq_std_tty);
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

      app.initialize();
      app.setPropertyValue("signal_time_tagger", "num_time_tags_to_collect", num_time_tags_to_collect);
      if(cal_value)
	app.setPropertyValue("signal_time_tagger", "calibration_value", cal_value);

      app.start();
      app.wait(max_expected_run_time_usecs);
      app.stop();

      app.finish();

      OA::Property collected_time_tags_p(app, "signal_time_tagger", "collected_time_tags");
      collected_time_tags_p.getULongLongSequenceValue(collected_time_tags, MAX_NUM_TIME_TAGS_TO_COLLECT);
      cal_value = computeStatistics(collected_time_tags, num_time_tags_to_collect, cal_value);
    }

  } catch (std::string &e) {
    std::cerr << "ERROR: " << e << "\n";
  }
  return cal_value;

}

int main(int argc, char **argv) {

  int ret = 0;
  const char *platform;
  uint32_t num_time_tags_to_collect;

  try {

    if(argc == 1) {
      std::cout << "INFO: No arguments supplied. Using defaults." << std::endl;
      std::cout << "INFO: num_time_tags_to_collect: 10" << std::endl;
      std::cout << "INFO: platform: e3xx" << std::endl;
      num_time_tags_to_collect = 10;
      platform = "e3xx";
    } else if(argc != 3) {
      std::ostringstream oss;
      oss << "wrong number of arguments" << "\n";
      oss << "Usage is: " << argv[0] << " <num_time_tags_to_collect> <platform>\n";
      throw oss.str();
    } else {
      num_time_tags_to_collect = atoi(argv[1]);
      platform = argv[2];
    }

    uint64_t collected_time_tags[MAX_NUM_TIME_TAGS_TO_COLLECT];

    std::cout << "Computing calibration value: " << std::endl;
    int64_t cal_value = runApp(platform, num_time_tags_to_collect, 0, collected_time_tags);     

    if(cal_value){
      std::cout << "Timestamping Accuracy: " << std::endl;
      runApp(platform, num_time_tags_to_collect, cal_value, collected_time_tags);
    }

  } catch (std::string &e) {
    std::cerr << "ERROR: " << e << "\n";
    ret = 1;
  }

  return ret;
}
