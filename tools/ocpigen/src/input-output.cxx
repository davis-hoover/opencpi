#ifndef __INPUT-OUTPUT_H__
#define __INPUT-OUTPUT_H__

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

#define TESTS "-tests.xml"
#define MS_CONFIG "bypass", "metadata", "throttle", "full"

#include <cstddef>
#include <string>
#include <strings.h>
#include <cassert>
#include <vector>
#include <strings.h>
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
#include "comp.h"
#include "input-output.h"

namespace OL = OCPI::Library;

struct InputOutput;

Worker *emulator = NULL;
static const char *s_stressorMode[] = { MS_CONFIG, NULL };
const char *
tryWorker(const char *wname, const std::string &matchName, bool matchSpec, bool specific) {
  ocpiInfo("Considering worker \"%s\"", wname);
  const char *dot = strrchr(wname, '.');
  std::string
    name(wname, OCPI_SIZE_T_DIFF(dot, wname)),
    file,
    empty;
  if (excludeWorkers.find(wname) != excludeWorkers.end()) {
    if (verbose)
      fprintf(stderr, "Skipping worker \"%s\" since it was specifically excluded.\n", wname);
    ocpiCheck(excludeWorkersTmp.erase(wname) == 1);
    return NULL;
  }
  //OU::format(file, "../%s/%s.xml", wname, name.c_str());
  // Find the worker under lib, so we are looking at things that are built and also so that
  // the actual platform-specific build is easily relative to the OWD here
  OU::format(file, "../lib/%s/%s.xml", dot+1, name.c_str());
  if (!OS::FileSystem::exists(file)) {
    if (matchSpec && specific)
      return OU::esprintf("For worker \"%s\", cannot open file \"%s\"", wname, file.c_str());
    if (verbose)
      fprintf(stderr, "Skipping worker \"%s\" since \"%s\" not found.\n", wname, file.c_str());
    return NULL;
  }
  const char *err;
  Worker *w = Worker::create(file.c_str(), testFile, argPackage, NULL, NULL, NULL, 0, err);
  bool missing;
  if (!err && (matchSpec ? w->m_specName == matchName :
                w->m_emulate && w->m_emulate->m_implName == matchName) &&
      !(err = w->parseBuildFile(true, &missing, testFile))) {
    if (verbose)
      fprintf(stderr,
              "Found worker for %s:  %s\n", matchSpec ? "this spec" : "emulating this worker",
              wname);
    matchedWorkers++;
    if (missing) {
      if (verbose)
        fprintf(stderr, "Skipping worker \"%s\" since it isn't built for any target\n", wname);
      return NULL;
    }
    if (matchSpec) {
      if (w->m_isDevice) {
        if (verbose)
          fprintf(stderr, "Worker has device signals.  Looking for emulator worker.\n");
        std::string workerNames;
        if ((err = OU::file2String(workerNames, "../lib/workers", ' ')))
          return err;
  addDep("../lib/workers", false); // if we add or remove a worker from the library...
        for (OU::TokenIter ti(workerNames.c_str()); ti.token(); ti.next()) {
          if ((err = tryWorker(ti.token(), w->m_implName, false, false)))
            return err;
        }
      }
      workers.push_back(w);
    } else {
      // Found an emulator
      if (emulator)
        return OU::esprintf("Multiple emulators found for %s", matchName.c_str());
      emulator = w;
    }
    return NULL;
  }
  delete w;
  return err;
}

