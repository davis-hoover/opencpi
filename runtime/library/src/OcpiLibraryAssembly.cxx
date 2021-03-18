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

#include <inttypes.h>
#include <strings.h>
#include <iostream>
#include "OcpiLibraryAssembly.h"
#include "OcpiUtilValue.h"
#include "OcpiUtilEzxml.h"

namespace OCPI {
  namespace Library {
    namespace OU = OCPI::Util;
    namespace OE = OCPI::Util::EzXml;
    // Attributes specific to an application assembly
    static const char *assyAttrs[] = { COLLOCATION_POLICY_ATTRS,
				       "maxprocessors", "minprocessors", "roundrobin", "done",
				       NULL};
    // The instance attributes relevant to app assemblies - we don't really deal with "container" here
    // FIXME: It should be in the upper level
    static const char *instAttrs[] = { COLLOCATION_POLICY_ATTRS,
				       "model", "platform", "container", NULL};
#if 0
    Assembly::Assembly(const char *file, const OCPI::Util::PValue *params)
      : OU::Assembly(file, assyAttrs, instAttrs, params), m_refCount(1) {
      findImplementations(params);
    }
    Assembly::Assembly(const std::string &string, const OCPI::Util::PValue *params)
      : OU::Assembly(string, assyAttrs, instAttrs, params), m_refCount(1) {
      findImplementations(params);
    }
#endif
    Assembly::Assembly(ezxml_t a_xml, const char *a_name, const OCPI::Util::PValue *params)
      : OU::Assembly(a_xml, a_name, false, assyAttrs, instAttrs, params), m_refCount(1) {
      findImplementations(params);
    }
    Assembly::~Assembly() {
      for (size_t n = 0; n < m_instances.size(); n++)
	delete m_instances[n];
    }

    void
    Assembly::
    operator ++( int )
    {
      m_refCount++;
    }

    void
    Assembly::
    operator --(int)
    {
      if (--m_refCount == 0)
	delete this;
    }

