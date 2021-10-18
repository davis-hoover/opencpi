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

#include <set>
#include <limits>
#include <climits>
#include "OcpiUtilExceptionApi.h"
#include "OcpiUtilEzxml.h"
#include "OcpiUtilMisc.h"
#include "OcpiUtilDataTypes.h"
#include "OcpiUtilValue.h"
#include "OcpiUtilWorker.h"
#include "OcpiUtilAssembly.h"

namespace OCPI {
  namespace Util {
    namespace OA = OCPI::API;
    namespace OE = OCPI::Util::EzXml;

    Assembly::Assembly(const char *file, const char **extraTopAttrs,
                       const char **extraInstAttrs, const PValue *params)
      : m_copy(NULL), m_xmlOnly(false), m_isImpl(false) {
      const char *cp = file;
      while (isspace(*cp))
        cp++;
      const char *err;
      if (*cp == '<') {
        size_t len = strlen(cp);
        m_copy = new char[len + 1];
        strcpy(m_copy, cp);
        err = OE::ezxml_parse_str(m_copy, len, m_xml);
      } else
        err = OE::ezxml_parse_file(file, m_xml);
      if (err || (err = parse(NULL, extraTopAttrs, extraInstAttrs, params)))
        throw Error("%s", err);
    }
    Assembly::Assembly(const std::string &string, const char **extraTopAttrs,
                       const char **extraInstAttrs, const PValue *params)
      : m_xmlOnly(false), m_isImpl(false) {
      m_copy = new char[string.size() + 1];
      strcpy(m_copy, string.c_str());
      const char *err = OE::ezxml_parse_str(m_copy, string.size(), m_xml);
      if (err || (err = parse(NULL, extraTopAttrs, extraInstAttrs, params)))
        throw Error("%s", err);
    }
    Assembly::Assembly(const ezxml_t top, const char *defaultName, bool a_isImpl,
                       const char **extraTopAttrs, const char **extraInstAttrs,
                       const PValue *params)
      : m_xml(top), m_copy(NULL), m_xmlOnly(true), m_isImpl(a_isImpl) {
      const char *err = parse(defaultName, extraTopAttrs, extraInstAttrs, params);
      if (err)
        throw Error("Error parsing assembly xml string due to: %s", err);
    }
    Assembly::~Assembly() {
      if (m_xml && !m_xmlOnly)
        ezxml_free(m_xml);
      delete [] m_copy;
      for (size_t i = 0; i < m_instances.size(); ++i)
        delete m_instances[i];
    }

    unsigned Assembly::s_count = 0;

    const char *Assembly::
    addInstance(ezxml_t ix, const char **extraInstAttrs, const PValue *params, bool addXml) {
      unsigned n = (unsigned)m_instances.size();
      Instance *i = new Instance;
      m_instances.push_back(i);
      i->m_freeXml = addXml;
      return i->parse(ix, *this, n, extraInstAttrs, params);
    }

    const char *Assembly::
    parse(const char *defaultName, const char **extraTopAttrs, const char **extraInstAttrs,
          const PValue *params) {
      // This is where common initialization is done except m_xml and m_copy
      m_doneInstance = UINT_MAX;
      m_cMapPolicy = RoundRobin;
      m_processors = 0;
      ezxml_t ax = m_xml;
      const char *err;
      static const char *baseAttrs[] = { "name", "package", NULL};
      bool maxProcs = false, minProcs = false, roundRobin = false;
      // FIXME: move app-specific parsing up into library assy
      if ((err = OE::checkAttrsVV(ax, baseAttrs, extraTopAttrs, NULL)) ||
          (err = OE::checkElements(ax, OCPI_ASSY_ELEMENTS, NULL)) ||
          (err = OE::getNumber(ax, "maxprocessors", &m_processors, &maxProcs)) ||
          (err = OE::getNumber(ax, "minprocessors", &m_processors, &minProcs)) ||
          (err = OE::getBoolean(ax, "roundrobin", &roundRobin)) ||
          (err = m_collocation.parse(ax)))
        return err;
      if (maxProcs)
        m_cMapPolicy = MaxProcessors;
      else if (minProcs)
        m_cMapPolicy = MinProcessors;
      else if (roundRobin)
        m_cMapPolicy = RoundRobin;
      else
        m_cMapPolicy = RoundRobin;
      ezxml_t plx = ezxml_cchild(ax, "policy");
      if (plx) {
        const char * tmp = ezxml_attr(plx, "mapping" );
        if ( tmp ) {
          if (!strcasecmp(tmp, "maxprocessors"))
            m_cMapPolicy = MaxProcessors;
          else if (!strcasecmp(tmp, "minprocessors"))
            m_cMapPolicy = MinProcessors;
          else if (!strcasecmp(tmp, "roundrobin"))
            m_cMapPolicy = RoundRobin;
          else
            return esprintf("Invalid policy mapping option: %s", tmp);
        }
        tmp  = ezxml_attr(plx, "processors");
        if (tmp) {
          m_processors = (size_t)atoi(tmp);
        }
      }
      OE::getNameWithDefault(ax, m_name, defaultName ? defaultName : "unnamed%u", s_count);
      OE::getOptionalString(ax, m_package, "package");
      if (m_package.empty() || m_package[0] == '.') {
	const char *env = getenv("OCPI_PROJECT_PACKAGE");
	if (!env)
	  env = getenv("OCPI_DEFAULT_PACKAGE");
	std::string prefix = env ? env : "local";
       if (m_package[0] == '.')
	 prefix += m_package;
       m_package = prefix;
      }
      for (ezxml_t ix = ezxml_cchild(ax, "Instance"); ix; ix = ezxml_cnext(ix))
        if ((err = addInstance(ix, extraInstAttrs, params)))
          return err;
      const char *finished = ezxml_cattr(ax, "finished");
      if (!finished) // remove in 3.0
        finished = ezxml_cattr(ax, "done"); // remove in 3.0
      unsigned n;
      if (finished) {
        if ((err = getInstance(finished, n)))
          return err;
        m_doneInstance = n;
      }
      // Note the mapped properties are AFTER the instances so that a value
      // set on an instance is overriden by one on a mapped property.
      // Not likely, but the instance level stuff may be shared someday
      m_mappedProperties.resize(OE::countChildren(ax, "property"));
      MappedProperty *p = &m_mappedProperties[0];
      for (ezxml_t px = ezxml_cchild(ax, "property"); px; px = ezxml_cnext(px), p++)
        if ((err = p->parse(px, *this, params)))
          return err;
      // Add top level externals that simply define single port external connections
      // name defaults from port.  Externals go before connections since they might
      // define an external that is used by a connection
      for (ezxml_t ex = ezxml_cchild(ax, "External"); ex; ex = ezxml_cnext(ex))
        if ((err = parseExternal(ex, NULL, NULL, params)))
          return err;
      n = 0;
      for (ezxml_t cx = ezxml_cchild(ax, "Connection"); cx; cx = ezxml_cnext(cx), ++n) {
        m_connections.push_back(new Connection);
        if ((err = m_connections.back()->parse(cx, *this, n, params)))
          return err;
      }
      n = 0;
      for (ezxml_t ix = ezxml_cchild(ax, "Instance"); ix; ix = ezxml_cnext(ix), n++)
        if ((err = m_instances[n]->parseConnection(ix, *this, params)))
          return err;
      // Check instance parameters that don't name instances properly
      // Set the last/fourth (singleAssignment) parameter to true for those that should
      // only be a single assignment per  workers should only make a  once.
      if ((err = checkInstanceParams("selection", params, false, true)) ||
          (err = checkInstanceParams("transport", params)) ||
          (err = checkInstanceParams("transferRole", params)) ||
          (err = checkInstanceParams("portBufferCount", params)) ||
          (err = checkInstanceParams("portBufferSize", params)) ||
          (err = checkInstanceParams("worker", params, false, true)) ||
          (err = checkInstanceParams("property", params, true)))
        return err;
      return NULL;
    }

