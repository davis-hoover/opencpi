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

#include "VfsHttpFs.hh"
#include "Vfs.hh"
#include "UtilHttpClient.hh"
#include "UtilMisc.hh"
#include "UtilAutoMutex.hh"
#include "OsFileSystem.hh"
#include "OsMutex.hh"
#include <iostream>
#include <string>
#include <ctime>
#include <cassert>

OCPI::VFS::Http::HttpFsBase::
HttpFsBase (const std::string & scheme,
            const std::string & root)

{
  if (root.length() && root[root.length()-1] == '/') {
    m_root = root.substr (0, root.length() - 1);
  }
  else {
    m_root = root;
  }

  if (m_root.length() && m_root[0] != '/') {
    throw std::string ("invalid root");
  }

  m_cwd = "/";
  m_scheme = scheme;
  m_baseURI = scheme;
  m_baseURI += ":/";

  if (m_root.length()) {
    std::string::size_type firstSlash = m_root.find ('/', 1);
    std::string firstPathComponent;

    if (firstSlash == std::string::npos) {
      firstPathComponent = m_root.substr (1);
    }
    else {
      firstPathComponent = m_root.substr (1, firstSlash-1);
    }

    m_baseURI += '/';
    m_baseURI += OCPI::Util::Uri::encode (firstPathComponent, ":");

    if (firstSlash != std::string::npos) {
      std::string remainingPathComponents = m_root.substr (firstSlash);
      m_baseURI += OCPI::Util::Uri::encode (remainingPathComponents, "/");
    }
  }

  m_baseURI += "/";
}

OCPI::VFS::Http::HttpFsBase::
~HttpFsBase ()

{
}

/*
 * ----------------------------------------------------------------------
 * URI mapping
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::Http::HttpFsBase::
baseURI () const

{
  return m_baseURI;
}

std::string
OCPI::VFS::Http::HttpFsBase::
nameToURI (const std::string & fileName) const

{
  return nativeFilename (fileName);
}

std::string
OCPI::VFS::Http::HttpFsBase::
URIToName (const std::string & uri) const

{
  if (uri.length() < m_baseURI.length() ||
      uri.compare (0, m_baseURI.length(), m_baseURI) != 0) {
    std::string reason = "URI \"";
    reason += uri;
    reason += "\" not understood by this file system, expecting \"";
    reason += m_baseURI;
    reason += "\" prefix";
    throw reason;
  }

  std::string remainingName = uri.substr (m_baseURI.length() - 1);
  return OCPI::Util::Uri::decode (remainingName);
}

/*
 * ----------------------------------------------------------------------
 * File Name Mapping
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::Http::HttpFsBase::absoluteNameLocked (const std::string & name) const

{
  return OCPI::VFS::joinNames (m_cwd, name);
}

/*
 * ----------------------------------------------------------------------
 * Directory Management
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::Http::HttpFsBase::
cwd () const

{
  OCPI::Util::AutoMutex lock (m_lock);
  return m_cwd;
}

void
OCPI::VFS::Http::HttpFsBase::
cd (const std::string & fileName)

{
  testFilenameForValidity (fileName);
  OCPI::Util::AutoMutex lock (m_lock);
  m_cwd = absoluteNameLocked (fileName);
}

void
OCPI::VFS::Http::HttpFsBase::
mkdir (const std::string &)

{
  /*
   * cannot create directories via HTTP
   */

  throw std::string ("mkdir not supported over HTTP");
}

void
OCPI::VFS::Http::HttpFsBase::
rmdir (const std::string &)

{
  /*
   * cannot remove directories via HTTP
   */

  throw std::string ("rmdir not supported over HTTP");
}


/*
 * ----------------------------------------------------------------------
 * Directory Listing
 * ----------------------------------------------------------------------
 */

#if 0
OCPI::VFS::Vfs::Iterator *
OCPI::VFS::Http::HttpFsBase::
list (const std::string &, const std::string &)

{
  throw std::string ("cannot list files via HTTP");
  return 0; // silence some compilers
}

void
OCPI::VFS::Http::HttpFsBase::
closeIterator (OCPI::VFS::Vfs::Iterator *)

{
  throw std::string ("should not be here");
}
#endif

OCPI::VFS::Dir &OCPI::VFS::Http::HttpFsBase::openDir(const std::string &){
  throw std::string ("cannot list files via HTTP");
  return *(OCPI::VFS::Dir*)0; // silence some compilers
}

/*
 * ----------------------------------------------------------------------
 * File Information
 * ----------------------------------------------------------------------
 */

OCPI::Util::Http::ClientStream *
OCPI::VFS::Http::HttpFsBase::
hgpr (const std::string & fileName,
      bool head, bool get, bool post, bool a_remove)

{
  testFilenameForValidity (fileName);
  std::string nn = nativeFilename (fileName);
  OCPI::Util::Uri uri (nn);

  OCPI::Util::Http::ClientStream * conn = makeConnection ();

  /*
   * To do: protect against circular redirections
   */

 again:
  try {
    if (head) {
      conn->head (uri);
    }
    else if (get) {
      conn->get (uri);
    }
    else if (post) {
      conn->post (uri);
    }
    else if (a_remove) {
      conn->remove (uri);
    }
    else {
      assert (0);
    }
  }
  catch (OCPI::Util::Http::Redirection & redir) {
    if (redir.newLocation == uri.get()) {
      std::string reason = "redirection to identity at \"";
      reason += uri.get();
      reason += "\"";
      throw reason;
    }

    std::string duri = OCPI::Util::Uri::decode (redir.newLocation);

    if (duri.length() < m_baseURI.length() ||
        duri.compare (0, m_baseURI.length(), m_baseURI) != 0) {
      throw;
    }

    uri = redir.newLocation;
    goto again;
  }
  catch (OCPI::Util::Http::ClientError & error) {
    std::string reason = "file not found: \"";
    reason += error.reasonPhrase;
    reason += "\"";
    delete conn;
    throw reason;
  }
  catch (OCPI::Util::Http::ServerError & error) {
    std::string reason = "server error: \"";
    reason += error.reasonPhrase;
    reason += "\"";
    delete conn;
    throw reason;
  }
  catch (...) {
    delete conn;
    throw;
  }

  return conn;
}

