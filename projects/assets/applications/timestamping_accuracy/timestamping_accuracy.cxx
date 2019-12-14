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
 * NUM_TIME_TAGS_TO_COLLECT
 * 
 * The expected input signal is a 1 PPS signal from a high precision GPS receiver
 * (e.g FS740). Because the rising edge of this input signal is expected on each
 * second boundary of GPS time, the delta from the nearest second boundary can be
 * used to compute accuracy measurements. The average, minimum, maximum, and
 * standard deviation of the delta for the timestamps captured are reported. The
 * average can be used as a calibration constant for a timestamper worker.
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "OcpiApi.hh"
#include <iostream>
#include <stdlib.h>
#include <cmath>     //std::pow()
#include <algorithm> // std::min_element, std::max_element

const int NUM_TIME_TAGS_TO_COLLECT=100;
const int EXTRA_TIME_BUFFER=5; //Seconds buffer for application timeout
//to prevent hanging application
const int    MAX_EXPECTED_RUN_TIME_USECS=(NUM_TIME_TAGS_TO_COLLECT+EXTRA_TIME_BUFFER)*1e6;
const double NUM_MICROSECONDS_PER_FRAC_SEC = .000233;

namespace OA = OCPI::API;
using namespace std;

void computeStatistics(uint32_t collected_time_tags_frac[NUM_TIME_TAGS_TO_COLLECT]){
  int64_t delta_from_nearest_sec[NUM_TIME_TAGS_TO_COLLECT];
  int64_t delta_corr[NUM_TIME_TAGS_TO_COLLECT];
  int64_t avg_delta, avg_delta_corr = 0;
  double  var, var_corr, std_dev, std_dev_corr = 0;

  for (int a = 0; a < NUM_TIME_TAGS_TO_COLLECT; a++){
    if(collected_time_tags_frac[a] <= std::pow(2.,32.)/2)
      delta_from_nearest_sec[a] = collected_time_tags_frac[a];
    else
      delta_from_nearest_sec[a] = -(std::pow(2.,32.) - collected_time_tags_frac[a]);
    avg_delta += (int64_t)(delta_from_nearest_sec[a] - avg_delta) / (a + 1);
  }

  for (int a = 0; a < NUM_TIME_TAGS_TO_COLLECT; a++)
    var += (int64_t)(delta_from_nearest_sec[a] - avg_delta) * 
      (int64_t)(delta_from_nearest_sec[a] - avg_delta);
  var /= NUM_TIME_TAGS_TO_COLLECT;
  std_dev = sqrt(var);

  cout << "Min Delta from nearest second              " << 
    *std::min_element(delta_from_nearest_sec, delta_from_nearest_sec + NUM_TIME_TAGS_TO_COLLECT - 1) *
    NUM_MICROSECONDS_PER_FRAC_SEC << " us" << endl;
  cout << "Max Delta from nearest second              " << 
    *std::max_element(delta_from_nearest_sec, delta_from_nearest_sec + NUM_TIME_TAGS_TO_COLLECT - 1) *
    NUM_MICROSECONDS_PER_FRAC_SEC << " us" << endl;
  cout << "Average Delta from nearest second          " << 
    avg_delta * NUM_MICROSECONDS_PER_FRAC_SEC << " us" << endl;
  cout << "Standard Deviation from nearest second     " << 
    std_dev * NUM_MICROSECONDS_PER_FRAC_SEC << " us" << endl;


  //Report statistics with average subtracted

  for (int a = 0; a < NUM_TIME_TAGS_TO_COLLECT; a++){
    if(delta_from_nearest_sec[a] >= avg_delta)
      delta_corr[a] = delta_from_nearest_sec[a] - avg_delta;
    else
      delta_corr[a] = -(avg_delta - delta_from_nearest_sec[a]);
    avg_delta_corr += 
      (int64_t)(delta_corr[a] - avg_delta_corr) / (a + 1);
  }

   for (int a = 0; a < NUM_TIME_TAGS_TO_COLLECT; a++)
     var_corr += (int64_t)(delta_corr[a] - avg_delta_corr) * (int64_t)(delta_corr[a] - avg_delta_corr);
   var_corr /= NUM_TIME_TAGS_TO_COLLECT;
   std_dev_corr = sqrt(var_corr);

   cout << "Min Delta with average subtracted          " << 
     *std::min_element(delta_corr, delta_corr + NUM_TIME_TAGS_TO_COLLECT - 1) *
     NUM_MICROSECONDS_PER_FRAC_SEC << " us" << endl;
   cout << "Max Delta with average subtracted          " << 
     *std::max_element(delta_corr, delta_corr + NUM_TIME_TAGS_TO_COLLECT - 1) *
     NUM_MICROSECONDS_PER_FRAC_SEC << " us" << endl;
   cout << "Average Delta with average subtracted      " << 
     avg_delta_corr * NUM_MICROSECONDS_PER_FRAC_SEC << " us" << endl;
   cout << "Standard Deviation with average subtracted " << 
     std_dev_corr * NUM_MICROSECONDS_PER_FRAC_SEC << " us" << endl;
}

int main(/*int argc, char **argv*/) {

  OA::PValue pvs[] = { OA::PVBool("verbose", true), OA::PVBool("dump", false), OA::PVEnd };
  OA::Application app("timestamping_accuracy.xml", pvs);
  app.initialize();
  app.setPropertyValue("signal_time_tagger", "num_time_tags_to_collect", NUM_TIME_TAGS_TO_COLLECT);

  app.start();
  app.wait(MAX_EXPECTED_RUN_TIME_USECS);
  app.stop();

  app.finish();

  uint32_t max_num_time_tags_to_collect;
  app.getPropertyValue("signal_time_tagger", "MAX_NUM_TIME_TAGS_TO_COLLECT", max_num_time_tags_to_collect);

  uint32_t collected_time_tags_frac[max_num_time_tags_to_collect];
  OA::Property collected_time_tags_frac_p(app, "signal_time_tagger", "collected_time_tags_frac");
  collected_time_tags_frac_p.getULongSequenceValue(collected_time_tags_frac,max_num_time_tags_to_collect);

  computeStatistics(collected_time_tags_frac);

  return 0;
}
