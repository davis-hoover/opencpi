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
#include "OsSemaphore.hh"
#include "OsSizeCheck.hh"
#include "OsDataTypes.hh"
#include <cassert>
#include <pthread.h>
#include "OsPosixError.hh"

namespace {
  struct SemaphoreData {
    pthread_mutex_t mutex;
    pthread_cond_t cond;
    volatile unsigned int value;
  };
}

inline
SemaphoreData &
o2sd (OCPI::OS::uint64_t * ptr)

{
  return *reinterpret_cast<SemaphoreData *> (ptr);
}

OCPI::OS::Semaphore::Semaphore (unsigned int initial)

{
  ocpiAssert ((compileTimeSizeCheck<sizeof (m_osOpaque), sizeof (SemaphoreData)> ()));
  ocpiAssert (sizeof (m_osOpaque) >= sizeof (SemaphoreData));

  SemaphoreData & sd = o2sd (m_osOpaque);
  int res;

  if ((res = pthread_mutex_init (&sd.mutex, 0))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }

  if ((res = pthread_cond_init (&sd.cond, 0))) {
    pthread_mutex_destroy (&sd.mutex);
    throw OCPI::OS::Posix::getErrorMessage (res);
  }

  sd.value = initial;
}

OCPI::OS::Semaphore::~Semaphore ()

{
  SemaphoreData & sd = o2sd (m_osOpaque);
  pthread_cond_destroy (&sd.cond);
  pthread_mutex_destroy (&sd.mutex);
}

void
OCPI::OS::Semaphore::post ()

{
  SemaphoreData & sd = o2sd (m_osOpaque);
  int res;

  if ((res = pthread_mutex_lock (&sd.mutex))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }

  sd.value++;

  if ((res = pthread_cond_signal (&sd.cond))) {
    pthread_mutex_unlock (&sd.mutex);
    throw OCPI::OS::Posix::getErrorMessage (res);
  }

  if ((res = pthread_mutex_unlock (&sd.mutex))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
}

void
OCPI::OS::Semaphore::wait ()

{
  SemaphoreData & sd = o2sd (m_osOpaque);
  int res;

  if ((res = pthread_mutex_lock (&sd.mutex))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }

  while (!sd.value) {
    if ((res = pthread_cond_wait (&sd.cond, &sd.mutex))) {
      pthread_mutex_unlock (&sd.mutex);
      throw OCPI::OS::Posix::getErrorMessage (res);
    }
  }

  if (--sd.value) {
    if ((res = pthread_cond_signal (&sd.cond))) {
      pthread_mutex_unlock (&sd.mutex);
      throw OCPI::OS::Posix::getErrorMessage (res);
    }
  }

  if ((res = pthread_mutex_unlock (&sd.mutex))) {
    throw OCPI::OS::Posix::getErrorMessage (res);
  }
}

