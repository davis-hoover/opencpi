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

// This contains generic port declarations
#ifndef OCPI_COMP_H_
#define OCPI_COMP_H_

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
#include "parameters.h"
#include "hdl-device.h"
#include "wip.h"
#include "data.h"

#define TESTS "-tests.xml"
#define MS_CONFIG "bypass", "metadata", "throttle", "full"
namespace OL = OCPI::Library;
// The package serves two purposes: the spec and the impl.
// If the spec already has a package prefix, then it will only
// be used as the package of the impl.
// FIXME: share this with the one in parse.cxx

class Worker;
typedef std::pair<ParamConfig*,Worker*> WorkerConfig;


unsigned matchedWorkers; // count them even if they are not built or usable
Workers workers;
std::string testFile;
WorkersIter findWorker(const char *name, Workers &ws);

size_t timeout, duration;
const char *finishPort;
bool doneWorkerIsUUT; 
const char *argPackage;
std::string specName, specPackage;
bool verbose;
Strings excludeWorkers, excludeWorkersTmp;
bool testingOptionalPorts;

const char *remove(const std::string &name);
const char *
findPackage(ezxml_t spec, const char *package, const char *specName,
          const std::string &parent, const std::string &specFile, std::string &package_out);
// If the spec in/out arg may be set in advance if it is inline or xi:included
// FIXME: share this with the one in parse.cxx
const char *
getSpec(ezxml_t xml, const std::string &parent, const char *a_package, ezxml_t &spec,
        std::string &specFile, std::string &a_specName);
struct comp
{
  inline bool operator()(const WorkerConfig &lhs, const WorkerConfig &rhs) const;
};
typedef std::set<WorkerConfig, comp> WorkerConfigs;
#endif
