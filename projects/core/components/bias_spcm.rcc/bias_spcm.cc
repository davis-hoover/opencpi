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
 * THIS FILE WAS ORIGINALLY GENERATED ON Thu Jun  5 21:24:44 2014 EDT
 * BASED ON THE FILE: bias_cc.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the bias_cc worker in C++
 */

#include "OcpiApi.hh"
#include "bias_spcm-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants

class Bias_spcmWorker : public Bias_spcmWorkerTypes::Bias_spcmWorkerBase {
  RCCResult run(bool /*timedout*/) {
    const uint32_t *inData  = in.data().data().data();   // data arg of data message at "in" port
    uint32_t *outData = out.data().data().data();  // same at "out" port

#if 0 // no good for remote execution of unit test.
    // FIXME:  We need to prevent such workers from executing remotely
    static int x = 0;
    if (!x) {
      OCPI::API::Application &app = getApplication(); // test this method
      std::string name, value;
      fprintf(stderr, "Dump of all initial property values:\n");
      for (unsigned n = 0; app.getProperty(n, name, value); n++)
	fprintf(stderr, "Property %2u: %s = \"%s\"\n", n, name.c_str(), value.c_str());
      x = 1;
    }
#endif
    out.checkLength(in.length());               // make sure input will fit in output buffer
    for (unsigned n = in.data().data().size(); n; n--) // n is length in sequence elements of input
      *outData++ = *inData++ + properties().biasValue;
    out.setInfo(in.opCode(), in.length());      // Set the metadata for the output message
    return RCC_ADVANCE; // yes, let ZLMs through, like other BIAS workers
    // return in.length() ? RCC_ADVANCE : RCC_ADVANCE_DONE;
  }
  // notification that t1 property will be read
  RCCResult t1_read() {
    return RCC_OK;
  }
};

BIAS_SPCM_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
BIAS_SPCM_END_INFO
