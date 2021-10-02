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

#include <cerrno>
#include <cstdio>
#include <string>
#include <cstring>
#include <pthread.h>
#include "OsSpinLock.hh"
#include "OsPosixError.hh"
#include "OsAssert.hh"

namespace {
  pthread_mutex_t gemMutex = PTHREAD_MUTEX_INITIALIZER;
};

std::string
OCPI::OS::Posix::getErrorMessage (int errorCode, const char *where)

{
  std::string res;

  if (where) {
    res = "in ";
    res += where;
    res += ": ";
  }
  res += "posix error ";
  char tmp[32];
  std::sprintf (tmp, "(%d)", errorCode);
  res += tmp;
  /*
   * std::strerror is not reentrant
   */
  pthread_mutex_lock (&gemMutex);
  const char * message = std::strerror (errorCode);
  if (message) {
    res += ": ";
    res += message;
  }
  pthread_mutex_unlock (&gemMutex);
  ocpiDebug("POSIX ERROR: %s", res.c_str());
  return res;
}
