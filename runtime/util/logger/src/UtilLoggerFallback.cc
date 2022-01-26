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
#include "UtilLogger.hh"
#include "UtilLoggerFallback.hh"

/*
 * ----------------------------------------------------------------------
 * Fallback: if one logger fails, fall back to another
 * ----------------------------------------------------------------------
 */

OCPI::Logger::Fallback::FallbackBuf::FallbackBuf ()
  : m_first (true), m_locked (false)
{
}

OCPI::Logger::Fallback::FallbackBuf::~FallbackBuf ()
{
  if (!m_first) {
    sync ();
  }

  if (m_locked) {
    m_lock.unlock ();
  }

  for (Delegatees::iterator it = m_delegatee.begin(); it != m_delegatee.end(); it++) {
    if ((*it).adopted) {
      delete (*it).delegatee;
    }
  }
}

void
OCPI::Logger::Fallback::FallbackBuf::addOutput (Logger * delegatee,
                                               bool adopt, bool retry)
{
  m_selfLock.lock ();
  Delegatee d;
  d.delegatee = delegatee;
  d.adopted = adopt;
  d.retry = retry;
  m_delegatee.push_back (d);
  m_selfLock.unlock ();
}

void
OCPI::Logger::Fallback::FallbackBuf::setLogLevel (unsigned short logLevel)
{
  m_lock.lock ();
  m_locked = true;
  m_logLevel = logLevel;
  m_producerName.clear ();
  ocpiAssert (m_first);
}

void
OCPI::Logger::Fallback::FallbackBuf::setProducerId (const char * producerId)
{
  m_selfLock.lock ();
  Delegatees::iterator it;
  for (it = m_delegatee.begin(); it != m_delegatee.end(); it++) {
    (*it).delegatee->setProducerId (producerId);
  }
  m_selfLock.unlock ();
}

void
OCPI::Logger::Fallback::FallbackBuf::setProducerName (const char * producerName)
{
  ocpiAssert (m_locked);
  ocpiAssert (m_first);
  m_producerName = producerName;
}

int
OCPI::Logger::Fallback::FallbackBuf::sync ()
{
  bool good = true;

  if (!m_first) {
    ocpiAssert (m_locked);

    m_selfLock.lock ();
    Delegatees::iterator it;
    for (it = m_delegatee.begin(), good = false;
         it != m_delegatee.end() && !good; it++) {
      if ((*it).retry && !(*it).delegatee->good()) {
        (*it).delegatee->clear ();
      }

      if ((*it).delegatee->good ()) {
        (*it).delegatee->setLogLevel (m_logLevel);
        (*it).delegatee->setProducerName (m_producerName.c_str());
        (*it).delegatee->write (m_logMessage.data(), (std::streamsize)m_logMessage.length());
        (*it).delegatee->flush ();
      }

      if ((*it).delegatee->good()) {
        good = true;
      }
    }
    m_selfLock.unlock ();
    m_logMessage.clear ();
    m_first = true;
  }

  if (m_locked) {
    m_locked = false;
    m_lock.unlock ();
  }

  return (good ? 0 : -1);
}

std::streambuf::int_type
OCPI::Logger::Fallback::FallbackBuf::overflow (int_type c)
{
  ocpiAssert (m_locked);

  if (m_first) {
    m_first = false;
    m_logMessage.clear ();
  }

  if (traits_type::eq_int_type (c, traits_type::eof())) {
    return traits_type::not_eof (c);
  }

  m_logMessage += traits_type::to_char_type (c);
  return c;
}

std::streamsize
OCPI::Logger::Fallback::FallbackBuf::xsputn (const char * data, std::streamsize count)
{
  ocpiAssert (m_locked);

  if (m_first) {
    overflow (traits_type::eof());
  }

  m_logMessage.append (data, (size_t)count);
  return count;
}

OCPI::Logger::Fallback::Fallback ()
  : Logger (m_obuf)
{
}

OCPI::Logger::Fallback::~Fallback ()
{
}

void
OCPI::Logger::Fallback::addOutput (Logger & delegatee, bool retry)
{
  m_obuf.addOutput (&delegatee, false, retry);
}

void
OCPI::Logger::Fallback::addOutput (Logger * delegatee,
                                  bool adopt, bool retry)
{
  m_obuf.addOutput (delegatee, adopt, retry);
}
