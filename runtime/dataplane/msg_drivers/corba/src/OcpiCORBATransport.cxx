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
 *   This file contains the Interface for the CORBA URLs
 */

#include <list>
#include "OcpiUtilIOP.h"
#include "OcpiMessageEndpoint.h"
#include "DtMsgDriver.h"


//namespace OX = OCPI::Util::EzXml;
namespace OM = OCPI::Metadata;
namespace OU = OCPI::Util;
//namespace OA = OCPI::API;
namespace OT = OCPI::DataTransport;

namespace OCPI {  
  namespace Msg {
    namespace CORBA {

      // This message channel is for connecting by URL to connect to CORBA on the other side,
      // and that the assumption is that there is a way to talk to the other CORBA using ocpi
      // rdma transports.
      // Thus the URL is of the form:
      // corbaloc:<omni-ocpi-endpoint>[,<omni-ocpi-endpoint>]*/<key-string>

      // Where <omni-ocpi-endpoint> is "omniocpi:" followed by the ocpi endpoint string.

      // Note that double slash (//) immediately after the ocpi sub-protocol colon is ignored
      // and doesn't count as the slash before the key.

      // Note that this string is ALSO usable by CORBA as a real corbaloc (for omniorb anyway).
      
      class XferFactory;
      class XferServices;	
      class MsgChannel : public DataTransfer::Msg::TransferBase<XferServices,MsgChannel>
      {
      private:
	typedef std::list<std::string> RdmaEndpoints;
	RdmaEndpoints m_rdmaEndpoints;
	std::string m_key, m_url;
	OT::MessageCircuit *m_circuit;
      public:

	MsgChannel(XferServices & xf,
		   const OM::Protocol &protocol,
		   const char  * url,
		   const OCPI::Util::PValue *ourParams,
		   const OCPI::Util::PValue *otherParams)
	  : DataTransfer::Msg::TransferBase<XferServices,MsgChannel>(xf, *this),
	    m_url(url), m_circuit(0)
	{
	  (void)ourParams, (void)otherParams;
	  std::string corbalocURL;
	  if (!strncasecmp(url, "ior:", sizeof("ior:") - 1)) {
	    // Convert IOR to corbaloc
	    OU::IOP::IOR ior(url);
	    corbalocURL = ior.corbaloc();
	  } else
	    corbalocURL = url;

	  ocpiAssert(!strncasecmp(url, "corbaloc:", sizeof("corbaloc:") - 1));
	  url += sizeof("corbaloc:") - 1;
	  for (const char *p; *url && url[-1] != '/'; url = p + 1) {
	    for (p = url; *p && *p != ',' && *p != '/'; p++)
	      // Skip over slashes after colon
	      if (*p == ':' && p[1] == '/' && p[2] == '/')
		p += 2;
	    if (!*p)
	      throw OU::Error("No key found (after slash) in url: %s", m_url.c_str());
	    if (!strncmp(url, "omniocpi:", sizeof("omniocpi:") - 1))
	      url += sizeof("omniocpi:") - 1;
	    if (!strncmp(url, "ocpi-", 5))
	      m_rdmaEndpoints.push_back(std::string(url, OCPI_SIZE_T_DIFF(p, url)));
	  }
	  if (m_rdmaEndpoints.empty())
	    throw OU::Error("No usable opencpi endpoints in url: %s", m_url.c_str());
	  // The key is encoded according to RFC 2396, but we will leave it that way
	  m_key = url;

#if 1
	  std::string info;
	  protocol.printXML(info, 0);
#else
	  // Now must encode the procotol info in a string, with the key being the first line
	  char *temp = strdup("/tmp/tmpXXXXXXX");
	  int tempfd = mkstemp(temp);
	  free(temp);
	  if (tempfd < 0)
	    throw OU::Error("Can't open temp file for protocol processing");
	  FILE *f = fdopen(tempfd, "w+");
	  // We use the # to terminate the key since that is also how URIs work:  the end of
	  // a URI is either null or #.
	  fprintf(f, "%s#", url);
	  protocol.printXML(f, 0);
	  fflush(f);
	  off_t size = ftello(f);
	  char *info = new char[size];
	  fseeko(f, 0, SEEK_SET);
	  fread(info, size, 1, f);
	  fclose(f);
	  // End of kludge that can be fixed when XML printing is to a stream...
#endif
	  // Here we try all endpoints in turn.
	  for (RdmaEndpoints::const_iterator i = m_rdmaEndpoints.begin();
	       i != m_rdmaEndpoints.end(); i++)
	    try {
	      m_circuit = &OT::MessageEndpoint::connect(i->c_str(), 4096, info.c_str(), NULL);
	    } catch (...) {
#ifndef NDEBUG
	      printf("CORBA URL connection failed: endpoint '%s' key '%s'\n",
		     i->c_str(), m_key.c_str());
#endif
	    }
	  if (!m_circuit)
	    throw OU::Error("No endpoints in CORBA URL '%s' could be connected",
			    m_url.c_str());
	}

