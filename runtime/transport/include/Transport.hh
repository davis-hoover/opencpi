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
 *   This file contains the Implementation for the OCPI transport.
 *
 * Revision History: 
 * 
 *    Author: John F. Miller
 *    Date: 1/2005
 *    Revision Detail: Created
 *
 */

#ifndef OCPI_DataTransport_Transport_H_
#define OCPI_DataTransport_Transport_H_

#include <vector>
#include <list>
#include "OsTimer.hh"
#include "OsMutex.hh"
#include "BaseParentChild.hh"
#include "TimeEmit.hh"
#include "UtilMisc.hh"
#include "XferException.hh"
#include "XferEndPoint.hh"
#include "TransportCircuit.hh"
#include "TransportConstants.hh"
#include "TransportManager.hh"

namespace OCPI {
  namespace Transport {

    class Circuit;

    // New circuit request listener
    class NewCircuitRequestListener {

    public:

      /**********************************
       * This method gets called when a new circuit is available and ready for use
       *********************************/
      virtual void newCircuitAvailable( Circuit* new_circuit ) = 0;

      /**********************************
       * This method gets called when an error gets generated
       *********************************/
      //      virtual void error( OCPI::Util::EmbeddedException& ex ) = 0;

      virtual ~NewCircuitRequestListener(){}

    };
    
    /**********************************
     * Constant definitions
     *********************************/
    const OCPI::OS::uint32_t NewConnectionFlag = 0x01;
    const OCPI::OS::uint32_t SendCircuitFlag   = 0x02;
    const OCPI::OS::uint32_t RcvCircuitFlag    = 0x04;

    class Transport : public OCPI::Util::Parent<Circuit> , public OCPI::Time::Emit

    {
    public:

      friend class Circuit;

      /**********************************
       * Constructors
       *********************************/
      Transport(TransportManager *tpg, bool uses_mailboxes, OCPI::Time::Emit *parent);
      Transport(TransportManager *tpg, bool uses_mailboxes);

      /**********************************
       * Destructor
       *********************************/
      virtual ~Transport();      

      void cleanForContext(void *context);
      OCPI::Xfer::EndPoint &addRemoteEndPoint( const char* ep );
      bool                        isLocalEndpoint(const OCPI::Xfer::EndPoint &ep) const;
      OCPI::Xfer::EndPoint* getEndpoint(const char* ep, bool local);
      // void                        removeLocalEndpoint(  const char* ep );
      OCPI::Xfer::EndPoint &getLocalCompatibleEndpoint(const char *ep, bool exclusive = false);
      //      OCPI::Xfer::EndPoint &getLocalEndpointFromProtocol(const char *ep);
      OCPI::Xfer::EndPoint &getLocalEndpoint(const char *ep);


      /**********************************
       * Creates a new circuit within a connection based upon the source
       * Port set and destibnation ports set(s)
       *********************************/
      // ports in the connection are used.
      Circuit * createCircuit(CircuitId cid, // when zero, allocate one
			      OCPI::Xfer::EndPoint *outEp, Descriptors *outDesc,
			      OCPI::Xfer::EndPoint *inEp,
			      unsigned bufCount, unsigned bufLen,
                              uint32_t flags = 0,
			      const char *protocol = NULL,
			      OCPI::OS::Timer *timer = 0);

      // ports in the connection are used.
      //Circuit * createCircuit( OCPI::Xfer::EndPoint *ep );

      // Initialize descriptor from endpoint info
      static void fillDescriptorFromEndPoint(OCPI::Xfer::EndPoint &ep,
					     Descriptors &desc);
      // Use this one when you know there is only one input port
      Port * createInputPort(Descriptors& desc,
			     const OCPI::Base::PValue *params = NULL);
      // Use this one when you know there is only one output port
      // And the input port is remote
      Port * createOutputPort(Descriptors& outputDesc,
			      const Descriptors& inputDesc );
      // Use this when you are connecting the new outport to 
      // a local input port.
      Port * createOutputPort(Descriptors& outputDesc,
			      Port& inputPort );


      /**********************************
       * Deletes a circuit
       *********************************/
      //      void deleteCircuit( CircuitId circuit );        
      void deleteCircuit( Circuit* circuit );        

      /**********************************
       * Retrieves the requested circuit
       *********************************/
      Circuit* getCircuit( CircuitId circuit_id );
      size_t getCircuitCount();

      /**********************************
       * General house keeping 
       *********************************/
      void dispatch(OCPI::Xfer::EventManager* event_manager=NULL);
      //      std::vector<std::string> getListOfSupportedEndpoints();

      /**********************************
       * Set the callback listener for new circuit requests on this transport
       *********************************/
      void setNewCircuitRequestListener( NewCircuitRequestListener* listener );


      /**********************************
       * Does this transport support mailboxes?
       *********************************/
      inline bool supportsMailboxes(){return m_uses_mailboxes;}
      void setListeningEndpoint( OCPI::Xfer::EndPoint* ep){m_CSendpoint=ep;}

    protected:

      /**********************************
       * This method gets the Node-wide mutex used to lock our mailbox
       * on the specified endpoint for mailbox communication
       *********************************/
      OCPI::OS::Mutex* getMailBoxLock( const char* mbid );

      /**********************************
       * Clear remote mailbox
       *********************************/
      void clearRemoteMailbox(size_t offset, OCPI::Xfer::EndPoint* loc );

      /**********************************
       * Send remote port our offset information
       *********************************/
      void sendOffsets( OCPI::Util::VList& offsets, OCPI::Xfer::EndPoint &ep,
			size_t extraSize = 0, OCPI::Xfer::Offset extraFrom = 0,
			OCPI::Xfer::Offset extraTo = 0);

      /**********************************
       * Request a new connection
       *********************************/
      void requestNewConnection( Circuit* circuit, bool send, const char *protocol, OCPI::OS::Timer *timer);

    private:
      void init();

      /**********************************
       * Our mailbox handler
       *********************************/
      void checkMailBoxes();

      // List of interprocess mutex's that we use to lock mailboxes
      OCPI::Util::VList m_mailbox_locks;

      // mailbox support
      bool                               m_uses_mailboxes;

      // These are the endpoints we own. the local list is initialized with 
      // an allocated endpoint for each driver
      OCPI::Xfer::EndPoints m_localEndpoints, m_remoteEndpoints;

      // List of circuits
      std::list<Circuit*> m_circuits;
      typedef std::list<Circuit*>::iterator CircuitsIter;

      // New circuit listener
      NewCircuitRequestListener* m_newCircuitListener;

      // Our lock
      OCPI::OS::Mutex &m_mutex;

      // used to name circuits
      OCPI::OS::uint32_t m_nextCircuitId;
      OCPI::Xfer::EndPoint*  m_CSendpoint;
      ContainerComms *m_CScomms;

      // Cached transfer list
      static OCPI::Util::VList  m_cached_transfers;
      static OCPI::Util::VList   active_transfers;

    public:
      TransportManager *m_transportManager;
    };

  }
}


#endif


