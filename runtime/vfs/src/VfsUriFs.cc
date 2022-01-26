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

#include "VfsUriFs.hh"
#include "Vfs.hh"
#include "UtilUri.hh"
#include "OsAssert.hh"
#include "OsRWLock.hh"
#include "UtilAutoRDLock.hh"
#include "UtilAutoWRLock.hh"
#include <iostream>
#include <string>
#include <ctime>
#include <map>
#include <vector>

/*
 * ----------------------------------------------------------------------
 *
 * An "URI" file system in which the file names are URI components.
 *
 * ----------------------------------------------------------------------
 */

OCPI::VFS::UriFs::UriFs ()

{
  m_cwd = "/";
}

OCPI::VFS::UriFs::~UriFs ()

{
  /*
   * There mustn't be any open files or iterators
   */

  ocpiAssert (m_openFiles.size() == 0);
  ocpiAssert (m_openIterators.size() == 0);

  /*
   * Delete all adopted file systems
   */

  for (MountPoints::iterator it = m_mountPoints.begin();
       it != m_mountPoints.end(); it++) {
    if ((*it).adopted) {
      delete (*it).fs;
    }
  }
}

/*
 * ----------------------------------------------------------------------
 * Mounting File Systems
 * ----------------------------------------------------------------------
 */

void
OCPI::VFS::UriFs::mount (OCPI::VFS::Vfs * fs, bool adopt)

{
  OCPI::Util::AutoWRLock lock (m_lock);

  MountPoint mp;
  mp.adopted = adopt;
  mp.baseURI = fs->baseURI();
  mp.fs = fs;
  m_mountPoints.push_back (mp);
}

void
OCPI::VFS::UriFs::unmount (OCPI::VFS::Vfs * fs)

{
  OCPI::Util::AutoWRLock lock (m_lock);

  std::string mountPoint = URIToName (fs->baseURI());

  MountPoints::iterator it;

  for (it = m_mountPoints.begin(); it != m_mountPoints.end(); it++) {
    if ((*it).fs == fs) {
      break;
    }
  }

  if (it == m_mountPoints.end()) {
    throw std::string ("no such mount point");
  }

  /*
   * Make sure that there are no open files or iterators
   */

  for (OpenIterators::iterator oiit = m_openIterators.begin();
       oiit != m_openIterators.end(); oiit++) {
    if ((*oiit).second == fs) {
      throw std::string ("file system in use");
    }
  }

  for (OpenFiles::iterator ofit = m_openFiles.begin();
       ofit != m_openFiles.end(); ofit++) {
    if ((*ofit).second == fs) {
      throw std::string ("file system in use");
    }
  }

  m_mountPoints.erase (it);
}

/*
 * ----------------------------------------------------------------------
 * File Name Mapping
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::UriFs::absoluteNameLocked (const std::string & name) const

{
  return OCPI::VFS::joinNames (m_cwd, name);
}

/*
 * ----------------------------------------------------------------------
 * File Name URI Mapping
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::UriFs::baseURI () const

{
  return std::string();
}

std::string
OCPI::VFS::UriFs::nameToURI (const std::string & fileName) const

{
  std::string absName = absoluteName (fileName);
  return absoluteNameToURI (absName);
}

std::string
OCPI::VFS::UriFs::absoluteNameToURI (const std::string & absName) const

{
  if (absName.length() == 0 || absName[0] != '/') {
    throw std::string ("invalid file name");
  }

  if (absName.length() == 1) {
    return std::string ();
  }

  std::string::size_type pos = 1;
  std::string::size_type nextSlash = absName.find ('/', 1);
  std::string result;

  if (nextSlash == std::string::npos) {
    result = absName.substr (1);
    result += "://";
    return result;
  }

  result = absName.substr (1, nextSlash-1);
  result += ":/";

  pos = nextSlash + 1;

  do {
    std::string pathComponent;

    if ((nextSlash = absName.find ('/', pos)) == std::string::npos) {
      pathComponent = absName.substr (pos);
      pos = std::string::npos;
    }
    else {
      pathComponent = absName.substr (pos, nextSlash-pos);
      pos = nextSlash + 1;
    }

    result += '/';
    result += OCPI::Util::Uri::encode (pathComponent, ":");
  }
  while (pos != std::string::npos);

  return result;
}

std::string
OCPI::VFS::UriFs::URIToName (const std::string & uriName) const

{
  if (uriName.length() == 0) {
    return "/";
  }

  OCPI::Util::Uri uri (uriName);
  std::string result = "/";
  result += uri.getScheme ();
  result += "/";
  result += OCPI::Util::Uri::decode (uri.getAuthority ());
  result += OCPI::Util::Uri::decode (uri.getPath ());

  /*
   * Make sure that we know of a file system that can handle this URI.
   * findFs throws an exception if we don't.
   */

  {
    OCPI::Util::AutoRDLock lock (m_lock);
    std::string localName;
    findFs (result, localName);
  }

  return result;
}