    // Process an assignment for a specific port or a specific instance, or just an external
    // port of the assembly.
    // assign arg now points to:  <instance>=<port>=<value> or <externalport>=<value>
    // If the removeExternal is true, remove any external port connection since the caller
    // will replace it.
    const char *Assembly::
    getPortAssignment(const char *pName, const char *assign, size_t &instn, size_t &portn,
		      const OU::Port *&port, const char *&value, bool removeExternal) {
      unsigned neqs = 0;
      const char *eq = strchr(assign, '?'); // points past instance or external port
      for (const char *cp = assign; *cp && (!eq || cp < eq); cp++)
	if (*cp == '=')
	  neqs++;
      std::string pname;
      eq = strchr(assign, '='); // points past instance or external port
      auto ci = m_connections.end();
      if (neqs == 1) { // find an external port with this name
	pname.assign(assign, OCPI_SIZE_T_DIFF(eq, assign));
	const OU::Assembly::Port *ap = NULL;
	for (ci = m_connections.begin(); ci != m_connections.end(); ci++) {
	  const OU::Assembly::Connection &c = **ci;
	  if (c.m_externals.size() &&
	      !strcasecmp(pname.c_str(), c.m_externals.front().first->m_name.c_str())) {
	    ap = &c.m_ports.front();
	    instn = ap->m_instance;
	    assert(ap->m_name.size());
	    pname = ap->m_name; // pname is now internal name
	    break;
	  }
	}
	if (!ap)
	  throw OU::Error("No external port found for %s assignment '%s'", pName, assign);
      } else if (neqs == 2) {
	const char *err, *iassign = assign;
	if ((err = findInstanceForParam(pName, iassign, instn))) // iassign points to port name
	  return err;
	eq = strchr(iassign, '=');
	pname.assign(iassign, OCPI_SIZE_T_DIFF(eq, iassign));
	// There might be an external connection on this port that has to be removed...
	if (removeExternal)
	  for (ci = m_connections.begin(); ci != m_connections.end(); ci++) {
	    const OU::Assembly::Connection &c = **ci;
	    const OU::Assembly::Port *ap = &c.m_ports.front();
	    if (c.m_externals.size() && ap->m_instance == instn &&
		!strcasecmp(ap->m_name.c_str(), pname.c_str()))
		  break;
	  }
      } else
	return OU::esprintf("Parameter assignment for \"%s\", \"%s\" is invalid.  Format is:"
			    "<instance>=<port>=<filename> of <external-port>=<filename>",
			    pName, assign);
      unsigned nPorts;
      const OU::Port *p = m_instances[instn]->m_candidates[0].impl->m_metadataImpl.ports(nPorts);
      for (unsigned nn = 0; nn < nPorts; nn++, p++)
	if (!strcasecmp(pname.c_str(), p->m_name.c_str())) {
	  value = eq + 1;
	  portn = nn;
	  port = p;
	  if (removeExternal && ci != m_connections.end())
	      m_connections.erase(ci);
	  return NULL;
	}
      return OU::esprintf("Port \"%s\" not found for instance in \"%s\" parameter assignment: %s",
			  pname.c_str(), pName, assign);
    }
    // After all the other implementations are established, so we know port directions etc.,
    // insert file read/write components
    const char *Assembly::
    addFileIoInstances(const OCPI::Util::PValue *params) {
      const char *assign;
      for (unsigned n = 0; OU::findAssignNext(params, "file", NULL, assign, n); ) {
	const char *value, *err;
	size_t instn, portn;
	const OU::Port *port;
	if ((err = getPortAssignment("file", assign, instn, portn, port, value, true)))
	  return err;
	bool reading = port->m_provider;
	// create a file read/write instance connected to the specified instance and port
	ezxml_t inst = ezxml_new("instance");
	ezxml_set_attr_d(inst, "component", reading ? "ocpi.core.file_read" : "ocpi.core.file_write");
	ezxml_set_attr_d(inst, reading ? "connect" : "connectInput", utilInstance(instn).cname());
	ezxml_set_attr_d(inst, reading ? "to" : "from", port->cname());
	ezxml_t fpx = ezxml_add_child(inst, "property", 0);
	ezxml_set_attr_d(fpx, "name", "filename");
	// Parse the file name like a URL, with ? for "query" and & or ; delimiting
	// name=value pairs
	const char *p = strchr(value, '?');
	if (p) {
	  std::string s(value, OCPI_SIZE_T_DIFF(p, value));
	  ezxml_set_attr_d(fpx, "value", s.c_str());
	  do {
	    const char *tp = strchr(++p, '=');
	    if (!tp)
	      return OU::esprintf("Invalid file option: %s", assign);
	    s.assign(p, OCPI_SIZE_T_DIFF(tp, p));
	    ezxml_t x = ezxml_add_child(inst, "property", 0);
	    ezxml_set_attr_d(x, "name", s.c_str());
	    p = strchr(++tp, ';');
	    if (!p) p = strchr(tp, '&');
	    if (!p) p = tp + strlen(tp);
	    s.assign(tp, OCPI_SIZE_T_DIFF(p, tp));
	    ezxml_set_attr_d(x, "value", s.c_str());
	  } while (*p++);
	} else
	  ezxml_set_attr_d(fpx, "value", value);
	char *x = ezxml_toxml(inst);
	ocpiInfo("adding file I/O component: %s", x);
	free(x);
	if ((err = OU::Assembly::addInstance(inst, NULL, NULL, true)) ||
	    (err = utilInstance(nUtilInstances() - 1).parseConnection(inst, *this, params)))
	  return err;
	addInstance(params);
      }
      return NULL;
    }
    // The util::assembly only knows port names, not worker port ordinals
    // (because it has not been correlated with any implementations).
    // It may not even know port names if connect shortcuts are used.
    // Here is where we process the matchup between the port names in the util::assembly
    // and the port names in implementations in the libraries
    bool Assembly::Instance::
    resolveUtilPorts(const Implementation &i, OU::Assembly &utilAssy) {
      // This test works even when there are no ports
      if (m_assyPorts) {
	// We have processed an implementation before, just check for consistency
	if (i.m_metadataImpl.nPorts() != m_nPorts) {
	  ocpiInfo("Rejected: port number mismatch (%u vs %u) between implementations of worker %s.",
		   i.m_metadataImpl.nPorts(), m_nPorts, i.m_metadataImpl.specName().c_str());
	  return false;
	}
	// FIXME: we should compare more implementation info for compatibility?
	return true;
      }
      // The one-time action for the first implementation found for an instance
      // If it fails for some reason, we just rejected it and wait for another one.
      // We undo any side effects on failure so that if a good match comes later,
      // we can accept it.
      OU::Port *ports = i.m_metadataImpl.ports(m_nPorts);
      OU::Assembly::Port **ap = new OU::Assembly::Port *[m_nPorts];
      for (unsigned n = 0; n < m_nPorts; n++)
	ap[n] = NULL;
      const OU::Assembly::Instance &inst = m_utilInstance;
      OU::Port *p;

      // build the map from implementation port ordinals to util::assembly::ports
      for (std::list<OU::Assembly::Port*>::const_iterator pi = inst.m_ports.begin();
	   pi != inst.m_ports.end(); pi++) {
	OU::Port *found = NULL;
	OU::Assembly::Port &asp = **pi;
	if (asp.m_name.empty()) {
	  // Resolve empty port names to be unambiguous if possible
	  p = ports;
	  for (unsigned n = 0; n < m_nPorts; n++, p++)
	    if (!p->m_isInternal &&
                ((asp.m_role.m_provider && p->m_provider) ||
		 (!asp.m_role.m_provider && !p->m_provider))) {
	      if (found) {
		ocpiInfo("Rejected \"%s\": the '%s' connection at instance '%s' is ambiguous: "
			 " port name must be specified.", i.m_artifact.name().c_str(),
			 asp.m_role.m_provider ? "input" : "output",
			 m_utilInstance.m_name.c_str());
		goto rejected;
	      }
	      if (ap[n]) {
		ocpiInfo("Rejected \"%s\": the '%s' connection at instance '%s' is redundant: "
			 " implicit port '%s' already has a connection.",
			 i.m_artifact.name().c_str(), asp.m_role.m_provider ? "input" : "output",
			 m_utilInstance.m_name.c_str(), p->m_name.c_str());
		goto rejected;
	      }
	      ap[n] = &asp;
	      asp.m_name = p->m_name;
	      found = p;
	    }
	  if (!found) {
	    ocpiInfo("Rejected \"%s\": there is no %s port for connection at instance '%s'.",
		     i.m_artifact.name().c_str(), asp.m_role.m_provider ? "input" : "output",
		     m_utilInstance.m_name.c_str());
	    goto rejected;
	  }
	} else {
	  p = ports;
	  for (unsigned n = 0; n < m_nPorts; n++, p++)
	    if (!strcasecmp(ports[n].m_name.c_str(), asp.m_name.c_str())) {
	      if (p->m_isInternal) {
		ocpiInfo("Rejected: the \"%s\" port of instance '%s' is internal.",
			 asp.m_name.c_str(), m_utilInstance.m_name.c_str());
		goto rejected;
	      }
	      if (ap[n]) {
		ocpiInfo("Rejected \"%s\": the '%s' connection at instance '%s' is redundant: "
			 " port '%s' already has a connection.", i.m_artifact.name().c_str(),
			 asp.m_role.m_provider ? "input" : "output",
			 m_utilInstance.m_name.c_str(), p->m_name.c_str());
		goto rejected;
	      }
	      ap[n] = &asp;
	      asp.m_role.m_knownRole = true;
	      asp.m_role.m_provider = p->m_provider;
	      found = p;
	      break;
	    }
	  if (!found) {
	    ocpiInfo("Rejected \"%s\": assembly instance '%s' of worker '%s' has no port named "
		     "'%s'", i.m_artifact.name().c_str(),
		     inst.m_name.c_str(), i.m_metadataImpl.specName().c_str(),
		     asp.m_name.c_str());
	    goto rejected;
	  }
	}
	asp.m_ordinal = found->m_ordinal;
      }
      // Final side effects on success
      if (inst.m_externals) {
	// If the OU::Assembly instance specified that unconnected ports
	// should be externalized, we do that now.
	p = ports;
	for (unsigned n = 0; n < m_nPorts; n++, p++) {
	  bool found = false;
	  for (auto pi = inst.m_ports.begin(); pi != inst.m_ports.end(); pi++)
	    if (!strcasecmp((*pi)->m_name.c_str(), p->m_name.c_str())) {
	      found = true;
	      break;
	    }
	  // FIXME: should this externalization only apply to spec ports?
	  if (!found) // Not mentioned in the assembly. Add an external.
	    utilAssy.addExternalConnection(NULL, inst.m_ordinal, p->m_name.c_str(), NULL,
					   p->m_provider, false, true);
	}
      }
      p = ports;
      for (unsigned n = 0; n < m_nPorts; n++, p++)
	if (ap[n] && ap[n]->m_name.empty())
	  // This is a mutable member of a const object.
	  ap[n]->m_name = p->m_name;
      m_assyPorts = ap;
      return true;
    rejected:
      delete [] ap;
      return false;
    }