    // Given a assignment value that is an instance assignment, find the instance and modify
    // the parameter value to point past the = sign.  Two output args.
    const char *Assembly::
    findInstanceForParam(const char *pName, const char *&assign, size_t &instn) {
      const char *eq = strchr(assign, '=');
      if (!eq)
        return esprintf("Parameter assignment for \"%s\", \"%s\" is invalid. "
                        "Format is: <instance>=<parameter-value>", pName, assign);
      size_t len = OCPI_SIZE_T_DIFF(eq, assign);
      for (unsigned nn = 0; assign && nn < m_instances.size(); nn++)
        if (!strncasecmp(assign, m_instances[nn]->m_name.c_str(), len) &&
            m_instances[nn]->m_name.length() == len) {
          instn = nn;
          assign = eq + 1;
          return NULL;
        }
      return esprintf("No instance found for \"%s\" assignment for \"%s\" parameter",
                      assign, pName);
    }

    // Error check parameters for that have instance names
    const char *Assembly::
    checkInstanceParams(const char *pName, const PValue *params, bool checkMapped,
                        bool singleAssignment) {
      const char *assign;
      // Keep track of which instances we have seen for this parameter, using ordinals
      std::set<unsigned> instancesSeen;
      bool emptySeen = false;
      for (unsigned n = 0; findAssignNext(params, pName, NULL, assign, n); ) {
        const char *eq = strchr(assign, '=');
        if (!eq || (!emptySeen && !eq[1])) // empty value only if wildcard previously
          return esprintf("Parameter assignment '%s' is invalid. "
                          "Format is: [<instance>]=<parameter-value>", assign);
        size_t len = OCPI_SIZE_T_DIFF(eq, assign);
        if (len == 0) { // an empty assignment is ok as default for later ones
          emptySeen = true; // this means a later empty assigned value is ok
          continue;
        }
	bool optional = false;
	if (assign[0] == '?' && len > 1)
	  assign++, len--, optional = true;
        for (unsigned nn = 0; assign && nn < m_instances.size(); nn++)
          if ((m_instances[nn]->m_name.length() == len &&
	       !strncasecmp(assign, m_instances[nn]->m_name.c_str(), len)) ||
	      (m_instances[nn]->m_specName.length() == len &&
	       !strncasecmp(assign, m_instances[nn]->m_specName.c_str(), len))) {
            if (singleAssignment && !instancesSeen.insert(nn).second)
              return esprintf("%s assignment '%s' is a reassignment of that instance.",
                              pName, assign);
            assign = NULL;
        }
        if (assign && checkMapped) {
          MappedProperty *mp = &m_mappedProperties[0];
          for (size_t nn = m_mappedProperties.size(); assign && nn; nn--, mp++)
            if (mp->m_name.length() == len && !strncasecmp(assign, mp->m_name.c_str(), len))
              assign = NULL;
        }
        if (assign && !optional)
          return esprintf("No instance for %s assignment '%s'", pName, assign);
      }
      return NULL;
    }

    const char * Assembly::
    getInstance(const char *a_name, unsigned &n) {
      for (n = 0; n < m_instances.size(); n++)
        if (m_instances[n]->m_name == a_name)
          return NULL;
      return esprintf("No instance named \"%s\" found", a_name);
    }

