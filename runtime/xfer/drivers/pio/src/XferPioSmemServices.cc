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
 *        This file contains the MCHOST implementation for shared memory functions
 *        originally in /vobs/Ocpi/prod_utils/system/smem/src/smem.cxx. Any
 *        target with an MCOS port can use this implementation.
 *
 * Author: Tony Anzelmo
 *
 * Date: 12/31/03
 *
 */

#ifndef OCPI_NT_SMEM_SERVICES_H_
#define OCPI_NT_SMEM_SERVICES_H_

#include <cstdio>
#include <map>
#include "XferException.hh"
#include "XferEndPoint.hh"
#include "XferPioSmemServices.hh"
#include "XferPioFileMapping.hh"

namespace OCPI {
namespace Xfer {
namespace PIO {

  std::map<std::string, BaseSmem*> BaseSmemServices::s_cache; 

  typedef void* SMB_handle;
  typedef void* SMB_mapping_handle;

  // HostSmem specializes by adding FileMapping (for host-only)
  class HostSmem :  public BaseSmem 
  {
  public:

    HostSmem (
              EndPoint* loc, 
              SMB_handle handle, 
              FileMapping* mapper) 
      : BaseSmem (loc ), m_handle(handle), m_pMapper (mapper) 
    { 
      m_maphandle = NULL;
    }

    SMB_handle                     m_handle;
    SMB_mapping_handle             m_maphandle;
    FileMapping                   *m_pMapper;
    virtual ~HostSmem()
    {
      delete m_pMapper;
    }

  };

  // HostSmemServices implements Smem services on host platforms that have an MCOS port.
  class HostSmemServices : public BaseSmemServices
  {
  public:

    // Compute virtual address to return to caller for a Map call.
    void* computeMappedVA ()
    {
      HostSmem* pSmem = static_cast<HostSmem*>(m_pSmem);

      // If we mapped at 0, then this code is identical. If we mapped at non-zero
      // (caller specified non-zero offset/size), this accounts for it.
      void* va = (void *)((char *)pSmem->m_mappedva + (pSmem->m_reqoffset - pSmem->m_mappedoffset));

      return va;
    }



    // Create a named shared memory object.
    void create (EndPoint* loc )
    {

      // Begin exception handler
      OCPI::OS::int32_t rc = 0;
      SMB_handle handle = 0;
      FileMapping *pMapper = 0;
      m_location = loc;

      try
        {
          // Verify state
          if (m_pSmem)
            {
              throw DataTransferEx (RESOURCE_EXCEPTION, "HostSmemServices::Create: Already created/attached to an instance");
            }

          // Use plaform-specific file mapping mechanism.
          pMapper = CreateFileMapping();
          if (pMapper == 0)
            {
              throw DataTransferEx (RESOURCE_EXCEPTION, 
                                    "HostSmemServices::Create: CreateFileMapping returned NULL reference");
            }
                

#if 1
	  m_pSmem = new HostSmem(loc, handle, pMapper);
	  BaseSmemServices::add(m_pSmem);
          ocpiDebug("Creating mapping of size %zu name %s", loc->size(), m_pSmem->m_name.c_str());
          if ((rc = pMapper->CreateMapping ("", m_pSmem->m_name.c_str(),
					    FileMapping::ReadWriteAccess, loc->size())))
	    throw OU::Error("CreatMapping failed: %u", rc);
#else
          ocpiDebug("Creating mapping of size %zu", loc->size() );
          rc = pMapper->CreateMapping ("", m_name.c_str(),
				       FileMapping::ReadWriteAccess, loc->size());
          if (rc == 0)
            {
              pSmem = new HostSmem ( loc, handle, pMapper);
              if (pSmem == 0)
                {
                  throw DataTransferEx (RESOURCE_EXCEPTION, 
                                        "HostSmemServices::Create: Failed to allocate a new HostSmem instance");
                }
              this->BaseSmemServices::add (pSmem);
              m_pSmem = pSmem;
            }
#endif
        }
      catch( ... ) 
        {
          delete m_pSmem;
	  m_pSmem = 0;
          throw;
        }
    }