    static bool reject(const Assembly::Instance &/*inst*/, const Implementation &impl,
		       const char *fmt, ...) {
      if (OS::logWillLog(OCPI_LOG_INFO)) {
	std::string reason;
	va_list ap;
	va_start(ap, fmt);
	OU::formatAddV(reason, fmt, ap);
	va_end(ap);
	ocpiInfo("  Rejected implementation \"%s%s%s\" in "
		 "\"%s\" due to %s",
		 impl.m_metadataImpl.cname(), impl.m_staticInstance ? "/" : "",
		 impl.m_staticInstance ? ezxml_cattr(impl.m_staticInstance, "name") : "",
		 impl.m_artifact.name().c_str(), reason.c_str());
      }
      return false;
    }
    // Perform connectivity checks for a candidate implementation for this instance
    // Return true if the implementation is still acceptable
    bool Assembly::Instance::
    checkConnectivity(Candidate &cand, Assembly &assy) {
      const Implementation &i = *cand.impl;
      if (!resolveUtilPorts(i, assy))
	return reject(*this, i, "incompatible/inconsistent ports"); 
      // Here is where we know about the assembly and thus can check for
      // some connectivity constraints.  If the implementation has hard-wired connections
      // that are incompatible with the assembly, we reject it.
      if (i.m_externals) {
	OU::Port::Mask m = 1;
	for (unsigned n = 0; n < OU::Port::c_maxPorts; n++, m <<= 1)
	  if (m & i.m_externals) {
	    // This port cannot be connected to another instance in the same container.
	    // Thus it PRECLUDES other connected instances on the same container.
	    // So the connected instance cannot have an INTERNAL requirement.
	    // But we can't check is here because it is a constraint about
	    // a pair of choices, not just one choice.
	  }
      }
      if (i.m_internals) {
	OCPI::Library::Connection *c = i.m_connections;
	unsigned nPorts;
	OU::Port *p = i.m_metadataImpl.ports(nPorts);
	OU::Port::Mask m = 1;
	unsigned bump = 0;
	for (unsigned n = 0; n < nPorts; n++, m <<= 1, c++, p++)
	  if (m & i.m_internals) {
	    // Find the assembly connection port for this instance and this
	    // internally/statically connected port
	    OU::Assembly::Port *ap = m_assyPorts[n];
	    if (ap && !ap->m_connection->m_externals.size()) {
	      // We found the assembly connection port
	      // Now check that the port connected in the assembly has the same
	      // name as the port connected in the artifact
	      if (!ap->m_connectedPort)
		return reject(*this, i,
			      "artifact having port \"%s\" connected while application doesn't.",
			      p->m_name.c_str());
	      // This check can only be made for the port of the internal connection that is
	      // for a later instance, since null-named ports are resolved as each
	      // instance is processed
	      if (ap->m_connectedPort->m_instance < m_utilInstance.m_ordinal &&
		  (strcasecmp(ap->m_connectedPort->m_name.c_str(),
			      c->port->m_name.c_str()) || // port name different
		   assy.utilInstance(ap->m_connectedPort->m_instance).m_specName !=
		   c->impl->m_metadataImpl.specName())) {             // or spec name different
		reject(*this, i, "incompatible connection on port \"%s\"", p->m_name.c_str());
		ocpiInfo("    Artifact connects it to port '%s' of spec '%s', "
			 "but application connects it to port '%s' of spec '%s'",
			 c->port->m_name.c_str(), c->impl->m_metadataImpl.specName().c_str(),
			 ap->m_connectedPort->m_name.c_str(),
			 assy.utilInstance(ap->m_connectedPort->m_instance).m_specName.c_str());
		return false;
	      }
	      bump = 1;; // An implementation with hardwired connections gets a score bump
	    } else if (m_utilInstance.m_hasMaster || (ap && ap->m_connection->m_externals.size())) 
	      // I'm a slave and my master might delegate a port to me --or--
	      // I am connected externally to something that cannot be confirmed yet, like a delegated port
	      // I.e. there might be a problem but I cannot reject YET.
	      return true;
	    else {
	      // There is no connection in the assembly for a statically connected impl port
	      ocpiInfo("  Rejected \"%s\" because artifact has port '%s' connected while "
		       "application doesn't mention it.", i.m_artifact.name().c_str(),
		       p->m_name.c_str());
	      return false;
	    }
	  }
	cand.score += bump;
      }
      return true;
    }
    // The callback for the findImplementations() method below.
    // Return true if we found THE ONE.
    // Set accepted = true, if we actually accepted one
    bool Assembly::
    foundImplementation(const Implementation &i, bool &accepted) {
      if (m_tempInstance->foundImplementation(i, m_model, m_platform))
	accepted = true;
      return false; // we never terminate the search among possibilities...
    }
    // The library assembly instance has a candidate implementation.
    // Check it out, and maybe accept it as a candidate
    bool Assembly::Instance::
    foundImplementation(const Implementation &impl, std::string &model, std::string &platform) {
      ocpiInfo("  Considering implementation \"%s%s%s\" from artifact \"%s\"",
	       impl.m_metadataImpl.cname(),
	       impl.m_staticInstance ? "/" : "",
	       impl.m_staticInstance ? ezxml_cattr(impl.m_staticInstance, "name") : "",
	       impl.m_artifact.name().c_str());
      // Check for worker name match
      std::string fullWorker;
      if (m_utilInstance.m_implName.size() &&
	  // Just the worker name without model - no dots
	  strcasecmp(m_utilInstance.m_implName.c_str(), impl.m_metadataImpl.cname()) &&
	  // Just the worker name with model - one dot
	  strcasecmp(m_utilInstance.m_implName.c_str(),
		     OU::format(fullWorker, "%s.%s",
				impl.m_metadataImpl.cname(), impl.m_metadataImpl.model().c_str())) &&
	  // The fully qualified name
	  strcasecmp(m_utilInstance.m_implName.c_str(),
		     OU::format(fullWorker, "%s.%s.%s", impl.m_metadataImpl.package().c_str(),
				impl.m_metadataImpl.cname(), impl.m_metadataImpl.model().c_str()))) {
	ocpiInfo("    Rejected: worker name is \"%s.%s\", while requested worker name is \"%s\"",
		 impl.m_metadataImpl.cname(), impl.m_metadataImpl.model().c_str(),
		 m_utilInstance.m_implName.c_str());
	return false;
      }
      // Check for model and platform matches
      if (model.size() && strcasecmp(model.c_str(), impl.m_metadataImpl.model().c_str())) {
	ocpiInfo("    Rejected: model requested is \"%s\", but the model for this implementation is \"%s\"",
		 model.c_str(), impl.m_metadataImpl.model().c_str());
	return false;
      }
      unsigned score;
      if (m_utilInstance.m_selection.empty())
	score = 1;
      else {
	OU::ExprValue val;
	const char *err =
	  OU::evalExpression(m_utilInstance.m_selection.c_str(), val, &impl.m_metadataImpl);
	if (!err && !val.isNumber())
	  err = "selection expression has string value";
	if (err)
	  throw
	    OU::Error("Error for instance \"%s\" with selection expression \"%s\": %s",
		      m_utilInstance.m_name.c_str(), m_utilInstance.m_selection.c_str(), err);
	int64_t n = val.getNumber();
	if (n <= 0) {
	  ocpiInfo("    Rejected: selection expression \"%s\" has value: %" PRIi64,
		   m_utilInstance.m_selection.c_str(), n);
	  return false;
	}
	score = (unsigned)(n < 0 ? 0 : n);
      }
      // Check for scalability suitability.
      std::string error;
      if (impl.m_metadataImpl.m_scaling.check(m_scale, error)) {
	ocpiInfo("    Rejected: %s", error.c_str());
	return false;
      }
      strip_pf(platform);

      // To this point all the checking has applied to the worker we are looking at.
      // From this point some of the checking may actually apply to the slave if there is one.
      // The aspects that could apply to the slave are:
      // 1. Platform choices
      // 2. Property-based selection
      if (platform.size() && strcasecmp(platform.c_str(),
					impl.m_metadataImpl.attributes().platform().c_str())) {
	ocpiInfo("    Rejected: platform requested is \"%s\", but the platform is \"%s\"",
		 platform.c_str(), impl.m_metadataImpl.attributes().platform().c_str());
	return false;
      }
      // Check for property and parameter matches
      // Mentioned Property values have to be initial, and if parameters, they must match
      // values.
      const OU::Assembly::Properties &aProps = m_utilInstance.m_properties;
      for (unsigned ap = 0; ap < aProps.size(); ap++) {
	const char
	  *apName = aProps[ap].m_name.c_str(),
	  *apValue = aProps[ap].m_value.c_str();

	OU::Property *up = impl.m_metadataImpl.getProperty(apName);
	if (!up) {
	  ocpiInfo("    Rejected: initial property \"%s\" not found", apName);
	  return false;
	}
	if (!aProps[ap].m_hasValue)
	  continue; // used by dumpfile
	OU::Property &uProp = *up;
	if (!uProp.m_isWritable && !uProp.m_isParameter) {
	  ocpiInfo("    Rejected: initial property \"%s\" was neither writable nor a parameter",
		   apName);
	  return false;
	}
	OU::Value aValue; // FIXME - save this and use it later
	const char *err = uProp.parseValue(apValue, aValue, NULL, &impl.m_metadataImpl);
	if (err) {
	  ocpiInfo("    Rejected: the value \"%s\" for the \"%s\" property, \"%s\", was invalid: %s",
		   apValue, uProp.m_isImpl ? "implementation" : "spec", apName, err);
	  return false;
	}
	// We know the supplied value is valid.
	if (uProp.m_isParameter) {
	  std::string pStr;
	  assert(uProp.m_default);
	  uProp.m_default->unparse(pStr); // FIXME: canonical value could be cached if props are compared
	  // Now we have canonicalized the default value in pStr.
	  std::string aStr;
	  aValue.unparse(aStr);
	  if (aStr != pStr) {
	    ocpiInfo("    Rejected: property \"%s\" is a parameter compiled with value \"%s\"; requested value is \"%s\"",
		     apName, pStr.c_str(), apValue);
	    return false;
	  }
	  ocpiDebug("    Requested '%s' parameter value '%s' matched compiled value '%s'",
		    apName, apValue, pStr.c_str());
	}
      }
      if (m_utilInstance.slaveInstances().size() && !impl.m_metadataImpl.slaveAssy()) {
	ocpiInfo("    Rejected because the instance in the application indicates slaves therefore is a proxy,"
	         " but the candidate implementation which implements the correct OCS is not a proxy");
	return false;
      }
      // FIXME:  Check consistency between implementation metadata here...
      m_candidates.push_back(Candidate(impl, score));
      ocpiInfo("    Accepted implementation before connectivity checks with score %u", score);
      return true;
    }