    const char *Assembly::
    addConnection(const char *a_name, ezxml_t x, size_t count, Connection *&c) {
      for (auto ci = m_connections.begin(); ci != m_connections.end(); ci++)
        if (!strcasecmp((*ci)->m_name.c_str(), a_name))
          return esprintf("Duplicate connection named '%s' in assembly", a_name);
      Connection *tmp = new Connection;
      const char *err, *s;
      if (((s = ezxml_cattr(x, "transport")) && (err = tmp->m_parameters.add("transport", s))) ||
	  ((s = ezxml_cattr(x, "buffersize")) && (err = tmp->m_parameters.add("buffersize", s))))
	return err;
      m_connections.push_back(tmp);
      c = m_connections.back();
      c->m_name = a_name;
      c->m_count = count;
      return NULL;
    }
    const char *Assembly::
    addPortConnection(ezxml_t ix, size_t from, const char *fromPort, size_t to,
		      const char *toPort, const PValue *params) {
      std::string l_name = m_instances[from]->m_name + "." + (fromPort ? fromPort : "output");
      Connection *c;
      Port *toP, *fromP;
      const char *err;
      if ((err = addConnection(l_name.c_str(), ix, 0, c)) ||
          (err = c->addPort(*this, to, toPort, true, false, true, 0, params, toP)) ||
          (err = c->addPort(*this, from, fromPort, false, false, true, 0, params, fromP)))
        return err;
      return NULL;
    }
    // This is called to create an external connection either from the very short shortcut
    // as an attribute of an instance (saying this port should be externalized with its
    // own name), or with the other short cut: a top level "external" that just describes
    // the instance, port and other options.
    // It is also called from upper layers when ports are externalized (and port direction is known)
    // Hence the isInput, bidi, known optional arguments
    const char *Assembly::
    addExternalConnection(ezxml_t x, size_t a_instance, const char *port, const PValue *params,
                          bool isInput, bool bidi, bool known) {
      const char *err;
      Connection *c;
      External *e;
      if ((err = addConnection(port, x, 0, c)) ||
	  (err = addExternal(port, NULL, NULL, 0, e)))
	return err;
      c->addExternal(*e, 0, 0);
      Port *p;
      return c->addPort(*this, a_instance, port, isInput, bidi, known, 0, params, p);
    }

    const char *Assembly::
    addExternal(const char *a_name, const char *role, const char *url, size_t count, External *&a_ext) {
#if 0 // c++ 11
      auto rv = m_externals.emplace(a_name, a_name); // c++17 could use try_emplace
#else
      auto rv = m_externals.insert(std::make_pair(a_name, External(a_name)));
#endif
      if (!rv.second)
	return esprintf("Duplicate external port name: %s", a_name);
      External &e = rv.first->second;
      if (url)
	e.m_url = url;
      e.m_count = count;
      if (count)
	e.m_connected.resize(count);
      if (role) {
        if (!strcasecmp(role, "provider") || !strcasecmp(role, "input") ||
	    !strcasecmp(role, "consumer") || !strcasecmp(role, "slave")) {
          e.m_role.m_provider = true;
          e.m_role.m_knownRole = true;
        } else if (!strcasecmp(role, "user") || !strcasecmp(role, "output") ||
		   !strcasecmp(role, "producer") || !strcasecmp(role, "master")) {
          e.m_role.m_provider = false;
          e.m_role.m_knownRole = true;
        } else if (!strcasecmp(role, "bidirectional")) {
          e.m_role.m_bidirectional = true;
          e.m_role.m_knownRole = true;
        } else if (*role)
          return esprintf("Invalid external role: %s", role);
      }
      a_ext = &e;
      return NULL;
    }

    // Note that this may be called both from an application/mapped property as well as an
    // instance property - we essentially merge the info from both, checking for inconsistencies
    const char *Assembly::Property::
    setValue(ezxml_t px) {
      const char *cp, *err;
      if ((cp = ezxml_cattr(px, "value"))) {
        if (ezxml_cattr(px, "valueFile"))
          return esprintf("For instance property \"%s\", having both \"value\" and \"valueFile\""
                          " attributes is invalid", m_name.c_str());
        if (m_hasValue)
          return esprintf("For instance property \"%s\", already has application value \"%s\"",
                          m_name.c_str(), m_value.c_str());
        m_hasValue = true;
        m_value = cp;
      } else if ((cp = ezxml_cattr(px, "valueFile"))) {
        if (m_hasValue)
          return esprintf("For instance property \"%s\", already has application value \"%s\"",
                          m_name.c_str(), m_value.c_str());
        if ((err = file2String(m_value, cp, ',')))
          return err;
        m_hasValue = true;
      }
      if ((cp = ezxml_cattr(px, "dumpFile"))) {
        if (cp && m_dumpFile.length())
          return esprintf("For instance property \"%s\", duplicate dumpFile attributes",
                          m_name.c_str());
        m_dumpFile = cp;
      }
      return NULL;
    }

    void Assembly::Property::
    setValue(const char *name, const char *value) {
      m_name = name;
      m_value = value;
      m_hasValue = true;
    }

    const char *Assembly::MappedProperty::
    parse(ezxml_t px, Assembly &a, const PValue *params) {
      const char *err;
      std::string instance;

      if ((err = OE::checkAttrs(px, "name", "value", "valuefile", "dumpFile", "instance", "property", NULL)) ||
          (err = OE::getRequiredString(px, m_name, "name", "property")) ||
          (err = OE::getRequiredString(px, instance, "instance", "property")) ||
          (err = a.getInstance(instance.c_str(), m_instance)))
        return err;
      MappedProperty *p = &a.m_mappedProperties[0];
      for (size_t n = a.m_mappedProperties.size(); n && p < this; n--, p++)
        if (p->m_name == m_name)
          return esprintf("Duplicate mapped property: %s", m_name.c_str());
      const char *cp = ezxml_cattr(px, "property");
      m_instPropName = cp ? cp : m_name.c_str();
      if ((err = a.m_instances[m_instance]->addProperty(m_instPropName.c_str(), px)))
	return err;
      // Add any top-level property assignment in params for this mapped property
      const char *propAssign;
      for (unsigned n = 0; findAssignNext(params, "property", m_name.c_str(), propAssign, n); ) {
	std::string assign = m_instPropName + "=" + propAssign;
	if ((err = a.m_instances[m_instance]->setProperty(assign.c_str())))
	  return err;
      }
      return NULL;
    }

