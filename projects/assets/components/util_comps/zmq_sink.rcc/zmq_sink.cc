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
#include "OcpiOsDebugApi.hh" // OCPI_LOG_INFO

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Zmq_sinkWorkerTypes;

class Zmq_sinkWorker : public Zmq_sinkWorkerBase {

public:
  Zmq_sinkWorker(): m_context(NULL), m_socket(NULL) { }

private:
  zmq::context_t *m_context;
  zmq::socket_t  *m_socket;

  RCCResult start() {
    // If we are comming out of the Suspended state, m_context and/or
    // m_socket could already be initialized, hence the NULL ptr checks
    if(!m_context) {
      m_context = new zmq::context_t(1);
    }

    if(!m_socket) {
      // FIXME - add different sink types
      //if(properties().type == TYPE_PUSH) {
      //  m_socket = new zmq::socket_t(*m_context, ZMQ_PUSH);
      //} else if(properties().type == TYPE_PUB) {
      //  m_socket = new zmq::socket_t(*m_context, ZMQ_PUB);
      //} else {
      //  return RCC_FATAL;
      //}
      m_socket = new zmq::socket_t(*m_context, ZMQ_PUB);
    }

    m_socket->setsockopt(ZMQ_LINGER, 0);
    m_socket->setsockopt(ZMQ_SNDTIMEO, 0);

    try{
      m_socket->bind(properties().address);
    } catch(zmq::error_t& e){
      log(OCPI_LOG_INFO, "zmq_sink.rcc worker caught the following zmq bind error:");
      log(OCPI_LOG_INFO, e.what());
      return RCC_FATAL;
    }

    return RCC_OK;
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

    if(input.eof()) {
      log(OCPI_LOG_INFO, "saw EOF in input");

      return RCC_DONE;
    }

    // Construct zmq message from input
    zmq::message_t message(input.length());
    memcpy((uint8_t *)message.data(), (uint8_t *)input.data(), input.length());

    try {
      // Send zmq message
      m_socket->send(message);
      log(OCPI_LOG_DEBUG, "Sent ZMQ message of length: %zu bytes", message.size());

    } catch(zmq::error_t& e){
      log(OCPI_LOG_INFO, "zmq_sink.rcc worker caught the following zmq send error:");
      log(OCPI_LOG_INFO, e.what());
      return RCC_FATAL;
    }

    return RCC_ADVANCE;
  }

}; // End of Zmq_sinkWorker class

ZMQ_SINK_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
ZMQ_SINK_END_INFO
