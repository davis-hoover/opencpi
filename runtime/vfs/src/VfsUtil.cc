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

#include <istream>
#include <string>

#include "VfsUtil.hh"
#include "Vfs.hh"
#include "VfsIterator.hh"
#include "UtilMisc.hh"

/*
 * ----------------------------------------------------------------------
 * isXMLDocument()
 * ----------------------------------------------------------------------
 */

bool
OCPI::VFS::
isXMLDocument (Vfs * fs, const std::string & fileName)

{
  /*
   * Ask OCPI::Util::Misc::isXMLDocument. Have to open file first.
   */

  bool result;

  try {
    std::istream * istr = fs->openReadonly (fileName);

    try {
      result = OCPI::Util::isXMLDocument (istr);
    }
    catch (...) {
      try {
        fs->close (istr);
      }
      catch (...) {
      }
      throw;
    }

    fs->close (istr);
  }
  catch (const std::string & oops) {
    std::string reason = "Cannot determine file type: ";
    reason += oops;
    throw reason;
  }

  return result;
}

/*
 * ----------------------------------------------------------------------
 * Recursive Copying and Deleting
 * ----------------------------------------------------------------------
 */

void
OCPI::VFS::
copyFilesRecursively (Vfs * srcFs, const std::string & srcDir,
                      Vfs * destFs, const std::string & destDir,
                      const std::string & pattern)

{
  if (OCPI::VFS::relativeName (pattern) != pattern)
    throw std::string ("pattern must not contain directory separator");

  Iterator it(*srcFs, srcDir, pattern.c_str());
  bool isDir;
  std::string name;

  while (it.next(name, isDir)) {
    std::string
      srcName(joinNames(srcDir, name)),
      destName(joinNames(destDir, name));
    if (isDir)
      copyDirectoryRecursively(srcFs, srcName,	destFs, destName, pattern);
    else
      srcFs->copy(srcName, destFs, destName);
  }
}

void
OCPI::VFS::
copyDirectoryRecursively (Vfs * srcFs, const std::string & srcName,
                          Vfs * destFs, const std::string & destName,
                          const std::string & pattern)

{
  destFs->mkdir (destName);
  copyFilesRecursively (srcFs, srcName, destFs, destName, pattern);
}

void
OCPI::VFS::
removeFilesRecursively (Vfs * fs,
                        const std::string & dir,
                        const std::string & pattern,
                        bool deleteEmptyDirectories)

{
  if (OCPI::VFS::relativeName (pattern) != pattern)
    throw std::string ("pattern must not contain directory separator");

  Iterator it(*fs, dir, pattern.c_str());
  bool isDir;
  std::string name;

  while (it.next(name, isDir)) {
    std::string fullName = joinNames(dir, name);
    if (isDir) {
      removeFilesRecursively(fs, fullName, pattern, deleteEmptyDirectories);
      /*
       * If deleteEmptyDirectories is true, see if that directory
       * is now empty. If yes, delete it.
       */
      if (deleteEmptyDirectories) {
	bool empty;
	{
	  Iterator it2(*fs, fullName);
	  empty = !it2.next(name, isDir);
	}
	if (empty)
          fs->rmdir(fullName);
      }
    } else
      fs->remove(fullName);
  }
}

void
OCPI::VFS::
removeDirectoryRecursively (Vfs * fs,
                            const std::string & dir,
                            const std::string & pattern,
                            bool deleteEmptyDirectories)

{
  removeFilesRecursively (fs, dir, pattern, deleteEmptyDirectories);

  if (deleteEmptyDirectories) {
    std::string name;
    bool isDir, empty;
    {
      Iterator it(*fs, dir);
      empty = !it.next(name, isDir);
    }
    if (empty)
      fs->rmdir(dir);
  }
}

/*
 * ----------------------------------------------------------------------
 * EventualEraser
 * ----------------------------------------------------------------------
 */

OCPI::VFS::EventualEraser::
EventualEraser ()

  : m_fs (0)
{
}

OCPI::VFS::EventualEraser::
EventualEraser (Vfs * fs, const std::string & name, bool isFile)

  : m_fs (fs),
    m_name (name),
    m_isFile (isFile)
{
}

OCPI::VFS::EventualEraser::
~EventualEraser ()

{
  if (m_fs) {
    try {
      if (m_isFile) {
        m_fs->remove (m_name);
      }
      else {
        OCPI::VFS::removeDirectoryRecursively (m_fs, m_name);
      }
    }
    catch (...) {
      // ignore any errors
    }
  }
}

void
OCPI::VFS::EventualEraser::
eventuallyErase (Vfs * fs, const std::string & name, bool isFile)

{
  if (m_fs) {
    throw std::string ("already in use");
  }

  m_fs = fs;
  m_name = name;
  m_isFile = isFile;
}

void
OCPI::VFS::EventualEraser::
cancel ()

{
  m_fs = 0;
}

