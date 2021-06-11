/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Fri Jun  4 11:28:51 2021 CDT
 * BASED ON THE FILE: atest.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the atest worker in C++
 */

#include "atest-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace AtestWorkerTypes;

class AtestWorker : public AtestWorkerBase {
  // notification that initial property has been written
  RCCResult initial_written() {
    return RCC_OK;
  }
  // notification that readonlyvolatile property will be read
  RCCResult readonlyvolatile_read() {
    return RCC_OK;
  }
  // notification that winitial property has been written
  RCCResult winitial_written() {
    return RCC_OK;
  }
  // notification that wreadonlyvolatile property will be read
  RCCResult wreadonlyvolatile_read() {
    return RCC_OK;
  }
  RCCResult run(bool /*timedout*/) {
    return RCC_DONE; // change this as needed for this worker to do something useful
    // return RCC_ADVANCE; when all inputs/outputs should be advanced each time "run" is called.
    // return RCC_ADVANCE_DONE; when all inputs/outputs should be advanced, and there is nothing more to do.
    // return RCC_DONE; when there is nothing more to do, and inputs/outputs do not need to be advanced.
  }
};

ATEST_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case
ATEST_END_INFO
