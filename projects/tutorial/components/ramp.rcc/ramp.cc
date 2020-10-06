/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Tue Sep 15 14:51:02 2020 EDT
 * BASED ON THE FILE: ramp.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the ramp worker in C++
 */

#include "ramp-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace RampWorkerTypes;

class RampWorker : public RampWorkerBase {
  int16_t last;
public:
  RampWorker() : last(0) {}
  RCCResult run(bool /*timedout*/) {
    size_t num = in.data().real().size();
    int16_t
      *idata = out.data().real().data(),
      *odata = out.data().real().data();

    out.data().real().resize(num);
    for (size_t n = 0; n < num; ++n)
      last = *odata++ = *idata++ + last;
    return RCC_ADVANCE;
  }
};

RAMP_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
RAMP_END_INFO