bool
OCPI::VFS::Http::HttpFsBase::
exists (const std::string & fileName, bool * isDir)

{
  OCPI::Util::Http::ClientStream * conn;

  try {
    conn = hgpr (fileName, true, false, false, false);
  }
  catch (const std::string &) {
    return false;
  }

  int code = conn->statusCode ();
  delete conn;

  if (code >= 200 && code < 300) {
    if (isDir) {
      isDir = 0;
    }
    return true;
  }

  return false;
}

unsigned long long
OCPI::VFS::Http::HttpFsBase::
size (const std::string & fileName)

{
  OCPI::Util::Http::ClientStream * conn = hgpr (fileName, true, false, false, false);
  unsigned long long res;

  try {
    res = conn->contentLength ();
  }
  catch (...) {
    delete conn;
    throw;
  }

  delete conn;
  return res;
}

std::time_t
OCPI::VFS::Http::HttpFsBase::
lastModified (const std::string & fileName)

{
  OCPI::Util::Http::ClientStream * conn = hgpr (fileName, true, false, false, false);
  std::time_t res;

  try {
    res = conn->lastModified ();
  }
  catch (...) {
    delete conn;
    throw;
  }

  delete conn;
  return res;
}

/*
 * ----------------------------------------------------------------------
 * File I/O
 * ----------------------------------------------------------------------
 */

std::iostream *
OCPI::VFS::Http::HttpFsBase::
open (const std::string &, std::ios_base::openmode)

{
  throw std::string ("file modification not supported");
  return 0;
}

std::istream *
OCPI::VFS::Http::HttpFsBase::
openReadonly (const std::string & fileName, std::ios_base::openmode)

{ 
  return hgpr (fileName, false, true, false, false);
}

std::ostream *
OCPI::VFS::Http::HttpFsBase::openWriteonly (const std::string & fileName, std::ios_base::openmode)

{
  return hgpr (fileName, false, false, true, false);
}

void
OCPI::VFS::Http::HttpFsBase::close (std::ios * str)

{
  OCPI::Util::Http::ClientStream * conn =
    dynamic_cast<OCPI::Util::Http::ClientStream *> (str);

  if (!conn) {
    throw std::string ("unrecognized stream");
  }

  try {
    conn->close ();
  }
  catch (OCPI::Util::Http::Redirection & redir) {
    std::string reason = "oops: unexpected redirection to \"";
    reason += redir.newLocation;
    reason += "\"";
    delete conn;
    throw reason;
  }
  catch (OCPI::Util::Http::ClientError & error) {
    std::string reason = "client-side error: \"";
    reason += error.reasonPhrase;
    reason += "\"";
    delete conn;
    throw reason;
  }
  catch (OCPI::Util::Http::ServerError & error) {
    std::string reason = "server error: \"";
    reason += error.reasonPhrase;
    reason += "\"";
    delete conn;
    throw reason;
  }
  catch (...) {
    delete conn;
    throw;
  }

  delete conn;
}

/*
 * ----------------------------------------------------------------------
 * File system operations
 * ----------------------------------------------------------------------
 */

void
OCPI::VFS::Http::HttpFsBase::remove (const std::string & fileName)

{
  OCPI::Util::Http::ClientStream * conn = hgpr (fileName, false, false, false, true);
  delete conn;
}

/*
 * ----------------------------------------------------------------------
 * Test whether a file name is valid. Throw an exception if not.
 * ----------------------------------------------------------------------
 */

void
OCPI::VFS::Http::HttpFsBase::testFilenameForValidity (const std::string & name) const

{
  if (name.length() == 1 && name[0] == '/') {
    /*
     * An exception for the name of the root directory
     */
    return;
  }

  std::string::size_type pos = (name[0] == '/') ? 1 : 0;

  do {
    std::string::size_type nextSlash = name.find ('/', pos);
    std::string pathComponent;

    if (nextSlash == std::string::npos) {
      pathComponent = name.substr (pos);
      pos = std::string::npos;
    }
    else {
      pathComponent = name.substr (pos, nextSlash - pos);
      pos = nextSlash + 1;
    }

    /*
     * See if the path component is okay
     */

    if (pathComponent == "." || pathComponent == "..") {
      std::string reason = "invalid file name: \"";
      reason += pathComponent;
      reason += "\": invalid path component";
      throw reason;
    }

    if (pathComponent.find_first_of ("<>\\|\"") != std::string::npos) {
      std::string reason = "invalid file name: \"";
      reason += pathComponent;
      reason += "\": invalid character in path component";
      throw reason;
    }
  }
  while (pos != std::string::npos);
}

std::string
OCPI::VFS::Http::HttpFsBase::nativeFilename (const std::string & fileName) const

{
  OCPI::Util::AutoMutex lock (m_lock);
  std::string an = absoluteNameLocked (fileName);
  std::string uri = m_baseURI.substr (0, m_baseURI.length() - 1);
  uri += OCPI::Util::Uri::encode (an, "/");
  return uri;
}