/*
 * ----------------------------------------------------------------------
 * Directory Management
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::UriFs::cwd () const

{
  OCPI::VFS::UriFs * me = const_cast<OCPI::VFS::UriFs *> (this);
  OCPI::Util::AutoRDLock lock (me->m_lock);
  return m_cwd;
}

void
OCPI::VFS::UriFs::cd (const std::string & fileName)

{
  OCPI::Util::AutoWRLock lock (m_lock);
  std::string absName = absoluteNameLocked (fileName);
  m_cwd = absName;
}

void
OCPI::VFS::UriFs::mkdir (const std::string & fileName)

{
  OCPI::Util::AutoRDLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (fileName, localName);
  mp->mkdir (localName);
}

void
OCPI::VFS::UriFs::rmdir (const std::string & fileName)

{
  OCPI::Util::AutoRDLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (fileName, localName);
  mp->rmdir (localName);
}

/*
 * Directory Listing
 */
#if 0
OCPI::VFS::Iterator *
OCPI::VFS::UriFs::list (const std::string & dir,
                             const std::string & pattern)

{
  OCPI::Util::AutoWRLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (dir, localName);
  OCPI::VFS::Iterator * it = mp->list (localName, pattern);
  m_openIterators[it] = mp;
  return it;
}

void
OCPI::VFS::UriFs::closeIterator (OCPI::VFS::Iterator * it)

{
  OCPI::Util::AutoWRLock lock (m_lock);
  OpenIterators::iterator openIt = m_openIterators.find (it);

  if (openIt == m_openIterators.end()) {
    throw std::string ("invalid iterator");
  }

  OCPI::VFS::Vfs * mp = (*openIt).second;
  m_openIterators.erase (openIt);
  mp->closeIterator (it);
}
#endif
OCPI::VFS::Dir &OCPI::VFS::UriFs::openDir(const std::string &name){
  OCPI::Util::AutoWRLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (name, localName);
  return mp->openDir(localName);
}
/*
 * ----------------------------------------------------------------------
 * File information
 * ----------------------------------------------------------------------
 */

bool
OCPI::VFS::UriFs::exists (const std::string & fileName, bool * isDir)

{
  OCPI::Util::AutoRDLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (fileName, localName);
  return mp->exists (localName, isDir);
}

unsigned long long
OCPI::VFS::UriFs::size (const std::string & fileName)

{
  OCPI::Util::AutoRDLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (fileName, localName);
  return mp->size (localName);
}

std::time_t
OCPI::VFS::UriFs::lastModified (const std::string & fileName)

{
  OCPI::Util::AutoRDLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (fileName, localName);
  return mp->lastModified (localName);
}

/*
 * ----------------------------------------------------------------------
 * File I/O
 * ----------------------------------------------------------------------
 */

std::iostream *
OCPI::VFS::UriFs::open (const std::string & fileName, std::ios_base::openmode mode)

{
  OCPI::Util::AutoWRLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (fileName, localName);
  std::iostream * res = mp->open (localName, mode);
  m_openFiles[res] = mp;
  return res;
}

