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

#include <stdint.h>
#include <assert.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/uio.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <netdb.h>
#include <cerrno>
#include <climits>
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <string>
#include "ocpi-config.h"
#include "OsAssert.hh"
#include "OsIovec.hh"
#include "OsSizeCheck.hh"
//#include "OsDataTypes.hh"
#include "OsPosixError.hh"
#include "OsPosixSocket.hh"
#include "OsSocket.hh"

static inline int &o2fd(uint64_t *o) { return *(int*)o; }
static inline const int &o2fd(const uint64_t *o) { return *(int*)o; }

namespace OCPI {
  namespace OS {
int Socket::
fd() const {
  return o2fd(m_osOpaque);
}

void Socket::
init() {
  m_nodelay = false;
  m_temporary = false;
  m_timeoutms = 0;
  m_sendSize = m_receiveSize = 0;
  ocpiAssert ((compileTimeSizeCheck<sizeof (m_osOpaque), sizeof (int)> ()));
  ocpiAssert (sizeof (m_osOpaque) >= sizeof (int));
  o2fd(m_osOpaque) = -1;
}
Socket::
Socket () {
  init();
}

#if 0
Socket::
Socket (const uint64_t * opaque) {
  m_temporary = true;
  m_timeoutms = 0;
  ocpiAssert ((compileTimeSizeCheck<sizeof(m_osOpaque), sizeof(int)> ()));
  ocpiAssert (sizeof(m_osOpaque) >= sizeof(int));
  o2fd(m_osOpaque) = o2fd(opaque);
}
#endif

Socket::
Socket(const std::string &remoteHost, uint16_t remotePort, bool udp) {
  init();
  connect(remoteHost, remotePort, udp);
}

Socket::
Socket (const Socket & other) {
  init();
  o2fd(m_osOpaque) = ::dup(o2fd(other.m_osOpaque));
}

Socket & Socket::
operator= (const Socket & other) {
  init();
  o2fd(m_osOpaque) = ::dup(o2fd(other.m_osOpaque));
  return *this;
}

Socket::
~Socket () {
  if (!m_temporary && o2fd(m_osOpaque) != -1)
    close();
}

void Socket::
setOpaque(uint64_t *o) {
  m_osOpaque[0] = *o;
  int sndbuf, rcvbuf, fileno = o2fd(m_osOpaque);
  socklen_t size = sizeof(int);
  if (getsockopt(fileno, SOL_SOCKET, SO_SNDBUF, &sndbuf, &size) ||
      getsockopt(fileno, SOL_SOCKET, SO_RCVBUF, &rcvbuf, &size))
    throw Posix::getErrorMessage(errno, "getsockopt");
  m_sendSize = (unsigned)sndbuf/2;
  m_receiveSize = (unsigned)rcvbuf/2;
  ocpiInfo("Socket connected.  rcvbuf %u sndbuf %u", sndbuf, rcvbuf);
}

void Socket::
connect(const std::string & remoteHost, uint16_t remotePort, bool udp) {
  struct sockaddr_in sin;

  std::memset (&sin, 0, sizeof (struct sockaddr_in));
  sin.sin_family = AF_INET;
#ifdef OCPI_OS_macos
  sin.sin_len = sizeof(sin);
#endif
  sin.sin_port = htons (remotePort);
  if (!::inet_aton (remoteHost.c_str(), &sin.sin_addr)) {
    Posix::netDbLock ();
    struct hostent * hent = ::gethostbyname (remoteHost.c_str());
    if (hent)
      memcpy (&sin.sin_addr.s_addr, hent->h_addr, (size_t)hent->h_length);
    else {
      int err = h_errno;
      Posix::netDbUnlock ();
      std::string s = "connect to \"";
      s += remoteHost;
      s += "\": ";
      const char *e;
      switch (err) {
      case HOST_NOT_FOUND:
        e = "unknown host";
        break;
      case NO_ADDRESS:
        e = "host has no address";
        break;
      default:
        e = "gethostbyname() failed0";
      }
      s += e;
      s += ":";
      s += strerror(err);
      s += remoteHost;
      throw s;
    }
    Posix::netDbUnlock ();
  }
  int fileno = ::socket (PF_INET, udp ? SOCK_DGRAM : SOCK_STREAM, udp ? IPPROTO_UDP : 0);
  if (fileno < 0)
    throw Posix::getErrorMessage(errno, "socket");
  ocpiInfo("Socket connecting to \"%s\" (%s) port %u",
	    remoteHost.c_str(), inet_ntoa(sin.sin_addr), remotePort);
  while (::connect(fileno, (struct sockaddr *) &sin, sizeof (sin)))
    if (errno != EINTR) {
      ocpiInfo("Connect failed to \"%s\" (%s) port %u with error \"%s\" (%d)",
		remoteHost.c_str(), inet_ntoa(sin.sin_addr), remotePort, strerror(errno), errno);
      throw Posix::getErrorMessage(errno, "connect");
    }
  uint64_t opaque;
  o2fd(&opaque) = fileno;
  setOpaque(&opaque);
}

size_t Socket::
recv(char *buffer, size_t amount, unsigned timeoutms, bool all) {
  int fileno = o2fd (m_osOpaque);
  if (timeoutms != m_timeoutms) {
    struct timeval tv;
    tv.tv_sec = (time_t)timeoutms/1000;
    tv.tv_usec = ((suseconds_t)timeoutms % 1000) * 1000;
    ocpiDebug("[Socket::recv] Setting socket timeout to %u ms", timeoutms);
    if (setsockopt(fileno, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) != 0)
      throw "Error setting timeout option for sending: " + Posix::getErrorMessage(errno, "setsockopt/recv");
    m_timeoutms = timeoutms;
  }
  if (amount > m_receiveSize) {
    int n2r = (int)amount;
    if (setsockopt(fileno, SOL_SOCKET, SO_RCVBUF, &n2r, sizeof(n2r)))
      throw Posix::getErrorMessage(errno, "setsockopt rcvbuf");
    ocpiInfo("Socket receive buffer size set to %u", n2r);
    m_receiveSize = amount;
  }
  size_t nread = 0;
  do {
    ssize_t n = ::recv(fileno, buffer, amount, 0);
    if (n < 0) {
      if (errno == EINTR)
	continue;
      else if (errno == EAGAIN || errno == EWOULDBLOCK) { // timeout errors
	assert(timeoutms);
	if (nread)
	  break; // return what we read if we timed out trying to get it all...
	return SIZE_MAX;
      } else
	throw "Error receiving from network: " + Posix::getErrorMessage (errno, "recv");
    } else {
      size_t nn = (size_t)n;
      nread += nn;
      if (nn == 0 || !all)
	break;
      buffer += nn, amount -= nn;
    }
  } while (amount);
  if (all && amount != 0)
    ocpiDebug("OS::Socket::recv got partial data before EOF: %zu looking for %zu",
	      nread, nread + amount);
  return nread;
}

size_t Socket::
recvfrom(char  *buf, size_t amount, int flags,
	 char * src_addr, size_t * addrlen, unsigned timeoutms) {
  if (timeoutms != m_timeoutms) {
    struct timeval tv;
    tv.tv_sec = (time_t)timeoutms/1000;
    tv.tv_usec = ((suseconds_t)timeoutms % 1000) * 1000;
    ocpiDebug("[Socket::recvfrom] Setting socket timeout to %u ms", timeoutms);
    if (setsockopt(o2fd (m_osOpaque), SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) != 0)
      throw Posix::getErrorMessage (errno, "setsockopt/recvfrom");
    m_timeoutms = timeoutms;
  }
  struct sockaddr * si_other = reinterpret_cast< struct sockaddr *>(src_addr);
  ssize_t ret = ::recvfrom (o2fd (m_osOpaque), buf, amount, flags, si_other, (socklen_t*)addrlen);
  if (ret == -1) {
    if (errno != EAGAIN && errno != EINTR)
      throw Posix::getErrorMessage(errno, "recvfrom");
    return 0;
  }
  return static_cast<size_t> (ret);
}

size_t Socket::
sendto (const char * data, size_t amount, int flags,  char * src_addr, size_t addrlen) {
  struct sockaddr * si_other = reinterpret_cast< struct sockaddr *>(src_addr);
  ssize_t ret = ::sendto (o2fd (m_osOpaque), data, amount, flags, si_other, (socklen_t)addrlen );
  if (ret == -1)
    throw Posix::getErrorMessage(errno, "sendto");
  return static_cast<size_t>(ret);
}

#ifdef OCPI_OS_macos
#define SEND_OPTS 0 // darwin uses setsockopt for this
#else
#define SEND_OPTS MSG_NOSIGNAL
#endif

// send the bytes to the socket, dealing properly with EINTR and error checking
// We assume this iov API being used means we do not want nagle buffering.
void Socket::
send(IOVec *iov, unsigned iovcnt) {
  ssize_t n2send = 0;
  int fileno = o2fd(m_osOpaque);
  for (unsigned n = 0; n < iovcnt; ++n)
    n2send += (ssize_t)iov[n].iov_len;
  if ((size_t)n2send > m_sendSize) {
    int n2s = (int)n2send;
    if (setsockopt(fileno, SOL_SOCKET, SO_SNDBUF, &n2s, sizeof(int)))
      throw Posix::getErrorMessage(errno, "setsockopt sndbuf");
    ocpiInfo("Socket send buffer size set to %u", n2s);
    m_sendSize = (size_t)n2send;
  }
  if (!m_nodelay) {
    int val = 1;
    if (setsockopt(fileno, IPPROTO_TCP, TCP_NODELAY, &val, sizeof(int)))
      throw Posix::getErrorMessage(errno, "setsockopt nodelay");
    ocpiInfo("Socket send no-delay option set to %u", val);
    m_nodelay = true;
  }
  size_t sent; // unsigned. needed outside for loop since it is updated in iteration clause...
  for (ssize_t nsent;
       (nsent = ::writev(fileno, (struct iovec*)iov, (int)iovcnt)) != n2send; n2send -= (ssize_t)sent) {
    if (nsent == 0)
      throw std::string("Error sending to network: got EOF");
    else if (nsent < 0) {
      if (errno == EINTR)
	nsent = 0;
      else
	throw "Error sending to network: " + Posix::getErrorMessage(errno, "send");
    }
    sent = (size_t)nsent;
    for (; sent > iov->iov_len; sent -= iov->iov_len, ++iov, --iovcnt)
      assert(iovcnt > 1);
    iov->iov_len -= sent;
    iov->iov_base = (uint8_t*)iov->iov_base + sent;
  }
}
// The return value here is for compatibility only
// The sending persists until until all is sent.
// Thus the only return value will be the same as the amount requested.
size_t Socket::
send(const char * data, size_t amount) {
  size_t n2send = amount, sent;
  for (ssize_t nsent;
       (nsent = ::send(o2fd(m_osOpaque), data, n2send, SEND_OPTS)) != (ssize_t)n2send;
       data += sent, n2send -= sent) {
    if (nsent == 0)
      throw std::string("Error sending to network: got EOF");
    else if (nsent < 0) {
      if (errno == EINTR)
	nsent = 0;
      else
	throw "Error sending to network: " + Posix::getErrorMessage(errno, "send");
    }
    sent = (size_t)nsent;
  }
  return amount;
}

// NOTE THIS CODE IS REPLICATED IN THE SERVER FOR DATAGRAMS
size_t Socket::
sendmsg (const void * iovect, int flags) {
  const struct msghdr * iov = static_cast<const struct msghdr *>(iovect);
  ssize_t ret = ::sendmsg (o2fd (m_osOpaque), iov, flags);
  if (ret == -1)
    throw Posix::getErrorMessage (errno, "sendmsg");
  return static_cast<size_t>(ret);
}

uint16_t Socket::
getPortNo () {
  struct sockaddr_in sin;
  socklen_t len = sizeof(sin);
  int ret = ::getsockname(o2fd (m_osOpaque), (struct sockaddr *) &sin, &len);
  if (ret != 0 || len != sizeof (sin))
    throw Posix::getErrorMessage (errno, "getsockname");
  return ntohs(sin.sin_port);
}

void Socket::
getPeerName (std::string & peerHost, uint16_t & peerPort) const {
  struct sockaddr_in sin;
  socklen_t len = sizeof (sin);
  int ret = ::getpeername(o2fd (m_osOpaque), (struct sockaddr *)&sin, &len);
  if (ret != 0 || len != sizeof(sin))
    throw Posix::getErrorMessage (errno, "getpeername");
  Posix::netDbLock ();
  struct hostent *hent =
    ::gethostbyaddr((const char *) &sin.sin_addr.s_addr, 4, sin.sin_family);
  if (hent && hent->h_name)
    peerHost = hent->h_name;
  else
    peerHost = inet_ntoa(sin.sin_addr);
  Posix::netDbUnlock ();
  peerPort = ntohs(sin.sin_port);
}

void Socket::
linger(bool opt) {
  struct linger lopt;
  lopt.l_onoff = opt ? 1 : 0;
  lopt.l_linger = 0;

  if (::setsockopt(o2fd (m_osOpaque), SOL_SOCKET, SO_LINGER, (char *) &lopt,
		   sizeof (struct linger)) != 0)
    throw Posix::getErrorMessage (errno, "setsockopt/linger");
#ifdef OCPI_OS_macos
  int x = 1;
  if (::setsockopt (o2fd (m_osOpaque), SOL_SOCKET, SO_NOSIGPIPE,
                    (void *) &x, sizeof (x)) != 0) {
    throw Posix::getErrorMessage (errno, "setsockopt/nosigpipe");
  }
#endif
}

void Socket::
shutdown (bool sendingEnd) {
  if (::shutdown(o2fd (m_osOpaque), sendingEnd ? SHUT_WR : SHUT_RD) != 0)
    throw Posix::getErrorMessage(errno, "shutdown");
}

void Socket::
close () {
  if (::close(o2fd(m_osOpaque)))
    throw Posix::getErrorMessage(errno, "socket close");
  o2fd(m_osOpaque) = -1;
}

#if 0
Socket Socket::
dup () {
  int newfd = ::dup(o2fd (m_osOpaque));
  uint64_t * fd2o = reinterpret_cast<uint64_t *> (&newfd);
  return Socket(fd2o);
}
#endif
  }
}
