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

// -*- c++ -*-

#ifndef OCPIOSSOCKET_H__
#define OCPIOSSOCKET_H__

/**
 * \file
 *
 * \brief Bidirectional communication between two peers.
 *
 * Revision History:
 *
 *     06/30/2005 - Frank Pilhofer
 *                  Use 64-bit type for our opaque data, to ensure
 *                  alignment.
 *
 *     04/19/2005 - Frank Pilhofer
 *                  Initial version.
 *
 */

#include "OsDataTypes.hh"
#include <string>

namespace OCPI {
  namespace OS {

    /**
     * \brief Bidirectional communication between two peers.
     *
     * Socket allows bidirectional communication between two peers.
     * Sockets can not be instantiated.  Socket instances are returned
     * by OCPI::OS::ClientSocket::connect() and
     * OCPI::OS::ServerSocket::accept().
     */

    class Socket {
      void init();
    protected:
      friend class ServerSocket;
      void setOpaque(uint64_t *opaque);
    public:
      /**
       * Constructor: Initialize an unconnected socket.
       * 
       * The only way to "connect" a socket instance is using the
       * assignment operator, assigning this instance from a
       * socket that was returned from a ClientSocket::connect()
       * or ServerSocket::accept() operation.
       *
       * \post The socket is not connected.
       */

      Socket();

      Socket(const std::string & remoteHost, uint16_t remotePort, bool udp = false);
      /**
       * Copy constructor: Assigns ownership of the \a other socket to
       *                   this instance. After this, \a other may not
       *                   be used.
       *
       * \param[in] other A socket instance.
       *
       * \pre \a other shall be connected.
       * \post This socket is connected.  \a other is unconnected.
       */

      Socket(const Socket &other);

      /**
       * Assignment operator: Assigns ownership of the \a other socket to
       *                      this instance. After this, \a other may not
       *                      be used.
       *
       * \param[in] other A socket instance.
       *
       * \pre \a other shall be connected.
       * \post This socket is connected.  \a other is unconnected.
       */

      Socket &operator=(const Socket &other);

      /**
       * Destructor.
       *
       * \pre The socket shall be unconnected.
       */

      ~Socket();

      /**
       * Receives data from the peer.
       *
       * Blocks until at least one octet can be read from the socket. Then
       * reads as much data as is available, up to at most \a amount octets.
       *
       * \param[out] buffer The memory location where to put the received data.
       * \param[in] amount  The maximum number of octets to read from the peer.
       * \return       The number of octets actually read, which may be
       *               less than "amount". A return value of zero indicates
       *               end of data (i.e., the other end has closed or shut
       *               down its end of the connection).
       *
       * \throw std::string In case of error, such as a broken connection.
       *
       * \pre The socket shall be connected.
       */
      size_t recv(char *buffer, size_t amount, unsigned timeoutms = 0, bool all = false);
      size_t recvfrom(char *buf, size_t amount, int flags, char *src_addr, size_t *addrlen,
		      unsigned timeoutms = 0);

      /**
       * Sends data to the peer.
       *
       * Keeps trying until all bytes are sent, and loops if interrupted with EINTR errors
       *
       * \param[in] data    The data to send.
       * \param[in] amount  The maximum number of octets to send to the peer.
       * \return            None
       *
       * \throw std::string In case of error, such as a broken connection.
       *
       * \pre The socket shall be connected.
       */

      size_t send(const char *data, size_t amount);
      // Note the iov is const, we keep trying until it is all sent
      void send(struct IOVec *iov, unsigned iovcnt);
      size_t sendmsg(const void *iovect, int flags);
      size_t sendto(const char *data, size_t amount, int flags, char *src_addr, size_t addrlen);

      /**
       * Returns the socket's local port number.
       *
       * \return The socket's local port number.
       *
       * \throw std::string Operating system error.
       *
       * \pre The socket shall be connected.
       */

      uint16_t getPortNo();

      /**
       * Returns the host name and the port number of the remote peer.
       *
       * \param[out] peerHost The name of the remote host.
       * \param[out] peerPort The port number of the peer on the remote host.
       *
       * \throw std::string Operating system error.
       *
       * \pre The socket shall be connected.
       */

      void getPeerName (std::string &peerHost, uint16_t &peerPort) const;

      /**
       * Configure behavior upon close().
       *
       * If the linger option is turned on (opt==true), then close() blocks
       * util all the peer has acknowledged reception of all data that was
       * sent to it, or throws an exception if the peer does not process
       * all data. If the linger option is turned off (opt==false), then
       * close() does not wait. In this case, it may be possible that an
       * error goes undetected, if the peer breaks after the connection
       * was closed.
       *
       * \param[in] opt Whether to "linger" at close().
       *
       * \throw std::string Operating system error.
       *
       * \pre The socket shall be connected.
       */

      void linger(bool opt = true);

      /**
       * Performs a half-close.
       *
       * Shutting down the sending end informs the peer that no more data
       * will be sent (if the peer then calls recv() on its end, it will
       * return 0). The socket can continue receiving data. If the
       * receiving end is closed, and the peer sends more data, the peer
       * will be signaled a "broken pipe" error.
       *
       * For example, in HTTP 1.0 connections, the client usually shuts
       * down the sending end of its socket after sending the request,
       * thus informing the server of the request's completion. The
       * client can then read the response from the socket.
       *
       * Note that shutting down both ends is not equivalent to closing
       * the socket, which must always be done separately.
       *
       * \param[in] sendingEnd Whether to close the sending end (true) or the
       *                  receiving end (false).
       *
       * \throw std::string Operating system error.
       *
       * \pre The socket shall be connected.
       */

      void shutdown(bool sendingEnd = true);

      /**
       * Closes (disconnects) the socket.
       *
       * A socket must be closed before it can be destructed.
       *
       * If the "linger" option is true, blocks while unsent data lingers
       * in the socket's internal buffers, until that data is acknowledged
       * by the peer.
       *
       * \throw std::string If unsent data remains in the socket's
       * buffers, and the peer stopped receiving data.
       *
       * \pre The socket shall be connected.
       * \post The socket is unconnected.
       */

      void close();

      /**
       * Creates a duplicate of the socket.
       *
       * The duplicate and the original can be used equivalently. This may
       * be done, e.g., to use one copy for sending and one for receiving
       * data.
       *
       * The shutdown() operation affects all duplicates of a socket. The
       * close() operation only affects one instance.
       *
       * \throw std::string Operating system error.
       *
       * \pre The socket shall be connected.
       * \post Both this socket and the newly created socket are connected.
       */

      Socket dup();

      int fd() const;

      void connect(const std::string &remoteHost, uint16_t remotePort, bool udp = false);

    protected:
      uint64_t m_osOpaque[1];
    private:
      bool     m_temporary; // kludge to make up for broken interface FIXME by changing the interface
      bool     m_nodelay; // has this socket had no-delay set?
      unsigned m_timeoutms;
      size_t   m_sendSize, m_receiveSize; // current setting of SO_SNDBUF and SO_RECVBUF
    };
  }
}

#endif
