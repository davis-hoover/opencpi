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
 *   This file contains the Interface for the OCPI port.
 *
 * Revision History: 
 * 
 *    Author: John F. Miller
 *    Date: 1/2005
 *    Revision Detail: Created
 *
 */

#ifndef OCPI_DataTransport_Port_H_
#define OCPI_DataTransport_Port_H_

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits>
#include "UtilList.hh"
#include "BaseParentChild.hh"
#include "TimeEmit.hh"
#include "XferEndPoint.hh"
#include "XferFactory.hh"
#include "XferServices.hh"
#include "TransportRDTInterface.hh"
#include "TransportConstants.hh"
#include "TransportPortMetaData.hh"
#include "TransportPortSet.hh"
#include "TransportBuffer.hh"


namespace OCPI {

  namespace Transport {

    typedef size_t BufferOrdinal;
    const size_t MAXBUFORD = std::numeric_limits<std::size_t>::max();
    class PullDataDriver;
    class PortSet;
    class Buffer;
    class OutputBuffer;
    class InputBuffer;
    class Circuit;

    // This is the OCPI specialized port class definition
    class Port :  public OCPI::Util::Child<PortSet,Port>, 	
      public OCPI::Time::Emit
    {
      // The templates this port has a ref count on.
      OCPI::Xfer::TemplateMap m_templates;

    public:

      friend class Circuit;

      /**********************************
       * Constructors
       *********************************/
      Port( PortMetaData* data, PortSet* ps );

      /**********************************
       * Destructor
       *********************************/
      virtual ~Port();


      // Get and cache and addref a template.
      OCPI::Xfer::XferServices &
      getTemplate(OCPI::Xfer::EndPoint &source, OCPI::Xfer::EndPoint &target);

      /**********************************
       * Advance the ports buffer 
       *********************************/
      void advance( Buffer* buffer, unsigned int len=0);


      /**********************************
       * Get port descriptor.  This is the data that is needed by an
       * external port to connect to this port.
       *********************************/
      void getPortDescriptor(Descriptors & my_desc, const Descriptors * other );



      /**********************************
       * This method determines if there is an empty output buffer, but does not affect the
       * state of the object.
       *********************************/
      bool hasEmptyOutputBuffer();



      /**********************************
       * This method determines if there is data available, but does not affect the
       * state of the object.
       *********************************/
      bool hasFullInputBuffer();


      /**********************************
       * Reteives the next available input buffer.
       *********************************/
      BufferUserFacet* getNextFullInputBuffer(uint8_t *&data, size_t &length, uint8_t &opcode, bool &end);
      // For use by bridge ports
      BufferUserFacet* getNextEmptyInputBuffer(uint8_t *&data, size_t &length);
      //      void sendInputBuffer(BufferUserFacet &b, size_t length, uint8_t opcode);

      /**********************************
       * This method retreives the next available buffer from the local (our)
       * port set.  A NULL port indicates local context.
       *********************************/
      Buffer* getNextEmptyOutputBuffer();
      BufferUserFacet* getNextEmptyOutputBuffer(uint8_t *&data, size_t &length);
      // For use by bridge ports
      //      BufferUserFacet* getNextFullOutputBuffer(uint8_t *&data, size_t &length, uint8_t &opcode);
      void releaseOutputBuffer(BufferUserFacet &b);
      /**********************************
       * Get the port dependency data
       *********************************/
      PortMetaData::OcpiPortDependencyData& getPortDependencyData();

      /**********************************
       * Finalize the port
       *********************************/
      virtual const Descriptors *
      finalize(const Descriptors *other, Descriptors &mine,
	       Descriptors *flow, bool &done);
      bool isFinalized(); 

      /**************************************
       * Get the buffer by index
       ***************************************/
      inline Buffer* getBuffer( BufferOrdinal index ){return m_buffers[index];}
      OutputBuffer* getOutputBuffer(BufferOrdinal idx);
      InputBuffer* getInputBuffer(BufferOrdinal idx);

      /**************************************
       * Are we a shadow port ?
       ***************************************/
      bool isShadow();

      /**************************************
       * Are we a Output port ?
       ***************************************/
      inline bool isOutput(){return m_data->output;}

      /**************************************
       * Get our ordinal id
       ***************************************/
      inline PortOrdinal getPortId(){return m_data->id;}

      /**************************************
       * Debug dump
       ***************************************/
      void debugDump();

      /**************************************
       * Get buffer count
       ***************************************/
      BufferOrdinal getBufferCount();
      size_t getBufferLength();

      /**********************************
       * Get port data
       *********************************/
      inline PortMetaData* getMetaData(){return m_data;}

      /**********************************
       * Get our associated circuit
       *********************************/
      Circuit* getCircuit();


      /***********************************
       * This method is used to send an input buffer thru an output port with Zero copy, 
       * if possible.
       *********************************/
      void sendZcopyInputBuffer(BufferUserFacet& src_buf, size_t len, uint8_t op, bool end);

      /**********************************
       * This method causes the specified input buffer to be marked
       * as available.
       *********************************/
      int32_t inputAvailable( Buffer* input_buf );
      inline void releaseInputBuffer(BufferUserFacet *ib) { (void)inputAvailable(static_cast<Buffer*>(ib)); }

      /**********************************
       * Send an output buffer
       *********************************/
      void sendOutputBuffer(BufferUserFacet* buf, size_t length, uint8_t opcode,
			    bool end = false, bool data = true);


      // Advanced buffer management
    protected:
      /**********************************
       * Advance the ports circular buffer
       *********************************/
      void advance( uint64_t value );


    private:

      /**********************************
       * Internal port initialization
       *********************************/
      void initialize();

      /**********************************
       * This routine is used to allocate the Output buffer offsets
       **********************************/
      virtual void createOutputOffsets();

      /**********************************
       * This routine is used to allocate the input buffer offsets
       **********************************/
      virtual void createInputOffsets();

      /**********************************
       * This method invokes the appropriate buffer allocation routine
       **********************************/
      void allocateBufferResources();

      // Our intialized flag
      bool m_initialized;

      // This ports meta data
      PortMetaData* m_data;

      // Handshake port control
      volatile OutputPortSetControl* m_hsPortControl;

      // This routine creates our buffers from the meta-data
      void createBuffers();

      // Last buffer that was processed
      BufferOrdinal m_lastBufferTidProcessed;

      // Sequence number of last buffer that was transfered
      uint32_t m_sequence;

      // Are we a shadow port
      bool m_shadow;

      // Our busy factor
      uint32_t m_busyFactor;

      // End of stream indicator
      bool m_eos;

      // Our mailbox
      uint16_t m_mailbox;

      // Our port dependency data
      PortMetaData::OcpiPortDependencyData m_portDependencyData;

      // Offset into the SMB to our offsets
      OCPI::Util::ResAddr m_offsetsOffset;

      // used to cycle through buffers
      BufferOrdinal m_lastBufferOrd;
      // The ordinal used on the bridge side
      BufferOrdinal m_nextBridgeOrd;

      // This port is externally connected
      enum ExternalConnectState {
        NotExternal,
        WaitingForUpdate,
        WaitingForShadowBuffer,
        DefinitionComplete
      };
      ExternalConnectState m_externalState;

      // Our pull driver
      PullDataDriver* m_pdDriver;

      // Associated Port set
      PortSet* m_portSet;

      // Buffers
      //      int m_localBufferCount;
      uint32_t m_bufferCount;
      Buffer** m_buffers; // [MAX_BUFFERS];



      /**********************************
       * Sets the feedback descriptor for this port.
       *********************************/
      virtual void setFlowControlDescriptorInternal( const Descriptors& );


    public:
      // The following methods are public but are only used by internal port managment classes


      /**************************************
       * Attaches a pull data driver to this port
       ***************************************/
      void attachPullDriver( PullDataDriver* pd );
      PullDataDriver* getPullDriver();

      /**************************************
       * Get the ordinal of the last buffer 
       * processed
       ***************************************/
      BufferOrdinal &getLastBufferOrd();

      // List of zCopy buffers to send to 
      OCPI::Util::VList m_zCopyBufferQ;

      /**************************************
       * Get the next full input buffer
       ***************************************/
      BufferOrdinal& getLastBufferTidProcessed();

      /**************************************
       * Get the buffer transfer sequence
       ***************************************/
      uint32_t& getBufferSequence();

      /**********************************
       * Has an End Of Stream been detcted on this port
       *********************************/
      bool isEOS();
      void setEOS();
      void resetEOS();


      /**************************************
       * Reset the port
       ***************************************/
      void reset();


      // Get/Set rank for scaled ports
      inline void setRank( uint32_t r ){m_data->rank=r;}
      inline uint32_t getRank(){return m_data->rank;}


      /**********************************
       * Get/Set the SMB name
       *********************************/
      OCPI::Xfer::EndPoint &getEndPoint();
      OCPI::Xfer::EndPoint *checkEndPoint();
      OCPI::Xfer::EndPoint &getShadowEndPoint();
      OCPI::Xfer::EndPoint &getLocalEndPoint();
      void setEndpoint( std::string& ep );

      /**********************************
       * Determines of a port is ready to go
       *********************************/
      bool ready();

      /**********************************
       * Once the circuit definition is complete, we need to update each port
       *********************************/
      void update();

      /**********************************
       * writes buffer offsets to address
       *********************************/
      void writeOffsets( PortMetaData::BufferOffsets* offset );


      /**********************************
       * get buffer offsets to dependent data
       *********************************/
      struct ToFrom_ {
	OCPI::Xfer::Offset from_offset, to_offset;
      };
      typedef ToFrom_ ToFrom;
      void getOffsets(OCPI::Xfer::Offset to_base_offset, OCPI::Util::VList& offsets );
      void releaseOffsets( OCPI::Util::VList& offsets );


      /**********************************
       * Get the shared memory object
       *********************************/
      OCPI::Xfer::SmemServices* getRealShemServices();
      OCPI::Xfer::SmemServices* getShadowShemServices();
      OCPI::Xfer::SmemServices* getLocalShemServices();
      uint16_t                            getMailbox();

      /**********************************
       * Get this source port's control structure
       *********************************/
      volatile OutputPortSetControl* getOutputControlBlock();
      void setOutputControlBlock( volatile OutputPortSetControl* scb );

      /**********************************
       * Get the offsets to the other Output ports control structures within the circuit
       *********************************/
      OCPI::Xfer::Offset getPortHSControl(PortOrdinal id);


      /**********************************
       * Can these two ports support Zero Copy transfers
       *********************************/
      virtual bool supportsZeroCopy( Port* port );

      /**************************************
       * Sets this ports busy factor
       ***************************************/
      void setBusyFactor(uint32_t bf );
      uint32_t getBusyFactor();

      inline PortSet* getPortSet(){return m_portSet;}
      void addBuffer( Buffer* buf );
    };