    const char *Assembly::Property::
    parse(ezxml_t px, Assembly::Property *first) {
      const char *err;
      if ((err = OE::checkAttrs(px, "name", "value", "valuefile", "dumpFile", NULL)) ||
          (err = OE::getRequiredString(px, m_name, "name", "property")))
        return err;
      for (Property *p = first; p && p < this; p++)
        if (!strcasecmp(p->m_name.c_str(), m_name.c_str()))
          return esprintf("Duplicate property \"%s\" in instance", m_name.c_str());
      return setValue(px);
    }

    Assembly::Instance::Instance() : m_freeXml(false) {}
    Assembly::Instance::~Instance() { if (m_freeXml) ezxml_free(m_xml); }

    const char *Assembly::Instance::
    checkSlave(Assembly &a, const char *instance, const char *slave) {
      unsigned n = UINT_MAX;
      if (instance) { // if no instance, this is a placeholder
	const char *err;
	if ((err = a.getInstance(instance, n)))
	  return err;
	Instance &si = *a.m_instances[n];
	if (si.m_hasMaster)
	  return esprintf("Instance %s is slave to multiple proxies", si.m_name.c_str());
	si.m_hasMaster = true;
	si.m_master = m_ordinal;
      }
      m_slaveInstances.emplace_back(n);
      m_slaveNames.emplace_back(slave); // slave can be NULL, implying the one slave
      return NULL;
    }

    const char *Assembly::Instance::
    parseSlave(Assembly &a, ezxml_t sx) {
      // new way uses instance and slave attrs, old way used "name" as instance name
      const char *err;
      if ((err = OE::checkAttrs(sx, "name", "instance", "slave", NULL)))
	return err;
      const char
	*name = ezxml_cattr(sx, "name"),
	*slave = ezxml_cattr(sx, "slave"),
	*instance = ezxml_cattr(sx, "instance");
      if (name) {
	if (slave || instance)
	  return esprintf("slave elements should have only \"slave\" and \"instance\" attributes");
	instance = name;
      } else if (!instance)
	return esprintf("slave elements must have \"instance\" attributes");
      return checkSlave(a, instance, slave);
    }

    // connect, then optionally, which local port (from) and which dest port (to).
    // external=port, connect=instance, then to or from?
    const char *Assembly::Instance::
    parseConnection(ezxml_t ix, Assembly &a, const PValue *params) {
      const char *err, *c, *e, *ci = NULL; // quiet compiler warning
      if ((c = ezxml_cattr(ix, "connect")) || (ci = ezxml_cattr(ix, "connectinput"))) {
        unsigned n;
        if ((err = a.getInstance(c ? c : ci, n)) ||
            (err = a.addPortConnection(ix, c ? m_ordinal : n, ezxml_cattr(ix, "from"),
                                       c ? n : m_ordinal, ezxml_cattr(ix, "to"),
                                       params)))
          return err;
      } else if (ezxml_cattr(ix, "transport"))
        return esprintf("Instance %s has transport attribute without connect attribute",
                        m_name.c_str());
      else if (ezxml_cattr(ix, "buffersize"))
        return esprintf("Instance %s has buffersize attribute without connect attribute",
                        m_name.c_str());
      if ((e = ezxml_cattr(ix, "external")) &&
	  (err = a.addExternalConnection(ix, m_ordinal, e, params)))
	return err;
      const char *slave = ezxml_cattr(ix, "slave");
      if (slave) {
	if (ezxml_cchild(ix, "slave"))
	  return esprintf("cannot have slave elements when you have a slave attribute");
	if ((err = checkSlave(a, slave, NULL)))
	  return err;
      } else
	for (ezxml_t cx = ezxml_cchild(ix, "slave"); cx; cx = ezxml_cnext(cx))
	  if ((err = parseSlave(a, cx)))
	    return err;
      return NULL;
    }

    // Parse the delays as expressions of doubles (seconds), and then convert to usecs
    // FIXME: this code is redundant with the tests.cxx
    static const char *
    parseDelay(ezxml_t x, Assembly::Delay &usecs, bool &hasDelay) {
      const char *delay = ezxml_cattr(x, "delay");
      if (delay) {
        ValueType vt(OA::OCPI_Double);
        Value v(vt);
        const char *err;
        if ((err = v.parse(delay)))
          return err;
        v.m_Double *= 1e6;
        if (v.m_Double < 0 || v.m_Double >= std::numeric_limits<Assembly::Delay>::max())
          return esprintf("delay value \"%s\" (%g) out of range, 0 to %g", delay, v.m_Double/1e6,
                          (double)std::numeric_limits<Assembly::Delay>::max()/1e6);
        usecs = static_cast<Assembly::Delay>(v.m_Double);
        hasDelay = true;
      } else
        hasDelay = false;
      return NULL;
    }

