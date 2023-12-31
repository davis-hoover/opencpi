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

#include <assert.h>
#include <unordered_set>
#include "assembly.h"
// Generic (actually non-HDL) assembly support
// This isn't as purely generic as it should be  FIXME

Assembly::
Assembly(Worker &w)
  : m_assyWorker(w), m_nWCIs(0), m_utilAssembly(NULL), m_language(w.m_language), m_nWti(0),
    m_nWmemi(0) {
}

Assembly::
~Assembly() {
}

void Worker::
deleteAssy() {
  delete m_assembly;
}

InstanceProperty::
InstanceProperty() : property(NULL) {
}

// Find the OM::Assembly::Instance's port in the instance's worker
const char *Assembly::
findPort(OM::Assembly::Port &ap, InstancePort *&found) {
  Instance &i = m_instances[ap.m_instance];
  found = NULL;
  unsigned nn = 0;
  for (PortsIter pi = i.m_worker->m_ports.begin(); pi != i.m_worker->m_ports.end(); pi++, nn++) {
    Port &p = **pi;
    if (ap.m_name.empty()) {
	// Unknown ports can be found for data ports that have matching known roles
      if (ap.m_role.m_knownRole && p.matchesDataProducer(!ap.m_role.m_provider)) {
	if (found)
	  return OU::esprintf("Ambiguous connection to unnamed %s port on %s:%s",
			      ap.m_role.m_provider ? "input" : "output", i.m_wName.c_str(), i.cname());
	else
	  found = &i.m_ports[nn];
      }
    } else if (!strcasecmp(p.pname(), ap.m_name.c_str()))
      found = &i.m_ports[nn];;
  }
  if (!found)
    return OU::esprintf("Port '%s' not found for instance '%s' of worker '%s'",
			ap.m_name.c_str(), i.cname(), i.m_wName.c_str());
  return NULL;
}

