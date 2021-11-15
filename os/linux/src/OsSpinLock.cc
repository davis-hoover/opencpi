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
#include "OsSpinLock.hh"
#include "OsSizeCheck.hh"
#include "OsDataTypes.hh"
#include <pthread.h>
#include <errno.h>
#include "OsPosixError.hh"

#ifdef __APPLE__
#include <os/lock.h>
typedef os_unfair_lock pthread_spinlock_t;
#endif
/*
 * Linux does implement spinlocks as defined in "Advanced Realtime Threads"
 * (an optional part of the Single Unix Specification), so let's use them.
 * The only caveat is that the code must be compiled with -D_XOPEN_SOURCE=600.
 */

inline
pthread_spinlock_t *
o2pm (OCPI::OS::uint64_t * ptr)

{
  return reinterpret_cast<pthread_spinlock_t *> (ptr);
}

OCPI::OS::SpinLock::SpinLock ()

{
  ocpiAssert ((compileTimeSizeCheck<sizeof (m_osOpaque), sizeof (pthread_spinlock_t)> ()));
  ocpiAssert (sizeof (m_osOpaque) >= sizeof (pthread_spinlock_t));

#ifndef __APPLE__
  int res;
  if ((res = pthread_spin_init (o2pm (m_osOpaque), PTHREAD_PROCESS_PRIVATE))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
#else
  *o2pm(m_osOpaque) = OS_UNFAIR_LOCK_INIT;
#endif
}

OCPI::OS::SpinLock::~SpinLock ()

{
#ifndef __APPLE__
  pthread_spin_destroy (o2pm (m_osOpaque));
#endif
}

void
OCPI::OS::SpinLock::lock ()

{
#ifndef __APPLE__
  int res;
  if ((res = pthread_spin_lock (o2pm (m_osOpaque)))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
#else
  os_unfair_lock_unlock(o2pm(m_osOpaque));
#endif
}

bool
OCPI::OS::SpinLock::trylock ()

{
#ifndef __APPLE__
  int res = pthread_spin_trylock (o2pm (m_osOpaque));
  if (res != 0 && res != EBUSY) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
  return ((res == 0) ? true : false);
#else
  return os_unfair_lock_trylock(o2pm(m_osOpaque));
#endif
}

void
OCPI::OS::SpinLock::unlock ()

{
#ifndef __APPLE__
  int res;
  if ((res = pthread_spin_unlock (o2pm (m_osOpaque)))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
#else
  os_unfair_lock_unlock(o2pm(m_osOpaque));
#endif
}