    // Called both from app-level property as well as instance-level property
    const char *Assembly::Instance::
    addProperty(const char *name, ezxml_t px) {
      const char *err;
      bool isProperty = !strcasecmp(ezxml_name(px), "property");
      do { // break to add instance and property name to error
        if ((err = OE::checkElements(px, isProperty ? "set" : NULL, NULL)))
          break;
        Delay delay = 0; // some compilers' warnings don't recognize parseDelay setting these
        bool hasDelay = false; // ditto
        if ((err = parseDelay(px, delay, hasDelay)))
          return err;
        const char
          *value = ezxml_cattr(px, "value"),
          *valueFile = ezxml_cattr(px, "valueFile");
        bool hasValue = value || valueFile;
        if (hasDelay && !hasValue)
          return esprintf("property setting for \"%s\" has delay but no value", name);
        // Scan existing properties.  Other than errors we either update the existing one
        // or add one (for a new delay).  n will be non-zero if we are reusing a pvalue
        size_t n = 0;
        Property *p = &m_properties[0];
        for (n = m_properties.size(); n; n--, p++)
          if (!strcasecmp(p->m_name.c_str(), name)) {
            if (p->m_hasValue) {             // existing has a value
              if (hasValue) {                // new has a value
                if (p->m_hasDelay) {         // existing has delay
                  if (hasDelay) {            // new has delay
                    if (delay == p->m_delay) {
                      err = esprintf("two property values have the same delay: %g",
                                     (double)delay / 1000000);
                      break;
                    } // else: skip it since delays are different
                  } // else: skip it since existing has delay but we don't
                } else if (!hasDelay) {
                  err = "duplicate initial property value";
                  break;
                } // else: skip it since existing has no delay but we do
              } else if (!p->m_hasDelay)
                break;  // reuse since we have no value and existing has no delay
            } else
              break; // reuse since existing has no value
          }
        if (err)
          break;
        // Avoid using this property element if it is just a container for <set> elements
        if (strcasecmp(ezxml_name(px), "property") || hasValue || ezxml_cattr(px, "dumpFile")) {
          if (!n) {
            m_properties.resize(m_properties.size() + 1);
            p = &m_properties.back();
            p->m_name = name;
          }
          p->m_hasDelay = hasDelay;
          p->m_delay = delay;
          if ((err = p->setValue(px)))
            break;
        }
        // Recurse for <set> elements
        if (isProperty)
          for (ezxml_t sx = ezxml_cchild(px, "set"); sx; sx = ezxml_cnext(sx))
            if ((err = OE::checkAttrs(sx, "value", "valuefile", "delay", NULL)) ||
                (err = addProperty(name, sx)))
              break;
      } while (0);
      return err ?
        (isProperty ?
        esprintf("error for instance \"%s\" property \"%s\":  %s", m_name.c_str(), name, err) :
         err) :
        NULL;
    }

    const char *Assembly::Instance::
    setProperty(const char *propAssign) {
      const char *eq = strchr(propAssign, '=');
      if (!eq)
        return esprintf("Property assignment '%s=%s' is invalid. "
                        "Format is: <instance>=<prop>=<value>",
                        m_name.c_str(), propAssign);
      std::string pName(propAssign, OCPI_SIZE_T_DIFF(eq, propAssign));
      Property *p = &m_properties[0];
      for (unsigned nn = 0; nn < m_properties.size(); nn++, p++)
        if (!strcasecmp(pName.c_str(), p->m_name.c_str())) {
          p->m_value = eq + 1;
          p->m_hasValue = true;
          propAssign = NULL;
          break;
        }
      if (propAssign) {
        Property prop;
        prop.m_name = pName;
        prop.m_hasValue = true;
        prop.m_value = eq + 1;
        m_properties.push_back(prop);
      }
      return NULL;
    }
    // There is no non-default constructor so initialize here...
    const char *Assembly::Instance::
    parse(ezxml_t ix, Assembly &a, unsigned ordinal, const char **extraInstAttrs,
	  const PValue *params) {
      m_ordinal = ordinal;
      m_hasMaster = false;
      const char *err;
      static const char *instAttrs[] =
        { "component", "Worker", "Name", "connect", "to", "from", "external", "selection",
          "buffersize", "index", "externals", "slave", "transport", "connectInput", NULL};
      if ((err = OE::checkAttrsVV(ix, instAttrs, extraInstAttrs, NULL)) ||
          (err = OE::getBoolean(ix, "externals", &m_externals)) ||
          (err = m_collocation.parse(ix)))
        return err;
      m_xml = ix;
      std::string component, myBase;
      if (a.isImpl()) {
        if (ezxml_cattr(ix, "component"))
          return "'component' attributes are invalid in this implementation assembly";
        if ((err = OE::getRequiredString(ix, m_implName, "worker", "instance")))
          return err;
        baseName(m_implName.c_str(), myBase); // leading directory and authoring model stripped off
      } else if ((err = OE::getRequiredString(ix, component, "component", "instance")))
        return err;
      else {
	myBase = component; // no slashes, no authoring model
	const char *compName = strrchr(component.c_str(), '.');
	if (compName)
	  if (component[0] == '.')
	    m_specName = a.m_package + component;
	  else
	    m_specName = component;
	else
	  m_specName = a.m_package + "." + component;
      }
      size_t toDot = myBase.find_last_of('.');
      if (toDot != myBase.npos)
	myBase.erase(0, toDot+1);
      // FIXME: somehow pass in valid elements or do this test somewhere else...
      if ((err = OE::checkElements(ix, "property", "signal", "slave", NULL)))
	return err;
      // Figure out the name of this instance.
      if (!OE::getOptionalString(ix, m_name, "name")) {
        // default is component%u unless there is only one, in which case it is "component".
        unsigned me = 0, n = 0;
        for (ezxml_t x = ezxml_cchild(a.xml(), "instance"); x; x = ezxml_cnext(x)) {
          std::string base;
          const char
            *c = ezxml_cattr(x, "component"),
            *w = ezxml_cattr(x, "worker");
          if (a.isImpl() && w)
            baseName(w, base); // strip off the authoring model suffix
          else if (!a.isImpl() && c)
	    base = c;
	  else
	    continue; // ignore bad other instances here, errors will be caught later
	  assert(!base.empty());
	  const char *dot = strrchr(base.c_str(), '.');
          if (!strcasecmp(dot ? dot + 1 : base.c_str(), myBase.c_str())) {
            if (x == ix)
              me = n;
            n++;
          }
        }
        if (n > 1)
          formatString(m_name, "%s%u", myBase.c_str(), me);
        else
          m_name = myBase;
      }
      if (!a.isImpl()) {
        if (!findAssign(params, "worker", m_name.c_str(), m_implName) &&
	    !findAssign(params, "worker", m_specName.c_str(), m_implName))
          OE::getOptionalString(ix, m_implName, "worker");
      }
      if (!findAssign(params, "selection", m_name.c_str(), m_selection) &&
	  !findAssign(params, "selection", m_specName.c_str(), m_selection))
        OE::getOptionalString(ix, m_selection, "selection");
      ocpiInfo("Component %2d: %s name: %s impl: %s spec: %s selection: %s", ordinal,
                component.c_str(), m_name.c_str(), m_implName.c_str(), m_specName.c_str(),
                m_selection.c_str());
      for (ezxml_t px = ezxml_cchild(ix, "property"); px; px = ezxml_cnext(px)) {
        const char *name = ezxml_cattr(px, "name");
        if (!name)
          return "missing name attribute in property element";
        if ((err = OE::checkAttrs(px, "name", "value", "valuefile", "dumpFile", "delay", NULL)) ||
            (err = addProperty(name, px)))
          return err;
      }
      const char *propAssign;
      // Now deal with instance-based property parameters that might override the XML ones
      // First, process the parameters for ALL instances, then the parameters for specific
      // instances
      for (unsigned n = 0; findAssignNext(params, "property", NULL, propAssign, n); )
        if (propAssign[0] == '=' && (err = setProperty(propAssign + 1)))
          return err;
      for (unsigned n = 0; findAssignNext(params, "property", m_name.c_str(), propAssign, n); )
        if ((err = setProperty(propAssign)))
          return err;
      // Now check for additional or override values from parameters
      return m_parameters.parse(ix, "name", "component", "worker", "selection", "connect", "buffersize",
                                "external", "from", "to", "externals", "slave", "transport", "optional",
                                "connectInput", NULL);
    }