static const char *roleName(OM::Assembly::Role &r) { return r.isProducer() ? "producer" : "consumer"; }
// A key challenge here is that we may not know the width of the connection until we look at
// real ports
const char *Assembly::
parseConnection(OM::Assembly::Connection &aConn) {
  const char *err;
  Connection &c = *new Connection(&aConn);
  m_connections.push_back(&c);
  //  findBool(aConn.m_parameters, "signal", c.m_isSignal);
  // In case the connection has no count, we default it to the
  // width of the narrowest attached port
  InstancePort *found;
  size_t minCount = 1000;
  for (auto api = aConn.m_ports.begin(); api != aConn.m_ports.end(); api++) {
    OM::Assembly::Port &ap = *(*api).first;
    if ((err = findPort(ap, found)))
      return err;
    if ((*api).second + (c.m_count ? c.m_count : 1) > found->m_port->count())
      return OU::esprintf("invalid index/count (%zu/%zu) for connection %s, port %s of "
			  "instance %s has count %zu",
			  (*api).second, c.m_count ? c.m_count : 1, c.m_name.c_str(),
			  ap.m_name.empty() ? "<unknown>" : ap.m_name.c_str(),
			  m_instances[ap.m_instance].m_worker->cname(),
			  found->m_port->count());
    size_t count = found->m_port->count() - (*api).second;
    if (count < minCount)
      minCount = count;
  }
  if (!c.m_count)
    c.m_count = minCount;
  for (auto api = aConn.m_ports.begin(); api != aConn.m_ports.end(); api++) {
    OM::Assembly::Port &ap = *(*api).first;
    if ((err = findPort(ap, found)) ||
	(err = found->m_port->fixDataConnectionRole(ap.m_role)))
      return err;
    if (!found->m_role.m_knownRole || found->m_role.m_bidirectional)
      found->m_role = ap.m_role;
    // Note that the count may not be known here yet
    if ((err = c.attachPort(*found, (*api).second))) //, aConn.m_count)))
      return err;
    assert(c.m_count != 0);
  }
  if (aConn.m_externals.size() > 1)
    return "multiple external attachments on a connection unsupported";
  // Create instance ports (and underlying ports of this assembly worker).
  for (auto ei = aConn.m_externals.begin(); ei != aConn.m_externals.end(); ei++) {
    OM::Assembly::External &ext = *ei->first;
    assert(aConn.m_ports.size() == 1);
    OM::Assembly::Port &ap = *aConn.m_ports.front().first;
    assert(ap.m_role.m_knownRole);
    // Inherit the role of the first internal connection
    if (!ext.m_role.m_knownRole)
      ext.m_role = ap.m_role;
    else if (ext.m_role.isProducer() != ap.m_role.isProducer())
      return OU::esprintf("External port \"%s\" has inconsistent role (%s) vs. connected internal "
			  "port \"%s\" with role %s",
			  ext.m_name.c_str(),roleName(ext.m_role),ap.cname(), roleName(ap.m_role));
    assert(c.m_attachments.size() == 1);
    InstancePort &intPort = c.m_attachments.front()->m_instPort; // intPort corresponds to ap
    assert(intPort.m_port);
    // Connect ei->second + count on the external side, to ap.m_index + count on tne port side
    if (ei->second + aConn.m_count > ext.m_count)
      return OU::esprintf("External port '%s' can't connect to index/count %zu/%zu "
			  "when the count of the external port itself is %zu",
			  ext.cname(), ei->second, aConn.m_count, ext.m_count);
    size_t index = aConn.m_ports.front().second;
    if (index + aConn.m_count > intPort.m_port->count())
      return OU::esprintf("Connection to external port '%s' can't connect to index/count %zu/%zu "
			  "of internal port \"%s\" when the count of the internal port itself is %zu",
			  ext.cname(), index, aConn.m_count, ap.cname(), intPort.m_port->count());
    Port *p = m_assyWorker.findPort(ext.m_name.c_str());
    if (m_assyWorker.m_type == Worker::Application) { // a proxy
      // We are dealing with a connection that implies a delegation, so the assembly worker port
      // already exists.
      if (!p)
	return OU::esprintf("External connection in slave assembly for worker %s specifies port %s"
			    " which does not exist", m_assyWorker.cname(), ext.m_name.c_str());
      if (p->m_arrayCount != ext.m_count)
	return OU::esprintf("External port \"%s\" in slave assembly for worker %s specifies count "
			    "%zu, while proxy port has count %zu", ext.m_name.c_str(),
			    m_assyWorker.cname(), ext.m_count, p->m_arrayCount);

    } else if (!p) {
      // Create the external port of this assembly
      // Start with a copy of the port, then patch it
      ocpiDebug("Clone of port %s of instance %s of worker %s for assembly worker %s: %s/%zu/%zu",
		intPort.m_port->pname(), intPort.m_instance->cname(),
		intPort.m_port->worker().m_implName, m_assyWorker.m_implName,
		intPort.m_port->m_countExpr.c_str(), intPort.m_port->m_arrayCount,
		ext.m_count ? ext.m_count : c.m_count);
      assert(ext.m_count <= intPort.m_port->count());
      // The external port inherits the array-ness of the internal port if there is no "count".
      p = &intPort.m_port->clone(m_assyWorker, ext.m_name,
				 ext.m_count ? ext.m_count : intPort.m_port->m_arrayCount,
				 &ext.m_role, err);
      if (err)
	return OU::esprintf("External connection %s for port %s of instance %s error: %s",
			    c.m_name.c_str(), intPort.m_port->pname(), intPort.m_instance->cname(),
			    err);
    }
    InstancePort *ip = new InstancePort(NULL, p, &ext);
    if ((err = c.attachPort(*ip, ei->second)))
      return err;
  }
  return NULL;
}

Instance::
Instance()
  : m_worker(NULL), m_clocks(NULL), m_iType(Application), m_attach(NULL), m_hasConfig(false),
    m_config(0), m_emulated(false), m_inserted(false) {
}

