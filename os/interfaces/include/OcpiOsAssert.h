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

// -*- c++ -*-

#ifndef OCPIOSASSERT_H__
#define OCPIOSASSERT_H__

#include "OcpiOsDebug.h"

namespace OCPI {
  namespace OS {

    /**
     * \brief Typedef for an assertion callback function.
     *
     * The callback takes three parameters:
     *
     * - \em cond The expression that was tested, and which evaluates to
     *            false.
     * - \em file The name of the source file that contains this assertion.
     * - \em line The line in the source file where this expression tested
     *            false.
     *
     * The callback shall not return.
     */

    typedef void (*AssertionCallback) (const char * cond,
                                       const char * file,
                                       unsigned int line);

    /**
     * Set a callback function to call when an assertion fails.
     *
     * \param[in] cb The callback function.
     */

    void setAssertionCallback (AssertionCallback cb)
      throw ();

    /**
     * An internal function used by the ocpiAssert macro.
     *
     * "Test" an assertion condition. There isn't really anything to test.
     * This is just to avoid warnings like "statement has no effect" when
     * testing for something like ocpiAssert (sizeof(int) == 4).
     *
     * Not called by user code.
     */

    bool testAssertion (bool)
      throw ();

    /**
     * Default assertion callback.
     *
     * Prints a message and a stack trace (if built with debugging enabled)
     * to standard error (std::cerr), then aborts.
     *
     * This function can be used with setAssertionCallback() to reset the
     * assertion callback to the default.
     */

    bool assertionFailed (const char *, const char *, unsigned int)
      throw ();

    void debugPrint(const char *, ...);
  }
}

inline
bool
::OCPI::OS::testAssertion (bool cond)
  throw ()
{
  return !!cond;
}

/**
 * \def ocpiAssert(cond)
 *
 * Tests a "sanity check" condition. When the NDEBUG preprocessor
 * symbol is not defined, the condition is evaluated. If true, the
 * program continues. If false, a message and stack trace are
 * printed to std::cout.
 * \n
 * If the "sanity check" failed, the function does not return, but
 * first breaks into the debugger using debugBreak(), and then
 * aborts the program.
 * \n
 * If the NDEBUG preprocessor symbol is defined, then the condition
 * is not evaluated, and the program continues regardless of the
 * condition's value.
 */

#if defined (ocpiAssert)
#undef ocpiAssert
#endif

// When you really want to blow up with a string, even when asserts are off
inline void ocpiAbort(const char *err) { ::OCPI::OS::assertionFailed(err, __FILE__, __LINE__); }
// When you really want to ignore the return value even if the header has warn_ignore_result
#define ocpiIgnore(...) do { auto _ignore_ret = __VA_ARGS__; (void)_ignore_ret; } while (0)
#define ocpiWeird(...) ocpiLog(OCPI_LOG_WEIRD, __VA_ARGS__)
#define ocpiInfo(...) ocpiLog(OCPI_LOG_INFO, __VA_ARGS__)
#define ocpiBad(...) ocpiLog(OCPI_LOG_BAD, __VA_ARGS__)
#if defined(NDEBUG)
#define ocpiAssert(cond) ((void)0)
#define ocpiCheck(cond) ((void)(cond))
#define ocpiDebug(fmt, ...) ((void)0)
#define ocpiDebug1(fmt, ...) ((void)0)
#define ocpiDebug2(fmt, ...) ((void)0)
#define ocpiDebug3(fmt, ...) ((void)0)
#define ocpiLog(n, ...) ((n) > OCPI_LOG_DEBUG_MIN ? 0 : (::OCPI::OS::logPrint(n, __VA_ARGS__),0))
#else
#define ocpiAssert(cond) ((::OCPI::OS::testAssertion ((cond) ? true : false)) || ::OCPI::OS::assertionFailed (#cond, __FILE__, __LINE__))
#define ocpiCheck(cond) ocpiAssert(cond)
#define ocpiDebug(...) ::OCPI::OS::logPrint(OCPI_LOG_DEBUG_MIN, __VA_ARGS__)
#define ocpiDebug1(fmt, ...) ::OCPI::OS::logPrint(OCPI_LOG_DEBUG_MIN+1, (fmt), __VA_ARGS__)
#define ocpiDebug2(fmt, ...) ::OCPI::OS::logPrint(OCPI_LOG_DEBUG_MIN+2, (fmt), __VA_ARGS__)
#define ocpiDebug3(fmt, ...) ::OCPI::OS::logPrint(OCPI_LOG_DEBUG_MIN+3, (fmt), __VA_ARGS__)
#define ocpiLog(n, ...) ::OCPI::OS::logPrint(n, __VA_ARGS__)
#endif

#endif
