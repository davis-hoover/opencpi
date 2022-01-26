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
 *	This file contain the "C" implementation for Posix file mapping functions
 *	required by the system services. It is normally included by targets
 *	that support Posix and thus shared across target OSs.
 *
 * Author: Tony Anzelmo
 *
 * Date: 10/16/03
 *
 */

#ifndef OCPI_POSIX_FILEMAPPING_SERVICES_H_
#define OCPI_POSIX_FILEMAPPING_SERVICES_H_
#include <inttypes.h>
#include <string>
#include <cstdio>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include "ocpi-config.h"
#include "OsAssert.hh"
#include "XferPioFileMapping.hh"
#include "UtilMisc.hh"

#ifndef OCPI_OS_VERSION_zynq
// This fails on zynq and we have not dug into it yet.
#define REAL_SHM 1
#endif
namespace OCPI {
namespace Xfer {
namespace PIO {
  namespace OU = OCPI::Util;
  // PosixFileMapping implements basic file mapping support on Posix compliant platforms.
  class PosixFileMapping : public FileMapping
  {
    size_t m_size;
  public:
    // Create a mapping to a named file.
    //	strFilePath - Path to a file. If null, no backing store.
    //	strMapName	- Name of the mapping. Can be null.
    //	eAccess		- The type of access desired.
    //	iMaxSize	- Maximum size of mapping object.
    // Returns 0 for success or a platform specific error number.
    int CreateMapping (const char*  strFilePath, const char* strMapName, AccessType eAccess, size_t iMaxSize)
    {
      // Common call to do shm_open
      int rc = InitMapping (strFilePath, strMapName, eAccess, O_CREAT);
      if (rc == 0)
	{
#ifdef REAL_SHM
	  // Set the size of the shared area if not already large enough
	  // Note Darwin/MacOS doesn't allow truncating it more than once, so it can't expand either
	  struct stat statbuf;
	  rc = fstat (m_fd, &statbuf);
	  if (rc == 0 && statbuf.st_size < (off_t)iMaxSize)
	    rc = ftruncate(m_fd, (off_t)iMaxSize);
	  m_errno = errno;
	  if (rc != 0)
	    {
	      ocpiDebug("PosixFileMapping::CreateMapping: ftruncate failed with errno %d",
		     m_errno);
	      TerminateMapping ();
	    }
	  ocpiDebug("shm fd %d truncate was %llu now %zu",
		    m_fd, (unsigned long long)statbuf.st_size, iMaxSize);
#endif
	  m_size = iMaxSize;

	}
      return rc;
    }

    // Open an existing mapping to a named file.
    //	strMapName	- Name of the mapping.
    //	eAccess		- The type of access desired.
    // Returns 0 for success or a platform specific error number.
    int OpenMapping (const char* strMapName, AccessType eAccess)
    {
      return InitMapping (NULL, strMapName, eAccess, 0);
    }

    // Close an existing mapping.
    // Returns 0 for success or a platform specific error number.
    int CloseMapping ()
    {
      return TerminateMapping ();
    }

    // Map a segment of the file into the address space.
    //	iOffset		- Byte offset into file for this view.
    //	lLength		- Number of bytes to map.
    // Returns that virtual address or 0 if failure.
    void* MapView (uint32_t iOffset, size_t lLength, AccessType eAccess)
    {
      // Map access to protection
      int iProtect = MapAccessToProtect (eAccess);

      // Mapping a length of 0 means map the whole mapping.
      void* iRet = 0;
      int fRet = 0;
      if (lLength == 0)
	{
#ifdef REAL_SHM
	  // Use the file "size"
	  struct stat statbuf;
	  fRet = fstat (m_fd, &statbuf);
	  lLength = (size_t)statbuf.st_size;
#else
	  lLength = m_size;
#endif
	}

      // Do the mapping
      if (fRet == 0)
	{
#ifdef REAL_SHM
	  iRet = mmap(NULL, lLength, iProtect, MAP_SHARED, m_fd, (off_t)iOffset);
#else
          iRet = mmap(NULL, lLength, iProtect, MAP_PRIVATE|MAP_ANON, -1, (off_t)iOffset);
#endif
	  ocpiDebug("mmap on %d at offset %u length %zu returns %p errno %d",
		    m_fd, iOffset, lLength, iRet, errno);
	  if (iRet != MAP_FAILED)
	    ocpiDebug("mmap value at %p is %" PRIx32, iRet, *(uint32_t*)iRet);
	}
      m_length = lLength;
      return iRet;
    }