    // Close shared memory object.
    void close ()
    {
      // Verify state
      HostSmem* pSmem = static_cast<HostSmem*>(m_pSmem);
      if (pSmem == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION, "HostSmemServices::Close: No active instance");
        }

      // Close mappers.
      if (pSmem->m_pMapper)
        {
          (void)pSmem->m_pMapper->CloseMapping ();
        }

      // Remove from the dictionary, ignoring reference count.
      pSmem->m_refcnt = 0;
      this->BaseSmemServices::remove (pSmem);
      delete pSmem;
      m_pSmem = 0;
    }

    // Attach to an existing shared memory object by name.
    OCPI::OS::int32_t attach(EndPoint* loc)
    {
      // Begin exception handler
      OCPI::OS::int32_t rc = 0;
      SMB_handle handle = 0;
      HostSmem* pSmem = 0;
      FileMapping* pMapper = 0;

      m_location = loc;
      try 
        {
          // Verify state
          if (m_pSmem)
            {
              return 0;
            }

          // Lookup existing named shared memory object.
          if ((pSmem = static_cast<HostSmem *>(this->BaseSmemServices::lookup(*loc))) == 0)
            {
              // Attempt to attach to host OS shared memory.
              //                EndPoint loc = OcpiSmemServices::HostOnly;

              pMapper = CreateFileMapping();
              if (pMapper == 0)
                {
                  throw DataTransferEx (RESOURCE_EXCEPTION, 
                                        "HostSmemServices::Attach: CreateFileMapping returned NULL reference");
                }
#if 1
	      pSmem = new HostSmem(m_location, handle, pMapper);
	      BaseSmemServices::add(pSmem);
              if (pMapper->OpenMapping(pSmem->m_name.c_str(),
				       FileMapping::AllAccess))
                throw DataTransferEx(RESOURCE_EXCEPTION,
				     "XferPioSmemServices::Attach: could not attach");
#else
              rc = pMapper->OpenMapping (m_name.c_str(), FileMapping::AllAccess);
              if (rc == 0)
                {
                  // Add this instance with the name.
                  pSmem = new HostSmem (m_location, handle, pMapper);
                  if (pSmem == 0)
                    {
                      throw DataTransferEx (RESOURCE_EXCEPTION, 
                                            "HostSmemServices::Create: Failed to allocate a new HostSmem instance");
                    }
                  this->BaseSmemServices::add (pSmem);
                }
              else {
                throw DataTransferEx (RESOURCE_EXCEPTION, 
                                      "HostSmemServices::Attach: CreateFileMapping could not attach");
              }
#endif
            }
        }
      catch( ... ) 
        {
          delete pMapper;
          delete m_pSmem;
          m_pSmem = 0;
          throw;
        }
      if (rc == 0)
        {
          m_pSmem = pSmem;
        }
      return 0;
    }

    // Detach from shared memory object
    OCPI::OS::int32_t detach ()
    {
      // Verify state
      HostSmem* pSmem = static_cast<HostSmem*>(m_pSmem);
      if (pSmem == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION,"HostSmemServices::Detach: No active instance");
        }

      // Close on last detach
      //          OCPI::OS::int32_t rc = 0;
      if (pSmem->m_refcnt == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION, "HostSmemServices::Detach: Request with no current attach active");
        }
      if (--pSmem->m_refcnt == 0)
        {
          close ();
        }
      m_pSmem = 0;
      return 0;
    }

    // Map a view of the shared memory area at some offset/size and return the virtual address.
    void* map(Offset offset, size_t size )
    {
      ( void ) size;
      void* pva=NULL;

      // Verify state
      HostSmem* pSmem = static_cast<HostSmem*>(m_pSmem);
      if (pSmem == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION,"HostSmemServices::Map: No active instance");
        }

