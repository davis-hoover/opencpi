/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Sat Aug 14 09:44:59 2021 EDT
 * BASED ON THE FILE: peak_detector.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the peak_detector worker in C++
 */
#include <algorithm>
#include "peak_detector-worker.hh"
using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Peak_detectorWorkerTypes;

class Peak_detectorWorker : public Peak_detectorWorkerBase {

  int16_t max_buff, min_buff;

  RCCResult start(){
    max_buff = -32768;
    min_buff = 32767;
    return RCC_OK;
  }

  RCCResult run(bool /*timedout*/) {

    // 1. Make sure there is room on the output port
    const size_t num_of_elements = in.iq().data().size();
    out.iq().data().resize(num_of_elements);
    out.setOpCode(in.opCode());

    // 2. Do work
    const IqstreamIqData *idata = in.iq().data().data();
    IqstreamIqData *odata = out.iq().data().data();
    for (unsigned n = num_of_elements; n; --n) {
      max_buff = std::max(std::max(idata->I,idata->Q),max_buff);
      min_buff = std::min(std::min(idata->I,idata->Q),min_buff);
      *odata++ = *idata++; // copy this message to output buffer
    }
    properties().max_peak = max_buff;
    properties().min_peak = min_buff;

    // 3. Advance ports
    return RCC_ADVANCE;
  }
};

PEAK_DETECTOR_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
PEAK_DETECTOR_END_INFO

