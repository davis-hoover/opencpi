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
 * Aggregate a set of files into a single data stream.
 *
 * Revision History:
 *
 *     06/10/2009 - Frank Pilhofer
 *                  GCC bug 40391 workaround.
 *
 *     05/27/2005 - Frank Pilhofer
 *                  Initial version.
 */

#include <iostream>
#include <string>
#include <map>
#include <set>
#include <ctime>
#include <cstring>
#include <cstdlib>
#include "OsAssert.hh"
#include "OsMutex.hh"
#include "UtilUri.hh"
#include "UtilMisc.hh"
#include "UtilAutoMutex.hh"
#include "Vfs.hh"
#include "VfsIterator.hh"
#include "VfsStreamFsWriter.hh"

/*
 * ----------------------------------------------------------------------
 * StreamFsWriterStream: std::ostream implementation for StreamFs
 * ----------------------------------------------------------------------
 */

namespace OcpiUtilStreamFsWriter {

  class StreamFsWriterStream : public std::ostream {
  protected:
    class StreamBuf : public std::streambuf {
    public:
      StreamBuf (std::ostream *);
      ~StreamBuf ();

    protected:
      int sync ();
      pos_type seekoff (off_type off, std::ios_base::seekdir way,
                        std::ios_base::openmode which);
      int_type overflow (int_type c);
      std::streamsize xsputn (const char *, std::streamsize);

    protected:
      std::ostream * m_stream;
      unsigned long long m_payload;
    };

  public:
    StreamFsWriterStream (std::ostream *, const std::string & name);
    ~StreamFsWriterStream ();

    const std::string & fileName () const;

  protected:
    StreamBuf m_buf;
    std::string m_name;
  };

  StreamFsWriterStream::StreamBuf::
  StreamBuf (std::ostream * str)
    : m_stream (str),
      m_payload (0)
  {
  }

  StreamFsWriterStream::StreamBuf::
  ~StreamBuf ()
  {
  }

  int
  StreamFsWriterStream::StreamBuf::
  sync ()
  {
    m_stream->flush ();
    return m_stream->good() ? 0 : -1;
  }

  std::streambuf::pos_type
  StreamFsWriterStream::StreamBuf::
  seekoff (off_type off, std::ios_base::seekdir way,
           std::ios_base::openmode)
  {
    if (way != std::ios_base::cur || off != 0) {
      return -1;
    }

    return OCPI::Util::unsignedToStreamsize (m_payload);
  }

  std::streambuf::int_type
  StreamFsWriterStream::StreamBuf::
  overflow (int_type i)
  {
    if (traits_type::eq_int_type (i, traits_type::eof())) {
      return traits_type::not_eof (i);
    }

    m_stream->put ((traits_type::char_type)i);

    if (m_stream->fail()) {
      return traits_type::eof ();
    }

    m_payload++;
    return i;
  }

  std::streamsize
  StreamFsWriterStream::StreamBuf::
  xsputn (const char * data, std::streamsize count)
  {
    if (count <= 0) {
      return 0;
    }

    m_stream->write (data, count);

    if (m_stream->fail()) {
      return 0;
    }

    m_payload += (decltype(m_payload))count;
    return count;
  }

  StreamFsWriterStream::StreamFsWriterStream (std::ostream * str,
                                              const std::string & name)
    : std::ostream (0),
      m_buf (str),
      m_name (name)
  {
    this->init (&m_buf);
  }

  StreamFsWriterStream::~StreamFsWriterStream ()
  {
  }

  const std::string &
  StreamFsWriterStream::fileName () const
  {
    return m_name;
  }

}

using namespace OcpiUtilStreamFsWriter;

/*
 * ----------------------------------------------------------------------
 * StreamFsWriter
 * ----------------------------------------------------------------------
 */

OCPI::VFS::StreamFs::StreamFsWriter::
StreamFsWriter ()

  : m_fs (0),
    m_stream (0),
    m_cwd ("/")
{
}

OCPI::VFS::StreamFs::StreamFsWriter::
StreamFsWriter (std::ostream * stream)

  : m_fs (0),
    m_stream (0),
    m_cwd ("/")
{
  openFs (stream);
}

OCPI::VFS::StreamFs::StreamFsWriter::
StreamFsWriter (Vfs * fs, const std::string & name)

  : m_fs (0),
    m_stream (0),
    m_cwd ("/")
{
  openFs (fs, name);
}

OCPI::VFS::StreamFs::StreamFsWriter::
~StreamFsWriter ()

{
  if (m_stream) {
    try {
      closeFs ();
    }
    catch (...) {
    }
  }
}

void
OCPI::VFS::StreamFs::StreamFsWriter::
openFs (std::ostream * stream)