      // If this instance is not currently mapped...
      OCPI::OS::int32_t rc = 0;
      //          OCPI::OS::uint32_t offsetToAdd = offset;
      if (pSmem->m_maphandle == 0)
        {
          // Map a view using platform dependent file mapping.
          pSmem->m_mappedva = pSmem->m_pMapper->MapView (0, 0, FileMapping::AllAccess);
          if (pSmem->m_mappedva == 0)
            {
              rc = pSmem->m_pMapper->GetLastError ();
            }
          else
            {
              pSmem->m_maphandle = (void *)-1;
            }
          pSmem->m_mappedoffset = 0;
          pSmem->m_mappedsize = pSmem->m_size;
                                
        }
      pSmem->m_reqoffset = offset;

      // Bump mapping count and return the virtual address of this mapping.
      // The address is the mapped virtual address plus the difference in the
      // requested offset and the actual mapped offset. If an attempt is made
      // to map before an already mapped area, throw an exception because we
      // can't produce a valid VA (the area is not mapped).
      if (rc == 0)
        {
          if (offset < pSmem->m_mappedoffset)
            {
              throw DataTransferEx (RESOURCE_EXCEPTION, 
                                    "HostSmemServices::Map: caller's offset is less than mapped offset");
            }
          pSmem->m_mapcnt++;

          // Determine the virtual address to return
          pva = computeMappedVA ();
        }

      return pva;
    }

    // Unmap the current mapped view.
    OCPI::OS::int32_t unMap ()
    {
      // Verify state
      HostSmem* pSmem = static_cast<HostSmem*>(m_pSmem);
      if (pSmem == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION,"HostSmemServices::UnMap: No active instance");
        }

      // Unmap on last reference
      //          OCPI::OS::int32_t rc = 0;
      if (pSmem->m_mapcnt == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION,"HostSmemServices::UnMap: Request with no current mapping active");
        }
      if (--pSmem->m_mapcnt == 0)
        {                        
          pSmem->m_pMapper->UnMapView (pSmem->m_mappedva);
          pSmem->m_maphandle = 0;
          pSmem->m_mappedva = 0;
        }
      return 0;
    }

    // Enable mapping
    void* enable ()
    {
      void* pva=NULL;

      // Verify state
      HostSmem* pSmem = static_cast<HostSmem*>(m_pSmem);
      if (pSmem == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION,"HostSmemServices::Enable: No active instance");
        }
      if (pSmem->m_maphandle == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION,"HostSmemServices::Enable: No active mapping");
        }

      if ( 1 ) 
        {
          //                        rc = this->SMBEnable (pva);
        }
      else
        {
          pva = (void *)((char *)pSmem->m_mappedva + (pSmem->m_reqoffset - pSmem->m_mappedoffset));
        }

      return pva;
                        
    }

    // Disable mapping
    OCPI::OS::int32_t disable ()
    {
      // Verify state
      HostSmem* pSmem = static_cast<HostSmem*>(m_pSmem);
      if (pSmem == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION,"HostSmemServices::Disable: No active instance");
        }
      if (pSmem->m_maphandle == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION,"HostSmemServices::Disable: No active mapping");
        }
      return 0;
    }

    //        GetHandle - platform dependent opaque handle for Smem instance.
    void* getHandle ()
    {
      HostSmem* pSmem = static_cast<HostSmem*>(m_pSmem);
      if (pSmem == 0)
        {
          throw DataTransferEx (RESOURCE_EXCEPTION,"HostSmemServices::GetHandle: No active instance");
        }
      return pSmem->m_handle;
    }

  public:
    // Ctor/dtor
    HostSmemServices (EndPoint& cloc )
      :BaseSmemServices(cloc)
    {
      EndPoint* loc = &cloc;
      if (cloc.local())
	create(loc);
      else
	attach(loc);
    }

    virtual ~HostSmemServices ()
    {
      ocpiAssert(m_pSmem->m_refcnt > 0);
      if (--m_pSmem->m_refcnt == 0)
	delete m_pSmem;
    }
  private:
  };


  // Platform dependent global that creates an instance
  SmemServices& createHostSmemServices (EndPoint& loc )
  {
    return *new HostSmemServices (loc);
  }

}
}
}
#endif
