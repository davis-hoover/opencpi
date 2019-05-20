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

/*

 Definitions for worker metadata encoding,decoding.
 Offline, in tools, this information is encoded into a string format
 suitable for program level arguments (argv).  All properties are encoded into
 a single string.  This relieves runtime of any parsing overhead (time or space)
 or dependencies on external parsing libraries.

 The "scope" of this property support is configuration properties for CP289
 components.  Thus it is not (yet) intended to support SCA GPP components.

 This file defines the binary (non-string) format of SCA component properties,
 as well as the functions to encode (binary to string) and decode
 (string to binary).

*/

//  This file implements worker metadata
// FIXME: rename this worker, not implementation
#ifndef OCPI_UTIL_WORKER_H
#define OCPI_UTIL_WORKER_H

#include <map>
#include "ezxml.h"
#include "OcpiOsAssert.h"
#include "OcpiUtilException.h"
#include "OcpiUtilProperty.h"
#include "OcpiUtilProtocol.h"
#include "OcpiUtilPort.h"
#include "OcpiUtilMemory.h"

#define CONTROL_OP_I CONTROL_OP
#define OCPI_CONTROL_OPS                                                        \
  CONTROL_OP_I(initialize,   Initialize,     INITIALIZED, EXISTS,      NONE,        NONE,      NONE) \
  CONTROL_OP(start,          Start,          OPERATING,   SUSPENDED,   INITIALIZED, NONE,      NONE) \
  CONTROL_OP(stop,           Stop,           SUSPENDED,   OPERATING,   FINISHED,    NONE,      NONE) \
  CONTROL_OP(release,        Release,        EXISTS,      INITIALIZED, OPERATING,   SUSPENDED, FINISHED) \
  CONTROL_OP(test,           Test,           NONE,        INITIALIZED, NONE,        NONE,      NONE) \
  CONTROL_OP(beforeQuery,    BeforeQuery,    NONE,        INITIALIZED, OPERATING,   SUSPENDED, FINISHED) \
  CONTROL_OP(afterConfigure, AfterConfigure, NONE,        INITIALIZED, OPERATING,   SUSPENDED, NONE) \
  /**/
#define OCPI_CONTROL_STATES \
    CONTROL_STATE(EXISTS) \
    CONTROL_STATE(INITIALIZED) \
    CONTROL_STATE(OPERATING) \
    CONTROL_STATE(SUSPENDED) \
    CONTROL_STATE(FINISHED) \
    CONTROL_STATE(UNUSABLE) \
    CONTROL_STATE(NONE) \
    /**/

namespace OCPI {
  namespace Util {

    // Attributes of an artifact and/or implementation
    // Generally shared by all the implementations in an artifact
    class Attributes {
    protected:
      std::string
	m_uuid,
	m_os, m_osVersion, m_arch,
	m_platform,
	m_tool, m_toolVersion,
	m_opencpiVersion,
	m_runtime, m_runtimeVersion;
      bool m_dynamic;
    public:
      inline const std::string &uuid() const { return m_uuid; }
      inline const std::string &os() const { return m_os; }
      inline const std::string &osVersion() const { return m_osVersion; }
      inline const std::string &arch() const { return m_arch; }
      inline const std::string &platform() const { return m_platform; }
      inline const std::string &opencpiVersion() const { return m_opencpiVersion; }
      inline bool dynamic() const { return m_dynamic; }
    protected:
      // Parse from target string
      void parse(const char *pString);
      // Parse from xml
      void parse(ezxml_t x);
      void validate();
    };

#if 0
    class Test {
      friend class Implementation;
      unsigned int m_testId;
      unsigned int m_nInputs, m_nResults;
      unsigned int *m_inputValues;  // reference to property[n]
      unsigned int *m_resultValues;
    };
#endif

    // This class represents what we know, generically, about a component implementation
    // Currently there is no separate "spec" metadata - it is redundant in each implementation
    class Worker : public IdentResolver {
      friend class Port;
    protected:
      std::string
	m_specName,
	m_name,
	m_model,
	m_package;
      std::vector<const char *> m_slaves; // the model.impl name of a slave, in the m_xml
      Attributes *m_attributes; // not a reference due to these being in arrays
      Port *m_ports;
      Memory *m_memories;
      //      Test *m_tests;
      unsigned m_nPorts, m_nMemories; //, size , m_nTests
      uint8_t m_version;  // version of the model-specific API this worker is written to
    private: // FIXME: make more of this stuff private
      size_t m_totalPropertySize;
      bool   m_isSource;
      //      Test &findTest(unsigned int testId) const;
    public:
      unsigned m_nProperties;
      Property *m_properties;
      Property *m_firstRaw;
      ezxml_t m_xml;
      unsigned m_ordinal; // ordinal within artifact
      // Scalability
      std::string m_validScaling; // Expression for error checking overall scaling
      Port::Scaling m_scaling;
      std::map<std::string, Port::Scaling> m_scalingParameters;
      Worker();
      ~Worker();
      inline uint8_t version() const { return m_version; }
      inline const std::string &model() const { return m_model; }
      inline const std::string &package() const { return m_package; }
      inline const std::string &specName() const { return m_specName; }
      //      inline const std::string &name() const { return m_name; }
      inline const char *cname() const { return m_name.c_str(); }
      inline const std::vector<const char *> &slaves() const { return m_slaves; }
      inline const Attributes &attributes() const { return *m_attributes; }
      inline bool isSource() const { return m_isSource; }
      const char *parse(ezxml_t xml, Attributes *attr = NULL);
      virtual const char
	*getNumber(ezxml_t x, const char *attr, size_t *np, bool *found = NULL,
		   size_t defaultValue = 0, bool setDefault = true) const;
      // These two use exceptions
      Property &findProperty(const char *id) const;
      unsigned whichProperty(const char *id) const;
      // This one returns NULL
      Property *getProperty(const char *id) const;
      const char *getValue(const char *sym, ExprValue &val) const;
      inline Property *properties() const { return m_properties; }
      inline unsigned nProperties() const { return m_nProperties; }
      inline Property *properties(unsigned &np) const {
        np = m_nProperties;
        return m_properties;
      }
      inline Property &property(unsigned long which) const
      {
        ocpiAssert(which < m_nProperties);
        return m_properties[which];
      }
      inline Port *findMetaPort(const std::string &id) const { return findMetaPort(id.c_str()); }
      virtual Port *findMetaPort(const char *name, const Port *except = NULL) const;
      virtual Port &metaPort(unsigned long which) const {
        ocpiAssert(m_ports && which < m_nPorts);
        return m_ports[which];
      }
      inline Port* ports( unsigned int& n_ports ) const
      {
        n_ports = m_nPorts;
        return m_ports;
      }
      inline Port* getPorts() const
      {
        return m_ports;
      }
      inline unsigned int nPorts() const
      {
        return m_nPorts;
      }
      inline Memory* memories(size_t &nMemories) const
      {
        nMemories = m_nMemories;
        return m_memories;
      }
      inline size_t totalPropertySize( ) const
      {
        return m_totalPropertySize;
      }
      const char *finalizeProperties(size_t &offset, uint64_t &totalSize , const IdentResolver *resolver);
      enum ControlOperation {
#define CONTROL_OP(x, c, t, s1, s2, s3, s4)  Op##c,
	OCPI_CONTROL_OPS
#undef CONTROL_OP
	OpsLimit
      };
      enum ControlState {
#define CONTROL_STATE(s) s,
	OCPI_CONTROL_STATES
#undef CONTROL_STATE
      };
      static const char *s_controlStateNames[];
      static const char *s_controlOpNames[];
    };
  }
}
#endif
