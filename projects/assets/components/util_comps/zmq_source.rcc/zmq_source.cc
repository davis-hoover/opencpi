/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Wed Feb 10 14:41:38 2021 CST
 * BASED ON THE FILE: zmq_receive.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the zmq_receive worker in C++
 */

#include "zmq_source-worker.hh"
#include <zmq.hpp>
#include "OcpiOsDebugApi.hh" // OCPI_LOG_INFO

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Zmq_sourceWorkerTypes;

class Zmq_sourceWorker : public Zmq_sourceWorkerBase {

public:
  Zmq_sourceWorker(): m_context(NULL), m_socket(NULL) { }

private:
  zmq::context_t *m_context;
  zmq::socket_t  *m_socket;

  RCCResult start() {
    // If we are comming out of a suspended state, m_context and/or
    // m_socket could already be initialized, hence the NULL ptr checks
    if(!m_context) {
      m_context = new zmq::context_t(1);
    }

    
    if(!m_socket) {
      // FIXME - add different source types
      //if(properties().type == TYPE_PULL) {
      //  m_socket = new zmq::socket_t(*m_context, ZMQ_PULL);
      //} else if(properties().type == TYPE_SUB) {
      //  m_socket = new zmq::socket_t(*m_context, ZMQ_SUB);
      //} else {
      //  return RCC_FATAL;
      //}
      m_socket = new zmq::socket_t(*m_context, ZMQ_SUB);
    }

    m_socket->setsockopt(ZMQ_SUBSCRIBE,"",0);
    m_socket->setsockopt(ZMQ_LINGER, 0);
    m_socket->setsockopt(ZMQ_TCP_KEEPALIVE, 1);
    m_socket->setsockopt(ZMQ_TCP_KEEPALIVE_CNT, 60);
    m_socket->setsockopt(ZMQ_RCVTIMEO, 0);

    try{
      m_socket->connect(properties().address);
    } catch(zmq::error_t& e){
      log(OCPI_LOG_INFO, "zmq_source.rcc worker caught the following zmq connect error:");
      log(OCPI_LOG_INFO, e.what());
      return RCC_FATAL;
    }

    return RCC_OK;
  }

  RCCResult release() {
    if(m_socket) {
      m_socket->disconnect(properties().address);
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
    zmq::message_t message;

    try{
      // Receive data on zmq socket but don't block
	    bool incomingData = m_socket->recv(&message, ZMQ_NOBLOCK);
      if(!incomingData){
        // No Data on the socket just continue
        return RCC_OK;
      }

    } catch(zmq::error_t& e){
      if(e.num() == EAGAIN){
        // No Data on the socket just continue
        // This was never hit in testing but left in as a safety precaution
        return RCC_OK;

      } else {
         // An actual error occured print it and return fatal
         log(OCPI_LOG_INFO, "ZeroMQ receive failed with the following error: ");
         log(OCPI_LOG_INFO, e.what());
         return RCC_FATAL;
      }
    }
    log(OCPI_LOG_DEBUG, "Received ZMQ message of length: %zu bytes", message.size());

    output.setLength(message.size());
    memcpy((uint8_t *)output.data(), (uint8_t *)message.data(), message.size());

    return RCC_ADVANCE;
  }
}; // End of Zmq_sourceWorker class

ZMQ_SOURCE_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case
ZMQ_SOURCE_END_INFO