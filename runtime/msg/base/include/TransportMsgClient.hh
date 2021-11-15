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
 * Abstract:
 *   This file contains the Interface for the Ocpi transport client class.
 *
 * Author: John F. Miller
 *
 * Date: 3/1/05
 *
 */

#ifndef OCPI_Transport_Client_H_
#define OCPI_Transport_Client_H_

#include "OsTimer.hh"
#include "UtilList.hh"
#include <string>
#include "Transport.hh"
#include "TransportIntEventHandler.hh"
#include "TransportMsgThreadHook.hh"
#include "TransportMsgCircuit.hh"


namespace OCPI {
  namespace Msg {
  
    /**********************************
     * This is the class that is used to implement a server event callback handler
     **********************************/
    class ClientEventHandler
    {
    public:

      /**********************************
       *  This method gets called when data is available on a circuit
       **********************************/        
      virtual void dataAvailable( MessageCircuit* circuit ) = 0;

      /**********************************
       * This method gets called when an error gets generated
       *********************************/
      virtual void error( OCPI::Util::EmbeddedException& ex ) = 0;

      virtual ~ClientEventHandler(){};

    };


    /**********************************
     * This class is used in conjuction with the OCPI transport to create a client circuit
     **********************************/
    class CTransportControl;
    class Client : public ThreadHook
    {

    public:

      friend class CTransportControl;


      /**********************************
       *  Constructors
       **********************************/
      Client( std::string&     our_end_point, // In - endpoint
              int             buffer_size,       // In - Buffer size in bytes
              ClientEventHandler* cb = NULL     // In - Client event handler
              );

      /**********************************
       *  Create/connect (via a new circuit): return true if timedout
       **********************************/
      bool connect( std::string& server_end_point, OCPI::OS::ElapsedTime delay = 0);
      inline OCPI::DataTransport::BufferUserFacet *getNextInputBuffer(void *&data, uint32_t &length) {
	return m_circuit ? m_circuit->getNextInputBuffer(data, length) : NULL;
      }
      inline void freeBuffer(OCPI::DataTransport::BufferUserFacet *buffer) {
	if (m_circuit)
	  m_circuit->freeBuffer(buffer);
      }
      /**********************************
       *  Dispatch control, this method needs to be called periodically to provide 
       * the client class with houskeeping time.
       **********************************/
      inline void dispatch(DataTransfer::EventManager* eh=NULL);

      /**********************************
       *  Remove a message circuit
       **********************************/
      void remove( MessageCircuit* circuit );


      /**********************************
       *  Destructor
       **********************************/
      virtual ~Client();


      // Our exception monitor class
      //      OCPI::Util::ExceptionMonitor m_exceptionMonitor;

      // Message circuits
      OCPI::Util::VList m_circuits;

      // Thread control flag
      bool runThreadFlag;

    protected:


      /**********************************
       *  local init
       **********************************/
      void init(DataTransfer::SMBResources* res);

      // our event handler
      //      ClientEventHandler* m_event_handler;

      // buffer count
      int m_buffer_size;

      // Ocpi transport 
      OCPI::DataTransport::Transport* m_transport;

      // Init flag
      bool m_init;

      // Our location
      std::string m_endpoint_string;
      DataTransfer::EndPoint* m_end_point;

      // Total number of connections
      static int m_count;

      // Thread safe control
      OCPI::OS::Mutex* m_mutex;

      // Transport controller
      // CTransportControl* m_transport_controller;
      MessageCircuit *m_circuit;
    };

    /**********************************
     ****
     * inline declarations
     ****
     *********************************/

  }
}

#endif