	virtual ~MsgChannel()
	{
	  if (m_circuit)
	    delete m_circuit;
	}
	  
	OCPI::DataTransport::BufferUserFacet*  getNextEmptyOutputBuffer(uint8_t *&data, size_t &length)
	{
	  return m_circuit->getNextEmptyOutputBuffer(data, length, NULL);
	}

	void sendOutputBuffer(OCPI::DataTransport::BufferUserFacet* b, size_t msg_size, uint8_t opcode )
	{
	  m_circuit->sendOutputBuffer(b, msg_size, opcode);
	}

	OCPI::DataTransport::BufferUserFacet*  getNextFullInputBuffer(uint8_t *&data, size_t &length,
								      uint8_t &opcode)
	{
	  return m_circuit->getNextFullInputBuffer(data, length, opcode);
	}

	void releaseInputBuffer(OCPI::DataTransport::BufferUserFacet* b)
	{
	  m_circuit->releaseInputBuffer(b);
	}
      };


      class XferServices : public DataTransfer::Msg::ConnectionBase<XferFactory,XferServices,MsgChannel>
      {
	const OM::Protocol &m_protocol;
      public:
	XferServices ( const OM::Protocol & protocol , const char  * other_url, 
		       const OU::PValue *our_props=0,
		       const OU::PValue *other_props=0 );
	MsgChannel* getMsgChannel( const char  *a_url,
				   const OU::PValue *ourParams,
				   const OU::PValue *otherParams)
	{
	  return new MsgChannel( *this, m_protocol, a_url, ourParams, otherParams);
	}
	virtual ~XferServices ()
	{
	}
      };

      class Device
	: public DataTransfer::Msg::DeviceBase<XferFactory,Device>
      {
      public:
	Device(const char* a_name)
	  : DataTransfer::Msg::DeviceBase<XferFactory,Device>(a_name, *this)
	{

	}
	void configure(ezxml_t x);
	virtual ~Device(){}
      };
     
      class XferFactory
	: public DataTransfer::Msg::DriverBase<XferFactory, Device, XferServices,
					       DataTransfer::Msg::msg_transfer>
      {

      public:
	inline const char* getProtocol() {return "corbaloc";};
	XferFactory()throw ();
	virtual ~XferFactory()throw ();
 
	void configure(ezxml_t)
	{
	  // Empty
	}
	  
	bool supportsTx( const char* url,
			 const OCPI::Util::PValue * /* ourParams */,
			 const OCPI::Util::PValue * /*otherParams */ )
	{
	  return !strncasecmp(url, "corbaloc:", sizeof("corbaloc:") - 1) ||
	    !strncasecmp(url, "ior:", sizeof("ior:") - 1);
	}

	virtual XferServices* getXferServices( const OM::Protocol & protocol,
					       const char* url,
					       const OU::PValue *ourParams,
					       const OU::PValue *otherParams)
	{
	  if (!m_services)
	    m_services = new XferServices( protocol, url, ourParams, otherParams);
	  return m_services;
	}

      private:
	XferServices* m_services;

      };

	
      XferServices::
      XferServices ( const OM::Protocol &a_protocol , const char  * other_url,
		     const OU::PValue *ourParams,
		     const OU::PValue *otherParams)
	: DataTransfer::Msg::ConnectionBase<XferFactory,XferServices,MsgChannel>
	  (*this, a_protocol, other_url, ourParams, otherParams),
	  m_protocol(a_protocol)
      {
      }

      XferFactory::
      XferFactory()
	throw ()
	: m_services(NULL)
      {
	// Empty
      }

      XferFactory::	
      ~XferFactory()
	throw ()
      {
	

      }
      void
      Device::
      configure(ezxml_t x) {
	DataTransfer::Msg::Device::configure(x);
      }

      DataTransfer::Msg::RegisterTransferDriver<XferFactory> driver;

    }
  }
}