const char *InputOutput::parse(ezxml_t x, std::vector<InputOutput> *inouts) {
    const char
      *name = ezxml_cattr(x, "name"),
      *port = ezxml_cattr(x, "port"),
      *file = ezxml_cattr(x, "file"),
      *script = ezxml_cattr(x, "script"),
      *view = ezxml_cattr(x, "view"),
      *err;
    if ((err = OE::checkAttrs(x, "name", "port", "file", "script", "view", "messageSize",
                              "messagesInFile", "suppressEOF", "stopOnEOF", "disableBackpressure", "testOptional",
                              "stressorMode", (void*)0)))
      return err;
    size_t nn;
    bool suppress, stop, backpressure, testOptional;
    if ((err = OE::getNumber(x, "messageSize", &m_messageSize, 0, true, false)) ||
        (err = OE::getBoolean(x, "messagesInFile", &m_messagesInFile)) ||
        (err = OE::getBoolean(x, "suppressEOF", &m_suppressEOF, false, true, &suppress)) ||
        (err = OE::getBoolean(x, "stopOnEOF", &m_stopOnEOF, false, true, &stop)) ||
        (err = OE::getBoolean(x, "disableBackpressure", &m_disableBackpressure, false, false,
                              &backpressure)) ||
        (err = OE::getBoolean(x, "testOptional", &m_testOptional, false, false,
                              &testOptional)) ||
        (err = OE::getEnum(x, "stressorMode", s_stressorMode, "input stress mode", nn, m_msMode)))
      return err;
    if (!ezxml_cattr(x, "stopOnEOF"))
      m_stopOnEOF = true; // legacy exception to the default-is-always-false rule
    m_msMode = (MsConfig)nn;
    bool isDir;
    if (file) {
      if (script)
        return OU::esprintf("specifying both \"file\" and \"script\" attribute is invalid");
      if (!OS::FileSystem::exists(file, &isDir) || isDir)
        return OU::esprintf("%s file \"%s\" doesn't exist or is a directory", OE::ezxml_tag(x),
                            file);
      m_file = file;
    } else if (script)
      m_script = script;
    if (view)
      m_view = view;
    if (port) {
      Port *p;
      if (!(p = wFirst->findPort(port)) && (!emulator || !(p = emulator->findPort(port))))
        return OU::esprintf("%s port \"%s\" doesn't exist", OE::ezxml_tag(x), port);
      if (!p->isData())
        return OU::esprintf("%s port \"%s\" exists, but is not a data port",
                            OE::ezxml_tag(x), port);
      if (p->isDataProducer()) {
        if (suppress)
          return
            OU::esprintf("the \"suppressEOF\" attribute is invalid for an output port:  \"%s\"",
                          port);
        if (!stop)
          m_stopOnEOF = true;
        if (m_msMode != bypass)
          return
            OU::esprintf("the \"stressorMode\" attribute is invalid for an output port:  \"%s\"",
                          port);
      } else {
        if (stop)
          return
            OU::esprintf("the \"stopOnEOF\" attribute is invalid for an input port:  \"%s\"",
                          port);
        if (backpressure)
          return
            OU::esprintf("the \"disableBackpressure\" attribute is invalid for an input port:  \"%s\"",
                          port);
      }
      m_port = static_cast<DataPort *>(p);
      if (testOptional) {
        testingOptionalPorts = true;
        optionals.resize(optionals.size() + 1);
        optionals.push_back(static_cast<DataPort *>(p));
      }
    }
    if (name) {
      if (inouts) {
        for (unsigned n = 0; n < inouts->size()-1; n++) {
          if (!strcasecmp(name, (*inouts)[n].m_name.c_str())) {
            return OU::esprintf("name \"%s\" is a duplicate %s name", name, OE::ezxml_tag(x));
          }
        }
      }
      m_name = name;
    }

    return NULL;
  }  
static InputOutput *findIO(Port &p, InputOutputs &ios) {
  for (unsigned n = 0; n < ios.size(); n++)
    if (ios[n].m_port == &p)
      return &ios[n];
  return NULL;
}
static const char *s_smode[] = { MS_CONFIG, NULL };
static InputOutput *findIO(const char *name, InputOutputs &ios) {
  for (unsigned n = 0; n < ios.size(); n++)
    if (!strcasecmp(ios[n].m_name.c_str(), name))
      return &ios[n];
  return NULL;
}
const char *doInputOutput(ezxml_t x, void *) {
  std::vector<InputOutput> &inouts = !strcasecmp(OE::ezxml_tag(x), "input") ? inputs : outputs;
  inouts.resize(inouts.size() + 1);
  return inouts.back().parse(x, &inouts);
}
const char *doPlatform(const char *platform, Strings &platforms) {
  platforms.insert(platform); // allow duplicates
  return NULL;
}
const char *doWorker(Worker *w, void *arg) {
  Workers &set = *(Workers *)arg;
  for (WorkersIter wi = set.begin(); wi != set.end(); ++wi)
    if (w == *wi)
      OU::esprintf("worker \"%s\" is already in the list", w->cname());
  set.push_back(w);
  return NULL; 
  }
const char *emulatorName() {
  InputOutput *io;
  const char *em =  emulator ? strrchr(emulator->m_specName, '.') : NULL;
  if (em)
    em++;
  else if (emulator)
    em = emulator->m_specName;
  return em;
}
#endif