std::istream *
OCPI::VFS::UriFs::openReadonly (const std::string & fileName, std::ios_base::openmode mode)

{
  OCPI::Util::AutoWRLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (fileName, localName);
  std::istream * res = mp->openReadonly (localName, mode);
  m_openFiles[res] = mp;
  return res;
}

std::ostream *
OCPI::VFS::UriFs::openWriteonly (const std::string & fileName, std::ios_base::openmode mode)

{
  OCPI::Util::AutoWRLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (fileName, localName);
  std::ostream * res = mp->openWriteonly (localName, mode);
  m_openFiles[res] = mp;
  return res;
}

void
OCPI::VFS::UriFs::close (std::ios * str)

{
  OCPI::Util::AutoWRLock lock (m_lock);
  OpenFiles::iterator ofit = m_openFiles.find (str);

  if (ofit == m_openFiles.end()) {
    throw std::string ("invalid stream");
  }

  OCPI::VFS::Vfs * mp = (*ofit).second;
  m_openFiles.erase (ofit);
  mp->close (str);
}

/*
 * ----------------------------------------------------------------------
 * File System Operations
 * ----------------------------------------------------------------------
 */

void
OCPI::VFS::UriFs::copy (const std::string & oldName,
                             OCPI::VFS::Vfs * destFs,
                             const std::string & newName)

{
  OCPI::Util::AutoRDLock lock (m_lock);

  OCPI::VFS::UriFs * otherFs =
    dynamic_cast<OCPI::VFS::UriFs *> (destFs);

  std::string oldLocalName;
  OCPI::VFS::Vfs * oldFs = findFs (oldName, oldLocalName);

  if (!otherFs) {
    oldFs->copy (oldLocalName, destFs, newName);
    return;
  }

  std::string newLocalName;
  OCPI::VFS::Vfs * newFs = otherFs->findFs (newName, newLocalName);
  oldFs->copy (oldLocalName, newFs, newLocalName);
}

void
OCPI::VFS::UriFs::move (const std::string & oldName,
                             OCPI::VFS::Vfs * destFs,
                             const std::string & newName)

{
  OCPI::Util::AutoRDLock lock (m_lock);

  OCPI::VFS::UriFs * otherFs =
    dynamic_cast<OCPI::VFS::UriFs *> (destFs);

  std::string oldLocalName;
  OCPI::VFS::Vfs * oldFs = findFs (oldName, oldLocalName);

  if (!otherFs) {
    oldFs->move (oldLocalName, destFs, newName);
    return;
  }

  std::string newLocalName;
  OCPI::VFS::Vfs * newFs = otherFs->findFs (newName, newLocalName);
  oldFs->move (oldLocalName, newFs, newLocalName);
}

void
OCPI::VFS::UriFs::remove (const std::string & fileName)

{
  OCPI::Util::AutoRDLock lock (m_lock);
  std::string localName;
  OCPI::VFS::Vfs * mp = findFs (fileName, localName);
  mp->remove (localName);
}

/*
 * ----------------------------------------------------------------------
 * Find the file system that is responsible for some file.
 * ----------------------------------------------------------------------
 */

OCPI::VFS::Vfs *
OCPI::VFS::UriFs::findFs (const std::string & fileName,
                               std::string & localName) const

{
  std::string absName = absoluteNameLocked (fileName);
  std::string fileUri = absoluteNameToURI (absName);

  /*
   * Look for a mount point that knows how to handle this URI.
   *
   * This is done to allow mounted file systems to handle multiple
   * "base" URIs. For example, FileFs allows any alias of the local
   * host name in the authority component.
   */

  bool good = false;

  for (MountPoints::const_iterator it = m_mountPoints.begin();
       it != m_mountPoints.end(); it++) {
    try {
      localName = (*it).fs->URIToName (fileUri);
      good = true;
    }
    catch (...) {
    }

    if (good) {
      return (*it).fs;
    }
  }

  throw std::string ("no file system to handle file");
  return 0;
}