    // Get the port from the instance, creating it if needed.
    // The instance owns the port, and we need to deal with cases when the port is
    // mentioned more than once (like for multiple connections with different indices)
    // The port may be named or unnamed.
    const char *Assembly::Instance::
    getPort(const char *name, bool isInput, bool isBidi, bool isKnown, Port *&port) {
      assert(name || isKnown); // if not named, must at least know the role
      for (auto it = m_ports.begin(); it != m_ports.end(); ++it) {
	port = &*it;
	if (!name) {
	  if (it->m_name.empty() && it->m_role.m_provider == isInput &&
	      it->m_role.m_bidirectional)
	    return NULL;
	} else if (!strcasecmp(name, it->m_name.c_str())) {
	  if (isKnown && it->m_role.m_knownRole &&
	      (isInput != it->m_role.m_provider || isBidi != it->m_role.m_bidirectional))
	    return esprintf("Inconsistent use of port \"%s\" of instance \"%s\" as input "
			    "or output or bidirectional", name, m_name.c_str());
	  else
	    return NULL;
	}
      }
      m_ports.push_back(Port()); // emplace...
      port = &m_ports.back();
      if (name)
        port->m_name = name;
      port->m_role.m_provider = isInput;
      port->m_role.m_bidirectional = isBidi;
      port->m_role.m_knownRole = isKnown;
      port->m_instance = m_ordinal;
      return NULL;
    }

    Assembly::Connection::
    Connection() : m_count(0) {}

#if 0
    Assembly::Connection::
    Connection(const Connection &other)
      : m_name(other.m_name), m_externals(other.m_externals), m_ports(other.m_ports),
	m_parameters(other.m_parameters), m_count(other.m_count)
    {
      Port *p0 = NULL, *p1 = NULL;
      for (auto it = m_ports.begin(); it != m_ports.end(); ++it) {
	//	(*it).m_connection = this;
	assert(!(p0 && p1));
	(p0 ? p1 : p0) = (*it).first;
      }
      if (p0 && p1) {
	p0->m_connectedPort = p1;
	p1->m_connectedPort = p0;
      }
    }
#endif
    const char *Assembly::Connection::
    parse(ezxml_t cx, Assembly &a, unsigned &n, const PValue *params) {
      const char *err;
      if ((err = OE::checkElements(cx, "port", "external", NULL)) ||
          //      (err = OE::checkAttrs(cx, "name", "transport", "external", "count", NULL)) ||
          (err = OE::getNumber(cx, "count", &m_count, NULL, 0)))
        return err;

      OE::getNameWithDefault(cx, m_name, "conn%u", n);
      if ((err = m_parameters.parse(cx, "name", "external", "count", NULL)))
        return err;

      const char *role = ezxml_cattr(cx, "external");
      ezxml_t ext = ezxml_cchild(cx, "external");
      if (ext && role)
	return esprintf("A connection cannot both an external attribute and an external child element");
      if ((role || ext) && (err = a.parseExternal(ext, this, role, params)))
	return err;
      if (OE::countChildren(cx, "port") < 1)
        return "no ports found under connection";
      for (ezxml_t x = ezxml_cchild(cx, "port"); x; x = ezxml_cnext(x))
        if ((err = parsePort(x, a)))
          return err;
      return NULL;
    }