{
  OCPI::Util::AutoMutex lock (m_mutex);

  if (m_stream) {
    throw std::string ("already open");
  }

  m_stream = stream;
  m_fs = 0;
  m_cwd = "/";
  m_pos = 0;
  m_openFiles = 0;
  m_baseURI = "streamfs://[somestream]/";
}

void
OCPI::VFS::StreamFs::StreamFsWriter::
openFs (Vfs * fs, const std::string & name)

{
  OCPI::Util::AutoMutex lock (m_mutex);

  if (m_stream) {
    throw std::string ("already open");
  }

  m_stream = 0;
  m_fs = fs;
  m_name = name;
  m_cwd = "/";
  m_pos = 0;
  m_openFiles = 0;

  std::string authority = fs->nameToURI (name);
  m_baseURI  = "streamfs://";
  m_baseURI += OCPI::Util::Uri::encode (authority);
  m_baseURI += "/";

  m_stream = m_fs->openWriteonly (m_name, std::ios_base::binary | std::ios_base::trunc);
}

void
OCPI::VFS::StreamFs::StreamFsWriter::
closeFs ()

{
  OCPI::Util::AutoMutex lock (m_mutex);

  ocpiAssert (!m_openFiles);

  if (m_stream) {
    std::ostream * omstream = m_stream;

    try {
      dumpTOC ();
    }
    catch (...) {
      m_stream = 0;

      if (m_fs) {
        try {
          m_fs->close (omstream);
        }
        catch (...) {
        }
      }

      throw;
    }

    m_stream = 0;

    if (m_fs) {
      m_fs->close (omstream);
    }
  }
}

/*
 * ----------------------------------------------------------------------
 * Write a Table of Contents at the end of the stream
 * ----------------------------------------------------------------------
 *
 * Four text lines are written for every file:
 * - The absolute file name.
 * - The position of the file's first octet in the stream.
 * - The size of the file, in octets.
 * - The last modification timestamp.
 *
 * At the very end, in the last 17 octets of the stream, the position
 * of the table of contents is written, with a final LF.
 *
 * Thus, a reader can seek to the end minus 17 octets, read the TOC's
 * position, then seek to the TOC, read the TOC, and then start reading
 * files.
 */

void
OCPI::VFS::StreamFs::StreamFsWriter::
dumpTOC ()

{
  /*
   * Current position, i.e., the position of the TOC, is in m_pos.
   */

  for (TOC::iterator it=m_toc.begin(); it!=m_toc.end() && m_stream->good(); it++) {
    std::string pos =
      OCPI::Util::unsignedToString ((*it).second.pos);
    std::string sizeStr =
      OCPI::Util::unsignedToString ((*it).second.size);
    std::string lm =
      OCPI::Util::unsignedToString (static_cast<unsigned long long> ((*it).second.lastModified));

    m_stream->put ('\n');
    m_stream->write ((*it).first.data(), (std::streamsize)(*it).first.length());
    m_stream->put ('\n');
    m_stream->write (pos.data(), (std::streamsize)pos.length());
    m_stream->put ('\n');
    m_stream->write (sizeStr.data(), (std::streamsize)sizeStr.length());
    m_stream->put ('\n');
    m_stream->write (lm.data(), (std::streamsize)lm.length());
  }

  std::string tp =
    OCPI::Util::unsignedToString (m_pos, 10, 16, ' ');

  m_stream->write ("\n<End Of TOC>\n", 14);
  m_stream->write (tp.data(), (std::streamsize)tp.length());
  m_stream->put ('\n');

  if (!m_stream->good()) {
    throw std::string ("output stream not good");
  }
}

/*
 * ----------------------------------------------------------------------
 * URI Mapping
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::StreamFs::StreamFsWriter::
baseURI () const

{
  return m_baseURI;
}

std::string
OCPI::VFS::StreamFs::StreamFsWriter::
nameToURI (const std::string & fileName) const

{
  std::string an = absoluteName (fileName);
  std::string uri = m_baseURI.substr (0, m_baseURI.length() - 1);
  uri += OCPI::Util::Uri::encode (an, "/");
  return uri;
}

std::string
OCPI::VFS::StreamFs::StreamFsWriter::
URIToName (const std::string & uri) const

{
  if (uri.length() < m_baseURI.length() ||
      uri.compare (0, m_baseURI.length(), m_baseURI) != 0 ||
      m_baseURI.compare (0, 24, "streamfs://[somestream]/") == 0) {
    throw std::string ("URI not understood by this file system");
  }

  std::string eap = uri.substr (m_baseURI.length() - 1);
  return OCPI::Util::Uri::decode (eap);
}

/*
 * ----------------------------------------------------------------------
 * File Name Mapping
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::StreamFs::StreamFsWriter::
absoluteNameLocked (const std::string & name) const

{
  return OCPI::VFS::joinNames (m_cwd, name);
}

/*
 * ----------------------------------------------------------------------
 * Directory Management
 * ----------------------------------------------------------------------
 */

