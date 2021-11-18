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

#include <iostream>
#include <iomanip>
#include <string>
#include <memory>
#include "ocpi-config.h"
#include "VfsIterator.hh"
#include "VfsZipFs.hh"
#include "VfsFileFs.hh"
#include "OsFileSystem.hh"

#if defined(OCPI_OS_VERSION_r5)
  #define unique_ptr auto_ptr
#endif

void
copyFilesRecursively (OCPI::VFS::Vfs * fs1, const std::string & name1,
                      OCPI::VFS::Vfs * fs2, const std::string & name2)
{
  std::unique_ptr<OCPI::VFS::Iterator> it(fs1->list (name1));
  std::string name;
  bool isDir;

  while (!it->next(name, isDir)) {
    std::string
      targetName = OCPI::VFS::joinNames (name2, name),
      absName = OCPI::VFS::joinNames(name1, name);

    if (isDir) {
      std::cout << "Recursing into "
                << targetName
                << "/"
                << std::endl;

      copyFilesRecursively (fs1, absName,
                            fs2, targetName);

      std::cout << "Done with "
                << targetName
                << "/"
                << std::endl;
    }
    else {
      std::cout << "Copying "
                << targetName
                << " (" << fs1->size(name) << " bytes) ... "
                << std::flush;
      fs1->copy (absName, fs2, targetName);
      std::cout << "done." << std::endl;
    }
  }
}

int
main (int argc, char *argv[])
{
  if (argc != 3) {
    std::cout << "usage: " << argv[0] << " <zipfile> <pattern>" << std::endl;
    return 1;
  }

  OCPI::VFS::FileFs localFs ("/");
  std::string zipName = OCPI::OS::FileSystem::fromNativeName (argv[1]);
  std::string absZipName = OCPI::OS::FileSystem::absoluteName (zipName);
  std::string patName = OCPI::OS::FileSystem::fromNativeName (argv[2]);
  std::string absPatName = OCPI::OS::FileSystem::absoluteName (patName);
  std::string patDirName = OCPI::OS::FileSystem::directoryName (absPatName);
  std::string patRelName = OCPI::OS::FileSystem::relativeName (absPatName);
  OCPI::VFS::ZipFs::ZipFs zipFs;

  std::ios_base::openmode mode = std::ios_base::in | std::ios_base::out;

  if (localFs.exists (absZipName)) {
    std::cout << "Using " << absZipName << std::endl;
  }
  else {
    std::cout << "Creating " << absZipName << std::endl;
    mode |= std::ios_base::trunc;
  }

  try {
    zipFs.openZip (&localFs, absZipName, mode);
  }
  catch (const std::string & oops) {
    std::cout << "error: " << oops << std::endl;
    return 1;
  }

  std::unique_ptr<OCPI::VFS::Iterator> toAdd(localFs.list (patDirName, patRelName));
  std::string name;
  bool isDir;

  try {
    while (toAdd->next(name, isDir)) {
      std::string absName(OCPI::VFS::joinNames(patDirName, name));
      if (isDir) {
        std::cout << "Recursing into "
                  << name
                  << "/"
                  << std::endl;
        copyFilesRecursively (&localFs,
                              absName,
                              &zipFs,
                              name);
        std::cout << "Done with "
                  << name
                  << "/"
                  << std::endl;
      }
      else {
        std::cout << "Copying "
                  << name
                  << " (" << localFs.size(absName) << " bytes) ... "
                  << std::flush;
        localFs.copy (absName,
                      &zipFs,
                      name);
        std::cout << "done." << std::endl;
      }
    }
  }
  catch (const std::string & oops) {
    std::cout << "oops: " << oops << std::endl;
  }
  return 0;
}
