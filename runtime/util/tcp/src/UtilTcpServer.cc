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

#include "UtilTcpServer.hh"
#include "UtilTcpStream.hh"
#include "OsServerSocket.hh"
#include "OsSocket.hh"
#include <string>

/*
 * ----------------------------------------------------------------------
 * OCPI::Util::Tcp::Server
 * ----------------------------------------------------------------------
 */

OCPI::Util::Tcp::Server::Server ()

{
  m_open = false;
}

OCPI::Util::Tcp::Server::Server (uint16_t portno, bool reuse)

{
  m_open = false;
  bind (portno, reuse);
}

OCPI::Util::Tcp::Server::~Server ()

{
  if (m_open) {
    close ();
  }
}

void
OCPI::Util::Tcp::Server::bind (uint16_t portNo, bool reuse)

{
  if (m_open) {
    throw std::string ("already bound");
  }

  m_socket.bind (portNo, reuse);
  m_open = true;
}

OCPI::Util::Tcp::Stream *
OCPI::Util::Tcp::Server::accept (unsigned long timeout)

{
  if (!m_open) {
    throw std::string ("not bound");
  }

  if (!m_socket.wait((long)timeout)) {
    return 0;
  }

  OCPI::OS::Socket conn;
  m_socket.accept(conn);
  return new OCPI::Util::Tcp::Stream(conn);
}

uint16_t
OCPI::Util::Tcp::Server::getPortNo ()

{
  if (!m_open) {
    throw std::string ("not bound");
  }

  return m_socket.getPortNo ();
}

void
OCPI::Util::Tcp::Server::close ()

{
  if (!m_open) {
    throw std::string ("not bound");
  }

  m_open = false;
  m_socket.close ();
}
