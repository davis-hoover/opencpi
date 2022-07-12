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
 * THIS FILE WAS ORIGINALLY GENERATED ON Sun Aug 10 16:57:14 2014 EDT
 * BASED ON THE FILE: proxy.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the proxy worker in C++
 */

#include "proxy0-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Proxy0WorkerTypes;

class Proxy0Worker : public Proxy0WorkerBase {
  RunCondition m_aRunCondition;
public:
  Proxy0Worker() : m_aRunCondition(RCC_NO_PORTS) {
    //Run function should never be called
    setRunCondition(&m_aRunCondition);
  }
private:
  RCCResult start() {
    slave.start();
    return RCC_OK;
  }
  RCCResult run(bool /*timedout*/) {
    return RCC_DONE;
  }
};

PROXY0_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
PROXY0_END_INFO
