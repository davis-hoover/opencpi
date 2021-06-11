/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Fri Jun  4 11:29:18 2021 CDT
 * BASED ON THE FILE: test_worker3.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the test_worker3 worker in C++
 */

#include "test_worker3-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Test_worker3WorkerTypes;

class Test_worker3Worker : public Test_worker3WorkerBase {
  RCCResult run(bool /*timedout*/) {
    return RCC_DONE; // change this as needed for this worker to do something useful
    // return RCC_ADVANCE; when all inputs/outputs should be advanced each time "run" is called.
    // return RCC_ADVANCE_DONE; when all inputs/outputs should be advanced, and there is nothing more to do.
    // return RCC_DONE; when there is nothing more to do, and inputs/outputs do not need to be advanced.
  }
};

TEST_WORKER3_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case
TEST_WORKER3_END_INFO
