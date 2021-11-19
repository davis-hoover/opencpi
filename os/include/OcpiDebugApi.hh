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

#ifndef OCPIOSDEBUG_H__
#define OCPIOSDEBUG_H__

/**
 * \file
 * \brief Operations related to debugging.
 *
 * Revision History:
 *
 *     06/30/2005 - Frank Pilhofer
 *                  Moved ocpiAssert to OcpiOsAssert.h
 *
 *     04/19/2005 - Frank Pilhofer
 *                  Initial version.
 */

#include <iostream>
#include <cstdarg>

#define OCPI_LOG_DEBUG_MIN 10
#define OCPI_LOG_DEBUG 10
#define OCPI_LOG_WEIRD 6
#define OCPI_LOG_INFO 8
#define OCPI_LOG_BAD 2

namespace OCPI {
  namespace OS {

    /**
     * Writes a stack trace of the current thread (similar to the "bt"
     * command in gdb) to the stream. The operation returns, and the
     * program can continue.
     *
     * \param[in] out The stream to print the stack trace to.
     *
     * \note On Linux, code must be linked with the "-rdynamic" option for
     * symbol names to be reported correctly.
     *
     * \note On VxWorks, the stack trace is always printed to the console
     * rather than being written to \a out.  The stack trace uses symbols
     * from the system symbol table, which must be populated.  Since
     * non-exported static or inline functions are not loaded into the
     * system symbol table, they will be misreported.  The stack trace
     * will instead show the name of the preceding non-static function.
     */

    void dumpStack (std::ostream & out);

    // version with no I/O library dependencies
    void dumpStack ();

    /**
     * Breaks the program, so that it can be debugged.
     *
     * In Windows, this starts the debugger if the program is not being
     * debugged already.
     *
     * In Unix, this sends a SIGINT signal to the current process, which
     * should be intercepted by the debugger if the program is being
     * debugged.
     *
     * In VxWorks DKM, this suspends the task.  After attaching the
     * debugger, taskResume() can be used from the console to resume
     * the task.
     *
     * This operation returns (as instructed by the debugger), and the
     * program can continue.
     */

    void debugBreak ();

    void logSetLevel(unsigned n);
    unsigned logGetLevel();
    bool logWillLog(unsigned n);
    void logPrint(unsigned n, const char *fmt, ...)__attribute__((format(printf, 2, 3)));
    void logPrintV(unsigned n, const char *fmt, va_list ap);
  }
}

#endif