    const char *Assembly::Connection::
    addPort(Assembly &a, size_t instance, const char *portName, bool isInput, bool bidi,
            bool known, size_t index, const PValue */*params*/, Assembly::Port *&port) {
      const char *err;
      if ((err = a.m_instances[instance]->getPort(portName, isInput, bidi, known, port)))
	return err;
      m_ports.emplace_back(port, index);
      port->m_connections.push_front(this);
      return NULL;
    }

    const char *Assembly::Connection::
    addExternal(External &e, size_t index, size_t count) {
      if (e.m_count) {
	if (count > e.m_count || index + count  > e.m_count)
	  return esprintf("Invalid index/count %zu/%zu when connecting to external port with count %zu",
			  index, count, e.m_count);
	size_t i = index;
	for (count = count ? count : 1; count--; i++) {
	  if(e.m_connected[i])
	    return esprintf("Duplicate connection to external \"%s\" index %zu of %zu",
			    e.m_name.c_str(), i, e.m_count);
	  e.m_connected[i] = true;
	}
      } else if (index)
	return esprintf("For external port %s, connection has index when no count is set",
			e.m_name.c_str());
      m_externals.emplace_back(&e, index);
      return NULL;
    }

    Assembly::Port::
    Port() : m_instance(SIZE_MAX) {}

    // Set parameters for the port, during and after XML parsing
    const char *Assembly::Port::
    setParam(Connection &c, const char *name, const char *value) {
      if (!strcasecmp(name, "buffersize") || !strcasecmp(name, "transport"))
	return c.m_parameters.add(name, value, true);
      return m_parameters.add(name, value, true);
    }

    const char *Assembly::Connection::
    parsePort(ezxml_t x, Assembly &a) {
      const char *err;
      std::string iName;
      unsigned instance;
      size_t index;
      if ((err = OE::checkElements(x, NULL)) ||
          (err = OE::getRequiredString(x, iName, "instance")) ||
          (err = OE::getNumber(x, "index", &index)) ||
          (err = a.getInstance(iName.c_str(), instance)))
        return err;
      std::string name, from, to;
      OE::getOptionalString(x, name, "name");
      OE::getOptionalString(x, from, "from");
      OE::getOptionalString(x, to, "to");
      bool isInput = false, isKnown = false;
      const char *onlyOne = "Only one of 'name', 'from' and 'to' attributes allowed in 'port' element";
      if (name.size()) {
        if (from.size() || to.size())
          return onlyOne;
      } else if (from.size()) {
        if (to.size())
          return onlyOne;
        isKnown = true;
        name = from;
      } else if (to.size()) {
        isInput = isKnown = true;
        name = to;
      } else
        return "One of 'name', 'from', or 'to' attribute must be present in 'port' element";
      // We don't know the role at all at this point
      Port *p;
      if ((err = addPort(a, instance, name.c_str(), isInput, false, isKnown, index, NULL, p)))
        return err;
      return p->m_parameters.parse(NULL, x, "name", "instance", "from", "to", NULL);
    }

