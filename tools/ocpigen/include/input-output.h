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
#ifndef OCPI_INPUTOUTPUT_H_
#define OCPI_INPUTOUTPUT_H_

#include <cstddef>
#include <string>
#include <strings.h>
#include <cassert>
#include <vector>
#include <sstream>
#include <set>
#include <limits>
#include <algorithm>
#include "OcpiUtilEzxml.h"
#include "OcpiUtilAssembly.h"
#include "OcpiOsDebugApi.h"
#include "OcpiOsFileSystem.h"
#include "OcpiUtilMisc.h"
#include "OcpiLibraryManager.h"
#include "ocpigen.h"
#include "parameters.h"
#include "hdl-device.h"
#include "wip.h"
#include "data.h"
#include "comp.h"
#include "input-output.h"

#define TESTS "-tests.xml"
#define MS_CONFIG "bypass", "metadata", "throttle", "full"

//Make typedefinitions here and explain what they do. 
typedef std::pair<ParamConfig*,Worker*> WorkerConfig;
typedef std::vector<DataPort *> DataPorts;
typedef WorkerConfigs::const_iterator WorkerConfigsIter;

struct InputOutput;
Worker *emulator;
WorkerConfigs configs;
DataPorts optionals;
Worker *wFirst;
enum MsConfig {bypass, metadata, throttle, full};
extern char *s_stressorMode[];
const char *
tryWorker(const char *wname, const std::string &matchName, bool matchSpec, bool specific); 

struct InputOutput {
  // this is a singleton in this context
  // Given a worker, see if it is what we want, either matching a spec, or emulating a device
  std::string m_name, m_file, m_script, m_view;
  const DataPort *m_port;
  size_t m_messageSize;
  bool m_messagesInFile, m_suppressEOF, m_disableBackpressure, m_stopOnEOF, m_testOptional;
  MsConfig m_msMode;
  InputOutput() //is this supposed to be here or in the .cxx?
    : m_port(NULL), m_messageSize(0), m_messagesInFile(false), m_suppressEOF(false),
      m_disableBackpressure(false), m_stopOnEOF(false), m_testOptional(false), m_msMode(bypass) {}
  const char *parse(ezxml_t x, std::vector<InputOutput> *inouts); 
};  

typedef std::vector<InputOutput> InputOutputs;

InputOutputs inputs, outputs; // global ones that may be applied to any case
static InputOutput *findIO(Port &p, InputOutputs &ios);
static InputOutput *findIO(const char *name, InputOutputs &ios);
const char *doInputOutput(ezxml_t x, void *); 
OrderedStringSet onlyPlatforms, excludePlatforms;
const char *doPlatform(const char *platform, Strings &platforms); 
const char *doWorker(Worker *w, void *arg); 
const char *emulatorName();
#endif
