/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Mon Sep 14 15:17:22 2020 EDT
 * BASED ON THE FILE: square.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the square worker in C++
 */

#include "square-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace SquareWorkerTypes;

class SquareWorker : public SquareWorkerBase {
  RCCResult run(bool /*timedout*/) {
    size_t num = out.data().real().capacity() & ~63;
    out.data().real().resize(num);
    int16_t *odata = out.data().real().data();

    for (unsigned n = 0; n < num; ++n)
      *odata++ = (n & 63) < 32 ? ~0 : 0;
    return RCC_ADVANCE;
  }
};

SQUARE_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
SQUARE_END_INFO
