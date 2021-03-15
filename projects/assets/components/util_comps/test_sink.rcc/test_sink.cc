/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Sat Sep 12 12:08:08 2020 EDT
 * BASED ON THE FILE: source.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the source worker in C++
 */

#include <cinttypes>
#include "test_sink-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Test_sinkWorkerTypes;

class Test_sinkWorker : public Test_sinkWorkerBase {
  RCCResult run(bool /*timedout*/) {
    if (firstRun())
      properties().timeFirst = getTime();
    if (in.opCode()) {
      log(6, "Opcode: %u, length %zu, first word 0x%" PRIx64 "\n",
	  in.opCode(), in.length(), *(uint64_t*)in.data());
      return RCC_ADVANCE;
    }
    size_t n = in.length()/sizeof(uint32_t);
    if (n) {
      if (properties().suppressReads)
	properties().valuesReceived += n;
      else
	for (uint32_t *p = (uint32_t*)in.data(); n--; ++p, ++properties().valuesReceived)
	  if (*p != properties().valuesReceived)
	    return setError("Bad count:  expected %u, got %u", properties().valuesReceived, *p);
      return RCC_ADVANCE;
    }
    if (in.eof()) {
      properties().timeEOF = getTime();
      uint64_t nanos = nanoTime(properties().timeEOF - properties().timeFirst);
      properties().bytesPerSecond =
	(properties().valuesReceived * sizeof(uint32_t) * 1000000000llu) / (nanos ? nanos : 1);
      return RCC_ADVANCE_DONE;
    }
    return setError("Unexpected ZLM without EOF");
  }
};

TEST_SINK_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
TEST_SINK_END_INFO