// When evaluating an expression for an instance's property value, allow use of assembly-provided values
// when indicated by a leading $.
const char *Instance::
getValue(const char *sym, OB::ExprValue &val) const {
  if (*sym == '$')
    return m_assy->m_assyWorker.getValue(++sym, val);
  const InstanceProperty *ipv = &m_properties[0];
  for (unsigned n = 0; n < m_properties.size(); n++, ipv++)
    if (!strcasecmp(ipv->property->cname(), sym))
      return extractExprValue(*ipv->property, ipv->value, val);
  return m_worker->getValue(sym, val);
}

// Add the assembly's parameters to the instance's parameters when that is appropriate.
// Note this must be done BEFORE actual workers and paramconfigs are selected.
// Thus we are not in a position to see whether the worker actually supports this
// parameter - we assume for now that these are builtin params that all workers support.
// For each parameter property of the assembly:
// Find the value in the assy worker's paramconfig.

const char *Assembly::
addAssemblyParameters(OM::Assembly::Properties &aiprops) {
  if (m_assyWorker.m_model == RccModel)
    return NULL; // proxy assemblies cannot have parameters at this point
  for (PropertiesIter api = m_assyWorker.m_ctl.properties.begin();
       api != m_assyWorker.m_ctl.properties.end(); api++)
    if ((*api)->m_isParameter) {
      const OM::Property &ap = **api;
      assert(m_assyWorker.m_paramConfig);
      Param *p = &m_assyWorker.m_paramConfig->params[0];
      for (unsigned nn = 0; nn < m_assyWorker.m_paramConfig->params.size(); nn++, p++)
	if (&ap == p->m_param && !p->m_isDefault) {
	  // We have a non-default-value parameter value in this assy wkr's configuration
	  OM::Assembly::Property *aip = &aiprops[0];
	  size_t n;
	  for (n = aiprops.size(); n; n--, aip++)
	    if (!strcasecmp(ap.m_name.c_str(), aip->m_name.c_str()))
	      break;
	  if (n == 0) {
	    // There is no explicit value of the parameter for the instance
	    // So add a parameter value for the instance, xml-style
	    // FIXME: use emplace_back from c++ with a proper constructor!
	    aiprops.resize(aiprops.size() + 1);
	    aip = &aiprops.back();
	    aip->m_name = ap.m_name;
	    aip->m_hasValue = true;
	    aip->m_value = p->m_uValue;
	  }
	}
    }
  return NULL;
}

// Add parameter values from the list of values that came from the instance XML,
// possibly augmented by values from the assembly.  This happens AFTER we know
// about the worker, so we can do error checking and value parsing
const char *Instance::
addParameters(const OM::Assembly::Properties &aiprops, InstanceProperty *&ipv) {
  Worker &w = *m_worker;
  const char *err;
  const OM::Assembly::Property *ap = &aiprops[0];
  for (size_t n = aiprops.size(); n; n--, ap++) {
    const OM::Property *p = w.findProperty(ap->m_name.c_str());
    if (!p)
      return OU::esprintf("property '%s' is not a property of worker '%s'", ap->m_name.c_str(),
			  w.m_implName);
    // If the assembly is for an application worker, we are parsing a slave assembly
    if (!p->m_isParameter && m_assy->m_assyWorker.m_type != Worker::Application)
      return OU::esprintf("property '%s' is not a parameter property of worker '%s'",
			  ap->m_name.c_str(), w.m_implName);
    // set up the ipv and parse the value
    ipv->property = p;
    ipv->value.setType(*p); // in case we are reusing it
    if ((err = ipv->property->parseValue(ap->m_value.c_str(), ipv->value, NULL, this)))
      return err;
    if (p->m_default) {
      std::string defValue, newValue;
      p->m_default->unparse(defValue);
      ipv->value.unparse(newValue);
      if (defValue == newValue)
	continue;
    }
    ipv++;
  }
  return NULL;
}
void Assembly::
addParamConfigParameters(const ParamConfig &pc, const OM::Assembly::Properties &aiprops,
			 InstanceProperty *&ipv) {
  const Param *p = &pc.params[0];
  // For each parameter in the config
  for (unsigned nn = 0; nn < pc.params.size(); nn++, p++) {
    if (!p->m_param) // an orphaned parameter if the number of them grew..
      continue;
    const OM::Assembly::Property *ap = &aiprops[0];
    size_t n;
    for (n = aiprops.size(); n; n--, ap++)
      if (!strcasecmp(ap->m_name.c_str(), p->m_param->m_name.c_str()))
	break;
    if (n == 0) {
      // a setting in the param config is not mentioned explicitly
      ipv->property = p->m_param;
      ipv->value = p->m_value;
      ipv++;
    }
  }
}