std::string
OCPI::VFS::StreamFs::StreamFsWriter::
cwd () const

{
  OCPI::Util::AutoMutex lock (m_mutex);
  return m_cwd;
}

void
OCPI::VFS::StreamFs::StreamFsWriter::
cd (const std::string & fileName)

{
  OCPI::Util::AutoMutex lock (m_mutex);
  m_cwd = absoluteName (fileName);
}

void
OCPI::VFS::StreamFs::StreamFsWriter::
mkdir (const std::string &)

{
  /* no-op */
}

void
OCPI::VFS::StreamFs::StreamFsWriter::
rmdir (const std::string &)

{
  throw std::string ("not supported on this file system");
}

#if 0
/*
 * ----------------------------------------------------------------------
 * Directory Listing
 * ----------------------------------------------------------------------
 */

OCPI::VFS::Iterator *
OCPI::VFS::StreamFs::StreamFsWriter::
list (const std::string &, const std::string &)

{
  throw std::string ("not supported on this file system");
}

void
OCPI::VFS::StreamFs::StreamFsWriter::
closeIterator (OCPI::VFS::Iterator *)

{
  ocpiAssert (0);
}
#endif
/*
 * ----------------------------------------------------------------------
 * File information
 * ----------------------------------------------------------------------
 */

bool
OCPI::VFS::StreamFs::StreamFsWriter::
exists (const std::string &, bool *)

{
  throw std::string ("not supported on this file system");
  return false;
}

unsigned long long
OCPI::VFS::StreamFs::StreamFsWriter::
size (const std::string &)

{
  throw std::string ("not supported on this file system");
  return 0;
}

std::time_t
OCPI::VFS::StreamFs::StreamFsWriter::
lastModified (const std::string &)

{
  throw std::string ("not supported on this file system");
  return 0;
}

/*
 * ----------------------------------------------------------------------
 * File I/O
 * ----------------------------------------------------------------------
 */

std::iostream *
OCPI::VFS::StreamFs::StreamFsWriter::
open (const std::string &, std::ios_base::openmode)

{
  throw std::string ("not supported on this file system");
  return 0;
}

std::istream *
OCPI::VFS::StreamFs::StreamFsWriter::
openReadonly (const std::string &,
              std::ios_base::openmode)

{
  throw std::string ("not supported on this file system");
  return 0;
}

std::ostream *
OCPI::VFS::StreamFs::StreamFsWriter::
openWriteonly (const std::string & fileName,
               std::ios_base::openmode)

{
  OCPI::Util::AutoMutex lock (m_mutex);

  if (m_openFiles) {
    throw std::string ("opening more than one file not supported");
  }

  if (!m_stream->good()) {
    throw std::string ("output stream is not good");
  }

  std::string nn = absoluteNameLocked (fileName);
  TOC::iterator it = m_toc.find (nn);

  if (it != m_toc.end()) {
    throw std::string ("file exists");
  }

  Node & inode = m_toc[nn];
  inode.pos = m_pos;
  m_openFiles++;

  return new StreamFsWriterStream (m_stream, nn);
}

void
OCPI::VFS::StreamFs::StreamFsWriter::
close (std::ios * str)

{
  OCPI::Util::AutoMutex lock (m_mutex);

  StreamFsWriterStream * sfws = dynamic_cast<StreamFsWriterStream *> (str);

  if (!sfws) {
    throw std::string ("not opened by this fs");
  }

  std::string fileName = sfws->fileName ();
  TOC::iterator it = m_toc.find (fileName);
  ocpiAssert (it != m_toc.end());

  std::streamoff fileSize = sfws->tellp ();
  ocpiAssert (fileSize >= 0);

  delete sfws;

  if (!m_stream->good()) {
    m_toc.erase (it);
    throw std::string ("output stream is not good");
  }

  m_pos += (decltype(m_pos))fileSize;
  (*it).second.size = (decltype(m_pos))fileSize;
  (*it).second.lastModified = std::time (0);

  ocpiAssert (m_openFiles == 1);
  m_openFiles--;
}

/*
 * ----------------------------------------------------------------------
 * File system operations
 * ----------------------------------------------------------------------
 */

void
OCPI::VFS::StreamFs::StreamFsWriter::
remove (const std::string &)

{
  throw std::string ("not supported on this file system");
}