    void Assembly::Instance::strip_pf(std::string& platform) const {
      // Remove trailing _pf from string
      const size_t pos = platform.rfind("_pf");
      if (pos != platform.npos && pos == platform.length()-3)
        platform.erase(pos);
    }

    void Assembly::
    addInstance(const OU::PValue *params) {
      unsigned n = (unsigned)m_instances.size();
      m_instances.push_back(new Instance(OU::Assembly::instance(n)));
      ocpiInfo("================================================================================");
      ocpiInfo("For instance %2u: \"%s\", finding and checking candidate implementations/workers",
	       n, utilInstance(n).cname());
      // if we have a deployment, don't do the work to figure out potential implementations
      if (m_deployed)
	return;
      m_tempInstance = m_instances.back();
      const OU::Assembly::Instance &inst = m_tempInstance->m_utilInstance;
      // need to deal with params that can filter impls: model and platform
      ezxml_t x = inst.xml();
      if (!OU::findAssign(params, "model", inst.m_name.c_str(), m_model) &&
	  !OU::findAssign(params, "model", inst.m_specName.c_str(), m_model))
	OE::getOptionalString(x, m_model, "model");
      if (!OU::findAssign(params, "platform", inst.m_name.c_str(), m_platform) &&
	  !OU::findAssign(params, "platform", inst.m_specName.c_str(), m_platform))
	OE::getOptionalString(x, m_platform, "platform");
      const char *scale;
      if (!OU::findAssign(params, "scale", inst.m_name.c_str(), scale) &&
	  !OU::findAssign(params, "scale", inst.m_specName.c_str(), scale))
	scale = ezxml_cattr(inst.xml(), "scale");
      m_tempInstance->m_scale = 1;
      if (scale && OE::getUNum(scale, &m_tempInstance->m_scale))
	throw OU::Error("Invalid scale factor: \"%s\"", scale);
      if (!Manager::findImplementations(*this, inst.m_specName.c_str()))
	throw OU::Error("No acceptable implementations found in any libraries "
			"for \"%s\".  Use log level 8 for more detail.",
			inst.m_specName.c_str());
      if (m_tempInstance->m_candidates.size() > m_maxCandidates)
	m_maxCandidates = (unsigned)m_tempInstance->m_candidates.size();
    }
    // A common method used by constructors
    void Assembly::findImplementations(const OU::PValue *params) {
      const char *err;
      if ((err = checkInstanceParams("model", params, false, true)) ||
	  (err = checkInstanceParams("platform", params, false, true)))
	throw OU::Error("%s", err);
      m_params = params; // for access by callback
      m_maxCandidates = 0;
      const char *deployment = NULL;
      m_deployed = OU::findString(params, "deployment", deployment);
      // Pass 1:  Initialize our instances list from the Util assy, but we might add to it later
      // for slaves or file I/O instances.  Find candidates implementations.
      for (unsigned n = 0; n < nUtilInstances(); n++)
	addInstance(params);
      // Pass 2:  Deal with connectivity in the core assembly.
      // final connectivity and prune candidates unacceptable due to connectivity issues
      ocpiInfo("================================================================================");
      ocpiInfo("Checking connectivity of candidates for each instance");
      for (unsigned n = 0; n < nUtilInstances(); n++) {
	Instance &i = *m_instances[n];
	ocpiInfo("================================================================================");
	ocpiInfo("Checking connectivity for instance %2u: \"%s\"", n, utilInstance(n).cname());
	for (CandidatesIter ci = i.m_candidates.begin(); ci != i.m_candidates.end(); )
	  if (i.checkConnectivity(*ci, *this))
	    ++ci;
	  else
	    ci = i.m_candidates.erase(ci);
      }
      // Pass 3:  Add instances due to file I/O or implied slaves
      // We now know all the implementation information about what is in the assembly, so now
      // add file I/O instances if requested, which might add instances and connections
      size_t nCore = nUtilInstances();
      if ((err = addFileIoInstances(params)))
	throw OU::Error("Error when adding file I/O components: %s", err);
      // Pass 4:  Recheck final connectivity
      for (size_t n = nCore; n < nUtilInstances(); n++) {
	Instance &i = *m_instances[n];
	for (CandidatesIter ci = i.m_candidates.begin(); ci != i.m_candidates.end(); )
	  if (i.checkConnectivity(*ci, *this))
	    ++ci;
	  else
	    ci = i.m_candidates.erase(ci);
      }
      for (unsigned n = 0; n < nUtilInstances(); n++) {
	Instance &i = *m_instances[n];
	if (i.m_candidates.empty())
	  throw OU::Error("No viable candidates found for instance \"%s\"",
			  i.m_utilInstance.cname());
      }
      if (m_deployed) // we don't have candidates here.  deployments are pre-checked.
	return;
      // Pass 5:  Check for interface and connection compatibility.
      // We assume all implementations have the same protocol metadata
      //      unsigned nConns = m_connections.size();
      for (auto ci = m_connections.begin(); ci != m_connections.end(); ci++) {
	const OU::Assembly::Connection &c = **ci;
	if (c.m_ports.size() == 2) {
	  const OU::Worker // implementations on both sides of the connection
	    &i0 = m_instances[c.m_ports.front().m_instance]->m_candidates[0].impl->m_metadataImpl,
	    &i1 = m_instances[c.m_ports.back().m_instance]->m_candidates[0].impl->m_metadataImpl;
	  OU::Port // ports on both sides of the connection
	    *ap0 = i0.findMetaPort(c.m_ports.front().m_name),
	    *ap1 = i1.findMetaPort(c.m_ports.back().m_name);
	  if (!ap0 || !ap1)
	    throw OU::Error("Port name (\"%s\") in connection does not match any port in implementation",
			    (ap0 ? c.m_ports.back() : c.m_ports.front()).m_name.c_str());
	  if (ap0->m_provider == ap1->m_provider)
	    throw OU::Error("Port roles in connection are incompatible: "
			    "port \"%s\" of instance \"%s\" has m_provider=\"%s\" vs. "
			    "port \"%s\" of instance \"%s\" has m_provider=\"%s\"",
			    ap0->m_name.c_str(),
			    utilInstance(c.m_ports.front().m_instance).m_name.c_str(),
			    (ap0->m_provider ? "true" : "false"),
			    ap1->m_name.c_str(),
			    utilInstance(c.m_ports.back().m_instance).m_name.c_str(),
			    (ap1->m_provider ? "true" : "false"));
	  // Protocol on both sides of the connection
	  OU::Protocol &p0 = *ap0, &p1 = *ap1;
	  if (p0.m_name.size() && p1.m_name.size() && p0.m_name != p1.m_name)
	    throw OU::Error("Protocols in connection are incompatible: "
			    "port \"%s\" of instance \"%s\" has protocol \"%s\" vs. "
			    "port \"%s\" of instance \"%s\" has protocol \"%s\"",
			    ap0->m_name.c_str(),
			    utilInstance(c.m_ports.front().m_instance).m_name.c_str(),
			    p0.m_name.c_str(),
			    ap1->m_name.c_str(),
			    utilInstance(c.m_ports.back().m_instance).m_name.c_str(),
			    p1.m_name.c_str());

	  // FIXME:  more robust naming, namespacing, UUIDs, hash etc.

	}
      }
    }
    // A port is connected in the assembly, and the port it is connected to is on an instance
    // with an already chosen implementation. Now we can check whether this impl conflicts with
    // that one or not
    bool Assembly::
    badConnection(const Implementation &thisImpl, const OCPI::Util::Port &thisPort,
		  const Implementation &otherImpl, const OCPI::Util::Port &otherPort) {
      if (thisImpl.m_internals & (1u << thisPort.m_ordinal)) {
	if (!(otherImpl.m_internals & (1u << otherPort.m_ordinal)) ||
	    otherImpl.m_connections[otherPort.m_ordinal].impl != &thisImpl ||
	    otherImpl.m_connections[otherPort.m_ordinal].port != &thisPort) {
	  ocpiInfo("    This port \"%s\" of worker \"%s\" is preconnected and the other port is not "
		   "preconnected to us: we're incompatible", thisPort.cname(), thisPort.metaWorker().cname());
	  ocpiInfo("      Other port %u \"%s\" of worker \"%s\"  m_internals %x, other internals %x",
		   otherPort.m_ordinal, otherPort.cname(), otherPort.metaWorker().cname(),
		   thisImpl.m_internals, otherImpl.m_internals);
	  return true;
	}
      } else if (otherImpl.m_internals & (1u << otherPort.m_ordinal)) {
	ocpiInfo("    Port \"%s\" of \"%s\" is external; the other port is connected: we're incompatible",
		 thisPort.cname(), thisImpl.m_metadataImpl.cname());
	ocpiInfo("      other %u \"%s\"  m_internals %x, other internals %x", otherPort.m_ordinal,
		 otherPort.cname(), thisImpl.m_internals, otherImpl.m_internals);
	ocpiInfo("      me port ordinal %u port \"%s\"", thisPort.m_ordinal, thisPort.cname());
	return true;
      }
      return false;
    }
    Assembly::Instance::
    Instance(OU::Assembly::Instance &utilInstance, Instance *master)
      : m_utilInstance(utilInstance), m_assyPorts(NULL), m_nPorts(0), m_master(master) {
      // m_assyPorts will be initialized based on first impl found
    }
    Assembly::Instance::
    ~Instance()  {
      delete [] m_assyPorts;
    }
  }
}
