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

#include "OsAssert.hh"
#include "OsFileSystem.hh"
#include "OsFileIterator.hh"
#include "OsSizeCheck.hh"
#include "OsDataTypes.hh"
#include <string>
#include <ctime>
#include <new>
#include <sys/types.h>
#include <sys/stat.h>
#include <dirent.h>
#include <errno.h>
#include <unistd.h>
#include "OsPosixError.hh"

namespace {
  struct FileIteratorData {
    bool active;
    bool atend;
    std::string dir;
    std::string relPattern;
    std::string absPattern;
    std::string prefix;
    DIR * search;
    struct dirent * dirInfo;
    struct stat fileInfo;
  };

  bool
  glob (const std::string & str,
        const std::string & pat)

  {
    size_t strIdx = 0, strLen = str.length ();
    size_t patIdx = 0, patLen = pat.length ();
    const char * name = str.data ();
    const char * pattern = pat.data ();

    while (strIdx < strLen && patIdx < patLen) {
      if (*pattern == '*') {
        pattern++;
        patIdx++;
        while (strIdx < strLen) {
          if (glob (name, pattern)) {
            return true;
          }
          strIdx++;
          name++;
        }
        return (patIdx < patLen) ? false : true;
      }
      else if (*pattern == '?' || *pattern == *name) {
        pattern++;
        patIdx++;
        name++;
        strIdx++;
      }
      else {
        return false;
      }
    }
    
    while (*pattern == '*' && patIdx < patLen) {
      pattern++;
      patIdx++;
    }
    
    if (patIdx < patLen || strIdx < strLen) {
      return false;
    }
    
    return true;
  }

  bool
  matchingFileName (FileIteratorData & data)

  {
    ocpiAssert (!data.atend);

    if (data.dirInfo->d_name[0] == '.' && !data.dirInfo->d_name[1]) {
      return false;
    }
    else if (data.dirInfo->d_name[0] == '.' &&
             data.dirInfo->d_name[1] == '.' &&
             !data.dirInfo->d_name[2]) {
      return false;
    }

    return glob (data.dirInfo->d_name, data.relPattern);
  }
}

inline
FileIteratorData &
o2fid (OCPI::OS::uint64_t * ptr)

{
  return *reinterpret_cast<FileIteratorData *> (ptr);
}

inline
const FileIteratorData &
o2fid (const OCPI::OS::uint64_t * ptr)

{
  return *reinterpret_cast<const FileIteratorData *> (ptr);
}

OCPI::OS::FileIterator::FileIterator (const std::string & dir,
                                     const std::string & pattern)

{
  ocpiAssert ((compileTimeSizeCheck<sizeof (m_osOpaque), sizeof (FileIteratorData)> ()));
  ocpiAssert (sizeof (m_osOpaque) >= sizeof (FileIteratorData));

  std::string absoluteDirName = FileSystem::absoluteName (dir);
  std::string absolutePatName = FileSystem::joinNames (absoluteDirName, pattern);

  new (m_osOpaque) FileIteratorData ();

  FileIteratorData & data = o2fid (m_osOpaque);
  data.active = false;
  data.dir = FileSystem::directoryName (absolutePatName);
  data.relPattern = FileSystem::relativeName (absolutePatName);
  data.absPattern = absolutePatName;

  if (pattern.find ('/') != std::string::npos) {
    data.prefix = FileSystem::directoryName (pattern);
  }

  /*
   * This makes sure that the directory exists and initializes the
   * members to point to the first file, if it exists.
   */

  try {
    end ();
  }
  catch (...) {
    data.FileIteratorData::~FileIteratorData ();
    throw;
  }
}

OCPI::OS::FileIterator::FileIterator (const FileIterator & other)

{
  const FileIteratorData & otherData = o2fid (other.m_osOpaque);

  new (m_osOpaque) FileIteratorData;
  FileIteratorData & data = o2fid (m_osOpaque);
  data.active = false;
  data.dir = otherData.dir;
  data.relPattern = otherData.relPattern;
  data.absPattern = otherData.absPattern;
  data.prefix = otherData.prefix;

  /*
   * This makes sure that the directory exists and initializes the
   * members to point to the first file, if it exists.
   */

  try {
    end ();
  }
  catch (...) {
    data.FileIteratorData::~FileIteratorData ();
    throw;
  }
}

OCPI::OS::FileIterator::~FileIterator ()

{
  close();
  FileIteratorData & data = o2fid (m_osOpaque);
  data.FileIteratorData::~FileIteratorData ();
}

