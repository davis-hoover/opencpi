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
 * THIS FILE WAS ORIGINALLY GENERATED ON Fri Aug 31 13:40:06 2018 EDT
 * BASED ON THE FILE: copy_cc.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the copy_cc worker in C++
 */

#include "copy_cc-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Copy_ccWorkerTypes;

class Copy_ccWorker : public Copy_ccWorkerBase {
#if 1
  RCCResult run(bool /*timedout*/) {
    strcpy(out.data().mesg(), in.data().mesg());
    out.setLength(in.length());
    return RCC_ADVANCE;
  }
#else
  // This does not work yet - fix is in progress
  RunCondition m_rc;
public:
  Copy_ccWorker() : m_rc(1 <<  COPY_CC_IN, RCC_NO_PORTS) {
    setRunCondition(&m_rc);
  }
  RCCResult run(bool /*timedout*/) {
    out.send(in);
    return RCC_OK;
  }
#endif
};

COPY_CC_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
COPY_CC_END_INFO