const char *Instance::
init(::Assembly &assy, const char *iName, const char *wName, ezxml_t ix,
     OM::Assembly::Properties &xmlProperties) {
  m_assy = &assy;
  //  m_instance = ai;
  m_xml = ix;
  m_name = iName;
  m_wName = wName ? wName : "";
  // Find the real worker/impl for each instance, sharing the Worker among instances
  Worker *w = NULL;
  if (m_wName.empty())
    return OU::esprintf("instance %s has no worker", cname());
  for (Instance *ii = &assy.m_instances[0]; ii < this; ii++)
    if (!strcmp(m_wName.c_str(), ii->m_wName.c_str()))
      w = ii->m_worker;
  // There are two instance attributes that we use when considering workers
  // in our worker assembly:
  // 1.  Whether the instance is reentrant, which means one "instance" here can actually
  //     be dynamically used simultaneously for multiple application instances.
  //     This implies there will be no hard connections to its ports.
  // 2.  Which configuration of parameters it is built with.
  // FIXME: better modularity would be a core worker, a parameterized worker, etc.
  size_t paramConfig; // zero is with default parameter values
  bool hasConfig;
  const char *err;
  if ((err = OE::getNumber(m_xml, "paramConfig", &paramConfig, &hasConfig, 0)))
    return err;
  // We consider the property values in two places.
  // Here we are saying that a worker can't be shared if it has explicit properties,
  // or if it specifically has a non-default parameter configuration.
  // So we create a new worker and hand it the properties, so that it can
  // actually use these values DURING PARSING since some aspects of parsing
  // need them.  But later below, we really parse the properties after we
  // know the actual properties and their types from the worker.
  // FIXME: we are assuming that properties here must be parameters?
  // FIXME: we basically are forcing replication of workers...

  // Initialize this instance's explicit xml property/parameter values from the assembly XML.
  m_xmlProperties = xmlProperties;
  // Add any assembly-level parameters that also need to be applied to the instance
  // and used during worker and paramconfig selection
  if (assy.m_assyWorker.m_paramConfig && (err = assy.addAssemblyParameters(m_xmlProperties)))
    return err;
  if (!w || m_xmlProperties.size() || paramConfig) {
    if (!(w = Worker::create(m_wName.c_str(), assy.m_assyWorker.m_file, NULL,
			     assy.m_assyWorker.m_outDir, &assy.m_assyWorker,
			     hasConfig ? NULL : &m_xmlProperties, paramConfig, err)))
      return OU::esprintf("for worker %s: %s", m_wName.c_str(), err);
    assy.m_workers.push_back(w); // preserve order
  }
  m_worker = w;
  // Determine instance type as far as we can now
  switch (w->m_type) {
  case Worker::Application:   m_iType = Instance::Application; break;
  case Worker::Platform:      m_iType = Instance::Platform; break;
  case Worker::Device:        m_iType = Instance::Device; break;
  case Worker::Configuration: m_iType = Instance::Configuration; break;
  case Worker::Assembly:      m_iType = Instance::Assembly; break;
  default:;
    assert("Invalid worker type as instance" == 0);
  }
  // Parse property values now that we know the actual workers.
  m_properties.resize(w->m_ctl.properties.size());
  InstanceProperty *ipv = &m_properties[0];
  // Even though we used the ipv's to select a worker and paramconfig,
  // we queue them up here to actually apply to the instance in the generated code.
  // Someday this will force top-down building
  if ((err = addParameters(xmlProperties, ipv)))
    return err;
  if (w->m_paramConfig)
    assy.addParamConfigParameters(*w->m_paramConfig, xmlProperties, ipv);
  m_properties.resize(OCPI_SIZE_T_DIFF(ipv, &m_properties[0]));
  // Initialize the instance ports
  m_ports.resize(m_worker->m_ports.size());
  InstancePort *ip = &m_ports[0];
  for (unsigned nn = 0; nn < m_worker->m_ports.size(); nn++, ip++)
    ip->init(this, m_worker->m_ports[nn], NULL);
  // Allocate the instance-clock-to-assembly-clock map. Should be in HDL somewhere, but it needs
  // to happen earier...
  if (m_worker->m_clocks.size()) {
    m_clocks = new Clock*[m_worker->m_clocks.size()];
    for (unsigned nn = 0; nn < m_worker->m_clocks.size(); nn++)
      m_clocks[nn] = NULL;
  }
  // Parse type-specific aspects of the instance.
  return w->parseInstance(assy.m_assyWorker, *this, m_xml);
}
// This parses the assembly using the generic assembly parser in OU::
// It then does the binding to actual implementations.
const char *Assembly::
parseAssy(ezxml_t xml, const char **topAttrs, const char **instAttrs) {
  try {
    m_utilAssembly = new OM::Assembly(xml, m_assyWorker.m_implName, true, topAttrs, instAttrs);
  } catch (std::string &e) {
    return OU::esprintf("%s", e.c_str());
  }
  const char *err;

  // Reserve for instances to include enough space to add an adapter for each connection
  m_instances.reserve(m_utilAssembly->nUtilInstances() + m_utilAssembly->m_connections.size());
  // Set the size for just the instances, before adapters
  m_instances.resize(m_utilAssembly->nUtilInstances());
  Instance *i = &m_instances[0];
  // Initialize our instances based on the generic assembly instances
  for (unsigned n = 0; n < m_utilAssembly->nUtilInstances(); n++, i++) {
    OM::Assembly::Instance &ai = m_utilAssembly->instance(n);
    if ((err =
	 i->init(*this, ai.m_name.c_str(), ai.m_implName.c_str(), ai.xml(), ai.m_properties)))
      return err;
    // If the instance in the OM::Assembly has "m_externals=true",
    // and this instance port has no connections in the OM::Assembly
    // then we add an external connection for the instance port. Prior to this,
    // we didn't have access to the worker metadata to know what all the ports are.
    if (ai.m_externals) {
      InstancePort *ip = &i->m_ports[0];
      for (unsigned nn = 0; nn < i->m_worker->m_ports.size(); nn++, ip++) {
	if (ip->m_port->isData()) {
	  Port *p = NULL;
	  for (auto pi = ai.m_ports.begin(); pi != ai.m_ports.end(); pi++)
	    if ((*pi).m_name.empty()) {
	      // Port name empty means we don't know it yet.
	      InstancePort *found;
	      // Ignore errors here
	      if (!findPort(*pi, found))
		if (ip == found)
		  p = ip->m_port;
	    } else if (!strcasecmp((*pi).m_name.c_str(), ip->m_port->pname())) {
	      p = ip->m_port;
	      break;
	    }
	  if (!p)
	    ip->m_externalize = true;
	  //	  if (!p && (err = externalizePort(*ip, ip->m_port->pname(), NULL)))
	  //	    return err;
	  //	assy.m_utilAssembly->addExternalConnection(ai->m_ordinal, ip->m_port->pname());
	}
      }
    }
  }
  // All parsing is done.
  // Now we fill in the top-level worker stuff.
  if (m_assyWorker.m_type != Worker::Application) {
    ocpiCheck(asprintf((char**)&m_assyWorker.m_specName, "local.%s", m_assyWorker.m_implName) > 0);
    // Properties:  we only set the canonical hasDebugLogic property, which is a parameter.
    if ((err = m_assyWorker.doProperties(xml, m_assyWorker.m_file.c_str(), true, false, NULL, false)))
      return err;
  }
  // Parse the Connections, creating external ports for this assembly worker as needed.
  for (auto ci = m_utilAssembly->m_connections.begin();
       ci != m_utilAssembly->m_connections.end(); ++ci)
    if ((err = parseConnection(**ci)))
      return err;
  // Check for unconnected non-optional data ports
  i = &m_instances[0];
  if (m_assyWorker.m_type != Worker::Application) // if not a slave assembly
    for (unsigned n = 0; n < m_instances.size(); n++, i++)
      if (i->m_worker && !i->m_worker->m_reusable) {
	InstancePort *ip = &i->m_ports[0];
	for (unsigned nn = 0; nn < i->m_worker->m_ports.size(); nn++, ip++) {
	  Port *pp = ip->m_port;
	  if (ip->m_attachments.empty() && pp->isData() && !pp->isOptional() && !ip->m_externalize)
	    return OU::esprintf("Port %s of instance %s of worker %s"
				" is not connected and not optional",
				pp->pname(), i->cname(), i->m_worker->m_implName);
      }
    }
  return 0;
}

