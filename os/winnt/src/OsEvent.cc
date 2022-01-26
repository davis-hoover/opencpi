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
#include "OsEvent.hh"
#include "OsSizeCheck.hh"
#include "OsDataTypes.hh"
#include <windows.h>
#include <string>
#include "OsWin32Error.hh"

inline
HANDLE &
o2h (OCPI::OS::uint64_t * ptr)

{
  return *reinterpret_cast<HANDLE *> (ptr);
}

OCPI::OS::Event::Event (bool initial)

{
  ocpiAssert ((compileTimeSizeCheck<sizeof (m_osOpaque), sizeof (HANDLE)> ()));
  ocpiAssert (sizeof (m_osOpaque) >= sizeof (HANDLE));
  if (((o2h (m_osOpaque)) = CreateEvent (0, 0, initial, 0)) == 0) {
    throw OCPI::OS::Win32::getErrorMessage (GetLastError());
  }
}

OCPI::OS::Event::~Event ()

{
  CloseHandle (o2h (m_osOpaque));
}

void
OCPI::OS::Event::set ()

{
  SetEvent (o2h (m_osOpaque));
}

void
OCPI::OS::Event::wait ()

{
  WaitForSingleObject (o2h (m_osOpaque), INFINITE);
}

bool
OCPI::OS::Event::wait (unsigned int timeout)

{
  if (WaitForSingleObject (o2h (m_osOpaque), timeout) == WAIT_TIMEOUT) {
    return false;
  }

  return true;
}