    Assembly::External::
    External(const char *name) : m_name(name), m_count(0), m_connected(0) {
      m_role.m_knownRole = false;
      m_role.m_bidirectional = false;
      m_role.m_provider = false;
    }
    // There are four variants of "external" elements: (convenience has its price)
    // There are 7 attributes that apply variously as described below:
    //   Attributes that apply specifically to the external (port):
    //     name          - name of external (optional in cases 2, 3, 4)
    //     url           - url that is connected externally (optional, all cases)
    //     role          - role of external port (optional)
    //     count         - in case 1 (below)
    //     index         - in case 4 (below)
    //   Attributes that apply to the internal port being connected externally
    //     instance      - which instance does the internal port belong to
    //     port          - internal port that is connected to this external
    //     index         - index at internal port (case 2)
    //   Attributes that apply to the connection being established (case 2)
    //     count         - the count of the connection
    //
    // 1. the top-level element that just defines the external port, without a connection
    //    This element is *required* if there will be multiple connections to it
    //    Required:  name
    //    Optional:  url, role, count
    //    Invalid:   port, instance, index
    // 2. top-level element connection-shortcut references a new external port
    //    Required:  port and instance to specify the internal endpoint
    //    Optional:  name (defaults from port), url, index, count, role
    //    count is both the count of the connection and the count of the external port
    // 3. top-level element connection-shortcut references a predefined external port
    //    Required:  port and instance to specify the internal endpoint
    //    Optional:  name (defaults from port), url, index, count
    //    Invalid:   role
    //    count is the count of the connection
    // 4. a child element of "connection", introducing a new external port
    //    Required:  none
    //    Optional:  name, url, index
    //    Invalid:   port, instance, count
    // 5. a child element of "connection", referencing predefined external port
    //    Required:  none
    //    Optional:  name, url, index
    //    Invalid:   port, instance, count
    const char *Assembly::
    parseExternal(ezxml_t x, Connection *a_conn, const char *a_role, const PValue *pvl) {
      const char
	*l_name = ezxml_cattr(x, "name"),
	*url = ezxml_cattr(x, "url"),
	*port = ezxml_cattr(x, "port"),
	*l_instance = ezxml_cattr(x, "instance"),
	*role = a_role ? a_role : ezxml_cattr(x, "role");
      size_t index, count;
      bool hasIndex, hasCount;
      const char *err;
      if ((err = OE::getNumber(x, "count", &count, &hasCount)) ||
	  (err = OE::getNumber(x, "index", &index, &hasIndex)))
	return err;
      External *e = NULL;
      std::string nameString; // original or constructed name
      if (l_name) {
	nameString = l_name;
	auto eit = m_externals.find(l_name);
	if (eit != m_externals.end())
	  e = &eit->second;
      }
      Connection *conn = a_conn;
      if (!conn && !port && !l_instance) {
	// --------------------------------------------------------------------------------
	// Case 1: we are defining an external port, but not connecting it to any internal port
	if (!l_name)
	  return esprintf("Missing \"name\" attribute in top-level \"external\" element without "
			  "a port connection");
	if (e)
	  return esprintf("Duplicate external port named \"%s\"", l_name);
	if (hasIndex)
	  return esprintf("Index attribute not allowed in top-level \"external\" element without "
			  "a port/instance connection");
      } else if (!conn) {
	// --------------------------------------------------------------------------------
	// Case 2 or 3:  a top-level 'external' element that also makes a connection via port+instance
	if (!port || !l_instance)
	  return esprintf("An \"external\" element must have both \"port\" and \"instance\" "
			  "attributes or neither");
	if (!l_name) {
	  l_name = port; // index ? format(nameString, "%s%zu", port, index) : port;
	  auto eit = m_externals.find(l_name);
	  e = eit == m_externals.end() ? NULL : &eit->second;
	}
	if (e) {
	  // --------------------------------------------------------------------------------
	  // Case 3:  the top-level 'external' exists
	  if (role)
	    return esprintf("A top-level external element cannot respecify the \"role\" attribute");
	  if (hasCount && count > (e->m_count ? e->m_count : 1))
	    return esprintf("A top-level external element's \"count\" attribute (%zu) cannot "
			    "exceed predefined count of the external port (%zu)",
			    count, e->m_count);
	}
	// Case 2 or 3 - make top level connection, external is added later in all cases
	unsigned instanceNum;
	Port *dummy;
	std::string cName;
	if ((err = getInstance(l_instance, instanceNum)) ||
	    (err = addConnection(format(cName, "conn%zu", m_connections.size()), x, count, conn)) ||
	    (err = conn->addPort(*this, instanceNum, port, false, false, false, index, pvl, dummy)))
	  return err;
      } else if (port || l_instance || count) // case 4 or 5, an external child of connection
	return esprintf("An external element inside a connection element cannot have \"port\", "
			"\"instance\", or \"count\" attributes");
      else if (!e) {
	// --------------------------------------------------------------------------------
	// Case 4:  an 'external' element part of a 'connection' that introduces the external port
	//          or an external attribute of a connection (with no name)
        if (hasIndex)
	  return esprintf("An external element inside a connection element cannot have an \"index\" "
			  "attribute unless the external port is predefined separately");
	if (!l_name)
	  l_name = conn->m_name.empty() ?
	    format(nameString, "ext%zu", m_externals.size()) : conn->m_name.c_str();
	auto eit = m_externals.find(l_name);
	e = eit == m_externals.end() ? NULL : &eit->second;
      } else {
	// --------------------------------------------------------------------------------
	// Case 5: an external child element of a connection for a predefined external
	if (role)
	  return esprintf("An external element inside a connection element cannot have a \"role\" "
			  "attribute when the external port is predefined separately");
      }
      if ((!e && (err = addExternal(l_name, role, url, count, e))) || // create the external case 1,2,4
	  (conn && (err = conn->addExternal(*e, a_conn ? index : 0, count)))) // case 2, 3, 4, 5
	return err;
      return e->m_parameters.parse(pvl, x, "name", "url", "provider", "port", "instance", "index", "count", NULL);
    }
    Assembly::Role::Role()
      : m_knownRole(false), m_bidirectional(false), m_provider(false) {
    }
    Assembly::CollocationPolicy::
    CollocationPolicy()
      : m_minCollocation(1), m_maxCollocation(0), m_minContainers(1), m_maxContainers(0)
    {
    }
    const char *Assembly::CollocationPolicy::
    parse(ezxml_t x) {
      const char *err;
      if ((err = OE::getNumber(x, "minCollocation", &m_minCollocation, NULL, 0, false)) ||
          (err = OE::getNumber(x, "maxCollocation", &m_maxCollocation, NULL, 0, false)) ||
          (err = OE::getNumber(x, "minContainers", &m_minContainers, NULL, 0, false)) ||
          (err = OE::getNumber(x, "maxContainers", &m_maxContainers, NULL, 0, false)))
        return err;
      return NULL;
    }
    const char *Assembly::CollocationPolicy::
    apply(size_t scale, size_t nContainers, size_t &collocation, size_t &usedContainers,
          size_t &finalScale) const {
      finalScale = scale;
      usedContainers =
        m_maxContainers ? (m_maxContainers > nContainers ? nContainers : m_maxContainers) :
        nContainers;
      collocation = (scale + usedContainers - 1) / usedContainers; // initial spread-wide amount
      ocpiDebug("Applying collo policy of collo %zu/%zu, cont %zu/%zu to scale %zu cont %zu",
                m_minCollocation, m_maxCollocation, m_minContainers, m_maxContainers,
                scale, nContainers);
      // Essentially we start out using the maximum number of containers allowed
      if (collocation < m_minCollocation) {
        // We are spread too thin.  Use fewer containers
        usedContainers = (scale + m_minCollocation - 1)/m_minCollocation;
        collocation = m_minCollocation;
        if (usedContainers < m_minContainers) {
          // we are too concentrated, perhaps use more
          usedContainers = m_minContainers > nContainers ? nContainers : m_minContainers;
          collocation = (scale + usedContainers - 1)/usedContainers;
        }
      }
      if (m_maxCollocation && collocation > m_maxCollocation)
        return esprintf("scaled deployment needs collocation of %zu, but max allowed is %zu",
                        collocation, m_maxCollocation);
      ocpiDebug("Collocation policy result is: collocation %zu on %zu containers",
                collocation, usedContainers);
      return NULL;
    }
  }
}
