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
#include "OsRWLock.hh"
#include "OsSizeCheck.hh"
#include "OsDataTypes.hh"
#include <cassert>
#include <pthread.h>
#include <errno.h>
#include "OsPosixError.hh"

inline
pthread_rwlock_t *
o2prw (OCPI::OS::uint64_t * ptr)

{
  return reinterpret_cast<pthread_rwlock_t *> (ptr);
}

OCPI::OS::RWLock::RWLock ()

{
  ocpiAssert ((compileTimeSizeCheck<sizeof (m_osOpaque), sizeof (pthread_rwlock_t)> ()));
  ocpiAssert (sizeof (m_osOpaque) >= sizeof (pthread_rwlock_t));

  int res;
  if ((res = pthread_rwlock_init (o2prw (m_osOpaque), 0))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
}

OCPI::OS::RWLock::~RWLock ()

{
  pthread_rwlock_destroy (o2prw (m_osOpaque));
}

void
OCPI::OS::RWLock::rdLock ()

{
  int res;
  if ((res = pthread_rwlock_rdlock (o2prw (m_osOpaque)))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
}

bool
OCPI::OS::RWLock::rdTrylock ()

{
  int res = pthread_rwlock_tryrdlock (o2prw (m_osOpaque));
  if (res != 0 && res != EBUSY) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
  return ((res == 0) ? true : false);
}

void
OCPI::OS::RWLock::rdUnlock ()

{
  int res;
  if ((res = pthread_rwlock_unlock (o2prw (m_osOpaque)))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
}

void
OCPI::OS::RWLock::wrLock ()

{
  int res;
  if ((res = pthread_rwlock_wrlock (o2prw (m_osOpaque)))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
}

bool
OCPI::OS::RWLock::wrTrylock ()

{
  int res = pthread_rwlock_trywrlock (o2prw (m_osOpaque));
  if (res != 0 && res != EBUSY) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
  return ((res == 0) ? true : false);
}

void
OCPI::OS::RWLock::wrUnlock ()

{
  int res;
  if ((res = pthread_rwlock_unlock (o2prw (m_osOpaque)))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
}
