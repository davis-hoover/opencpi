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


#include "input-output.h"




InputOutput::InputOutput()
    : m_port(NULL), m_messageSize(0), m_messagesInFile(false),m_suppressEOF(false),
     m_disableBackpressure(false), m_stopOnEOF(false), m_testOptional(false), m_msMode(bypass) {}
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
static InputOutput *findIO(const char *name, InputOutputs &ios) {
  for (unsigned n = 0; n < ios.size(); n++)
    if (!strcasecmp(ios[n].m_name.c_str(), name))
      return &ios[n];
  return NULL;
}
