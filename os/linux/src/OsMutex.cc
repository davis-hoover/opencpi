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
#include "OsMutex.hh"
#include "OsSizeCheck.hh"
#include "OsDataTypes.hh"
#include <pthread.h>
#include <errno.h>
#include "OsPosixError.hh"

inline
pthread_mutex_t *
o2pm (OCPI::OS::uint64_t * ptr)

{
  return reinterpret_cast<pthread_mutex_t *> (ptr);
}

OCPI::OS::Mutex::Mutex (bool recursive)

  : m_locked(0)
{
  ocpiAssert ((compileTimeSizeCheck<sizeof (m_osOpaque), sizeof (pthread_mutex_t)> ()));
  ocpiAssert (sizeof (m_osOpaque) >= sizeof (pthread_mutex_t));

  int pttype;

  if (recursive) {
    pttype = PTHREAD_MUTEX_RECURSIVE;
  }
  else {
#ifdef NDEBUG
    pttype = PTHREAD_MUTEX_NORMAL;
#else
    pttype = PTHREAD_MUTEX_ERRORCHECK;
#endif
  }

  pthread_mutexattr_t ma;
  pthread_mutexattr_init (&ma);
  pthread_mutexattr_settype (&ma, pttype);

  int res;
  if ((res = pthread_mutex_init (o2pm (m_osOpaque), &ma))) {
    pthread_mutexattr_destroy (&ma);
    throw OCPI::OS::Posix::getErrorMessage (res);
  }

  pthread_mutexattr_destroy (&ma);
}

OCPI::OS::Mutex::~Mutex ()

{
  pthread_mutex_destroy (o2pm (m_osOpaque));
}

void
OCPI::OS::Mutex::lock ()

{
  int res;
  if ((res = pthread_mutex_lock (o2pm (m_osOpaque))))
    throw OCPI::OS::Posix::getErrorMessage (res);
  m_locked++;
}

bool
OCPI::OS::Mutex::trylock ()

{
  int res = pthread_mutex_trylock (o2pm (m_osOpaque));
  if (!res)
    m_locked++;
  else if (res != 0 && res != EBUSY)
    throw OCPI::OS::Posix::getErrorMessage (res);
  return (!res ? true : false);
}

void
OCPI::OS::Mutex::unlock (bool okIfUnlocked)

{
  int res;
  if (okIfUnlocked && !m_locked)
    return;
  ocpiAssert(m_locked);
  m_locked--;
 if ((res = pthread_mutex_unlock (o2pm (m_osOpaque))))
    throw OCPI::OS::Posix::getErrorMessage (res);
}
