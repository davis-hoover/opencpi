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
#include <stdlib.h>
#include <errno.h>
#include <unistd.h>
#include <sys/mman.h>
#include <cstring>
#include "ocpi-config.h"
#include "OcpiUtilCppMacros.h"
#include "OsLoadableModule.hh"
#include "OcpiDriverManager.h"
#include "OclContainer.h"

namespace OU =  OCPI::Util;

#define OCPI_OPTIONS_HELP \
  "Usage syntax is: ocpiocl [options] <command>\n" \
  "  Commands are:\n" \
  "    compile   - act like a compiler, building worker binaries\n" \
  "    search    - find available OpenCL devices\n" \
  "    probe     - test whether an OpenCL device exists\n" \
  "    targets   - print all targets found on this system\n" \

//           name      abbrev  type    value description
#define OCPI_OPTIONS \
  CMD_OPTION_S(define,     D,    String, NULL,    "Set preprocessor definition") \
  CMD_OPTION_S(include,    I,    String, NULL,    "Set include directory") \
  CMD_OPTION(  output,     o,    String, NULL,    "Set name of output file") \
  CMD_OPTION(  target,     t,    String, NULL,    "Target device type to compile for") \
  CMD_OPTION(  verbose,    v,    Bool,   "false", "Provide verbose output during operation") \
  CMD_OPTION(  loglevel,   l,    UChar,  "0",     "Set logging level used during operation") \

#include "CmdOption.hh"

namespace OC = OCPI::Container;
namespace OCL = OCPI::OCL;
namespace OA = OCPI::API;
namespace OD = OCPI::Driver;

// FIXME:  this assumes that the environment and or configuration will be set to the default
// location.  This is "pending" while we figure out the difference between a default place
// for the OpenCL ICD, vs an actual runtime implementation library.
// For now we will assume it is a configuration value in ocpi-config.h
const char *defaultLib = OCPI_CPP_STRINGIFY(OCPI_OPENCL_LIB);

static int mymain(const char **ap) {
  OCPI::OS::logSetLevel(options.loglevel());
  OCPI::Driver::ManagerManager::suppressDiscovery();
  const char *env = getenv("OCPI_OPENCL_LIB");
  const char *lib = env && env[0] ? env : defaultLib;
  try {
    OCPI::OS::LoadableModule lm(lib, true);
  } catch (...) {
    options.bad("Missing/invalid OpenCL support library:  %s", lib);
    return 1;
  }
  if (!*ap)
    return 0;
  // Now we explicitly load the remote container driver
  std::string err;
  OD::Driver *d = OD::ManagerManager::loadDriver("container", "ocl", err);
  if (!d)
    options.bad("Error during loading of OCL container driver: %s", err.c_str());
  OCL::Driver &driver = *static_cast<OCL::Driver*>(d);
  if (!strcasecmp(*ap, "search")) {
    OA::PVarray vals(5);
    unsigned n = 0;
    vals[n++] = OA::PVBool("printOnly", true);
    if (options.verbose())
      vals[n++] = OA::PVBool("verbose", true);
    vals[n++] = OA::PVEnd;
    driver.search(vals, NULL, true);
  } else if(!strcasecmp(*ap, "probe")) {
    if (!*++ap)
      options.bad("Missing device name argument to probe");
    if (!driver.open(*ap, options.verbose(), true, err))
      options.bad("Error during probe for \"%s\": %s", *ap, err.c_str());
  } else if(!strcasecmp(*ap, "compile")) {
    if (!options.target())
      options.bad("The target (-t) option must be specified for the compile command");
    size_t numIncludes, numDefines, numSources;
    const char
      **includes = options.include(numIncludes),
      **defines = options.define(numDefines),
      **sources = ++ap;
    for (numSources = 0; *ap++; numSources++)
      ;
    if (!numSources)
      options.bad("No source files supplied after \"compile\" command.");
    std::vector<int> fds(numSources, -1);
    std::vector<off_t> sizes(numSources*2, 0);
    std::vector<const char *> mapped(numSources*2, NULL);
    void *maddr = NULL;
    for (unsigned n = 0; n < numSources; n++) {
      ocpiDebug("Compiling OCL input file %s", sources[n]);
      if ((fds[n] = open(sources[n], O_RDONLY)) < 0 ||
	  (sizes[n*2+1] = lseek(fds[n], 0, SEEK_END)) == -1 ||
	  (maddr = mmap(NULL, sizes[n*2+1], PROT_READ, MAP_SHARED, fds[n], 0)) == MAP_FAILED)
	options.bad("Can't open or map source file: %s", sources[n]);
      mapped[n*2+1] = (const char *)maddr;
      ocpiDebug("Mapped OCL input file %s has length %zu", sources[n], (size_t)sizes[n*2+1]);
      std::string line;
      OU::format(line, "# 1 \"%s\"\n", sources[n]);
      char *cp =  new char[line.size()+1];
      strcpy(cp, line.c_str());
      mapped[n*2] = cp;
      sizes[n*2] = line.size();
      ocpiDebug("Mapped OCL input file has: '%s' has length %zu %d/%d", mapped[n*2],
		(size_t)sizes[n*2], mapped[n*2][sizes[n*2]], mapped[n*2+1][sizes[n*2+1]]);
    }
    driver.compile(numSources*2, &mapped[0], &sizes[0], includes, defines, options.output(),
		   options.target(), options.verbose());
  } else if(!strcasecmp(*ap, "targets")) {
    std::set<std::string> targets;
    driver.search(NULL, NULL, false, NULL, NULL, &targets);
    for (std::set<std::string>::const_iterator ti = targets.begin(); ti != targets.end(); ti++)
      printf("%s%s", ti == targets.begin() ? "" : " ", (*ti).c_str());
    printf("\n");
  }
  return 0;
}
