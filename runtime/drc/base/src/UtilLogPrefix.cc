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

#include <cstdarg> // va_list, va_start(), va_end()
#include <cstdio>  // printf()
#include "OcpiOsDebugApi.hh"
#include "UtilLogPrefix.hh"

namespace OCPI {
  namespace Util {

LogPrefix::
LogPrefix(const char *prefix)
  : m_prefix(prefix ? prefix : ""),
    m_debug(false), m_info(false), m_warn(false), m_error(false)
    {}
LogPrefix::
LogPrefix(const std::string &prefix) : m_prefix(prefix) {}

void LogPrefix::
log_prefix(unsigned level, const char *msg, va_list ap) const {
  OCPI::OS::logPrintV(level, msg, ap);
}
void LogPrefix::
log_info(const char* msg, ...) const {
  va_list arg;
  va_start(arg, msg);
  log_prefix(OCPI_LOG_INFO, msg, arg);
  va_end(arg);
}
void LogPrefix::
log_debug(const char* msg, ...) const {
  va_list arg;
  va_start(arg, msg);
  log_prefix(OCPI_LOG_DEBUG, msg, arg);
  va_end(arg);
}
void LogPrefix::
log_warn(const char* msg, ...) const {
  va_list arg;
  va_start(arg, msg);
  log_prefix(OCPI_LOG_INFO, msg, arg);
  va_end(arg);
}
void LogPrefix::
log_error(const char* msg, ...) const {
  va_list arg;
  va_start(arg, msg);
  log_prefix(OCPI_LOG_BAD, msg, arg);
  va_end(arg);
}
const char *LogPrefix::
get_prefix() { return ""; }

} // namespace Util
} // namespace OCPI
