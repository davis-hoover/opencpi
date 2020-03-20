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
 * THIS FILE WAS ORIGINALLY GENERATED ON Thu Jun  6 16:48:41 2019 EDT
 * BASED ON THE FILE: zmq_sink.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the zmq_sink worker in C++
 */

#include "zmq_sink-worker.hh"
#include "zmq.hpp"
#include <cstdint>
#include "OcpiOsDebugApi.hh" // OCPI_LOG_INFO

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Zmq_sinkWorkerTypes;

class Zmq_sinkWorker : public Zmq_sinkWorkerBase {

public:
  Zmq_sinkWorker(): m_context(NULL), m_socket(NULL) { }
private:
  RCCResult start() {

    RCCResult ret = RCC_OK;

    // If we are comming out of the Suspended state, m_context and/or
    // m_socket could already be initialized, hence the NULL ptr checks
    if(!m_context) {
      m_context = new zmq::context_t(1);
    }

    if(!m_socket) {
      if(properties().type == TYPE_PUSH) {
        m_socket = new zmq::socket_t(*m_context, ZMQ_PUSH);
      } else if(properties().type == TYPE_PUB) {
        m_socket = new zmq::socket_t(*m_context, ZMQ_PUB);
      } else {
        ret = RCC_FATAL;
      }
    
      if(ret == RCC_OK) {

        int optval = 0;
        m_socket->setsockopt(ZMQ_LINGER,   &optval, sizeof(optval));
        m_socket->setsockopt(ZMQ_SNDTIMEO, &optval, sizeof(optval));

        m_socket->bind(properties().address);
      }
    }

    return ret;
  }
  RCCResult release() {

    if(m_socket) {
      m_socket->close();
      delete m_socket;
      m_socket = NULL;
    }

    if(m_context) {
      delete m_context;
      m_context = NULL;
    }

    return RCC_OK;
  }
  RCCResult run(bool /*timedout*/) {

    RCCResult ret = RCC_OK;

    try {

      if(in.eof()) {
        // UNDOCUMENTED / SUBJECT TO CHANGE - OCPI_LOG_INFO
        log(OCPI_LOG_INFO, "saw EOF in input");

        ret = RCC_DONE;
      }
    
      if(ret == RCC_OK) {
        zmq::message_t msg(in.length());
        size_t msg_size = msg.size();
        memcpy((uint8_t *)msg.data(), (uint8_t *)in.data(), in.length());
        m_socket->send(msg);

        // UNDOCUMENTED / SUBJECT TO CHANGE - OCPI_LOG_INFO
        log(OCPI_LOG_INFO, "sent ZMQ message of length: %zu bytes", msg_size);

        in.advance();
      }
    } catch(...) {

      // UNDOCUMENTED / SUBJECT TO CHANGE - OCPI_LOG_INFO
      log(OCPI_LOG_INFO, "zmq_sink.rcc worker caught exception!");

      ret = RCC_FATAL;
    }

    return ret;
  }

  zmq::context_t *m_context;
  zmq::socket_t  *m_socket;
};

ZMQ_SINK_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
ZMQ_SINK_END_INFO
