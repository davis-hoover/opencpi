/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Sat Sep 12 12:08:08 2020 EDT
 * BASED ON THE FILE: source.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the source worker in C++
 */

#include "test_source-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Test_sourceWorkerTypes;

class Test_sourceWorker : public Test_sourceWorkerBase {
  uint32_t m_values;
public:
  Test_sourceWorker() : m_values(0) {}
  RCCResult run(bool /*timedout*/) {
    size_t n = std::min<size_t>(out.maxLength()/sizeof(m_values), properties().valuesToSend - m_values);
    out.setLength(n * sizeof(m_values));
    if (n) {
      for (uint32_t *p = (uint32_t*)out.data(); n--; *p++ = m_values++)
	;
      return RCC_ADVANCE;
    }
    out.setEOF();
    return RCC_ADVANCE_DONE;
  }
};

TEST_SOURCE_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
TEST_SOURCE_END_INFO