    /**********************************
     ****
     * inline declarations
     ****
     *********************************/
    inline PortMetaData::OcpiPortDependencyData& Port::getPortDependencyData(){return m_portDependencyData;}
    inline uint32_t& Port::getBufferSequence(){return m_sequence;}
    inline bool Port::isShadow(){return m_shadow;}
    inline BufferOrdinal &Port::getLastBufferTidProcessed(){return m_lastBufferTidProcessed;}
    inline OCPI::Xfer::EndPoint &Port::getEndPoint(){
      ocpiAssert(m_data->m_real_location);
      return *m_data->m_real_location;
    }
    inline OCPI::Xfer::EndPoint *Port::checkEndPoint() { return m_data->m_real_location;}
    inline OCPI::Xfer::EndPoint &Port::getShadowEndPoint() {
      assert(m_data->m_shadow_location);
      return *m_data->m_shadow_location;
    }
    inline OCPI::Xfer::EndPoint &Port::getLocalEndPoint() { return m_shadow ? getShadowEndPoint() : getEndPoint(); }
    inline volatile OutputPortSetControl* Port::getOutputControlBlock(){return m_hsPortControl;}
    inline void Port::setOutputControlBlock( volatile OutputPortSetControl* scb ){m_hsPortControl=scb;}
    inline OutputBuffer* Port::getOutputBuffer(BufferOrdinal idx)
      {return reinterpret_cast<OutputBuffer*>(Port::getBuffer(idx));}
    inline InputBuffer* Port::getInputBuffer(BufferOrdinal idx)
      {return reinterpret_cast<InputBuffer*>(Port::getBuffer(idx));}



    inline void Port::setBusyFactor(uint32_t bf ){m_busyFactor=bf;}
    inline uint32_t Port::getBusyFactor(){return m_busyFactor;}
    inline void Port::setEOS(){m_eos=true;}
    inline BufferOrdinal& Port::getLastBufferOrd(){return m_lastBufferOrd;}
    inline void Port::attachPullDriver( PullDataDriver* pd ){m_pdDriver=pd;}
    inline PullDataDriver* Port::getPullDriver(){return m_pdDriver;}

    /**************************************
     * Our mailbox
     ***************************************/
    inline uint16_t        Port::getMailbox(){return m_mailbox;}

  }
}


#endif
