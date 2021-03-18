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

// This file declares the controller interface
// Controllers setup and manage data movement between port set pairs

#ifndef OCPI_DataTransport_Controller_H_
#define OCPI_DataTransport_Controller_H_

#include "OcpiUtilMisc.h"
#include "TransportTransfer.hh"
#include "OcpiBuffer.h"
#include "OcpiOutputBuffer.h"
#include "OcpiUtilRefCounter.h"

namespace DataTransfer {
  class XferRequest;
}
namespace OCPI {
namespace DataTransport {

class Port;
class Transport;

//  This is the controller base class, with a mix of pure virtual methods and default virtual methods
class Controller {
public:
  enum TransferType {
    OUTPUT,
    INPUT
  };
private:
  unsigned  m_FillQPtr;
  unsigned  m_EmptyQPtr;
  // Each PortPair struct has the transfers between that output-to-input pair
  struct OutPort2InPort {
    std::vector<Transfer *> m_outputTransfers, m_outputBroadcastTransfers;
    std::vector<Transfer *> m_inputTransfers, m_inputBroadcastTransfers;
  };
  std::vector<OutPort2InPort> m_inPort2outPort;

protected:
  PortSet   &m_output;
  PortSet   &m_input;
  unsigned  m_nextTid;  // Next input temporal id
  bool      m_zcopyEnabled;
  bool      m_isWholeOutputSet;

public:
  Controller(PortSet &output, PortSet &input);
  virtual ~Controller();

  //================================================================================
  // Setup methods
  void init(); // must be called after constructor returns
  std::vector<Transfer *> &getTransfers(unsigned outPort, unsigned outBuffer, unsigned inPort, unsigned inBuffer,
					bool broadcast, TransferType inout) {
    (void)outBuffer;(void)inBuffer;
    assert(outPort < m_output.getPortCount() && inPort < m_input.getPortCount() &&
	   outBuffer < m_output.getBufferCount() && inBuffer < m_input.getBufferCount());
    auto &out2in = m_inPort2outPort[outPort * m_input.getPortCount() + inPort];
    return broadcast ?
      (inout == OUTPUT ? out2in.m_outputBroadcastTransfers : out2in.m_inputBroadcastTransfers) :
      (inout == OUTPUT ? out2in.m_outputTransfers : out2in.m_inputTransfers);
  }
protected:
  inline Transfer &
  getTemplate(unsigned outPort, unsigned outBuffer, unsigned inPort, unsigned inBuffer,
	      bool broadcast, TransferType inout) {
    return
      *getTransfers(outPort, outBuffer, inPort, inBuffer, broadcast, inout)
      [outBuffer * m_input.getBufferCount() + inBuffer];
  }
  inline void
  setTemplate(Transfer &temp, unsigned outPort, unsigned outBuffer, unsigned inPort,
	      unsigned inBuffer, bool broadcast = false, TransferType inout = OUTPUT) {
    getTransfers(outPort, outBuffer, inPort, inBuffer, broadcast, inout)
      [outBuffer * m_input.getBufferCount() + inBuffer] = &temp;
  }
  virtual void createInputTransfers(Port &input);
  virtual void createOutputTransfers(Port &output) = 0; // no default
  virtual void createOutputBroadcastTemplates(Port &output);
  virtual void createInputBroadcastTemplates(Port &input);

  //================================================================================
  // Runtime methods


  // indicate that a buffer has been filled.
  // Since we manage circular buffers, the actual buffer is implied (next)
  //  virtual void bufferFull(OCPI::DataTransport::Port *port);

  // indicate that a remote input buffer has been freed.
  // Since we manage circular buffers, the actual buffer is implied (next)
  virtual void freeBuffer(OCPI::DataTransport::Port *port);



  // determine if we can produce from the indicated buffer
  virtual bool canBroadcast(Buffer *buffer);

  // determine if we have the output barrier token
  virtual bool haveOutputBarrierToken(OutputBuffer */*src_buf*/) { return true; }

