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

#include "VfsFilterFs.hh"
#include "Vfs.hh"
#include <iostream>
#include <string>

/*
 * ----------------------------------------------------------------------
 * FilterFS implementation
 * ----------------------------------------------------------------------
 */

OCPI::VFS::FilterFs::FilterFs (OCPI::VFS::Vfs & delegatee)

  : m_delegatee (delegatee)
{
}

OCPI::VFS::FilterFs::~FilterFs ()

{
}

/*
 * ----------------------------------------------------------------------
 * File Name URI Mapping
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::FilterFs::baseURI () const

{
  return m_delegatee.baseURI ();
}

std::string
OCPI::VFS::FilterFs::nameToURI (const std::string & fileName) const

{
  return m_delegatee.nameToURI (fileName);
}

std::string
OCPI::VFS::FilterFs::URIToName (const std::string & struri) const

{
  return m_delegatee.URIToName (struri);
}

/*
 * ----------------------------------------------------------------------
 * Directory Management
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::FilterFs::cwd () const

{
  return m_delegatee.cwd ();
}

void
OCPI::VFS::FilterFs::cd (const std::string & fileName)

{
  access (fileName, std::ios_base::in, true);
  m_delegatee.cd (fileName);
}

void
OCPI::VFS::FilterFs::mkdir (const std::string & fileName)

{
  std::string dirName = directoryName (fileName);
  access (dirName, std::ios_base::out, true);
  m_delegatee.mkdir (fileName);
}

void
OCPI::VFS::FilterFs::rmdir (const std::string & fileName)

{
  std::string dirName = directoryName (fileName);
  access (dirName, std::ios_base::out, true);
  m_delegatee.rmdir (fileName);
}

/*
 * ----------------------------------------------------------------------
 * Directory Listing
 * ----------------------------------------------------------------------
 */

#if 0
OCPI::VFS::Iterator *
OCPI::VFS::FilterFs::list (const std::string & dir,
                                const std::string & pattern)

{
  std::string absDirName = absoluteName (dir);
  std::string absPatName = OCPI::VFS::joinNames (dir, pattern);
  std::string patDirName = OCPI::VFS::directoryName (absPatName);
  access (patDirName, std::ios_base::in, true);
  return m_delegatee.list (dir, pattern);
}

void
OCPI::VFS::FilterFs::closeIterator (Iterator * it)

{
  return m_delegatee.closeIterator (it);
}
#endif
/*
 * ----------------------------------------------------------------------
 * File information
 * ----------------------------------------------------------------------
 */

bool
OCPI::VFS::FilterFs::exists (const std::string & fileName, bool * isDir)

{
  std::string absName = absoluteName (fileName);
  std::string dirName = OCPI::VFS::directoryName (absName);
  access (dirName, std::ios_base::in, true);
  return m_delegatee.exists (fileName, isDir);
}

unsigned long long
OCPI::VFS::FilterFs::size (const std::string & fileName)

{
  std::string absName = absoluteName (fileName);
  std::string dirName = OCPI::VFS::directoryName (absName);
  access (dirName, std::ios_base::in, true);
  return m_delegatee.size (fileName);
}

std::time_t
OCPI::VFS::FilterFs::lastModified (const std::string & fileName)

{
  std::string absName = absoluteName (fileName);
  std::string dirName = OCPI::VFS::directoryName (absName);
  access (dirName, std::ios_base::in, true);
  return m_delegatee.lastModified (fileName);
}

/*
 * ----------------------------------------------------------------------
 * File I/O
 * ----------------------------------------------------------------------
 */

std::iostream *
OCPI::VFS::FilterFs::open (const std::string & fileName,
                                std::ios_base::openmode mode)

{
  access (fileName, mode, false);
  return m_delegatee.open (fileName, mode);
}

std::istream *
OCPI::VFS::FilterFs::openReadonly (const std::string & fileName,
                                        std::ios_base::openmode mode)

{
  access (fileName, mode & ~(std::ios_base::out), false);
  return m_delegatee.openReadonly (fileName, mode);
}

std::ostream *
OCPI::VFS::FilterFs::openWriteonly (const std::string & fileName,
                                         std::ios_base::openmode mode)

{
  access (fileName, mode & ~(std::ios_base::in), false);
  return m_delegatee.openWriteonly (fileName, mode);
}

void
OCPI::VFS::FilterFs::close (std::ios * str)

{
  m_delegatee.close (str);
}

/*
 * ----------------------------------------------------------------------
 * File system operations
 * ----------------------------------------------------------------------
 */

void
OCPI::VFS::FilterFs::copy (const std::string & oldName,
                                OCPI::VFS::Vfs * destfs,
                                const std::string & newName)

{
  access (oldName, std::ios_base::in, false);

  FilterFs * destfilterfs = dynamic_cast<FilterFs *> (destfs);

  if (destfilterfs) {
    destfilterfs->access (newName, std::ios_base::out | std::ios_base::trunc, false);
    m_delegatee.copy (oldName, &destfilterfs->m_delegatee, newName);
  }
  else {
    m_delegatee.copy (oldName, destfs, newName);
  }
}

void
OCPI::VFS::FilterFs::move (const std::string & oldName,
                                OCPI::VFS::Vfs * destfs,
                                const std::string & newName)

{
  access (oldName, std::ios_base::in | std::ios_base::trunc, false);

  FilterFs * destfilterfs = dynamic_cast<FilterFs *> (destfs);

  if (destfilterfs) {
    destfilterfs->access (newName, std::ios_base::out | std::ios_base::trunc, false);
    m_delegatee.move (oldName, &destfilterfs->m_delegatee, newName);
  }
  else {
    m_delegatee.move (oldName, destfs, newName);
  }
}

void
OCPI::VFS::FilterFs::rename (const std::string & oldName,
                                  const std::string & newName)

{
  access (oldName, std::ios_base::in | std::ios_base::trunc, false);
  access (newName, std::ios_base::out | std::ios_base::trunc, false);
  m_delegatee.rename (oldName, newName);
}

void
OCPI::VFS::FilterFs::remove (const std::string & fileName)

{
  access (fileName, std::ios_base::trunc, false);
  m_delegatee.remove (fileName);
}
