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

#include "comp.h"


#define TESTS "-tests.xml"
#define MS_CONFIG "bypass", "metadata", "throttle", "full"

namespace OCPI {
  namespace Test {
    const char *
tryWorker(const char *wname, const std::string &matchName, bool matchSpec, bool specific); 

  }
}

typedef std::vector<DataPort *> DataPorts;
typedef WorkerConfigs::const_iterator WorkerConfigsIter;
//struct InputOutput;

Worker *emulator;
WorkerConfigs configs;
DataPorts optionals;
Worker *wFirst;
enum MsConfig {bypass, metadata, throttle, full};
extern char *s_stressorMode[];

struct InputOutput {
  // this is a singleton in this context
  // Given a worker, see if it is what we want, either matching a spec, or emulating a device
  std::string m_name, m_file, m_script, m_view;
  const DataPort *m_port;
  size_t m_messageSize;
  bool m_messagesInFile, m_suppressEOF, m_disableBackpressure, m_stopOnEOF, m_testOptional;
  MsConfig m_msMode;
  InputOutput(); 
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
