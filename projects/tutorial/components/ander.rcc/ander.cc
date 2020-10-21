/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Mon Sep 14 15:59:04 2020 EDT
 * BASED ON THE FILE: ander.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the ander worker in C++
 */

#include "ander-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace AnderWorkerTypes;

class AnderWorker : public AnderWorkerBase {
  size_t in1Left, in2Left;
  const int16_t *in1p, *in2p;
public:
  AnderWorker() : in1Left(0), in2Left(0) {}
private:
  RCCResult run(bool /*timedout*/) {
    if (!in1Left) {
      in1Left = in1.data().real().size();
      in1p = in1.data().real().data();
    }
    if (!in2Left) {
      in2Left = in2.data().real().size();
      in2p = in2.data().real().data();
    }

    size_t outLeft = out.iq().data().capacity();
    for (IqstreamIqData *outp = out.iq().data().data();
	 outLeft && in1Left && in2Left; --outLeft, ++outp, --in1Left, ++in1p, --in2Left, ++in2p) {
      outp->I = *in1p & *in2p;
      outp->Q = *in1p;
    }
    if (!in1Left)
      in1.advance();
    if (!in2Left)
      in2.advance();
    out.iq().data().resize(out.iq().data().capacity() - outLeft);
    out.advance();
    return RCC_OK;
  }
};

ANDER_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
ANDER_END_INFO
