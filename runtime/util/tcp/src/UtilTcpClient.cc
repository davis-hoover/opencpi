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

#include "UtilTcpClient.hh"
#include "OsSocket.hh"
#include <string>

/*
 * ----------------------------------------------------------------------
 * OCPI::Util::Tcp::Client
 * ----------------------------------------------------------------------
 */

OCPI::Util::Tcp::Client::Client ()

{
}

OCPI::Util::Tcp::Client::Client (const std::string & host, uint16_t port)

{
  connect (host, port);
}

OCPI::Util::Tcp::Client::~Client ()

{
}

void
OCPI::Util::Tcp::Client::connect (const std::string & host, uint16_t port)

{
  OCPI::OS::Socket conn;
  conn.connect(host, port);
  setSocket(conn);
}