  // initiate a broadcastdata transfer from the output buffer.
  virtual void broadCastOutput(Buffer *buffer);

public:
  // determine if we can produce from the indicated buffer
  virtual bool canProduce(Buffer *buffer) = 0;
  // determine if a transfer can be started while a previous transfer is queued.
  virtual bool canTransferBufferWhileOthersAreQueued() { return false; }
  // initiate a data transfer from the output buffer.
  // If the transfer can take place, it will be initiated, if not it will be queued in the circuit.
  virtual unsigned produce(Buffer *buffer, bool broadcast = false) = 0;
  // mark the input buffer as "Empty" and informs interested outputs that the input is now available.
  virtual Buffer* consume(Buffer *buffer) = 0;
  // determine if there is data available, but does not affect the state of the object.
  virtual bool hasFullInputBuffer(OCPI::DataTransport::Port *, InputBuffer **) const;
  // determine if there is an available buffer, but does not affect the
  virtual bool hasEmptyOutputBuffer(OCPI::DataTransport::Port *port) const;
  // get the next available buffer from the specified output port
  virtual Buffer* getNextEmptyOutputBuffer(OCPI::DataTransport::Port *src_port);
  // get the next available buffer from the specified input port
  virtual Buffer* getNextFullInputBuffer(OCPI::DataTransport::Port *input_port);
  // indicate that all remote input buffer has been emptied.
  virtual void freeAllBuffersLocal(OCPI::DataTransport::Port *port);
  // mark the input buffer as "Empty" and informs interested outputs that the input is now available.
  virtual void consumeAllBuffersLocal(OCPI::DataTransport::Port *port);
  virtual void modifyOutputOffsets(Buffer *me, Buffer *new_buffer, bool reverse);

};

Controller &controllerNotSupported(PortSet &output, PortSet &input);

template<class TheController>
Controller &
createController(PortSet &output, PortSet &input) {
  TheController &tc = *new TheController(output, input);
  // This must be after the constructor
  tc.init();
  return tc;
}

//  This controller is used for the following patterns: WP/PW
class Controller1 : public Controller {
public:
  virtual ~Controller1(){};
  Controller1(PortSet &output, PortSet &input)
    : Controller(output, input){}
  void createOutputTransfers(Port &s_port);
  // determine if we can produce from the indicated buffer
  bool canProduce(Buffer *buffer);
  // initiate a data transfer from the output buffer.
  // If the transfer can take place, it will be initiated, if not it will be queued in the circuit.
  unsigned produce(Buffer *buffer, bool bcast = false);
  // mark the input buffer as "Empty" and informs all interested outputs that
  // the input is now available.
  Buffer *consume(Buffer *buffer);
};

// This controller is used for pattern1 when either the output or input port(s) are  ActiveFlowControl
class Controller1AFCShadow : public Controller1 {
public:
  virtual ~Controller1AFCShadow(){};
  Controller1AFCShadow(PortSet &output, PortSet &input)
    : Controller1(output, input){}
  void createOutputTransfers(Port &s_port);
  // get the next available buffer from the specified input port
  Buffer* getNextFullInputBuffer(Port *input_port);
  // determine if there is data available, but does not affect the state of the object.
  bool hasFullInputBuffer(Port * port, InputBuffer**) const;
  // determine if we can produce from the indicated buffer
  bool canProduce(Buffer *buffer);
  // initiate a data transfer from the output buffer.  If the transfer can take place,
  // it will be initiated, if not it will be queued in the circuit.
  unsigned produce(Buffer *buffer, bool bcast = false);
  void modifyOutputOffsets(Buffer *me, Buffer *new_buffer, bool reverse);
  // mark the input buffer as "Empty" and informs all interested outputs that
  // the input is now available.
  Buffer *consume(Buffer *buffer);
};
// This controller is used for pattern1 when either the output or input port(s) are  ActiveFlowControl
class Controller1AFC : public Controller1AFCShadow {
public:
  Controller1AFC(PortSet &output, PortSet &input)
    : Controller1AFCShadow(output, input){}
  void createInputTransfers(Port &s_port);
  void createOutputTransfers(Port &s_port);

};
#if 0
// This controller is used for pattern1 when either the output or input port(s) are Passive
class Controller1Passive : public Controller1 {
public:
  virtual ~Controller1Passive(){};
  Controller1Passive(PortSet &output, PortSet &input);
  // get the next available buffer from the specified input port
  Buffer *getNextFullInputBuffer(Port *input_port);
  // determine if there is data available, but does not affect the state of the object.
  bool hasFullInputBuffer(Port *port, InputBuffer **) const;
  // determine if we can produce from the indicated buffer
  bool canProduce(Buffer *buffer);
  // initiate a data transfer from the output buffer.  If the transfer can take place,
  // it will be initiated, if not it will be queued in the circuit.
  unsigned produce(Buffer *buffer, bool bcast = false);
  void modifyOutputOffsets(Buffer *me, Buffer *new_buffer, bool reverse);
  // mark the input buffer as "Empty" and informs all interested outputs that
  // the input is now available.
  Buffer *consume(Buffer* buffer);
};
#endif
// This controller is used for the following patterns:  WP/S(lb)W
class Controller2 : public Controller {
  OCPI::DataTransport::Port *m_inputPort; // Port to produce to
public:
  Controller2(PortSet &output, PortSet &input);
  virtual ~Controller2(){};
  void createOutputTransfers(Port &s_port);
  virtual void addTransferPreState(DataTransfer::XferRequest *pt, Port &s_port,
				   unsigned s_tid, Port &t_port, unsigned t_tid);
  // determine if we can produce from the indicated buffer
  bool canProduce(Buffer * buffer);
  // initiate a data transfer from the output buffer.  If the transfer can take place,
  // it will be initiated, if not it will be queued in the circuit.
  unsigned produce(Buffer *buffer, bool bcast = false);
  // mark the input buffer as "Empty" and informs all interested outputs that
  // the input is now available.
  Buffer *consume(Buffer *buffer);
  // get the next available buffer from the specified input port
  Buffer *getNextFullInputBuffer(Port* input_port);
};

// This controller is used for the following patterns: WS(rr)/S(lb)W
class Controller3 : public Controller2 {
public:
  Controller3(PortSet &output, PortSet &input)
    : Controller2(output, input){}
  virtual ~Controller3(){};
  void addTransferPreState(DataTransfer::XferRequest* pt, Port &s_port, unsigned s_tid,
			   Port &t_port, unsigned t_tid);
  // determine if a transfer can be started while a previous transfer is queued.
  bool canTransferBufferWhileOthersAreQueued() {return false;}
  // determine if we have the output barrier token
  bool haveOutputBarrierToken(OutputBuffer *src_buf) {
    return src_buf->getControlBlock()->sequentialControlToken == src_buf->getPort()->getPortId();
  }
};

// Controller pattern 4, used for the following patterns:  WP/P(Parts)
class Controller4 : public Controller1 {
  // Inform all ports when an end of whole has been reached
  bool m_markEndOfWhole;
public:
  Controller4(PortSet &output, PortSet &input)
    : Controller1(output, input), m_markEndOfWhole(true) {}
  virtual ~Controller4(){};
  void createOutputTransfers(Port &s_port);
  // determine if we can produce from the indicated buffer
  bool canProduce(Buffer * buffer);
  // initiate a data transfer from the output buffer.  If the transfer can take place,
  // it will be initiated, if not it will be queued in the circuit.
  unsigned produce(Buffer *buffer, bool bcast = false);
  // get the next available buffer from the specified input port
  Buffer *getNextFullInputBuffer(Port *input_port);
};

} // namespace DataTransport
} // namespace OCPI

#define FORMAT_TRANSFER_EC_RETHROW(sep, tep)			 \
  throw OCPI::Util::Error("UNABLE_TO_CREATE_TX_REQUEST: %s->%s", \
			  (tep)->getEndPoint().name().c_str(),	 \
			  (sep)->getEndPoint().name().c_str());

#endif
