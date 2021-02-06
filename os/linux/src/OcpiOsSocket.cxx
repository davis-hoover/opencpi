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
#include <arpa/inet.h>
#include <netdb.h>
#include <cerrno>
#include <climits>
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <string>
#include "ocpi-config.h"
#include "OcpiOsAssert.h"
#include "OcpiOsIovec.h"
#include "OcpiOsSizeCheck.h"
//#include "OcpiOsDataTypes.h"
#include "OcpiOsPosixError.h"
#include "OcpiOsPosixSocket.h"
#include "OcpiOsSocket.h"

static inline int &o2fd(uint64_t *o) { return *(int*)o; }
static inline const int &o2fd(const uint64_t *o) { return *(int*)o; }

namespace OCPI {
  namespace OS {
int Socket::
fd() const throw() {
  return o2fd(m_osOpaque);
}

void Socket::
init() throw() {
  m_temporary = false;
  m_timeoutms = 0;
  ocpiAssert ((compileTimeSizeCheck<sizeof (m_osOpaque), sizeof (int)> ()));
  ocpiAssert (sizeof (m_osOpaque) >= sizeof (int));
  o2fd(m_osOpaque) = -1;
}
Socket::
Socket () throw () {
  init();
}

#if 0
Socket::
Socket (const uint64_t * opaque) throw (std::string) {
  m_temporary = true;
  m_timeoutms = 0;
  ocpiAssert ((compileTimeSizeCheck<sizeof(m_osOpaque), sizeof(int)> ()));
  ocpiAssert (sizeof(m_osOpaque) >= sizeof(int));
  o2fd(m_osOpaque) = o2fd(opaque);
}
#endif

Socket::
Socket(const std::string &remoteHost, uint16_t remotePort, bool udp)
  throw (std::string) {
  init();
  connect(remoteHost, remotePort, udp);
}

Socket::
Socket (const Socket & other) throw () {
  init();
  o2fd(m_osOpaque) = ::dup(o2fd(other.m_osOpaque));
}

Socket & Socket::
operator= (const Socket & other) throw () {
  init();
  o2fd(m_osOpaque) = ::dup(o2fd(other.m_osOpaque));
  return *this;
}

Socket::
~Socket () throw () {
  if (!m_temporary && o2fd(m_osOpaque) != -1)
    close();
}

void Socket::
setOpaque(uint64_t *o) throw() {
  m_osOpaque[0] = *o;
}

void Socket::
connect(const std::string & remoteHost, uint16_t remotePort, bool udp) throw (std::string) {
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
  ocpiDebug("Socket connecting to \"%s\" (%s) port %u",
	    remoteHost.c_str(), inet_ntoa(sin.sin_addr), remotePort);
  while (::connect(fileno, (struct sockaddr *) &sin, sizeof (sin)))
    if (errno != EINTR) {
      ocpiDebug("Connect failed to \"%s\" (%s) port %u with error \"%s\" (%d)",
		remoteHost.c_str(), inet_ntoa(sin.sin_addr), remotePort, strerror(errno), errno);
      throw Posix::getErrorMessage(errno, "connect");
    }
  o2fd(m_osOpaque) = fileno;
}

size_t Socket::
recv(char *buffer, size_t amount, unsigned timeoutms, bool all) throw (std::string) {
  if (timeoutms != m_timeoutms) {
    struct timeval tv;
    tv.tv_sec = timeoutms/1000;
    tv.tv_usec = (timeoutms % 1000) * 1000;
    ocpiDebug("[Socket::recv] Setting socket timeout to %u ms", timeoutms);
    if (setsockopt(o2fd (m_osOpaque), SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) != 0)
      throw "Error setting timeout option for sending: " + Posix::getErrorMessage(errno, "setsockopt/recv");
    m_timeoutms = timeoutms;
  }
  size_t nread = 0;
  do {
    ssize_t n = ::recv(o2fd(m_osOpaque), buffer, amount, 0);
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
	 char * src_addr, size_t * addrlen, unsigned timeoutms) throw (std::string) {
  if (timeoutms != m_timeoutms) {
    struct timeval tv;
    tv.tv_sec = timeoutms/1000;
    tv.tv_usec = (timeoutms % 1000) * 1000;
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
sendto (const char * data, size_t amount, int flags,  char * src_addr, size_t addrlen)
  throw (std::string) {
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
void Socket::
send(IOVec *iov, unsigned iovcnt) throw (std::string) {
  ssize_t n2send = 0;
  for (unsigned n = 0; n < iovcnt; ++n)
    n2send += iov[n].iov_len;
  size_t sent; // unsigned. needed outside for loop since it is updated in iteration clause...
  for (ssize_t nsent;
       (nsent = ::writev(o2fd(m_osOpaque), (struct iovec*)iov, (int)iovcnt)) != n2send; n2send -= sent) {
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
send(const char * data, size_t amount) throw (std::string) {
  size_t n2send = amount, sent;
  for (ssize_t nsent;
       (nsent = ::send(o2fd(m_osOpaque), data, n2send, SEND_OPTS)) != (ssize_t)n2send;
       data += sent, n2send -= sent)
    if (nsent == 0)
      throw std::string("Error sending to network: got EOF");
    else if (nsent < 0) {
      if (errno == EINTR)
	nsent = 0;
      else
	throw "Error sending to network: " + Posix::getErrorMessage(errno, "send");
    } else
      sent = (size_t)nsent;
  return amount;
}

// NOTE THIS CODE IS REPLICATED IN THE SERVER FOR DATAGRAMS
size_t Socket::
sendmsg (const void * iovect, int flags) throw (std::string) {
  const struct msghdr * iov = static_cast<const struct msghdr *>(iovect);
  ssize_t ret = ::sendmsg (o2fd (m_osOpaque), iov, flags);
  if (ret == -1)
    throw Posix::getErrorMessage (errno, "sendmsg");
  return static_cast<size_t>(ret);
}

uint16_t Socket::
getPortNo () throw (std::string) {
  struct sockaddr_in sin;
  socklen_t len = sizeof(sin);
  int ret = ::getsockname(o2fd (m_osOpaque), (struct sockaddr *) &sin, &len);
  if (ret != 0 || len != sizeof (sin))
    throw Posix::getErrorMessage (errno, "getsockname");
  return ntohs(sin.sin_port);
}

void Socket::
getPeerName (std::string & peerHost, uint16_t & peerPort) const throw (std::string) {
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
linger(bool opt) throw (std::string) {
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
shutdown (bool sendingEnd) throw (std::string) {
  if (::shutdown(o2fd (m_osOpaque), sendingEnd ? SHUT_WR : SHUT_RD) != 0)
    throw Posix::getErrorMessage(errno, "shutdown");
}

void Socket::
close () throw (std::string) {
  if (::close(o2fd(m_osOpaque)))
    throw Posix::getErrorMessage(errno, "socket close");
  o2fd(m_osOpaque) = -1;
}

#if 0
Socket Socket::
dup () throw (std::string) {
  int newfd = ::dup(o2fd (m_osOpaque));
  uint64_t * fd2o = reinterpret_cast<uint64_t *> (&newfd);
  return Socket(fd2o);
}
#endif
  }
}
