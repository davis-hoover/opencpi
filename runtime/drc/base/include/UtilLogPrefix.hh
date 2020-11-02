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

#ifndef _UTIL_LOG_PREFIX_HH
#define _UTIL_LOG_PREFIX_HH

#include <cstdarg> // va_list
#include <string>
namespace OCPI {
  namespace Util {

// Allow a templated class to inherit this and actuall use it.
// Templated classes that inherit this need to declare this.
#define OCPI_UTIL_LOGPREFIX_USE_METHOD_NAMES \
    using OCPI::Util::LogPrefix::log_info;   \
    using OCPI::Util::LogPrefix::log_debug; \
    using OCPI::Util::LogPrefix::log_warn; \
    using OCPI::Util::LogPrefix::log_error

/*! @brief Helper class which provides a generic logging API as well as a
 *         prefix for all log messages.
 ******************************************************************************/
class LogPrefix {
  std::string m_prefix;
  void log_prefix(unsigned level, const char *msg, va_list arg) const;
  bool m_debug, m_info, m_warn, m_error;
protected:
  LogPrefix(const char *prefix = NULL);
  LogPrefix(const std::string &prefix);
  // derived class supplies a potentially dynamic prefix
  virtual const char *get_prefix();
public:
  bool log_debug() { return m_debug; }
  bool log_info() { return m_info; }
  bool log_warn() { return m_warn; }
  bool log_error() { return m_error; }
  void
    #ifdef __GNUC__
    __attribute__((format(printf, 2, 3)))
    #endif
    log_debug(const char* msg, ...) const,
    #ifdef __GNUC__
    __attribute__((format(printf, 2, 3)))
    #endif
    log_info(const char* msg, ...) const,
    #ifdef __GNUC__
    __attribute__((format(printf, 2, 3)))
    #endif
    log_warn(const char* msg, ...) const,
    #ifdef __GNUC__
    __attribute__((format(printf, 2, 3)))
    #endif
    log_error(const char* msg, ...) const;
  inline void log_debug_str(const std::string &s) { log_debug("%s", s.c_str()); }
  inline void log_info_str(const std::string &s) { log_debug("%s", s.c_str()); }
  inline void log_warn_str(const std::string &s) { log_debug("%s", s.c_str()); }
  inline void log_error_str(const std::string &s) { log_debug("%s", s.c_str()); }
}; // class LogPrefix

} // namespace Util
} // namespace OCPI

#endif // _UTIL_LOG_PREFIX_HH
