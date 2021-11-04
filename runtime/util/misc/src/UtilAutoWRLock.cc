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

#include "UtilAutoWRLock.hh"
#include "OsAssert.hh"
#include "OsRWLock.hh"

OCPI::Util::AutoWRLock::AutoWRLock (OCPI::OS::RWLock & rwlock, bool locked)

  : m_locked (locked),
    m_rwlock (rwlock)
{
  if (locked) {
    m_rwlock.wrLock ();
  }
}

OCPI::Util::AutoWRLock::~AutoWRLock ()

{
  if (m_locked) {
    m_rwlock.wrUnlock ();
  }
}

void
OCPI::Util::AutoWRLock::lock ()

{
  ocpiAssert (!m_locked);
  m_rwlock.wrLock ();
  m_locked = true;
}

bool
OCPI::Util::AutoWRLock::trylock ()

{
  ocpiAssert (!m_locked);
  return (m_locked = m_rwlock.wrTrylock ());
}

void
OCPI::Util::AutoWRLock::unlock ()

{
  ocpiAssert (m_locked);
  m_rwlock.wrUnlock ();
  m_locked = false;
}
