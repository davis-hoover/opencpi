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

#include "UtilLogger.hh"
#include "UtilLoggerDebugLogger.hh"
#include "UtilLoggerOStreamOutput.hh"
#include "VfsHttpServer.hh"
#include "UtilTcpServer.hh"
#include "VfsFileFs.hh"
#include "OsFileSystem.hh"
#include <iostream>
#include <string>
#include <cstdlib>

namespace OV = OCPI::VFS;
namespace OU = OCPI::Util;
namespace OL = OCPI::Logger;
int
main (int argc, char *argv[])
{
  if (argc != 1 && argc != 2) {
    std::cout << "usage: " << argv[0] << std::endl;
    return 1;
  }

  uint16_t portNo = 0;

  if (argc == 2) {
    portNo = (uint16_t)std::strtoul (argv[1], 0, 0);
  }

  try {
    OL::OStreamOutput logger (std::cout);
    OV::FileFs localFs;
    OV::Http::Server server (&localFs, &logger);
    OU::Tcp::Server serverPort (portNo, true);

    OCPI::Logger::debug ("All", 42);

    std::cout << "Running on port "
              << serverPort.getPortNo()
              << "."
              << std::endl;

    OU::Tcp::Stream * stream;

    while ((stream = serverPort.accept())) {
      server.resetConn (stream, stream);
      server.run ();
      delete stream;
    }
  }
  catch (const std::string & oops) {
    std::cout << "Oops: " << oops << std::endl;
  }
  catch (...) {
    std::cout << "Oops." << std::endl;
  }

  return 0;
}