// Make this port an external port
// Not called for WCIs that are aggreated...
// Note that this is called for ports that are IMPLICITLY made external,
// rather than those that are explicitly connected as eternal
const char *Assembly::
externalizePort(InstancePort &ip, const char *name, size_t *ordinal) {
  Port &p = *ip.m_port;
  std::string extName = name;
  if (ordinal)
    OU::formatAdd(extName, "%zu", (*ordinal)++);
  Connection &c = *new Connection(NULL, extName.c_str());
  c.m_count = p.count();
  m_connections.push_back(&c);
  const char *err;
  ocpiDebug("Clone of port %s of instance %s of worker %s for assembly worker %s: %s/%zu",
	    ip.m_port->pname(), ip.m_instance->cname(),
	    ip.m_port->worker().m_implName, m_assyWorker.m_implName,
	    ip.m_port->m_countExpr.c_str(), ip.m_port->m_arrayCount);
  Port &extPort = p.clone(m_assyWorker, extName, p.m_arrayCount, NULL, err);
  if (err)
    return err;
  OM::Assembly::External *ext = new OM::Assembly::External(extPort.m_name.c_str());
  ext->m_role.m_provider = !p.m_master; // provisional
  ext->m_role.m_bidirectional = false;
  ext->m_role.m_knownRole = true;
  InstancePort &extIp = *new InstancePort(NULL, &extPort, ext);
  if ((err = c.attachPort(ip, 0)) ||
      (err = c.attachPort(extIp, 0)))
    return err;
  return NULL;
}

