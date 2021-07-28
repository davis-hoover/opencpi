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
#ifndef _OCPI_TESTS_H
#define _OCPI_TESTS_H
#include <cstddef>
#include <string>
#include <strings.h>
#include <cassert>
#include <vector>
#include <sstream>
#include <set>
#include <limits>
#include <algorithm>
#include "OcpiOsDebugApi.h"
#include "OcpiOsFileSystem.h"
#include "OcpiUtilMisc.h"
#include "OcpiUtilEzxml.h"
#include "OcpiLibraryManager.h"


#include "comp.h"
#include "input-output.h"
#include "cases.h"

#define TESTS "-tests.xml"
#define MS_CONFIG "bypass", "metadata", "throttle", "full"

namespace OL = OCPI::Library;

typedef std::pair<ParamConfig*,Worker*> WorkerConfig;
typedef std::vector<DataPort *> DataPorts;
typedef WorkerConfigs::const_iterator WorkerConfigsIter;

extern unsigned matchedWorkers; // count them even if they are not built or usable
extern Workers workers; 
std::string testFile;
extern size_t timeout, duration;
extern const char *finishPort;
extern bool doneWorkerIsUUT; 
extern const char *argPackage;
extern std::string specName, specPackage;
extern bool verbose;
extern Strings excludeWorkers, excludeWorkersTmp;
extern bool testingOptionalPorts;
extern Worker *emulator;
extern WorkerConfigs configs;
extern DataPorts optionals;
extern Worker *wFirst;
extern InputOutputs inputs, outputs; // global ones that may be applied to any case
extern OrderedStringSet onlyPlatforms, excludePlatforms;
extern OrderedStringSet allPlatforms;

extern WorkersIter findWorker(const char *name, Workers &ws);
const char *remove(const std::string &name);
const char *
findPackage(ezxml_t spec, const char *package, const char *specName,
          const std::string &parent, const std::string &specFile, std::string &package_out);
// If the spec in/out arg may be set in advance if it is inline or xi:included
// FIXME: share this with the one in parse.cxx
const char *
getSpec(ezxml_t xml, const std::string &parent, const char *a_package, ezxml_t &spec,
        std::string &specFile, std::string &a_specName);
const char *
tryWorker(const char *wname, const std::string &matchName, bool matchSpec, bool specific); 
static InputOutput *findIO(Port &p, InputOutputs &ios);
static InputOutput *findIO(const char *name, InputOutputs &ios);
const char *doInputOutput(ezxml_t x, void *); 
const char *doPlatform(const char *platform, Strings &platforms); 
const char *doWorker(Worker *w, void *arg); 
const char *emulatorName();
static const char *addWorker(const char *name, void *);
static const char *excludeWorker(const char *name, void *);
static const char *findWorkers();
void connectHdlFileIO(const Worker &w, std::string &assy, InputOutputs &ports);
void connectHdlStressWorkers(const Worker &w, std::string &assy, bool hdlFileIO, InputOutputs &ports);
const char *generateHdlAssembly(const Worker &w, unsigned c, const std::string &dir, const
                                      std::string &name, bool hdlFileIO, Strings &assyDirs, InputOutputs &ports);
#endif
