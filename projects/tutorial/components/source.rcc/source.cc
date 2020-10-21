/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Sat Sep 12 12:08:08 2020 EDT
 * BASED ON THE FILE: source.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the source worker in C++
 */

#include "source-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace SourceWorkerTypes;

class SourceWorker : public SourceWorkerBase {
  size_t samples;
public:
  SourceWorker() : samples(0) {}
  RCCResult run(bool /*timedout*/) {
    size_t n = std::min(out.data().real().capacity(), properties().nsamples - samples);
    if (n) {
      out.data().real().resize(n);
      samples += n;
      for (int16_t *p = out.data().real().data(); n--; *p++ = properties().value)
	;
      return RCC_ADVANCE;
    }
    out.setEOF();
    return RCC_ADVANCE_DONE;
  }
};

SOURCE_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
SOURCE_END_INFO