OCPI::OS::FileIterator &
OCPI::OS::FileIterator::operator= (const FileIterator & other)

{
  const FileIteratorData & otherData = o2fid (other.m_osOpaque);
  FileIteratorData & data = o2fid (m_osOpaque);
  data.active = false;
  data.dir = otherData.dir;
  data.relPattern = otherData.relPattern;
  data.absPattern = otherData.absPattern;
  data.prefix = otherData.prefix;
  return *this;
}

bool
OCPI::OS::FileIterator::end ()

{
  FileIteratorData & data = o2fid (m_osOpaque);

  if (!data.active) {
    std::string nativeDir = FileSystem::toNativeName (data.dir);
    data.active = true;

    if (!(data.search = opendir (nativeDir.c_str()))) {
      if (errno == ENOENT)
	data.atend = true;
      else
	throw OCPI::OS::Posix::getErrorMessage (errno);
    } else {
      data.atend = false;
      // Skip to the first matching file if not at end
      next ();
    }
  }

  return data.atend;
}

std::string
OCPI::OS::FileIterator::relativeName ()

{
  FileIteratorData & data = o2fid (m_osOpaque);
  ocpiAssert (data.active && !data.atend);

  if (data.prefix.empty()) {
    return data.dirInfo->d_name;
  }

  return FileSystem::joinNames (data.prefix, data.dirInfo->d_name);
}

const char *
OCPI::OS::FileIterator::relativeName(std::string &rel)

{
  rel = relativeName();
  return rel.c_str();
}

std::string
OCPI::OS::FileIterator::absoluteName ()

{
  FileIteratorData & data = o2fid (m_osOpaque);
  ocpiAssert (data.active && !data.atend);
  return FileSystem::joinNames (data.dir, data.dirInfo->d_name);
}

const char *
OCPI::OS::FileIterator::absoluteName(std::string &abs)

{
  FileIteratorData & data = o2fid (m_osOpaque);
  ocpiAssert (data.active && !data.atend);
  return FileSystem::joinNames(data.dir, data.dirInfo->d_name, abs);
}

bool
OCPI::OS::FileIterator::isDirectory ()

{
  FileIteratorData & data = o2fid (m_osOpaque);
  ocpiAssert (data.active && !data.atend);

  if ((data.fileInfo.st_mode & S_IFMT) == S_IFDIR) {
    return true;
  }

  return false;
}

unsigned long long
OCPI::OS::FileIterator::size ()

{
  FileIteratorData & data = o2fid (m_osOpaque);
  ocpiAssert (data.active && !data.atend);

  if ((data.fileInfo.st_mode & S_IFMT) != S_IFREG) {
    throw std::string ("not a regular file");
  }

  return (unsigned long long)data.fileInfo.st_size;
}

std::time_t
OCPI::OS::FileIterator::lastModified ()

{
  FileIteratorData & data = o2fid (m_osOpaque);
  ocpiAssert (data.active && !data.atend);
  return data.fileInfo.st_mtime;
}

bool
OCPI::OS::FileIterator::next ()

{
  FileIteratorData & data = o2fid (m_osOpaque);
  ocpiAssert (data.active && !data.atend);

  while (!data.atend) {
    if (!(data.dirInfo = readdir (data.search))) {
      data.atend = true;
      break;
    }

    if (!matchingFileName (data)) {
      continue;
    }

    std::string absoluteFileName = FileSystem::joinNames (data.dir, data.dirInfo->d_name);
    std::string nativeName = FileSystem::toNativeName (absoluteFileName);

    if (lstat (nativeName.c_str(), &data.fileInfo)) {
      continue;
    }
    if ((data.fileInfo.st_mode & S_IFMT) == S_IFLNK) {
      char buf[10]; // just enough for "." and ".."
      switch (readlink(nativeName.c_str(), buf, sizeof(buf))) {
      case 2:
	if (buf[1] != '.')
	  break;
	// fallthrough
      case 1:
	if (buf[0] != '.')
	  break;
	// fallthrough
      case 0:
      case -1:
	ocpiDebug("Skipping symlink at '%s': that is . or .. or a problem", nativeName.c_str());
	continue;
      }
    }
    /*
     * Good match
     */

    break;
  }

  return !data.atend;
}

void
OCPI::OS::FileIterator::close ()

{
  FileIteratorData & data = o2fid (m_osOpaque);

  if (data.active && data.search) {
    closedir (data.search);
    data.search = 0;
    data.atend = true;
  }
}
