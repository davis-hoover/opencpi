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

#include <signal.h>
#include <unistd.h>
#include <sys/time.h>
#include <execinfo.h>
#include <stdarg.h>
#include <cstdlib>
#include <iostream>
#include <cstdio>
#include <climits>
#include <cstring>
#include "OsDebug.hh"
#include "OsMutex.hh"

namespace OCPI {
  namespace OS {
    void
    dumpStack (std::ostream & out)

    {
      void * bt[40];

      int bts = backtrace (bt, 40);
      char ** btsyms = backtrace_symbols (bt, bts);

      for (int i=0; i<bts; i++) {
	out << btsyms[i] << std::endl;
      }

      free (btsyms);
    }
    // Version that has no IO library dependencies
    void
    dumpStack ()

    {
      void * bt[40];

      int bts = backtrace (bt, 40);
      char ** btsyms = backtrace_symbols (bt, bts);

      for (int i=0; i<bts; i++)
	if (write(2, btsyms[i], strlen(btsyms[i])) < 0 ||
	    write(2,"\n", 1) < 0)
	  break;

      free (btsyms);
    }

    void
    debugBreak ()

    {
      kill (getpid(), SIGINT);
    }

    // We can't use the C++ mutex since its destruction is unpredictable and
    // we want logging to work in destructors
    pthread_mutex_t mine = PTHREAD_MUTEX_INITIALIZER;
    static unsigned logLevel = UINT_MAX;
    void
    logSetLevel(unsigned level) {
      logLevel = level;
    }
    unsigned
    logGetLevel() {
      return logLevel;
    }
    void
    logPrint(unsigned n, const char *fmt, ...){
	va_list ap;
	va_start(ap, fmt);
	logPrintV(n, fmt, ap);
	va_end(ap);
    }
    bool
    logWillLog(unsigned n) {
      if (logLevel != UINT_MAX && n > logLevel)
	return false;
      if (logLevel == UINT_MAX) {
	const char *e = getenv("OCPI_LOG_LEVEL");
	logLevel = e ? (unsigned)atoi(e) : OCPI_LOG_WEIRD;
      }
      return n <= logLevel;
    }
    void
    logPrintV(unsigned n, const char *fmt, va_list ap){
      if (logWillLog(n)) {
	struct timeval tv;
	gettimeofday(&tv, NULL);
	pthread_mutex_lock (&mine);
	fprintf(stderr, "OCPI(%2d:%3u.%04u): ", n, (unsigned)(tv.tv_sec%1000),
		(unsigned)((tv.tv_usec+500)/1000));
	vfprintf(stderr, fmt, ap);
	if (fmt[strlen(fmt)-1] != '\n')
	  fprintf(stderr, "\n");
	fflush(stderr);
	pthread_mutex_unlock (&mine);
	// usleep(200000); // convenient when zynq is crashing so we get more logging out
      }
    }
  }
}