    // Unmap a segment of a file from the address space.
    //	pVA		- Virtual address of view to unmap
    // Returns 0 for success or a platform specific error number.
    int UnMapView (void *pVA)
    {
      int iRet = munmap (pVA, m_length);
      return iRet;
    }

    // Return the last error that occurred for a file mapping operation.
    int GetLastError ()
    {
      return m_errno;
    }

    // Constructor
    PosixFileMapping ()
      : m_fd(-1), m_errno(0), m_length(0), m_created(false)
    {}

    // Destructor
    ~PosixFileMapping () {
      TerminateMapping();
    };

  private:
    std::string m_name;
    int	m_fd;			// File descriptor
    int	m_errno;		// Last error.
    size_t m_length;		// Length of last mapping
    bool m_created;             // did we create it?

  private:

    // Common method to open shared memory
    int InitMapping (const char* strFilePath, std::string strMapName, AccessType eAccess, int iFlags)
    {
      ( void ) strFilePath;
      // Terminate any current mapping
      TerminateMapping ();

      // Convert access type to a Posix flag set.
      int iOpenFlags = MapAccessTypeToOpen (eAccess);

      if (strMapName.empty()) {
	static unsigned n = 0;
	OU::format(strMapName, "/ocpi%u.%u", getpid(), n++);
      }
      // A leading "/" is required.
      m_name = strMapName[0] == '/' ? strMapName : "/" + strMapName;
      // Open a shared memory object
#ifdef REAL_SHM
      m_fd = shm_open (m_name.c_str (), iOpenFlags | iFlags, 0666);
#else
      // Use anonymous mappings
      static int fakefd = 1000;
      m_fd = ++fakefd;
      (void)iOpenFlags;
#endif
      m_length = 0;
      if (m_fd == -1) {
	  m_errno = errno;
	  ocpiDebug("PosixFileMapping::InitMapping: shm_open of %s failed with errno %d: %s\n",
		    m_name.c_str (), m_errno, strerror(m_errno));
	  return m_errno;
	}
      m_created = iFlags == O_CREAT;
      ocpiDebug("shm open %s fd %d created %d\n", m_name.c_str(), m_fd, m_created);
      return 0;
    }

    // Terminate any existing mapping.
    int TerminateMapping ()
    {
      if ( m_fd != -1 ) {
      ocpiDebug("shm closing %s fd %d created %d", m_name.c_str(), m_fd, m_created);
	if (m_created)
	  shm_unlink(m_name.c_str());
	close (m_fd);
      }
      m_fd =  -1;
      return 0;
    }

    // Map an AccessType to a POSIX open flags
    int MapAccessTypeToOpen (AccessType eAccess)
    {
      switch (eAccess)
	{
	case ReadWriteAccess:
	case AllAccess:
	case CopyAccess:
	  return O_RDWR;
	case ReadOnlyAccess:
	  return O_RDONLY;
	default:
	  return -1;
	}
    }

    // Map an AccessType to a POSIX protection flags
    int MapAccessToProtect (AccessType eAccess)
    {
      switch (eAccess)
	{
	case ReadWriteAccess:
	case AllAccess:
	case CopyAccess:
	  return PROT_READ | PROT_WRITE;
	case ReadOnlyAccess:
	  return PROT_READ;
	default:
	  return -1;
	}
    }

  };

  FileMapping* CreateFileMapping()
  {
    return new PosixFileMapping ();
  }
}
}
}
#endif