InstancePort *Assembly::
findInstancePort(const char *name) {
  // First, find the external
  for (ConnectionsIter cci = m_connections.begin(); cci != m_connections.end(); cci++) {
    Connection &cc = **cci;
    if (cc.m_external && !strcasecmp(cc.m_external->m_instPort.m_port->pname(), name))
      // We found the external port, now find the internal connected port
      for (AttachmentsIter ai = cc.m_attachments.begin(); ai != cc.m_attachments.end(); ai++)
	if (cc.m_external != *ai)
	  return &(*ai)->m_instPort;
  }
  return NULL;
}

void Worker::
emitXmlInstances(FILE *) {
}

void Worker::
emitXmlConnections(FILE *) {
}

void Worker::
emitXmlWorker(std::string &out, bool verbose) {
  OU::formatAdd(out, "  <worker name=\"%s", m_implName);
  // FIXME - share this param-named implname with emitInstance
  if (m_paramConfig && m_paramConfig->nConfig)
    OU::formatAdd(out, "-%zu", m_paramConfig->nConfig);
  OU::formatAdd(out, "\" model=\"%s\"", m_modelString);
  OU::formatAdd(out, " package=\"%s\"", m_package.c_str());
  if (m_specName && strcasecmp(m_specName, m_implName))
    OU::formatAdd(out, " specname=\"%s\"", m_specName);
  if (m_ctl.sizeOfConfigSpace)
    OU::formatAdd(out, " sizeOfConfigSpace=\"%llu\"", (unsigned long long)m_ctl.sizeOfConfigSpace);
  if (m_ctl.controlOps) {
    bool first = true;
    for (unsigned op = 0; op < OM::Worker::OpsLimit; op++)
      if (m_ctl.controlOps & (1u << op)) {
	OU::formatAdd(out, "%s%s", first ? " controlOperations=\"" : ",",
		OM::Worker::s_controlOpNames[op]);
	first = false;
      }
    if (!first)
      out += "\"";
  }
  if (m_wci && m_wci->timeout())
    OU::formatAdd(out, " Timeout=\"%zu\"", m_wci->timeout());
  if (m_ctl.firstRaw)
    OU::formatAdd(out, " FirstRaw='%u'", m_ctl.firstRaw->m_ordinal);
  if (m_scalable)
    out += " Scalable='1'";
  if (m_requiredWorkGroupSize)
    OU::formatAdd(out, " requiredWorkGroupSize='%zu'", m_requiredWorkGroupSize);
  if (m_version) // keep old distinction between zero and 1 even though they are really the same
    OU::formatAdd(out, " version='%u'", m_version);
  if (m_workerEOF)
    out += " workerEOF='1'";
  if (m_emulate)
    out += " emulator='1'";
  out += ">\n";
  if (m_scalable) {
    OM::Port::Scaling s;
    if (!(s == m_scaling)) {
      std::string l_out;
      m_scaling.emit(out, NULL);
      OU::formatAdd(out, "  <scaling %s/>\n", l_out.c_str());
    }
  }
  // emit slaves when they are specified as an assembly
  if (m_paramConfig && m_paramConfig->m_slaves.size() && m_paramConfig->m_slavesAssembly) {
    ::Assembly &assy = *m_paramConfig->m_slavesAssembly;
    // Output the assembly again, but canonical, and without parameters.
    out += "    <slaves>\n";
    Instance *i = &assy.m_instances[0];
    for (unsigned n = 0; n < assy.m_instances.size(); ++i, ++n) {
      const char *dot = strrchr(i->m_wName.c_str(), '.');
      assert(dot);
      OU::formatAdd(out, "      <instance name='%s' component='%s' worker='%.*s",
		    i->cname(), i->m_worker->m_specName, (int)(dot - i->m_wName.c_str()),
		    i->m_wName.c_str());
      assert(i->m_worker->m_paramConfig);
      if (i->m_worker->m_paramConfig->nConfig)
	OU::formatAdd(out, "-%zu", i->m_worker->m_paramConfig->nConfig);
      out += dot;
      out += '\'';
      bool any = false;
      for (auto it = i->m_xmlProperties.begin(); it != i->m_xmlProperties.end(); ++it) {
	const OM::Property *p = i->m_worker->findProperty(it->m_name.c_str());
	assert(p);
	if (!p->m_isParameter) {
	  if (!any)
	    out += ">\n";
	  any = true;
	  OU::formatAdd(out, "        <property name='%s' value='%s'/>\n",
			p->cname(), it->m_value.c_str());
	}
      }
      out += any ? "      </instance>\n" : "/>\n";
    }
    auto &ua = *assy.m_utilAssembly;
    // predefine external ports that have counts
    for (auto it = ua.externals().begin(); it != ua.externals().end(); ++it)
      if (it->second.m_count)
	OU::formatAdd(out, "      <external name='%s' count='%zu'/>\n",
		      it->second.cname(), it->second.m_count);
    for (auto it = assy.m_connections.begin(); it != assy.m_connections.end(); ++it) {
      out += "      <connection";
      if ((*it)->m_count > 1)
	OU::formatAdd(out, " count='%zu'", (*it)->m_count);
      out += ">\n";
      for (auto ait = (*it)->m_attachments.begin(); ait != (*it)->m_attachments.end(); ++ait) {
	auto &at = **ait;
	if (at.m_instPort.m_external)
	  OU::formatAdd(out, "        <external name='%s'", at.m_instPort.m_external->cname());
	else
	  OU::formatAdd(out, "        <port name='%s' instance='%s'",
			at.m_instPort.m_port->pname(), at.m_instPort.m_instance->cname());
	if (at.m_index || at.m_instPort.m_port->m_arrayCount)
	  OU::formatAdd(out, " index='%zu'", (*ait)->m_index);
	out += "/>\n";
      }
      out += "      </connection>\n";
    }
    out += "    </slaves>\n";
  }
  for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++) {
    OM::Property *prop = *pi;
    prop->printAttrs(out, "property", 2, prop->m_isParameter); // suppress default values for parameters
    if (prop->m_isImpl)
      out += " isImpl='1'";
    else if (verbose){
      if (prop->m_specInitial)
        out += " specinitial='1'";
      if (prop->m_specReadable)
        out += " specreadable='1'";
      if (prop->m_specParameter)
        out += " specparameter='1'";
      if (prop->m_specWritable)
        out += " specwritable='1'";
      if (prop->m_isVolatile)  // if volitile is set it has to be done in the spec
        out += " specvolitile='1'";
    }
    if (prop->m_isDebug)
      out += " debug='1'";
    if (prop->m_isHidden)
      out += " hidden='1'";
    if (prop->m_isVolatile)
      out += " volatile='1'";
    else if (prop->m_isReadback)
      out += " readback='1'";
    if (prop->m_isInitial)
      out += " initial='1'";
    else if (prop->m_isWritable)
      out += " writable='1'";
    if (prop->m_readSync)
      out += " readSync='1'";
    if (prop->m_writeSync)
      out += " writeSync='1'";
    if (prop->m_readError)
      out += " readError='1'";
    if (prop->m_writeError)
      out += " writeError='1'";
    if (prop->m_isRaw)
      out += " raw='1'";
    if (!prop->m_isReadable && !prop->m_isWritable && !prop->m_isParameter)
      assert(prop->m_isPadding);
    if (prop->m_isPadding)
      out += " padding='1'";
    if (prop->m_isIndirect)
      OU::formatAdd(out, " indirect=\"%zu\"", prop->m_indirectAddr);
    if (prop->m_isParameter) {
      out += " parameter='1'";
      OB::Value *v =
	m_paramConfig && prop->m_paramOrdinal < m_paramConfig->params.size() &&
	!m_paramConfig->params[prop->m_paramOrdinal].m_isDefault ?
	&m_paramConfig->params[prop->m_paramOrdinal].m_value : prop->m_default;
      if (v) {
	std::string value;
	v->unparse(value);
	// FIXME: this code is in three places..
	out += " default='";
	std::string xml;
	OU::encodeXmlAttrSingle(value, xml);
	out += xml;
	out += "'";
      }
    }
    prop->printChildren(out, "property", 2);
  }
  unsigned nn;
  for (nn = 0; nn < m_ports.size(); nn++)
    m_ports[nn]->emitXML(out);
  for (nn = 0; nn < m_localMemories.size(); nn++) {
    LocalMemory* m = m_localMemories[nn];
    OU::formatAdd(out, "    <localMemory name=\"%s\" size=\"%zu\"/>\n", m->name, m->sizeOfLocalMemory);
  }
  out += "  </worker>\n";
}

void Worker::
emitXmlWorkers(FILE *f) {
  assert(m_assembly);
  // Define all workers
  std::unordered_set<std::string> workers;
  for (WorkersIter wi = m_assembly->m_workers.begin(); wi != m_assembly->m_workers.end(); wi++)
    if (!(*wi)->m_assembly || (*wi)->m_paramConfig->m_slaves.size()) {
      std::string out;
      (*wi)->emitXmlWorker(out);
      if (workers.insert(out).second)
	fputs(out.c_str(), f);
    }
}

InstancePort::
InstancePort()
{
  init(NULL, NULL, NULL);
}
InstancePort::
InstancePort(Instance *i, Port *p, OM::Assembly::External *ext) {
  init(i, p, ext);
}

void InstancePort::
init(Instance *i, Port *p, OM::Assembly::External *ext) {
  m_instance = i;
  m_port = p;
  m_connected.assign(p ? p->count() : 1, false);
  if (p)
    p->initRole(m_role);
  // If the external port tells us the direction and we're bidirectional, capture it.
  m_external = ext;
  if (ext && ext->m_role.m_knownRole && !ext->m_role.m_bidirectional)
    m_role = ext->m_role;
  m_hasExprs = false;
  m_externalize = false;
}
