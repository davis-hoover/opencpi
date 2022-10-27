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

#include <stdarg.h>
#include <unistd.h>
#include <cstdio>

#include "OsAssert.hh"
#include "UtilException.hh"

namespace OCPI {

  namespace API {
    Error::~Error(){}
  }
  namespace Util {
    bool g_exiting = false;
    // Convenience for single line, multi-string, API exceptions (API called badly)
    // Its easy to scan all callers for the terminating null
    ApiError::ApiError(const char *err, ...)
    {
      va_list ap;
      va_start(ap, err);
      setConcatenateV(err, ap);
      m_auxInfo = *this; // backward compatibility...
      ocpiInfo("ApiError Exception: %s", this->c_str());
      va_end(ap);
    }
    ApiError::~ApiError(){}
    Error::Error(){}

    Error::Error(va_list ap, const char *err) {
      setFormatV(err, ap);
      ocpiInfo("Error Exception: %s", this->c_str());
    }
    Error::Error(std::string &s) {
      append(s.c_str());
    }
    Error::Error(const char *err, ...) {
      va_list ap;
      va_start(ap, err);
      setFormatV(err, ap);
      va_end(ap);
      ocpiInfo("Error Exception: %s", this->c_str());
    }      
    Error::Error(unsigned level, const char *err, ...) {
      va_list ap;
      va_start(ap, err);
      setFormatV(err, ap);
      va_end(ap);
      OS::Log::print(level, "Error Exception: %s", this->c_str());
    }

    void Error::setConcatenateV(const char *err, va_list ap) {
      append(err);
      const char *s;
      while ((s = va_arg(ap, const char*)))
	append(s);
    }
    void Error::setFormat(const char *err, ...) {
      va_list ap;
      va_start(ap, err);
      setFormatV(err, ap);
      va_end(ap);
    }
    void Error::setFormatV(const char *err, va_list ap) {
      char *s;
      ocpiCheck(vasprintf(&s, err, ap) >= 0);
      if (g_exiting) {
	// We are in a very primitive mode here. No error checking.
	static const char pre[] = "\n***Exception during shutdown: ";
	static const char post[] = "***\n";
	write(2, pre, strlen(pre)) &&
	write(2, s, strlen(s)) &&
	write(2, post, strlen(post));
	OCPI::OS::dumpStack();
      }
      append(s);
      free(s);
    }
    Error::~Error(){}

    EmbeddedException::EmbeddedException( 
					 OCPI::OS::uint32_t errorCode, 
					 const char* auxInfo,
					 OCPI::OS::uint32_t errorLevel )
      : m_errorCode(errorCode), m_errorLevel(errorLevel)
    {
      if (auxInfo)
	m_auxInfo = auxInfo;
      setFormat("Code 0x%x, level %u, error: '%s'", errorCode, errorLevel, auxInfo);
    }
      // String error only (error code zero)
    EmbeddedException::EmbeddedException( const char* auxInfo )
      : m_errorCode(0), m_auxInfo(auxInfo), m_errorLevel(0)
    {
      append(auxInfo);
    }
    EmbeddedException::~EmbeddedException(){}
  }
}
