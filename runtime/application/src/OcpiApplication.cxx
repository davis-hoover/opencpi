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

#include <unistd.h>
#include <climits>
#include "OcpiOsFileSystem.h"
#include "OcpiContainerApi.h"
#include "OcpiOsMisc.h"
#include "OcpiUtilValue.h"
#include "OcpiPValue.h"
#include "OcpiTimeEmit.h"
#include "OcpiUtilMisc.h"
#include "ContainerLauncher.h"
#include "OcpiApplication.h"

namespace OC = OCPI::Container;
namespace OU = OCPI::Util;
namespace OE = OCPI::Util::EzXml;
namespace OL = OCPI::Library;
namespace OA = OCPI::API;
namespace OS = OCPI::OS;
namespace OCPI {
  namespace API {
    // This function is our hook before anything interesting happens so we can
    // divert some application PValue parameters into the discovery process
    static OL::Assembly &
    createLibraryAssembly(ezxml_t appXml, const char *name, const PValue *&params) {
      // Extract any extra application params from the environment
      const char *env = getenv("OCPI_APPLICATION_PARAMS");
      ocpiDebug("OCPI_APPLICATION_PARAMS:%s", env ? env : "");
      if (env) {
	OU::PValueList *envParams = new OU::PValueList;
        OU::PValueList tempParams;
        for (OU::TokenIter li(env); li.token(); li.next()) {
          const char *eq = strchr(li.token(), '=');
          if (!eq)
            ocpiBad("OCPI_APPLICATION_PARAMS value \"%s\" is invalid", env);
          std::string l_name(li.token(), OCPI_SIZE_T_DIFF(eq, li.token()));
          tempParams.add(l_name.c_str(), eq + 1);
        }
        envParams->add(params, tempParams);
        params = envParams->list(); // leak FIXME
      }
      // Among other things, this provides the simparams for simulation containers
      static const char *forDiscovery[] = {
        OCPI_DISCOVERY_PARAMETERS, OCPI_DISCOVERY_ONLY_PARAMETERS, NULL
      };
      // Patch/rename overloaded pvalue names for compatibility - note nasty cast, which should be ok
      for (OU::PValue *p = (OU::PValue *)params; p && p->name; p++)
        if (!strcasecmp(p->name, "buffersize"))
          p->name = "portbuffersize";
        else if (!strcasecmp(p->name, "buffercount"))
          p->name = "portbuffercount";
      OU::PValueList discoveryParams;
      for (const char **dp = forDiscovery; *dp; ++dp) {
        const PValue *p = OU::find(params, *dp);
        if (p)
          discoveryParams.add(*p);
      }
      OCPI::Driver::ManagerManager::getManagerManager().configureOnce(NULL,
                                                                      &discoveryParams[0]);
      bool verbose = false;
      OU::findBool(params, "verbose", verbose);
      if (verbose) {
        OA::Container *c;
        for (unsigned n = 0; (c = OA::ContainerManager::get(n)); n++)
          fprintf(stderr, "%s%u: %s [model: %s os: %s platform: %s]",
                  n ? ", " : "Available containers are:  ", n,
                  c->name().c_str(), c->model().c_str(), c->os().c_str(), c->platform().c_str());
        fprintf(stderr, "\n");
      }
      OA::useServers(NULL, params, verbose);
      return *new OL::Assembly(appXml, name, params);
    }
    // Deal with a deployment file referencing an app file
    // Be careful not to call too deep and invoke the one-time driver configuration.
    static OL::Assembly &
    createLibraryAssembly(const char *file, ezxml_t &deployXml, ezxml_t &appXml, char *&copy,
                          const PValue *&params) {
      std::string appFile(file);
      deployXml = NULL;
      copy = NULL;
      appXml = NULL;
      do {
        const char *err;
        const char *cp = appFile.c_str();
        while (isspace(*cp))
          cp++;
        if (*cp == '<') {
          size_t len = strlen(cp);
          copy = new char[len + 1]; // leak for now FIXME
          strcpy(copy, cp);
          if ((err = OE::ezxml_parse_str(copy, len, appXml)))
            throw OU::Error("Error: application XML string parse error: %s", err);
        } else {
          if (!OS::FileSystem::exists(appFile)) {
            appFile += ".xml";
            if (!OS::FileSystem::exists(appFile))
              throw OU::Error("Error: application file %s (or %s) does not exist\n", file,
                              appFile.c_str());
          }
          if ((err = OE::ezxml_parse_file(appFile.c_str(), appXml)))
            throw OU::Error("Can't parse application XML file \"%s\": %s", appFile.c_str(), err);
        }
        if (!strcasecmp(ezxml_name(appXml), "deployment")) {
          if ((err = OE::getRequiredString(appXml, appFile, "application")))
            throw OU::Error("For deployment XML file \"%s\": %s", file, err);
          deployXml = appXml;
        }
      } while (deployXml == appXml);
      std::string name;
      OU::baseName(appFile.c_str(), name);
      return createLibraryAssembly(appXml, name.c_str(), params);
    }

    ApplicationI::ApplicationI(Application &app, const char *file, const PValue *params)
      : m_earliest(OS::Time::now()), m_constructed(0), m_initialized(0), m_started(0), m_finished(0),
        m_assembly(createLibraryAssembly(file, m_deployXml, m_appXml, m_copy, params)),
        m_apiApplication(app) {
      init(params);
    }
    ApplicationI::ApplicationI(Application &app, ezxml_t xml, const char *a_name,
                               const PValue *params)
      : m_earliest(OS::Time::now()), m_constructed(0), m_initialized(0), m_started(0), m_finished(0),
        m_deployXml(NULL), m_appXml(NULL), m_copy(NULL),
        m_assembly(createLibraryAssembly(xml, a_name, params)), m_apiApplication(app)  {
      init(params);
    }
    ApplicationI::ApplicationI(Application &app, OL::Assembly &assy, const PValue *params)
      : m_earliest(OS::Time::now()), m_constructed(0), m_initialized(0), m_started(0), m_finished(0),
        m_deployXml(NULL), m_appXml(NULL), m_copy(NULL), m_assembly(assy),
        m_apiApplication(app) {
      m_assembly++;
      init(params);
    }
    ApplicationI::~ApplicationI() {
      try {
	clear();
      } catch (std::string &e) {
	ocpiBad("Exception during application shutdown: %s", e.c_str());
      } catch (const char *e) {
	ocpiBad("Exception during application shutdown: %s", e);
      } catch (std::exception &e) {
	ocpiBad("Exception during application shutdown: %s", e.what());
      } catch (...) {
	ocpiBad("Exception during application shutdown: unexpected exception");
      }
    }
    void ApplicationI::clear() {
      m_assembly--;
      ezxml_free(m_deployXml);
      ezxml_free(m_appXml);
      delete [] m_copy;
      delete [] m_bookings;
      delete [] m_properties;
      delete [] m_global2used;
      delete [] m_usedContainers;
      if (m_containerApps) {
        for (unsigned n = 0; n < m_nContainers; n++)
          delete m_containerApps[n];
        delete [] m_containerApps;
        for (auto li = m_launchers.begin(); li != m_launchers.end(); li++)
          (*li)->appShutdown(); // for now a launcher is only serially reusable, so no app id etc.
      }
    }
    unsigned ApplicationI::
    addContainer(unsigned container, bool existOk) {
      (void)existOk;
      ocpiAssert(existOk || !(m_allMap & (1u << container)));
      return getUsedContainer(container);
    }
    unsigned ApplicationI::
    getUsedContainer(unsigned container) {
      if (m_allMap & (1u << container))
        return m_global2used[container];
      m_usedContainers[m_nContainers] = container;
      m_allMap |= 1u << container;
      m_global2used[container] = m_nContainers;
      return m_nContainers++;
    }

    /*
     * We made choices during the feasibility analysis, but here we want to add some policy.
     * The default allocation will bias toward collocation, so this is basically to
     * spread things out.
     * Since exclusive/bitstream allocations are not really adjustable, we just deal with the
     * others.
     * we haven't remembered ALL deployments, just the "best".
     * we have preferred internally connected impls by scoring them up, which has inherently
     * consolidated then.
     * (preferred collocation)
     */
    // For dynamic instances only, distribute them according to policy
    void ApplicationI::
    policyMap(Deployment &d, unsigned instNum) {
      (void)instNum;
      // allMap is the bitmap of all suitable containers for the implementation
      d.m_usedContainers.resize(1, UINT_MAX);
      switch (m_cMapPolicy) {

      case MaxProcessors:
        // Limit use of processors to m_processors
        // If We have hit the limit, try to re-use.  If we can't, fall through to round robin
        if (m_nContainers >= m_processors)
          for (unsigned n = 0; n < m_nContainers; n++) {
            if (m_currConn >= m_nContainers)
              m_currConn = 0;
            if (d.m_feasible & (1u << m_usedContainers[m_currConn++])) {
              d.m_usedContainers[0] = m_currConn - 1;
              return;
            }
          }
        // Fall through - Not at our limit, let RR find the next available

      case RoundRobin:
        // Prefer adding a new container to an existing one, but if we can't
        // use a new one, rotate around the existing ones.
        for (unsigned n = 0; n < OC::Manager::s_nContainers; n++)
          if ((d.m_feasible & (1u << n)) && !(m_allMap & (1u << n))) {
            m_currConn = m_nContainers;
            d.m_usedContainers[0] = addContainer(n);
            ocpiDebug("instance %u used new container. best 0x%x curr %u cont %u",
                      instNum, d.m_feasible, m_currConn, n);
            return; // We added a new one - and used it
          }
        // We have to use one we have since only those are feasible
        do {
          if (++m_currConn >= m_nContainers)
            m_currConn = 0;
        } while (!(d.m_feasible & (1u << m_usedContainers[m_currConn])));
        d.m_usedContainers[0] = m_currConn;
        ocpiDebug("instance %u reuses container. best 0x%x curr %u cont %u",
                  instNum, d.m_feasible, m_currConn, m_usedContainers[m_currConn]);
        break;

      case MinProcessors:
        // Minimize processor - reuse when possible
        // use a new one, rotate around the existing ones.
        ocpiAssert(m_processors == 0);
        // Try to use first one already used that suits us
        for (unsigned n = 0; n < m_nContainers; n++)
          if (d.m_feasible & (1u << m_usedContainers[n])) {
            d.m_usedContainers[0] = n;
            return;
          }
        // Add one
        unsigned n;
        for (n = 0; n < OC::Manager::s_nContainers; n++)
          if (d.m_feasible & (1u << n))
            break;
        d.m_usedContainers[0] = addContainer(n);
      }
    }

    // Possible override the original policy in the xml
    void ApplicationI::
    setPolicy(const PValue *params) {
      uint32_t pcount;
      bool rr;
      if (OU::findULong(params, "MaxProcessors", pcount)) {
        m_cMapPolicy = MaxProcessors;
        m_processors = pcount;
      } else if (OU::findULong(params, "MinProcessors", pcount)) {
        m_cMapPolicy = MinProcessors;
        m_processors = pcount;
      } else if (OU::findBool(params, "RoundRobin", rr) && rr) {
        m_cMapPolicy = RoundRobin;
        m_processors = 0;
      }
    }

    // Now that we know a complete deployment, we can do a final check on the relative
    // position of proxies and slaves to be sure that proxies are either on the base
    // container or if not, all of its slaves are on the same system/launcher
    bool ApplicationI::
    resolveExplicitSlaves() {
      Instance *i = &m_instances[0];
      for (unsigned n = 0; n < m_nInstances; ++n, ++i) {
	const auto &impl = *i->m_deployment.m_impls[0];
	const auto &w = impl.m_metadataImpl;
	if (!w.slaveAssy())
	  continue;
	const auto &masterContainer = OC::Container::nthContainer(i->m_deployment.m_containers[0]);
	const OU::Assembly::Instance &ui = m_assembly.instance(n).m_utilInstance;
	for (unsigned ns = 0; ns < ui.m_slaveInstances.size(); ++ns) {
	  const auto &slave = m_instances[ui.slaveInstances()[ns]];
	  const auto &slaveContainer = OC::Container::nthContainer(slave.m_deployment.m_containers[0]);
	  if (&masterContainer != &OC::Container::baseContainer() &&
	      &masterContainer.launcher() != &slaveContainer.launcher()) {
	    std::string rejectSlave;
	    const auto &sui = m_assembly.instance(ui.slaveInstances()[ns]).m_utilInstance;
	    OU::format(rejectSlave,
		       "For instance \"%s\" for spec \"%s\" rejecting implementation \"%s%s%s\" "
		       "from artifact \"%s\" on container %s because it is neither on the base container "
		       "where the application is running, nor on the same system as its slave: \"%s\" "
		       "which is on container %s",
		       ui.cname(), ui.m_specName.c_str(),
		       impl.m_metadataImpl.cname(), impl.m_staticInstance ? "/" : "",
		       impl.m_staticInstance ? ezxml_cattr(impl.m_staticInstance, "name") : "",
		       impl.m_artifact.name().c_str(), masterContainer.cname(),
		       sui.cname(), slaveContainer.cname());
	    return false;
	  }
	}
      }
      return true;
    }

    // Deal with slaves when deploying this instance.
    bool ApplicationI::
    resolveInstanceSlaves(unsigned instNum, OL::Candidate &c, const std::string &reject) {
      ezxml_t slaves = c.impl->m_metadataImpl.slaveAssy();
      const OU::Assembly::Instance &ui = m_assembly.instance(instNum).m_utilInstance;
      if (slaves) {
	if (!c.slaves) {
	  // Do this work one time for this candidate of this instance, which caches this work so that it can
	  // be applied each time this candidate is considered for deployment
	  ocpiInfo("++++++++++++ Starting one-time processing of slave assembly for instance %u candidate %p",
		   instNum, &c);
	  // FIXME:  There should be a factory method that returns errors...
	  std::string error;
	  try {
	    c.slaves = new OL::Assembly(slaves, ui.cname(), NULL);
	  } catch (std::string &e) {
	    error = e;
	  } catch (const char *e) {
	    error = e ? e : "unexpected empty string error";
	  } catch (std::exception &e) {
	    error = e.what();
	  } catch (...) {
	    error = "unexpected exception";
	  }
	  if (!error.empty()) {
	    ocpiInfo("%s when processing slaves due to error: %s", reject.c_str(), error.c_str());
	    return false;
	  }
	  c.nInstances = m_nInstances;                      // remember for resize after deployment
	  c.nConnections = m_assembly.m_connections.size(); // remember for resize after deployment
	  // Patch the instances and ports in slave assembly for (repeated) insertion into the app
	  for (unsigned n = 0; n < c.slaves->instances().size(); ++n) {
	    auto &libInst = *c.slaves->instances()[n];
	    auto &utilInst = *(OU::Assembly::Instance*)&libInst.m_utilInstance; // ugly un-const
	    std::string old(utilInst.m_name);
	    if (ui.m_slaveNames.empty()) // don't rename for explicit slaves
	      OU::format(utilInst.m_name, "%s.%s", ui.cname(), old.c_str()); // proxy inst name is prefix
	    utilInst.m_ordinal += m_nInstances;
	    utilInst.m_master = instNum;
	    utilInst.m_hasMaster = true;
	    libInst.m_master = &m_assembly.instance(instNum);

	    for (auto it = utilInst.m_ports.begin(); it != utilInst.m_ports.end(); ++it)
	      (*it).m_instance = utilInst.m_ordinal;
	  }
	  ocpiInfo("++++++++++++ Ending one-time processing of slave assembly for instance %u candidate %p", 
		   instNum, &c);
	}
	ocpiInfo("++++++++++++ Starting insertion of slave instances for instance %u candidate %p",
		 instNum, &c);
	// (temporarily) add the slave assembly's instances to the app
	// but for compatibility, allow the app to specify existing slave instances
	m_instances[instNum].m_deployment.m_slaves.resize(c.slaves->nInstances(), SIZE_MAX);
	if (ui.m_slaveNames.empty()) { // backward compatibility - instances might be there
	  // add instances to the library assembly
	  m_assembly.instances().insert(m_assembly.instances().end(),
					c.slaves->instances().begin(),
					c.slaves->instances().end());
	  // add instances to the app
	  m_nInstances += c.slaves->nInstances();
	  m_instances.resize(m_nInstances);
	  Deployment &d = m_instances[instNum].m_deployment;
	  for (size_t n = c.nInstances; n < m_nInstances; ++n) {
	    m_instances[n].init(m_assembly, n, m_verbose, NULL);
	    d.m_slaves[n - c.nInstances] = n;
	  }
	} else {
	  Deployment &d = m_instances[instNum].m_deployment;
	  // The "multi-slave" legacy method with names and instances: UGH in hindsight
	  for (unsigned s = 0; s < ui.m_slaveNames.size(); ++s) {
	    if (ui.m_slaveNames[s])
	      for (unsigned n = 0; n < c.slaves->instances().size(); ++n) {
		if (!strcasecmp(ui.m_slaveNames[s], c.slaves->utilInstance(n).cname())) {
		  d.m_slaves[n] = ui.m_slaveInstances[s];
		  break;
		}
	      }
	    else if (s < d.m_slaves.size())
	      d.m_slaves[s] = ui.m_slaveInstances[s]; // implicit slave ordinal
	  }
	  for (unsigned n = 0; n < c.slaves->instances().size(); ++n)
	    if (d.m_slaves[n] == SIZE_MAX) {
	      ocpiInfo("%s due to missing explicit slave: %s", reject.c_str(),
		       c.slaves->utilInstance(n).cname());
	      return false;
	    }
	}
	// Process the slave assembly's connections (there will be none if we have explicit slaves)
	// For slave assy internal connections, we just add/copy those connections to the application
	// For slave assy connections with externals (i.e. to slave ports which can be delegated to),
	// if the app has a connection to the corresponding proxy port, we modify (repurpose) that
	// app connection to change its port from the proxy port to the port in the slave assy
	for (auto it = c.slaves->m_connections.begin(); it != c.slaves->m_connections.end(); ++it) {
	  OU::Assembly::Connection &slaveConn = **it;
	  if (slaveConn.m_externals.empty())
	    m_assembly.m_connections.push_back(&slaveConn);
	  else {
	    assert(slaveConn.m_ports.size() == 1 && slaveConn.m_externals.size() == 1 &&
		   slaveConn.m_count <= 1);
	    // Find the master's impl port corresponding to the slave assy external port
	    const OU::Port &masterImplPort =
	      *c.impl->m_metadataImpl.findMetaPort(slaveConn.m_externals.front().first->m_name);
	    // Find the app assy port for the master port.  If its null there is no app connection
	    OU::Assembly::Port *masterPort = m_assembly.assyPort(instNum, masterImplPort.m_ordinal);
	    if (masterPort) { // master port has at least one connection.  find it
	      OU::Assembly::Connection *appConn = NULL;
	      OU::Assembly::ConnPort *appConnPort = NULL; // warning
	      // find the app connection that connects to the master/external port
	      for (auto cit = m_assembly.m_connections.begin();
		   appConn == NULL && cit != m_assembly.m_connections.end(); ++cit)
		for (auto pit = (*cit)->m_ports.begin(); pit != (*cit)->m_ports.end(); ++pit)
		  if (pit->first == masterPort && pit->second == slaveConn.m_externals.front().second) {
		    appConn = *cit;
		    assert(appConn->m_count <= 1);
		    appConnPort = &*pit;
		    break;
		  }
	      if (appConn) { // there is an app connection to the master port with the same index
		// Save info to allow us to undo the delegation
		c.m_portFixups.emplace_front(appConn, &slaveConn, appConnPort);
		// Patch the app connection to point to a different port+index, delegating it.
		// since the slaveConn has an external, the front() *is* the internal port
		*appConnPort = slaveConn.m_ports.front(); // DELEGATE THE PORT
		// Remove the stale conn references from both ports
		masterPort->m_connections.remove(appConn);
		appConnPort->first->m_connections.remove(&slaveConn);
		// Add a new conn reference to the slave port
		appConnPort->first->m_connections.push_front(appConn); // conn to slave port
	      }
	    }
	  }
	}
	ocpiInfo("++++++++++++ Ending insertion of slave instances for instance %u candidate %p",
		 instNum, &c);
      }
      return true;
    }
    void ApplicationI::
    restoreSlaves(OL::Candidate &c) {
      if (!c.slaves)
	return;
      // patch up and restore the connections that were delegated
      for (; !c.m_portFixups.empty(); c.m_portFixups.pop_front()) {
	auto &fixup = c.m_portFixups.front();
	// Restore slave port.  Remove app conn, and add back slave conn
	fixup.connPort->first->m_connections.remove(fixup.appConn);
	fixup.connPort->first->m_connections.push_front(fixup.slaveConn);
	// Restore master port (add what was removed)
	fixup.masterConnPort.first->m_connections.push_front(fixup.appConn);
	// Restore app conn (slave conn was untouched)
	*fixup.connPort = fixup.masterConnPort;
      }
      m_nInstances = c.nInstances;
      m_instances.resize(m_nInstances);                // toss slaves from app assembly
      m_assembly.instances().resize(c.nInstances);     // toss slaves from lib assembly
      m_assembly.m_connections.resize(c.nConnections); // toss intraslave connections
    }

    // Check whether this candidate can be used relative to previous
    // choices for instances it is connected to or has a proxy/slave relationship with.
    // It has the side effect of initializing the m_deployment.m_slaves array for the instance
    bool ApplicationI::
    connectionsOk(OL::Candidate &c, unsigned instNum) {
      //      const OU::Assembly::Instance &ui = m_assembly.instance(instNum).m_utilInstance;
      std::string reject;
      OU::format(reject,
                 "    Rejecting implementation \"%s%s%s\" with score %u "
                 "from artifact \"%s\"",
                 c.impl->m_metadataImpl.cname(),
                 c.impl->m_staticInstance ? "/" : "",
                 c.impl->m_staticInstance ? ezxml_cattr(c.impl->m_staticInstance, "name") : "",
                 c.score, c.impl->m_artifact.name().c_str());
      if (!resolveInstanceSlaves(instNum, c, reject))
	return false;
      // Now check all connected ports, including when they are aliased to slave ports.
      unsigned nPorts;
      const OU::Port *port = c.impl->m_metadataImpl.ports(nPorts);
      for (unsigned nn = 0; nn < nPorts; ++port, ++nn) { // for each candidate port
        OU::Assembly::Port *ap = m_assembly.assyPort(instNum, nn);
	if (!ap || ap->m_connections.empty()) // port not connected in app
	  continue;
	// For connections to this port (presumably with different indices)
	for (auto ci = ap->m_connections.begin(); ci != ap->m_connections.end(); ++ci) {
	  auto &conn = **ci;
	  if (!conn.m_externals.empty()) { // no checking for externals
	    if (c.impl->m_internals & (1u << nn)) {
	      ocpiInfo("%s due to implementation port \"%s\" having an internal connection when "
		       "application specifies that port as external", reject.c_str(), ap->cname());
	      return false;
	    }
	    continue;
	  }
	  auto other = conn.m_ports.front().first == ap ?
	    conn.m_ports.back().first : conn.m_ports.front().first;
	  if (other->m_instance > instNum) // other's instance not processed yet
	    continue;
	  assert(other->m_instance != instNum);
	  const OL::Implementation *thisImpl = c.impl, *otherImpl = NULL;
	  const OU::Port *thisPort = port, *otherPort = NULL;
          otherImpl = m_instances[other->m_instance].m_deployment.m_impls[0];
	  otherPort = otherImpl->m_metadataImpl.findMetaPort(other->cname());
	  // check for prewired compatibility, post-delegation
	  if (m_assembly.badConnection(*thisImpl, *thisPort, *otherImpl, *otherPort)) {
	    ocpiInfo("%s due to connectivity conflict", reject.c_str());
	    ocpiInfo("      Other is instance \"%s\" for spec \"%s\" implementation \"%s%s%s\" "
		     "from artifact \"%s\".",
		     m_assembly.instance(other->m_instance).name().c_str(),
		     m_assembly.instance(other->m_instance).specName().c_str(),
		     otherImpl->m_metadataImpl.cname(),
		     otherImpl->m_staticInstance ? "/" : "",
		     otherImpl->m_staticInstance ?
		     ezxml_cattr(otherImpl->m_staticInstance, "name") : "",
		     otherImpl->m_artifact.name().c_str());
	    return false;
	  }
	} // loop of all the connections for this port
      } // loop of all ports of the instance
      return true;
    }

    // FIXME: we assume that if the implementation is not a static instance then it can't conflict
    bool ApplicationI::
    bookingOk(Booking &b, OL::Candidate &c, unsigned n) {
      if (c.impl->m_staticInstance && b.m_artifact &&
          (b.m_artifact != &c.impl->m_artifact ||
           b.m_usedImpls & ((uint64_t)1u << c.impl->m_ordinal))) {
        ocpiInfo("    For instance \"%s\" for spec \"%s\" rejecting implementation \"%s%s%s\" with score %u "
                  "from artifact \"%s\" due to insufficient available containers",
                  m_assembly.instance(n).name().c_str(),
                  m_assembly.instance(n).specName().c_str(),
                  c.impl->m_metadataImpl.cname(),
                  c.impl->m_staticInstance ? "/" : "",
                  c.impl->m_staticInstance ? ezxml_cattr(c.impl->m_staticInstance, "name") : "",
                  c.score, c.impl->m_artifact.name().c_str());
        return false;
      }
      return true;
    }

    void ApplicationI::
    checkPropertyValue(unsigned nInstance, const OU::Worker &w,
                       const OU::Assembly::Property &aProp, unsigned *&pn, OU::Value *&pv) {
      const char
        *pName = aProp.m_name.c_str(),
        *iName = m_assembly.instance(nInstance).name().c_str();
      const OU::Property &uProp = w.findProperty(pName);
      if (uProp.m_isParameter)
        return;
      if (!uProp.m_isWritable && (aProp.m_hasDelay || !uProp.m_isInitial))
        throw OU::Error("Cannot set property '%s' for instance '%s'. It is not writable.",
                        pName, iName);
      OU::Value *v;
      if (aProp.m_hasDelay) {
        const auto dpv =
          m_delayedPropertyValues.insert(std::make_pair(aProp.m_delay, DelayedPropertyValue()));
        dpv->second.m_instance = nInstance;
        dpv->second.m_property = &uProp;
        v = &dpv->second.m_value;
      }  else {
        *pn++ = uProp.m_ordinal; // remember position in property list
        v = pv++;
      }
      v->setType(uProp); // set the data type of the Value from the metadata property
      const char *err;
      if ((err = uProp.parseValue(aProp.m_value.c_str(), *v, NULL, &w)))
        throw OU::Error("Value for property \"%s\" of instance \"%s\" of "
                        "component \"%s\" is invalid for its type: %s",
                        pName, iName, w.specName().c_str(), err);
    }
    void ApplicationI::
    checkExternalParams(const char *pName, const OU::PValue *params) {
      // Error check instance assignment parameters for externals
      const char *assign;
      for (unsigned n = 0; OU::findAssignNext(params, pName, NULL, assign, n); ) {
        const char *eq = strchr(assign, '=');
        if (!eq)
          throw OU::Error("Parameter assignment '%s' is invalid. "
                          "Format is: <external>=<parameter-value>", assign);
        size_t len = (size_t)(eq - assign);
        for (auto ci = m_assembly.m_connections.begin(); ci != m_assembly.m_connections.end(); ++ci) {
          const OU::Assembly::Connection &c = **ci;
          if (c.m_externals.size()) {
            const OU::Assembly::External &e = *c.m_externals.front().first;
            if (e.m_name.length() == len && !strncasecmp(assign, e.m_name.c_str(), len)) {
              assign = NULL;
              break;
            }
          }
        }
        if (assign)
          throw OU::Error("No external port for %s assignment '%s'", pName, assign);
      }
    }
    // Prepare all the property values for an instance
    void ApplicationI::
    prepareInstanceProperties(unsigned nInstance, const OL::Implementation &impl, unsigned *&pn,
                              OU::Value *&pv) {
      const OU::Assembly::Properties &aProps = *m_bestDeployments[nInstance].m_properties;
      // Prepare all the property values in the assembly, avoiding those in parameters.
      for (unsigned p = 0; p < aProps.size(); p++) {
        if (aProps[p].m_dumpFile.size()) {
          // findProperty throws on error if bad name
#if 0
          const char *pName = aProps[p].m_name.c_str();
          OU::Property &uProp = impl.m_metadataImpl.findProperty(pName);
          if (!uProp.m_isReadable && !uProp.m_isParameter) // all is readable now
            throw OU::Error("Cannot dump property '%s' for instance '%s'. It is not readable.",
                            pName, m_assembly.instance(nInstance).name().c_str());
#endif
        }
        if (aProps[p].m_hasValue)
	  checkPropertyValue(nInstance, impl.m_metadataImpl, aProps[p], pn, pv);
      }
    }

#if 0
    // Prepare instance properties for a possible deployment
no since it is really worker specific. perhaps do it really earlier so it can be used where
initial properties are checked against parameters?
does the library database have anything interned per worker?
so we need to check instance props against (late binding) for a *candidate*
it is really per actual worker config...
    prepareInstanceProperties(
#endif
    void ApplicationI::
    finalizeProperties(const OU::PValue *params) {
      auto *d = &m_bestDeployments[0];
      // Collect and check the property values for each instance (not inferred slaves)
      assert(m_nInstances <= m_bestDeployments.size());
      for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++) {
        // The chosen, best, feasible implementation for the instance
        const char *iName = d->m_name.c_str();
        const OU::Assembly::Properties &aProps = *d->m_properties;
        size_t nPropValues = aProps.size();
        const char *sDummy;
        // Count any properties that were provided in parameters specific to instance
        for (unsigned nn = 0; OU::findAssignNext(params, "property", iName, sDummy, nn); )
          nPropValues++;
        // Count any parameter properties that were mapped to this instance
	// Note these cannot apply to inferred slaves so the ordinals should be ok
	OU::Assembly::MappedProperty *mp = &m_assembly.m_mappedProperties[0];
        unsigned nDummy = 0;
        for (size_t nn = m_assembly.m_mappedProperties.size(); nn; nn--, mp++)
          if (mp->m_instance == n &&
              OU::findAssignNext(params, "property", mp->m_name.c_str(), sDummy, nDummy))
            nPropValues++;
        // Account for the runtime properties set here, e.g. output port buffer size
        const OL::Implementation &impl = *d->m_impls[0];
        unsigned nPorts;
        for (OU::Port *p = impl.m_metadataImpl.ports(nPorts); nPorts; --nPorts, p++)
          if (p->m_isProducer)
            nPropValues++;
        if (nPropValues) {
          // This allocation will include dump-only properties, which won't be put into the
          // array by prepareInstanceProperties
          d->m_crew.m_propValues.resize(nPropValues);
          d->m_crew.m_propOrdinals.resize(nPropValues);
          OU::Value *pv = &d->m_crew.m_propValues[0];
          unsigned *pn = &d->m_crew.m_propOrdinals[0];
          // Note that for scaled instances we assume the impls are compatible as far as
          // properties go.  FIXME:  WE MUST CHECK COMPILED VALUES WHEN COMPARING IMPLS
          prepareInstanceProperties(n, impl, pn, pv);
          // Add buffer size property value to each output
          for (auto it = m_launchConnections.begin(); it != m_launchConnections.end(); ++it) {
            OC::Launcher::Connection &c = *it;
            if (c.m_out.m_member &&
		c.m_out.m_member->m_crew == m_launchMembers[d->m_firstMember].m_crew) {
              OU::Assembly::Property aProp;
              aProp.m_name = "ocpi_buffer_size_" + c.m_out.m_metaPort->m_name;
              if (!impl.m_metadataImpl.getProperty(aProp.m_name.c_str())) {
                ocpiInfo("Missing %s property for %s", aProp.m_name.c_str(), impl.m_metadataImpl.cname());
                continue;
              }
              aProp.m_hasValue = true;
              OU::format(aProp.m_value, "%zu", c.m_bufferSize);
              checkPropertyValue(n, impl.m_metadataImpl, aProp, pn, pv);
            }
          }
          nPropValues = (size_t)(pn - &d->m_crew.m_propOrdinals[0]);
          d->m_crew.m_propValues.resize(nPropValues);
          d->m_crew.m_propOrdinals.resize(nPropValues);
        }
      }
      // For all instances in the assembly, create the app-level property array
      m_nProperties = m_assembly.m_mappedProperties.size();
      d = &m_bestDeployments[0];
      for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++)
        m_nProperties += d->m_impls[0]->m_metadataImpl.nProperties();
      // Over allocate: mapped ones plus all the instances' ones
      Property *p = m_properties = new Property[m_nProperties];
      OU::Assembly::MappedProperty *mp = &m_assembly.m_mappedProperties[0];
      for (size_t n = m_assembly.m_mappedProperties.size(); n; n--, mp++, p++) {
        p->m_property =
          m_bestDeployments[mp->m_instance].m_impls[0]->m_metadataImpl.
	  whichProperty(mp->m_instPropName.c_str());
        p->m_name = mp->m_name;
        p->m_instance = mp->m_instance;
        p->m_dumpFile = NULL;
        ocpiDebug("Instance %s (%u) property %s (%u) named %s in assembly",
		  m_bestDeployments[p->m_instance].m_name.c_str(), p->m_instance,
                  mp->m_instPropName.c_str(), p->m_property, p->m_name.c_str());
      }
      d = &m_bestDeployments[0];
      for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++) {
        unsigned nProps;
        OU::Property *meta = d->m_impls[0]->m_metadataImpl.properties(nProps);
        for (unsigned nn = 0; nn < nProps; nn++, meta++, p++) {
          p->m_name = d->m_name + "." + meta->m_name;
          p->m_instance = n;
          p->m_property = nn;
          ocpiDebug("Instance %s (%u) property %s (%u) named %s", d->m_name.c_str(), n,
                    meta->m_name.c_str(), nn, p->m_name.c_str());
          // Record dump file for this property if there is one.
          const OU::Assembly::Properties &aProps = *d->m_properties;
          p->m_dumpFile = NULL;
          for (unsigned nnn = 0; nnn < aProps.size(); nnn++)
            if (aProps[nnn].m_dumpFile.size() &&
                !strcasecmp(aProps[nnn].m_name.c_str(),
                            meta->m_name.c_str())) {
              p->m_dumpFile = aProps[nnn].m_dumpFile.c_str();
              break;
            }
        }
      }
    }

    void ApplicationI::
    finalizeExternals() {
      // External ports that are not connected explicitly to anything need to be associated
      // with the base container in this process, so we make sure we are using it.
      for (auto ci = m_bestConnections.begin(); ci != m_bestConnections.end(); ++ci)
        if ((*ci).m_externals.size() && (*ci).m_externals.front().first->m_url.empty())
          getUsedContainer(OC::Container::baseContainer().ordinal());
    }

    // Apply parameters to ports
    const char *ApplicationI::
    finalizePortParam(const OU::PValue *params, const char *pName) {
      const char *assign;
      for (unsigned n = 0; OU::findAssignNext(params, pName, NULL, assign, n); ) {
        const char *value, *err;
        size_t instn, portn;
        const OU::Port *p;
        if ((err = m_assembly.getPortAssignment(pName, assign, instn, portn, p, value)))
          return err;
        // This is taking the string value of a app-level assigned port param and using the same param
        // name for a port param.  When the data types are different (at least), we need to
        // change the name.  We have a little heuristic rather than a real table.
        // FIXME: some more serious scheme for "port and instance params into underlying ones"
        const char *newName = !strncasecmp(pName, "port", 4) ? pName + 4 : pName;
        // Override any port parameters that might have been set in XML
        // Override any same-named connection params
	for (auto ci = m_bestConnections.begin(); ci != m_bestConnections.end(); ++ci)
	  for (auto pi = (*ci).m_ports.begin(); pi != (*ci).m_ports.end(); ++pi) {
	    OU::Assembly::Port &ap = *(*pi).first;
	    assert(!ap.m_name.empty());
	    if (ap.m_instance == instn && !strcasecmp(ap.m_name.c_str(), p->cname()))
	      ap.setParam(*ci, newName, value);
	  }
        // m_assembly.assyPort(instn, portn)->setParam(newName, value);
      }
      return NULL;
    }
    void ApplicationI::
    dumpDeployment(unsigned score) {
      (void)score;
      ocpiDebug("Deployment with score %u is:", score);
      Instance *i = &m_instances[0];
      for (unsigned n = 0; n < m_nInstances; n++, i++) {
        if (i->m_deployment.m_scale == 1) {
          const OL::Implementation &li = *i->m_deployment.m_impls[0];
          ocpiDebug(" Instance %2u: Container: %u Instance %s%s%s in %s",
                    n, i->m_deployment.m_containers[0],
                    li.m_metadataImpl.cname(),
                    li.m_staticInstance ? "/" : "",
                    li.m_staticInstance ? ezxml_cattr(li.m_staticInstance, "name") : "",
                    li.m_artifact.name().c_str());
        } else {
          ocpiDebug(" Instance %2u: Scale factor: %zu", n, i->m_deployment.m_scale);
          for (unsigned j = 0; j < i->m_deployment.m_scale; j++) {
            const OL::Implementation li = *i->m_deployment.m_impls[j];
            ocpiDebug("   Member %2u: Container: %u Instance %s%s%s in %s",
                      j, i->m_deployment.m_containers[j], li.m_metadataImpl.cname(),
                      li.m_staticInstance ? "/" : "",
                      li.m_staticInstance ? ezxml_cattr(li.m_staticInstance, "name") : "",
                      li.m_artifact.name().c_str());
          }
        }
      }
    }

    // After deciding on a possible instance deployment, record it and recurse for next one.
    // We record the implementation (possibly an array of them in the scaled case).
    // We record the container(s), and the feasible container map too for the unscaled case
    void ApplicationI::
    deployInstance(unsigned instNum, unsigned score, size_t scale,
                   unsigned *containers, const OL::Implementation **impls, CMap feasible) {
      auto const &ui = m_assembly.utilInstance(instNum);
      m_instances[instNum].m_deployment.
	set(ui.m_name, scale, containers, impls, feasible, ui.m_hasMaster, &ui.m_properties);
      ocpiDebug("doInstance ok");
      if (instNum < m_nInstances-1) {
        instNum++;
        if (scale == 1 && (*impls)->m_staticInstance) {
          // FIXME: We don't deal with static instances on scaled instances yet
          Booking
            &b = m_bookings[*containers],
            save = b;
          b.m_artifact = &(*impls)->m_artifact;
          b.m_usedImpls |= (uint64_t)1u << (*impls)->m_ordinal;
          doInstance(instNum, score);
          b = save;
        } else
          doInstance(instNum, score);
      } else if (resolveExplicitSlaves()) {
        dumpDeployment(score);
        if (score > m_bestScore) {
	  // Capture the deployment, which might have a variable number of instances
	  // based on the inclusion of slaves when instance candidates are proxies
	  m_bestDeployments.resize(m_nInstances);
          Instance *i = &m_instances[0];
          for (unsigned n = 0; n < m_nInstances; n++, i++)
            m_bestDeployments[n] = i->m_deployment;
          m_bestScore = score;
	  m_bestConnections.clear();
	  for (auto ci = m_assembly.m_connections.begin();
	       ci != m_assembly.m_connections.end(); ++ci)
	    m_bestConnections.push_back(**ci);
          ocpiDebug("Setting BEST");
        }
      }
    }

    void ApplicationI::
    doScaledInstance(unsigned instNum, unsigned score) {
      Instance *i = &m_instances[instNum];
      OL::Assembly::Instance &li = m_assembly.instance(instNum);
      const OU::Assembly::Instance &ui = li.m_utilInstance;
      for (Instance::ScalableCandidatesIter sci = i->m_scalableCandidates.begin();
           sci != i->m_scalableCandidates.end(); sci++) {
        CMap map = 0;
        for (Instance::CandidatesIter ci = sci->second.begin(); ci != sci->second.end(); ci++)
          map |= i->m_feasibleContainers[*ci];
        size_t nFeasible = 0, nCollocated, nUsed, scale;
        for (unsigned cont = 0; cont < OC::Manager::s_nContainers; cont++)
          if (map & (1u << cont))
            nFeasible++;
        const char *err =
          ui.m_collocation.apply(li.m_scale, nFeasible, nCollocated, nUsed, scale);
        if (err) {
          ocpiInfo("Scalable implementation %s rejected due to collocation constraints: %s",
                   li.m_candidates[sci->second.front()].impl->m_metadataImpl.cname(),
                   err);
          continue;
        }
        if (scale != li.m_scale) {
          ocpiInfo("Scaling of instance %s changed from %zu to %zu due to constraints",
                   ui.m_name.c_str(), li.m_scale, scale);
          li.m_scale = scale;
        }
        unsigned *containers = new unsigned[scale];
        const OL::Implementation **impls = new const OL::Implementation*[scale];
        unsigned nMember = 0;
        for (Instance::CandidatesIter ci = sci->second.begin(); ci != sci->second.end(); ci++) {
          CMap l_map = i->m_feasibleContainers[*ci];
          for (unsigned cont = 0; cont < OC::Manager::s_nContainers; cont++)
            if (l_map & (1u << cont))
              for (unsigned n = 0; n < nCollocated; n++) {
                containers[nMember] = cont;
                impls[nMember] = li.m_candidates[*ci].impl;
                if (++nMember == scale)
                  goto out;
              }
        }
      out:
        deployInstance(instNum, score + li.m_candidates[sci->second.front()].score, scale,
                       containers, impls, map); // the map isn't really relevant yet...
      }
    }

    void ApplicationI::
    doInstance(unsigned instNum, unsigned score) {
      OL::Assembly::Instance &li = m_assembly.instance(instNum);
      ocpiInfo("================================================================================");
      ocpiInfo("Trying to deploy candidates for instance %2d:  %s", instNum, li.name().c_str());
      if (li.m_scale > 1)
        doScaledInstance(instNum, score);
      else {
        for (unsigned m = 0; m < li.m_candidates.size(); m++) {
          OL::Candidate &c = li.m_candidates[m];
	  ocpiInfo("  --------------------------------------------------------------------------------");
	  ocpiInfo("  Trying candidate %u for instance %u: %s (artifact %s, implementation %s%s%s)",
		   m, instNum, li.name().c_str(), c.impl->m_artifact.name().c_str(),
		   c.impl->m_metadataImpl.cname(),
		   c.impl->m_staticInstance ? "/" : "",
		   c.impl->m_staticInstance ? ezxml_cattr(c.impl->m_staticInstance, "name") : "");
          ocpiDebug("doInstance %u %u %u", instNum, score, m);
          if (connectionsOk(c, instNum))
            for (unsigned cont = 0; cont < OC::Manager::s_nContainers; cont++) {
	      Instance &i = m_instances[instNum];
              ocpiDebug("doInstance container: cont %u feasible 0x%x", cont,
                        i.m_feasibleContainers[m]);
              if (i.m_feasibleContainers[m] & (1u << cont) &&
                  bookingOk(m_bookings[cont], c, instNum)) {
		// Bump the score if the optimized attribute of the worker (as compiled) matches the
		// optimized attribute of the container.  Since we generally want workers that match
		// what the container (and framework) is built for.
		unsigned bump =
		  OC::Container::nthContainer(cont).m_optimized == c.impl->m_artifact.optimized() ?
		  1 : 0;
                deployInstance(instNum, score + c.score + bump, 1, &cont, &c.impl,
                               i.m_feasibleContainers[m]);
                if (!c.impl->m_staticInstance)
                  break;
              }
            }
	  restoreSlaves(c);
        }
      }
    }
    void ApplicationI::Instance::
    collectCandidate(const OL::Candidate &c, unsigned n) {
      OU::Worker &w = c.impl->m_metadataImpl;
      std::string qname(w.package());
      qname += ".";
      qname += w.cname();
      ScalableCandidatesIter sci = m_scalableCandidates.find(qname);
      if (sci == m_scalableCandidates.end())
        sci = m_scalableCandidates.insert(ScalablePair(qname, Candidates())).first;
      sci->second.push_back(n);
    }

    // Prepare an instance for deployment
    // Called initially on all application instances, and then
    // also on any slave instances added dynamically
    const char *ApplicationI::Instance::
    init(const OL::Assembly &assy, size_t n, bool verbose, const PValue *params) {
      const OL::Candidates &cs = assy.instance(n).m_candidates;
      const OU::Assembly::Instance &ai = assy.utilInstance(n);
      size_t nCandidates = cs.size();
      m_feasibleContainers.resize(nCandidates);
      std::string container;
      if (!OU::findAssign(params, "container", ai.m_name.c_str(), container) &&
	  !OU::findAssign(params, "container", ai.m_specName.c_str(), container))
	OE::getOptionalString(ai.xml(), container, "container");
      CMap sum = 0;
      ocpiInfo("================================================================================");
      ocpiInfo("For instance %2zu: \"%s\" there were %zu candidates.  These had potential containers:",
	       n, ai.m_name.c_str(), nCandidates);
      for (unsigned m = 0; m < nCandidates; m++) {
	m_curMap = 0;        // to accumulate containers suitable for this candidate
	OU::Worker &w = cs[m].impl->m_metadataImpl;
	ocpiInfo("  --------------------------------------------------------------------------------");
	ocpiInfo("  Candidate %2u: checking implementation %s model %s os %s version %s arch %s "
		 "platform %s dynamic %u opencpi version %s",
		 m, w.cname(), w.model().c_str(), w.attributes().os().c_str(),
		 w.attributes().osVersion().c_str(), w.attributes().arch().c_str(),
		 w.attributes().platform().c_str(), w.attributes().dynamic(),
		 w.attributes().opencpiVersion().c_str());
	(void)OC::Manager::findContainers(*this, w, container.empty() ? NULL : container.c_str());
	m_feasibleContainers[m] = m_curMap;
	sum |= m_curMap;
	// if log level is >= info
	Container *c;
	if (m_curMap) {
	  std::string s;
	  for (unsigned nn = 0; (c = OC::Manager::get(nn)); nn++)
	    if (m_curMap & (1u << nn))
	      OU::formatAdd(s, "%s%u: %s", s.empty() ? "" : ", ", nn, c->name().c_str());
	  ocpiInfo("  Candidate %u %s is ok for containers: %s", m,
		   cs[m].impl->m_artifact.name().c_str(), s.c_str());
	} else
	  ocpiInfo("  Candidate %u %s is ok for no containers", m,
		   cs[m].impl->m_artifact.name().c_str());
	if (m_curMap && assy.instance(n).m_scale > 1)
	  collectCandidate(cs[m], m);
      }
      if (!sum) {
	if (verbose && n < assy.nAppInstances()) {
	  fprintf(stderr, "No containers were found for deploying instance '%s' (spec '%s').\n"
		  "  The implementations found were:\n",
		  ai.m_name.c_str(), ai.m_specName.c_str());
	  for (unsigned m = 0; m < nCandidates; m++) {
	    const OL::Implementation &lImpl = *cs[m].impl;
	    OU::Worker &mImpl = lImpl.m_metadataImpl;
	    fprintf(stderr, "  Name: %s, Model: %s, Arch: %s, Platform: %s%s%s, OpenCPI Version: %s, File: %s\n",
		    mImpl.cname(),
		    mImpl.model().c_str(),
		    lImpl.m_artifact.arch().c_str(),
		    lImpl.m_artifact.platform().c_str(),
		    lImpl.m_staticInstance ? ", Artifact instance: " : "",
		    lImpl.m_staticInstance ? ezxml_cattr(lImpl.m_staticInstance, "name") : "",
		    mImpl.attributes().opencpiVersion().c_str(),
		    lImpl.m_artifact.name().c_str());
	  }
	}
	return OU::esprintf("For instance \"%s\" for spec \"%s\": "
			    "no feasible containers found for %sthe %zu implementation%s found.",
			    ai.m_name.c_str(), ai.m_specName.c_str(),
			    nCandidates == 1 ? "" : "any of ",
			    nCandidates,
			    nCandidates == 1 ? "" : "s");
      }
      return NULL;
    }

     // The algorithmic way to figure out a deployment.
    void ApplicationI::
    planDeployment(const PValue *params) {
      m_bookings = new Booking[OC::Manager::s_nContainers];
      // Set the instance map policy
      setPolicy(params);
      // First pass - make sure there are some containers to support some candidate
      // and remember which containers can support which candidates
      Instance *i = &m_instances[0];
        ocpiInfo("================================================================================");
	ocpiInfo("Determining which candidates can run on which containers");
      for (size_t n = 0; n < m_nInstances; n++, i++) {
	const char *err = i->init(m_assembly, n, m_verbose, params);
	if (err)
	  throw OU::Error("%s", err);
      }

      // Second pass - search for best feasible choice
      // FIXME: we are assuming broadly that dynamic instances have universal connectivity
      // FIXME: we are assuming that an artifact is exclusive if is has static instances.
      // FIXME: we are assuming that if an artifact has a static instance, all of its instances are

      m_bestScore = 0;
      doInstance(0, 0);
      if (m_bestScore == 0)
        throw OU::Error("There are no feasible deployments for the application given the constraints. "
			" Try running with log level 8 to see why.");
      // Up to now we have just been "planning" and not doing things.
      // First deal with non-scaled, non-static instances
      auto *d = &m_bestDeployments[0];
      for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++)
        if (d->m_scale <= 1 &&
	    !d->m_impls[0]->m_staticInstance &&
	    d->m_slaves.empty() &&
	    !d->m_hasMaster)
	  policyMap(*d, n);
      // IN a second pass, deal with scaled or static or slaves
      d = &m_bestDeployments[0];
      for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++) {
	d->m_usedContainers.resize(d->m_scale, UINT_MAX);
        if (d->m_scale > 1) {
          for (unsigned s = 0; s < d->m_scale; s++)
            d->m_usedContainers[s] = getUsedContainer(d->m_containers[s]);
        } else if (d->m_usedContainers[0] == UINT_MAX)
	  d->m_usedContainers[0] = getUsedContainer(d->m_containers[0]);
      }
    }

    // The explicit way to figure out a deployment from a file
    // FIXME BROKEN FOR INFERRED SLAVES
    void ApplicationI::
    importDeployment(const char *file, ezxml_t &xml, const PValue *params) {
      if (!xml) {
        const char *err = OE::ezxml_parse_file(file, xml);
        if (err)
          throw OU::Error("Error parsing deployment file: %s", err);
      }
      if (!ezxml_name(xml) || strcasecmp(ezxml_name(xml), "deployment"))
        throw OU::Error("Invalid top level element \"%s\" in deployment file \"%s\"",
                        ezxml_name(xml) ? ezxml_name(xml) : "", file);
      Instance *i = &m_instances[0];
      m_bestDeployments.resize(m_nInstances);
      for (unsigned n = 0; n < m_nInstances; n++, i++) {
        ezxml_t xi;
        const char *iname = m_assembly.instance(n).name().c_str();
        for (xi = ezxml_cchild(xml, "instance"); xi; xi = ezxml_cnext(xi)) {
          const char *l_name = ezxml_cattr(xi, "name");
          if (!l_name)
            throw OU::Error("Missing \"name\" attribute for instance in deployment file \"%s\"",
                            file);
          if (!strcasecmp(l_name, iname))
            break;
        }
        if (!xi)
          throw
            OU::Error("Missing instance element for instance \"%s\" in deployment file", iname);
        const char
          *spec = ezxml_cattr(xi, "spec"),
          *worker = ezxml_cattr(xi, "worker"),
          *model = ezxml_cattr(xi, "model"),
          *artifact = ezxml_cattr(xi, "artifact"),
          *instance = ezxml_cattr(xi, "instance");
        i->m_containerName = ezxml_cattr(xi, "container");
        if (!spec || !worker || !model || !i->m_containerName || !artifact)
          throw
            OU::Error("Missing attributes for instance element \"%s\" in deployment file."
                      "  All of spec/worker/model/container/artifact must be present.", iname);
        /*
         * Importing a deployment means bypassing the library mechanism, or at least not
         * relying on it.  Basically we make our own library out of the specific artifacts
         * indicated in the deployment.
         */
        OL::Artifact &art = OL::Manager::getArtifact(artifact, NULL);
        OL::Implementation *impl = art.findImplementation(spec, instance);
        if (!impl)
          throw OU::Error("For deployment instance \"%s\", worker for spec %s/%s not found "
                          " in artifact \"%s\"", iname, spec, instance ? instance : "",
                          artifact);
	m_bestDeployments[n].m_impls.resize(1);
        m_bestDeployments[n].m_impls[0] = impl;
        if (!m_assembly.instance(n).resolveUtilPorts(*impl, m_assembly))
          throw OU::Error("Port mismatch for instance \"%s\" in artifact \"%s\"",
                          iname, artifact);
        bool execution;
        if (OU::findBool(params, "execution", execution) && !execution)
          continue;
        OC::Container *c = OC::Manager::find(i->m_containerName);
        if (!c)
          throw OU::Error("For deployment instance \"%s\", container \"%s\" was not found",
                          iname, i->m_containerName);
        m_bestDeployments[n].m_containers[0] = getUsedContainer(c->ordinal());
      }
    }

    const char *ApplicationI::
    timeDiff(OS::Time later, OS::Time earlier) {
      OS::Time diff = later - earlier;
      return OU::format(m_timeString, " [%u s %u ms]", diff.seconds(), diff.nanoseconds()/1000000);
    }

    void ApplicationI::
    init(const PValue *params) {
      try {
        // In order from class definition except for instance-related
        // We must initialize everything before anything that might cause an exception
        m_bookings = NULL;
        m_properties = NULL;
        m_nProperties = 0;
	//        m_curMap = 0;
	//        m_curContainers = 0;
        m_allMap = 0;
        m_global2used = new unsigned[OC::Manager::s_nContainers];
        m_nContainers = 0;
        m_usedContainers = new unsigned[OC::Manager::s_nContainers];
        m_containerApps = NULL; // ditto
        m_cMapPolicy = RoundRobin;
        m_processors = 0;
        m_currConn = OC::Manager::s_nContainers - 1;
        m_bestScore = 0;
        m_hex = false;
        m_hidden = false;
        m_uncached = false;
        m_launched = false;
        m_verbose = false;
        m_dump = false;
        m_dumpPlatforms = false;
        OU::findBool(params, "verbose", m_verbose);
        OU::findBool(params, "dump", m_dump);
        const char *dumpFile;
        if (OU::findString(params, "dumpFile", dumpFile))
          m_dumpFile = dumpFile;
        OU::findBool(params, "dumpPlatforms", m_dumpPlatforms);
        OU::findBool(params, "hex", m_hex);
        OU::findBool(params, "hidden", m_hidden);
        OU::findBool(params, "uncached", m_uncached);
        // Initializations for externals may add instances to the assembly
        initExternals(params);
        // Now that we have added any extra instances for external connections, do
        // instance-related initializations
        m_nInstances = m_assembly.nInstances();
	m_instances.resize(m_nInstances);
        // Check that params that reference instances are valid, and that cannot be
        // checked in the assembly parsing in any case (i.e. do not depend on
        // any library info).
        // Note these checks may ultimately be ignored if we import the deployment
        const char *err;
        if ((err = m_assembly.checkInstanceParams("container", params, false)) ||
            (err = m_assembly.checkInstanceParams("scale", params, false)))
          throw OU::Error("%s", err);
        // We are at the point where we need to either plan or import the deployment.
        const char *dfile = NULL;
        if (m_deployXml || OU::findString(params, "deployment", dfile))
          importDeployment(dfile, m_deployXml, params);
        else
          planDeployment(params);
        // This array is sized and initialized here since it is needed for property finalization
        initLaunchMembers();
        // All the implementation selection is done, so now do the final check of ports
        // and properties since they can be implementation specific
        if ((err = finalizePortParam(params, "portBufferCount")) ||
            (err = finalizePortParam(params, "portBufferSize")) ||
            (err = finalizePortParam(params, "transport")) ||
            (err = finalizePortParam(params, "transferRole")))
          throw OU::Error("Port parameter error: %s", err);
        initLaunchConnections();
        finalizeProperties(params);
        finalizeExternals();
        if (m_verbose) {
          fprintf(stderr, "Actual deployment is:\n");
          auto *d = &m_bestDeployments[0];
          for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++)
            if (d->m_scale > 1) {
              fprintf(stderr,
                      "  Instance %2u %s (spec %s) on %s containers:\n",
                      n, m_assembly.instance(n).name().c_str(),
                      m_assembly.instance(n).specName().c_str(),
                      OC::Container::nthContainer(d->m_containers[0]).
                      m_model.c_str());
              const OL::Implementation **impl = &d->m_impls[0];
              for (unsigned s = 0; s < d->m_scale; s++, impl++) {
                OC::Container &c =
                  OC::Container::nthContainer(d->m_containers[s]);
                std::time_t bd = OS::FileSystem::lastModified((**impl).m_artifact.name());
                char tbuf[30];
                ctime_r(&bd, tbuf);
                fprintf(stderr, "    Member %3u: container %2u: %s using %s%s%s in %s dated %s",
                        s, d->m_containers[s], c.name().c_str(),
                        (**impl).m_metadataImpl.cname(),
                        (**impl).m_staticInstance ? "/" : "",
                        (**impl).m_staticInstance ?
                        ezxml_cattr((**impl).m_staticInstance, "name") : "",
                        (**impl).m_artifact.name().c_str(), tbuf);
              }
            } else {
              d->m_usedContainers.resize(1, UINT_MAX);
              const OL::Implementation &impl = *d->m_impls[0];
              if (impl.m_staticInstance)
                d->m_usedContainers[0] =
		  getUsedContainer(d->m_containers[0]);
              OC::Container &c =
		OC::Container::nthContainer(m_usedContainers[d->m_usedContainers[0]]);
              std::time_t bd = OS::FileSystem::lastModified(impl.m_artifact.name());
              char tbuf[30];
              ctime_r(&bd, tbuf);
              fprintf(stderr,
                      "  Instance %2u %s (spec %s) on %s container %u: %s, using %s%s%s in %s dated %s",
                      n, m_assembly.instance(n).name().c_str(),
                      m_assembly.instance(n).specName().c_str(),
                      c.m_model.c_str(), c.ordinal(), c.name().c_str(),
                      impl.m_metadataImpl.cname(),
                      impl.m_staticInstance ? "/" : "",
                      impl.m_staticInstance ? ezxml_cattr(impl.m_staticInstance, "name") : "",
                      impl.m_artifact.name().c_str(), tbuf);
	    }
	  const OU::Port *p;
	  for (unsigned nn = 0; (p = getMetaPort(nn)); nn++) {
	    if (nn == 0)
	      fprintf(stderr, "External ports:\n");
	    fprintf(stderr, " %u: application port \"%s\" is %s\n", nn,
		    p->OU::Port::m_name.c_str(), p->m_provider ? "input" : "output");
	  }
        }
      } catch (...) {
        clear();
        throw;
      }
      m_constructed = OS::Time::now();
      if (m_verbose)
	fprintf(stderr,
		"Application XML parsed and deployments (containers and artifacts) chosen%s\n",
		timeDiff(m_constructed, m_earliest));
    }

    void ApplicationI::
    setLaunchPort(OC::Launcher::Port &p, const OU::Port *mp, const OU::PValue *connParams,
                  const std::string &a_name, const OU::PValue *portParams,
                  const OC::Launcher::Member *member, const OU::Assembly::External *ep,
                  size_t scale, size_t index) {
      p.m_scale = scale == 1 ? 0 : scale; // zero means no scaling/bridging/fanin/fanout
      p.m_index = index;
      p.m_member = member;
      p.m_metaPort = mp;
      if (member) {
        p.m_name = a_name.c_str();
        p.m_params.add(connParams, portParams);
      } else if (ep) {
        p.m_params = ep->m_parameters; // FIXME: are connparams being missed here?
        if (ep->m_url.length())
          p.m_url = ep->m_url.c_str();
        else
          p.m_name = ep->m_name.c_str();
      }
    }

    static void
    setLaunchTransport(OC::Launcher::Connection &lc, const OU::PValue *inParams,
                       const OU::PValue *outParams, const OU::PValue *cParams) {
      // Now finalize the transport selection
      // FIXME: cache results for same inputs
      // Check for collocated ports
      ocpiInfo("Negotiating connection from instance %s (in %s) port %s to instance %s (in %s) port %s "
               "(buffer size is %zu/0x%zx)",
               lc.m_out.m_member ? lc.m_out.m_member->m_name.c_str() : "<external>",
               lc.m_out.m_container ? lc.m_out.m_container->cname() : "<none>", lc.m_out.m_name,
               lc.m_in.m_member ? lc.m_in.m_member->m_name.c_str() : "<external>",
               lc.m_in.m_container ? lc.m_in.m_container->cname() : "<none>", lc.m_in.m_name,
               lc.m_bufferSize, lc.m_bufferSize);
      if (lc.m_in.m_container && lc.m_out.m_container &&
          lc.m_in.m_container != lc.m_out.m_container &&
          (!lc.m_in.m_container->portsInProcess() ||
           !lc.m_out.m_container->portsInProcess())) {
        ocpiDebug("Input container: %s, output container: %s",
                  lc.m_in.m_container->name().c_str(), lc.m_out.m_container->name().c_str());
        OC::BasicPort::
          determineTransport(lc.m_in.m_container->transports(),
                             lc.m_out.m_container->transports(),
                             inParams, outParams, cParams, lc.m_transport);
        assert(lc.m_transport.transport.length());
      }
    }
    // Find the launch connection
    const OC::Launcher::Connection &ApplicationI::
    findOtherConnection(const OC::Launcher::Port &p) {
      const OC::Launcher::Connection *lc = &m_launchConnections[0];
      for (unsigned n = 0; n < m_launchConnections.size(); n++, lc++)
        if (&p != &lc->m_in && &p != &lc->m_out &&
            ((lc->m_in.m_member == p.m_member &&
              lc->m_in.m_metaPort->m_ordinal == p.m_metaPort->m_bufferSizePort) ||
            ((lc->m_out.m_member == p.m_member &&
              lc->m_out.m_metaPort->m_ordinal == p.m_metaPort->m_bufferSizePort))))
          return *lc;
      assert("missing connection for buffersizeport"==0);
      return *lc;
    }
    // Initialize our own database of connections from the OU::Assembly connections
    // This can be done before any resources are actually allocated.  It is just
    // building the launch database.  finalizeLaunchConnections must be done after
    // containers are established for instances.
    void ApplicationI::
    initLaunchConnections() {
      // For each instance connection we need to compute how many members each side will
      // connect to on the other side.  I.e. at each member port, how many on the other
      // side will it be talking to.  In most cases you talk to everyone on the other side.
      // Basically we need a function which returns which on the other side we will talk
      // to.  We'll use a map.
      // Pass 1: figure out how many member connections we will have
      size_t nMemberConnections = 0;
      for (auto ci = m_bestConnections.begin(); ci != m_bestConnections.end(); ++ci) {
        Deployment *dIn = NULL, *dOut = NULL;
        for (auto pi = (*ci).m_ports.begin(); pi != (*ci).m_ports.end(); ++pi) {
          OU::Assembly::Role &r = (*pi).first->m_role;
          assert(r.m_knownRole && !r.m_bidirectional);
          (r.m_provider ? dIn : dOut) = &m_bestDeployments[(*pi).first->m_instance];
        }
        nMemberConnections += (dIn ? dIn->m_crew.m_size : 1) * (dOut ? dOut->m_crew.m_size : 1);
      }
      // Pass 1a: count the connections required that are internal to an instance crew
      auto *d = &m_bestDeployments[0];
      for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++) {
        const OU::Worker &firstImpl = d->m_impls[0]->m_metadataImpl;
        unsigned nPorts;
        OU::Port *p = firstImpl.ports(nPorts);
        for (unsigned nn = 0; nn < nPorts; nn++, p++)
          if (p->m_isInternal) {
            if (!p->m_isOptional || d->m_scale > 1)
              nMemberConnections += d->m_scale * d->m_scale;
            p++, nn++; // always skip one after an internal since that's the other half.
          }
      }
      // Pass 2: make the array and fill it in, also negotiate buffer sizes and transports
      m_launchConnections.resize(nMemberConnections);
      OC::Launcher::Connection *lc = &m_launchConnections[0];
      for (auto ci = m_bestConnections.begin(); ci != m_bestConnections.end(); ++ci) {
        const OU::Assembly::Port *aIn = NULL, *aOut = NULL;
        Deployment *dIn = NULL, *dOut = NULL;
        OU::Port *pIn = NULL, *pOut = NULL;
        size_t inScale = 1, outScale = 1;
        for (auto pi = (*ci).m_ports.begin(); pi != (*ci).m_ports.end(); ++pi) {
	  auto &ap = *(*pi).first;
          d = &m_bestDeployments[ap.m_instance];
          OU::Port *p =
            d->m_impls[0]->m_metadataImpl.findMetaPort(ap.m_name.c_str());
          assert(p);
          if (ap.m_role.m_provider) {
            aIn = &ap;
            dIn = d;
            pIn = p;
            inScale = d->m_crew.m_size;
          } else {
            aOut = &ap;
            dOut = d;
            pOut = p;
            outScale = d->m_crew.m_size;
          }
        }
        OU::Assembly::External *e = NULL;
        const OU::PValue *eParams = NULL;
        if ((*ci).m_externals.size()) {
          e = (*ci).m_externals.front().first;
          eParams = e->m_parameters;
          if (pIn)
            pOut = pIn;
          else
            pIn = pOut;
          m_externals.insert(ExternalPair(e->m_name.c_str(), External(*lc)));
        }
        const OU::PValue *connParams = (*ci).m_parameters;
        for (unsigned nIn = 0; nIn < inScale; nIn++) {
          OC::Launcher::Member *mIn = aIn ? &m_launchMembers[dIn->m_firstMember + nIn] : NULL;
          for (unsigned nOut = 0; nOut < outScale; nOut++, lc++) {
            OC::Launcher::Member *mOut = aOut ? &m_launchMembers[dOut->m_firstMember + nOut] : NULL;
            setLaunchPort(lc->m_in, pIn, connParams, pIn->m_name,
                          aIn ? aIn->m_parameters.list() : NULL, mIn, e, inScale, nIn);
            setLaunchPort(lc->m_out, pOut, connParams, pOut->m_name,
                          aOut ? aOut->m_parameters.list() : NULL, mOut, e, outScale, nOut);
            setLaunchTransport(*lc, aIn ? (const OU::PValue *)aIn->m_parameters : eParams,
                               aOut ? (const OU::PValue *)aOut->m_parameters : eParams,
                               (*ci).m_parameters);
          }
        }
      }
      // Pass 2a: add the internal connections
      d = &m_bestDeployments[0];
      for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++) {
        const OU::Worker &firstImpl = d->m_impls[0]->m_metadataImpl;
        size_t scale = d->m_scale;
        unsigned nPorts;
        OU::Port *p = firstImpl.ports(nPorts);
        for (unsigned nn = 0; nn < nPorts; nn++, p++)
          if (p->m_isInternal) {
            if (!p->m_isOptional || d->m_scale > 1) {
              // FIXME: any point in allowing buffer count override?
              for (unsigned nIn = 0; nIn < scale; nIn++) {
                OC::Launcher::Member *mIn = &m_launchMembers[d->m_firstMember + nIn];
                for (unsigned nOut = 0; nOut < scale; nOut++, lc++) {
                  OC::Launcher::Member *mOut = &m_launchMembers[d->m_firstMember + nOut];
                  setLaunchPort(lc->m_in, p, NULL, p->m_name, NULL, mIn, NULL, scale, nIn);
                  setLaunchPort(lc->m_out, p+1, NULL, (p+1)->m_name, NULL, mOut, NULL, scale,
                                nOut);
                  setLaunchTransport(*lc, NULL, NULL, NULL);
                  ocpiDebug("Internal connection %p on %s/%s-%s %u/%u", lc,
                            firstImpl.cname(), p->name().c_str(), (p+1)->name().c_str(),
                            nIn, nOut);
                }
              }
            }
            p++, nn++; // always skip one after an internal since that's the other half.
          }
      }
      // Perform buffer size negotiations including propagating buffer sizes between ports
      // of an instance that has said that one port's buffer size should be based on other port's
      // buffer size.  In two steps:
      // 1. Negotiate connections that do *not* have ports with cross-port buffersize references
      // 2. Negotiate connections that *do* have ports with cross-port buffersize references,
      //    if the connection of the cross port has been negotiated
      // 3. Repeat #2 until no propagation progress is being made.

      // Pass 1: set the buffer size for all connections that do not have ports with cross-port refs
      //         and in the same pass record connections for cross-port buffersize references.
      lc = &m_launchConnections[0];
      for (unsigned n = 0; n < m_launchConnections.size(); n++, lc++)
        if (lc->m_bufferSize == SIZE_MAX &&
            lc->m_in.m_metaPort->m_bufferSizePort == SIZE_MAX &&
            lc->m_out.m_metaPort->m_bufferSizePort == SIZE_MAX)
          lc->m_bufferSize =
            OU::Port::determineBufferSize(lc->m_in.m_metaPort, lc->m_in.m_params, SIZE_MAX,
                                          lc->m_out.m_metaPort, lc->m_out.m_params, SIZE_MAX, NULL);
        else {
          if (lc->m_in.m_metaPort->m_bufferSizePort != SIZE_MAX)
            lc->m_in.m_otherConn = &findOtherConnection(lc->m_in);
          if (lc->m_out.m_metaPort->m_bufferSizePort != SIZE_MAX)
            lc->m_out.m_otherConn = &findOtherConnection(lc->m_out);
        }
      // Pass 2 and beyond:  propagate buffer sizes from connections that are sized to ones that are not
      bool workDone;
      do {
        workDone = false;
        lc = &m_launchConnections[0];
        for (unsigned n = 0; n < m_launchConnections.size(); n++, lc++)
          if (lc->m_bufferSize == SIZE_MAX &&
              (!lc->m_in.m_otherConn || lc->m_in.m_otherConn->m_bufferSize != SIZE_MAX) &&
              (!lc->m_out.m_otherConn || lc->m_out.m_otherConn->m_bufferSize != SIZE_MAX)) {
            lc->m_bufferSize =
              OU::Port::determineBufferSize(lc->m_in.m_metaPort, lc->m_in.m_params,
                                            lc->m_in.m_otherConn ? lc->m_in.m_otherConn->m_bufferSize : SIZE_MAX,
                                            lc->m_out.m_metaPort, lc->m_out.m_params,
                                            lc->m_out.m_otherConn ? lc->m_out.m_otherConn->m_bufferSize : SIZE_MAX,
                                            NULL);
            // This connection can be negotiated now
            workDone = true;
          }
      } while (workDone);
      // Create an ordered set of pointers into the Externals
      m_externalsOrdered.resize(m_externals.size());
      External **e = &m_externalsOrdered[0];
      for (ExternalsIter ei = m_externals.begin(); ei != m_externals.end(); ++ei)
        *e++ = &(*ei).second;
    }
    void ApplicationI::
    finalizeLaunchPort(OC::Launcher::Port &p) {
      if (p.m_member)
        p.m_container = p.m_member->m_container;
      else if (p.m_name) { // external port
        p.m_container = &OC::Container::baseContainer();
        p.m_containerApp =
          m_containerApps[getUsedContainer(p.m_container->ordinal())];
      }
      if (p.m_container)
        p.m_launcher = &p.m_container->launcher();
    }
    // Finalize the launch connections, which depends on containers being established
    // for the instances.
    void ApplicationI::
    finalizeLaunchConnections() {
      OC::Launcher::Connection *lc = &m_launchConnections[0];
      for (unsigned n = 0; n < m_launchConnections.size(); n++, lc++) {
        finalizeLaunchPort(lc->m_in);
        finalizeLaunchPort(lc->m_out);
        // FIXME: can we nuke these three param args?
        setLaunchTransport(*lc, lc->m_in.m_params, lc->m_out.m_params, NULL);
      }
    }

    // Create the instance array for the launcher, which is flattened to have an instance
    // per member rather than an instance per app instance.
    void ApplicationI::
    initLaunchMembers() {
      auto *d = &m_bestDeployments[0];
      size_t nMembers = 0;
      for (size_t n = 0; n < m_bestDeployments.size(); n++, nMembers += d->m_scale, d++)
        d->m_firstMember = nMembers;
      m_launchMembers.resize(nMembers);
      d = &m_bestDeployments[0];
      OC::Launcher::Member *li = &m_launchMembers[0];
      for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++)
        for (unsigned m = 0; m < d->m_scale; m++, li++) {
          if (d->m_scale == 1)
            li->m_name = d->m_name;
          else
            OU::format(li->m_name, "%s.%u", d->m_name.c_str(), m);
          li->m_impl = d->m_impls[m];
          li->m_hasMaster = d->m_hasMaster;
          assert(!d->m_hasMaster || d->m_scale == 1);
          if ((unsigned)m_assembly.m_doneInstance == n)
            li->m_doneInstance = true;
          // We do not support scalable proxies.  checked elsewhere
          assert(d->m_slaves.empty() || d->m_scale == 1);
          // Initialize the slaves in the order declared by the proxy
          if (d->m_slaves.size()) {
            li->m_slaves.resize(d->m_slaves.size());
            li->m_slaveWorkers.resize(d->m_slaves.size());
	    for (unsigned s = 0; s < d->m_slaves.size(); ++s)
	      if (d->m_slaves[s] != UINT_MAX)
		li->m_slaves[s] = &m_launchMembers[m_bestDeployments[d->m_slaves[s]].m_firstMember];
          }
          li->m_member = m;
          d->m_crew.m_size = d->m_scale;
          li->m_crew = &d->m_crew;
        }
    }

    // Do the part of initializing launch instances that depends on containers established.
    void ApplicationI::
    finalizeLaunchMembers() {
      auto *d = &m_bestDeployments[0];
      OC::Launcher::Member *li = &m_launchMembers[0];
      for (unsigned n = 0; n < m_bestDeployments.size(); n++, d++)
        for (unsigned m = 0; m < d->m_scale; m++, li++) {
          li->m_containerApp = m_containerApps[d->m_usedContainers[m]];
          li->m_container = m_containers[d->m_usedContainers[m]];
        }
    }

    void ApplicationI::
    initExternals( const PValue * params ) {
      // Check that params that reference externals are valid.
      //      checkExternalParams("file", params);
      checkExternalParams("device", params);
      checkExternalParams("url", params);
    }
    bool
    ApplicationI::Instance::foundContainer(OCPI::Container::Container &c) {
      m_curMap |= 1u << c.ordinal();
      //      m_curContainers++;
      return false;
    }

    // Support querying the application for its ports for internal tools
    // Return a pointer or null, based on ordinal
    // The caller does:
    //    OU::Port *p;
    //    for(unsigned n = 0; app.getMetaPort(n); n++)
    //       do-something-with-p
    const OU::Port *ApplicationI::
    getMetaPort(unsigned n) const {
      if (n >= m_externalsOrdered.size())
        return NULL;
      OC::Launcher::Connection &lc = m_externalsOrdered[n]->m_connection;
      return lc.m_in.m_member ? lc.m_out.m_metaPort : lc.m_in.m_metaPort;
    }

    void ApplicationI::
    initialize() {
      m_nInstances = m_assembly.nInstances();
      ocpiDebug("Mapped %zu instances to %d containers", m_nInstances, m_nContainers);

      m_containers = new OC::Container *[m_nContainers];
      m_containerApps = new OC::Application *[m_nContainers];
      for (unsigned n = 0; n < m_nContainers; n++) {
        m_containers[n] = &OC::Container::nthContainer(m_usedContainers[n]);
        m_containerApps[n] = static_cast<OC::Application*>(m_containers[n]->createApplication());
        m_containerApps[n]->setApplication(&m_apiApplication);
      }
      finalizeLaunchMembers();
      finalizeLaunchConnections();
      OC::Launcher &local = OC::LocalLauncher::getSingleton();
      // First pass, record all the launchers, and do initial launch for the local containers.
      // This allows initial connection processing locally to avoid unnecessary round-trips
      // with remote launchers that have connections to local workers.
      for (unsigned n = 0; n < m_nContainers; n++)
        if (m_launchers.insert(&m_containers[n]->launcher()).second &&
            &m_containers[n]->launcher() == &local)
          m_containers[n]->launcher().launch(m_launchMembers, m_launchConnections);
      // Second pass, do initial launch on remote launchers
      for (auto li = m_launchers.begin(); li != m_launchers.end(); li++)
        if (*li != &local)
          (*li)->launch(m_launchMembers, m_launchConnections);
      bool more;
      do {
        more = false;
        for (auto li = m_launchers.begin(); li != m_launchers.end(); li++)
          if ((*li)->work(m_launchMembers, m_launchConnections))
            more = true;
      } while (more);
      for (unsigned n = 0; n < m_launchConnections.size(); n++) {
        OC::Launcher::Connection &c = m_launchConnections[n];
        if ((!c.m_in.m_url && !c.m_in.m_member) || (!c.m_out.m_url && !c.m_out.m_member))
          m_externals.insert(ExternalPair(c.m_in.m_member ? c.m_out.m_name : c.m_in.m_name,
                                          External(c)));
      }
      m_launched = true;
      m_initialized = OS::Time::now();
      if (m_verbose) {
	if (m_launchConnections.size()) {
#if 0
	  fprintf(stderr, "Connections between containers:\n");
	  OC::Launcher::Connection *lc = &m_launchConnections[0];
	  for (unsigned n = 0; n < m_launchConnections.size(); n++, lc++)
	    if (!lc->m_out.m_member || !lc->m_in.m_member ||
		lc->m_out.m_member->m_container != lc->m_in.m_member->m_container)
	      fprintf(stderr, "  From \"%s\" port \"%s\" (%zu buffers) to \"%s\" port \"%s\" "
		      "(%zu buffers) with buffer size %zu, using transport \"%s\"\n",
		      lc->m_out.m_member ? lc->m_out.m_member->m_name.c_str() : "<external>",
		      lc->m_out.m_name, lc->m_out.m_port->nBuffers(),
		      lc->m_in.m_member ? lc->m_in.m_member->m_name.c_str() : "<external>",
		      lc->m_in.m_name, lc->m_in.m_port->nBuffers(), lc->m_bufferSize,
		      lc->m_transport.transport.empty() ? "<none>" : lc->m_transport.transport.c_str());
#endif
	}
        fprintf(stderr,
                "Application established: containers, workers, connections all created%s\n",
		timeDiff(m_initialized, m_constructed));
      }
      m_initialized = OS::Time::now();
    }
    static void addAttr(std::string &out, bool attr, const char *string, bool last = false) {
      if (attr)
        OU::formatAdd(out, "%s%s", out.empty() ? " (" : ", ", string);
      if (last && out.size())
        out += ")";
    }
    void ApplicationI::
    dumpProperties(bool printParameters, bool printCached, const char *context) const {
      std::string value;
      if (m_verbose)
        fprintf(stderr, "Dump of all %s%sproperty values:\n",
                context ? context : "", context ? " " : "");
      PropertyAttributes attrs;
      for (unsigned n = 0; getProperty(n, value, AccessList({}),
                                       PropertyOptionList({m_hex ? HEX : NONE, UNREADABLE_OK}), &attrs); ++n)
        if ((printParameters || attrs.isVolatile || attrs.isWritable) &&
            (m_hidden || !attrs.isHidden) && (printCached || !attrs.isCached || attrs.isWritable)) {
          fprintf(stderr, "Property %3u: %s = \"%s\"", n, attrs.name.c_str(), value.c_str());
          std::string out;
          addAttr(out, attrs.isParameter, "parameter");
          addAttr(out, attrs.isCached, "cached");
          addAttr(out, attrs.isDebug, "debug");
          addAttr(out, attrs.isHidden, "hidden");
          addAttr(out, attrs.isHidden, "worker");
          addAttr(out, attrs.isUnreadable, "unreadable", true);
          fprintf(stderr, "%s\n", out.c_str());
        }
    }
    void ApplicationI::
    startMasterSlave(bool isMaster, bool isSlave, bool isSource) {
      for (unsigned n = 0; n < m_nContainers; n++)
        m_containerApps[n]->startMasterSlave(isMaster, isSlave, isSource);
    }
    void ApplicationI::start() {
      if (!m_launched)
        throw OU::Error("OA::Application::start() called before/without calling initialize().");
      if (m_dump)
        dumpProperties(true, true, "initial");
      if (m_dumpPlatforms)
        for (unsigned n = 0; n < m_nContainers; n++)
          m_containers[n]->dump(true, m_hex);
      ocpiInfo("Using %d containers to support the application", m_nContainers );
      ocpiInfo("Starting master workers that are not slaves.");
      startMasterSlave(true, false, false);  // 4
      startMasterSlave(true, false, true);   // 5
      ocpiInfo("Starting master workers that are also slaves, but not sources.");
      startMasterSlave(true, true, false);   // 6
      ocpiInfo("Starting master workers that are also slaves and are sources.");
      startMasterSlave(true, true, true);    // 7
      ocpiInfo("Starting workers that are not masters and not sources.");
      startMasterSlave(false, false, false); // 0
      startMasterSlave(false, true, false);  // 2
      ocpiInfo("Starting workers that are sources.");
      startMasterSlave(false, false, true);  // 1
      startMasterSlave(false, true, true);   // 3
      m_started = OS::Time::now();
      // Note: this does not start masters that are sources.
      if (m_verbose)
        fprintf(stderr, "Application started/running%s\n", timeDiff(m_started, m_initialized));
      m_started = OS::Time::now();
    };
    void ApplicationI::stop() {
      ocpiDebug("Stopping master workers that are not slaves.");
      for (unsigned n = 0; n < m_nContainers; n++)
        m_containerApps[n]->stop(true, false); // stop masters that are not slaves
      ocpiDebug("Stopping master workers that are also slaves.");
      for (unsigned n = 0; n < m_nContainers; n++)
        m_containerApps[n]->stop(true, true);  // stop masters that are slaves
      ocpiDebug("Stopping workers that are not masters.");
      for (unsigned n = 0; n < m_nContainers; n++)
        m_containerApps[n]->stop(false, false); // stop non-masters
    }
    void ApplicationI::
    setDelayedProperties() {
      if (m_delayedPropertyValues.size()) {
        if (m_verbose)
          fprintf(stderr, "Setting delayed property values while application is running.\n");
        OU::Assembly::Delay now = 0;
        for (auto it = m_delayedPropertyValues.begin();
             it != m_delayedPropertyValues.end(); ++it) {
          if (it->first > now) {
            usleep(it->first - now);
            now = it->first;
          }
          if (OS::logWillLog(OCPI_LOG_DEBUG)) {
            std::string uValue;
            it->second.m_value.unparse(uValue);
            ocpiDebug("Setting property \"%s\" of instance \"%s\" (worker \"%s\") after %f seconds to \"%s\"",
                      it->second.m_property->cname(),
                      m_assembly.instance(it->second.m_instance).name().c_str(),
                      m_launchMembers[m_bestDeployments[it->second.m_instance].m_firstMember].m_worker->cname(),
                      now/1.e6, uValue.c_str());
          }
          // FIXME: fan out of value to crew, and stash instance ptr, not index...
          m_launchMembers[m_bestDeployments[it->second.m_instance].m_firstMember].m_worker->
            setProperty(it->second.m_property->m_ordinal, it->second.m_value);
        }
        m_delayedPropertyValues.clear();
      }
    }
    bool ApplicationI::wait(OS::Timer *timer) {
      if (m_assembly.m_doneInstance != UINT_MAX) {
        OC::Launcher::Member *m =
	  &m_launchMembers[m_bestDeployments[m_assembly.m_doneInstance].m_firstMember];
        if (m->m_crew->m_size > 1) {
          ocpiInfo("Waiting for \"done\" worker, \"%s\" (%zu members), to finish",
                   m->m_worker->name().c_str(), m->m_crew->m_size);
          do {
            bool done = true;
            m = &m_launchMembers[m_bestDeployments[m_assembly.m_doneInstance].m_firstMember];
            for (unsigned n = (unsigned)m->m_crew->m_size; n; n--, m++) {
              if (!m->m_container->enabled())
                throw OU::Error("Container \"%s\" for worker \"%s\" was shutdown",
                                m->m_container->name().c_str(), m->m_worker->cname());
              if (!m->m_worker->isDone()) {
                done = false;
                break;
              }
            }
            if (done)
              return false;
            OS::sleep(1000);
          } while (!timer || !timer->expired());
        } else {
          ocpiInfo("Waiting for \"done\" worker, \"%s\", to finish",
                   m->m_worker->name().c_str());
          return m->m_worker->wait(timer);
        }
      }
      do {
        bool done = true;
        for (unsigned n = 0; n < m_nContainers; n++)
          if (!m_containerApps[n]->isDone())
            done = false;
        if (done)
          return false;
        OS::sleep(10);
      } while (!timer || !timer->expired());
      return true;
    }

    // Stuff to do after "done" (or perhaps timeout)
    void ApplicationI::finish() {
      const char *err;
      // Dumping all properties into a file MUST BE DONE FIRST here because it is used by unit
      // testing, and when workers are written with read-side-effects for properties, like
      // peak_detect in tutorial, we want the correct values to be here in this properties file,
      // sacrificing the correct values in the normal property dumps.
      // This is not a great way to write workers anyway, but at least this way unit testing works.
      // But for such workers the other two types of property dumps do not work when unit tested:
      // 1. dump-property-value into a file
      // 2. list all final property values
      // Perhaps the better fix would be to tag such properties so we only list them once.
      if (m_dumpFile.size()) {
        std::string value, dump;
        PropertyAttributes attrs;
        for (unsigned n = 0;
             getProperty(n, value, AccessList({}),
                         PropertyOptionList({OA::UNREADABLE_OK,
                               m_hex ? OA::HEX : OA::NONE, m_uncached ? OA::UNCACHED : OA::NONE}),
                         &attrs);
             ++n) {
          auto pos = attrs.name.find('.');
          if (pos != std::string::npos)
            attrs.name[pos] = ' ';
          OU::formatAdd(dump, "%s %s\n", attrs.name.c_str(), value.c_str());
        }
        if ((err = OU::string2File(dump, m_dumpFile)))
          throw OU::Error("error when dumping properties to a file: %s", err);
      }
      Property *p = m_properties;
      for (unsigned n = 0; n < m_nProperties; n++, p++)
        if (p->m_dumpFile) {
          std::string l_name, value;
          m_launchMembers[m_bestDeployments[p->m_instance].m_firstMember].m_worker->
            getProperty(p->m_property, l_name, value, NULL, m_hex);
          value += '\n';
          if ((err = OU::string2File(value, p->m_dumpFile)))
            throw OU::Error("Error writing '%s' property to file: %s", l_name.c_str(), err);
        }
      if (m_dump)
        dumpProperties(false, false, "final");
      if (m_dumpPlatforms)
        for (unsigned n = 0; n < m_nContainers; n++)
          m_containers[n]->dump(false, m_hex);
    }

    // Get an external port to use corresponding to an external port defined in the assembly.
    // This can happen after launch and can have new information for the connection
    // (e.g. transport) as well as for this particular external port (e.g. buffercount).
    // This means we need to parse the params on the fly here since they may be different
    // from what was in the assembly.
    ExternalPort &ApplicationI::
    getPort(const char *a_name, const OA::PValue *params) {
      if (!m_launched)
        throw OU::Error("GetPort cannot be called until the application is initialized.");
      Externals::iterator ei = m_externals.find(a_name);
      if (ei == m_externals.end())
        throw OU::Error("Unknown external port name for application: \"%s\"", a_name);
      External &ext = ei->second;
      if (ext.m_external) {
        if (params)
          ocpiInfo("Parameters ignored when getPort called for same port more than once");
      } else {
        if (params)
          throw OU::Error("Parameters ignored for external port in assembly");
        ext.m_external =
          ext.m_connection.m_in.m_member ?
          ext.m_connection.m_out.m_port : ext.m_connection.m_in.m_port;
        assert(ext.m_external);
      }
      return *static_cast<OC::ExternalPort*>(ext.m_external);
    }

    // The name might have a dot in it to separate instance from property name
    Worker &ApplicationI::getPropertyWorker(const char *a_name, const char *&pname) const {
      const char *dot;
      if (pname || (dot = strchr(a_name, '.'))) {
        size_t len = pname ? strlen(a_name) : (size_t)(dot - a_name);
        for (unsigned n = 0; n < m_nInstances; n++) {
          const char *wname = m_assembly.instance(n).name().c_str();
          if (!strncasecmp(a_name, wname, len) && !wname[len]) {
            Worker *w = m_launchMembers[m_bestDeployments[n].m_firstMember].m_worker;
            if (w)
              return *w;
            throw OU::Error("application is not yet initialized for property access");
          }
        }
        throw OU::Error("Unknown instance name in: %s", a_name);
      }
      Property *p = m_properties;
      for (unsigned n = 0; n < m_nProperties; n++, p++)
        if (!strcasecmp(a_name, p->m_name.c_str())) {
          pname = m_assembly.instance(p->m_instance).properties()[p->m_property].m_name.c_str();
          return *m_launchMembers[m_bestDeployments[p->m_instance].m_firstMember].m_worker;
        }
      throw OU::Error("Unknown application property: %s", a_name);
    }

    static inline const char *maybePeriod(const char *name) {
      const char *cp = strchr(name, '.');
      return cp ? cp + 1 : name;
    }
    // FIXME:  consolidate the constructors (others are in OcpiProperty.cxx) (have in internal class for init)
    // FIXME:  avoid the double lookup since the first one gets us the ordinal
    Property::Property(const Application &app, const char *aname, const char *pname)
      : m_worker(app.getPropertyWorker(aname, pname)),
        m_info(m_worker.setupProperty(pname ? pname : maybePeriod(aname), m_writeVaddr,
                                      m_readVaddr)),
        m_member(m_info) {
      init();
    }
    Property::Property(const Application &app, const std::string &iname, const char *pname)
      : m_worker(app.getPropertyWorker(iname.c_str(), pname)),
        m_info(m_worker.setupProperty(pname ? pname : maybePeriod(iname.c_str()),
                                      m_writeVaddr, m_readVaddr)),
        m_member(m_info) {
      init();
    }
    const OU::Property *ApplicationI::property(unsigned ordinal, std::string &a_name) const {
      if (ordinal >= m_nProperties)
        return NULL;
      Property &p = m_properties[ordinal];
      a_name = p.m_name;
      return
        &m_launchMembers[m_bestDeployments[p.m_instance].m_firstMember].
        m_worker->property(p.m_property);
    }

    const char *ApplicationI::
    getProperty(const char *prop_name, std::string &value, AccessList &list,
                PropertyOptionList &options, PropertyAttributes *attributes) const {
      Property &p = findProperty(prop_name);
      return m_launchMembers[m_bestDeployments[p.m_instance].m_firstMember].m_worker->
        getProperty(p.m_property, value, list, options, attributes);
    }

    const char *ApplicationI::
    getProperty(unsigned ordinal, std::string &value, AccessList &list,
                PropertyOptionList &options, PropertyAttributes *attributes) const {
      if (ordinal >= m_nProperties)
        return NULL;
      Property &p = m_properties[ordinal];
      OC::Worker &w = *m_launchMembers[m_bestDeployments[p.m_instance].m_firstMember].m_worker;
      w.getProperty(p.m_property, value, list, options, attributes);
      if (attributes)
        attributes->name = p.m_name.c_str(); // override the worker-level name
      return value.c_str();
    }
    bool ApplicationI::getProperty(unsigned ordinal, std::string &a_name, std::string &value,
                                   bool hex, bool *parp, bool *cachedp, bool uncached,
                                   bool *hiddenp) const {
      PropertyAttributes attrs;
      if (!getProperty(ordinal, value, {},
                       OA::PropertyOptionList({ hex ? HEX : NONE, uncached ? UNCACHED : NONE }),
                       &attrs))
        return false;
      if (parp)
        *parp = attrs.isParameter;
      if (cachedp)
        *cachedp = attrs.isCached;
      if (hiddenp)
        *hiddenp = attrs.isHidden;
      if (attrs.isUnreadable)
        value = "<unreadable>";
      a_name = attrs.name;
      return true;
    }

    ApplicationI::Property &ApplicationI::
    findProperty(const char * worker_inst_name, const char * prop_name) const {
      std::string nm;
      if (!prop_name) {
        prop_name = worker_inst_name;
        worker_inst_name = NULL;
      }
      if (worker_inst_name) {
        nm = worker_inst_name;
        nm += ".";
        nm += prop_name;
      } else {
        nm = prop_name;
        size_t eq = nm.find('=');
        if (eq != nm.npos)
          nm[eq] = '.';
      }
      Property *p = m_properties;
      for (unsigned n = 0; n < m_nProperties; n++, p++)
        if (!strcasecmp(nm.c_str(), p->m_name.c_str()))
          return *p;
      throw OU::Error("Unknown application property: %s", nm.c_str());
    }

    void ApplicationI::
    getProperty(const char * worker_inst_name, const char * prop_name, std::string &value,
                bool hex) {
      Property &p = findProperty(worker_inst_name, prop_name);
      std::string dummy;
      m_launchMembers[m_bestDeployments[p.m_instance].m_firstMember].m_worker->
        getProperty(p.m_property, dummy, value, NULL, hex);
    }

    void ApplicationI::
    setProperty(const char * worker_inst_name, const char * prop_name, const char *value,
                OA::AccessList &list) {
      Property &p = findProperty(worker_inst_name, prop_name);
      m_launchMembers[m_bestDeployments[p.m_instance].m_firstMember].m_worker->
        setProperty(p.m_property, value, list);
    }

    void ApplicationI::
    dumpDeployment(const char *appFile, const std::string &file) {
      FILE *f = file == "-" ? stdout : fopen(file.c_str(), "w");
      if (!f)
        throw OU::Error("Can't open file \"%s\" for deployment output", file.c_str());
      fprintf(f, "<deployment application='%s'>\n", appFile);
      Instance *i = &m_instances[0];
      for (unsigned n = 0; n < m_nInstances; n++, i++) {
        const OL::Implementation &impl = *i->m_deployment.m_impls[0];
        OC::Container &c =
          OC::Container::nthContainer(m_usedContainers[i->m_deployment.m_usedContainers[0]]);
        fprintf(f,
                "  <instance name='%s' spec='%s' worker='%s' model='%s' container='%s'\n"
                "            artifact='%s'",
                m_assembly.instance(n).name().c_str(), m_assembly.instance(n).specName().c_str(),
                impl.m_metadataImpl.cname(), c.m_model.c_str(), c.name().c_str(),
                impl.m_artifact.name().c_str());
        if (impl.m_staticInstance)
          fprintf(f, " instance='%s'", ezxml_cattr(impl.m_staticInstance, "name"));
        fprintf(f, "/>\n");
      }
      fprintf(f, "</deployment>\n");
      if (f != stdout && fclose(f))
        throw OU::Error("Can't close output file \"%s\".  No space?", file.c_str());
    }

    ApplicationI::Instance::Instance() : m_curMap(0) {
    }
    ApplicationI::Instance::~Instance() {
    }
    ApplicationI::Deployment::
    Deployment()
      : m_scale(0), m_feasible(0) {
    }
    ApplicationI::Deployment::
    ~Deployment() {
    }
    void ApplicationI::Deployment::
    set(const std::string &name, size_t scale, const unsigned *containers,
	const OL::Implementation * const *impls, CMap feasible, bool hasMaster,
	const OU::Assembly::Properties *properties) {
      m_name = name;
      m_scale = scale;
      m_impls.resize(scale);
      m_containers.resize(scale);
      m_hasMaster = hasMaster;
      m_properties = properties;
      for (unsigned n = 0; n < scale; ++n) {
	m_impls[n] = impls[n];
	m_containers[n] = containers[n];
      }
      m_feasible = feasible;
    }
    ApplicationI::Deployment &ApplicationI::Deployment::
    operator=(const ApplicationI::Deployment &d) {
      set(d.m_name, d.m_scale, &d.m_containers[0], &d.m_impls[0], d.m_feasible, d.m_hasMaster,
	  d.m_properties);
      m_slaves = d.m_slaves;
      return *this;
    }
  }
  namespace API {
    OCPI_EMIT_REGISTER_FULL_VAR( "Get Property", OCPI::Time::Emit::DT_u, 1, OCPI::Time::Emit::State, pegp );
    OCPI_EMIT_REGISTER_FULL_VAR( "Set Property", OCPI::Time::Emit::DT_u, 1, OCPI::Time::Emit::State, pesp );

    Application::
    Application(const char *file, const PValue *params)
      : m_application(*new ApplicationI(*this, file, params)) {
    }
    Application::
    Application(const std::string &string, const PValue *params)
      : m_application(*new ApplicationI(*this, string.c_str(), params)) {
    }
    Application::
    Application(ApplicationI &i)
      : m_application(i) {
    }
    ApplicationX::
    ApplicationX(ezxml_t xml, const char *a_name,  const PValue *params)
      : Application(*new ApplicationI(*this, xml, a_name, params)) {
    }
    Application::
    Application(Application &app,  const PValue *params)
      : m_application(*new ApplicationI(*this, app.m_application.assembly(), params)) {
    }

    Application::
    ~Application() { delete &m_application; }

    void Application::
    initialize() { m_application.initialize(); }

    void Application::
    start() { m_application.start(); }

    void Application::
    stop() { m_application.stop(); }

    void Application::
    setDelayedProperties() {
      m_application.setDelayedProperties();
    }
    bool Application::
    wait(unsigned long timeout_us, bool timeOutIsError) {
      return m_application.wait(timeout_us, timeOutIsError);
    }
    bool ApplicationI::
    wait(unsigned long timeout_us, bool timeOutIsError) {
      // FIXME: Right now, delayed properties don't (AV-4901):
      // (a) respect duration/timeout
      // (b) don't get accounted for when delaying timeout_us
      setDelayedProperties();
      OS::Timer *timer =
        timeout_us ? new OS::Timer((uint32_t)(timeout_us/1000000),
                                   (uint32_t)((timeout_us%1000000) * 1000ull))
                   : NULL;
      if (m_verbose) {
        if (timeout_us) {
	  if ((double)timeout_us/1.e6 > 1)
	    fprintf(stderr, "Waiting for up to %g seconds for application to finish%s\n",
		    (double)timeout_us/1.e6, timeOutIsError ? " before timeout" : "");
        } else
          fprintf(stderr, "Waiting for application to finish (no time limit)\n");
      }
      bool r = wait(timer);
      delete timer;
      m_finished = OS::Time::now();
      if (r) {
        if (timeOutIsError) {
          // in the other cases the caller is expected to stop the app and, under timeout
          // has the option of retrying the wait and not stopping
          // the timeout error is considered fatal
          stop();
          throw OU::Error("Application exceeded time limit of %g seconds",
                          (double)timeout_us/1.e6);
        }
        if (m_verbose && (double)timeout_us/1.e6 > 1)
          fprintf(stderr, "Application is now considered finished after waiting %g seconds",
                  (double)timeout_us/1.e6);
      } else if (m_verbose)
            fprintf(stderr, "Application finished");
      if (m_verbose)
	fprintf(stderr, "%s\n", timeDiff(m_finished, m_started));
      return r;
    }

    void Application::
    finish() {
      m_application.finish();
    }

    const std::string &Application::name() const {
      return m_application.name();
    }
    ExternalPort &Application::
    getPort(const char *a_name, const OA::PValue *params) {
      return m_application.getPort(a_name, params);
    }
    bool Application::getProperty(unsigned ordinal, std::string &a_name, std::string &value,
                                  bool hex, bool *parp, bool *cachedp, bool uncached,
                                  bool *hiddenp) {
      return m_application.getProperty(ordinal, a_name, value, hex, parp, cachedp, uncached,
                                       hiddenp);
    }

    void Application::
    getProperty(const char* w, const char* p, std::string &value, bool hex) {
      OCPI_EMIT_STATE_NR( pegp, 1 );
      m_application.getProperty(w, p, value, hex);
      OCPI_EMIT_STATE_NR( pegp, 0 );

    }
    const char *Application::
    getProperty(unsigned ordinal, std::string &value, AccessList &list, PropertyOptionList &options,
                PropertyAttributes *attributes) const {
      return m_application.getProperty(ordinal, value, list, options, attributes);
    }
    const char *Application::
    getProperty(const char *prop_name, std::string &value, AccessList &list,
                PropertyOptionList &options, PropertyAttributes *attributes) const {
      return m_application.getProperty(prop_name, value, list, options, attributes);
    }
    void Application::
    setProperty(const char* w, const char* p, const char *value) {
      OCPI_EMIT_STATE_NR( pesp, 1 );
      m_application.setProperty(w, p, value);
      OCPI_EMIT_STATE_NR( pesp, 0 );

    }
    void Application::
    setProperty(const char* p, const char *value, AccessList &list) {
      OCPI_EMIT_STATE_NR( pesp, 1 );
      m_application.setProperty(NULL, p, value, list);
      OCPI_EMIT_STATE_NR( pesp, 0 );

    }
    Worker &Application::
    getPropertyWorker(const char *a_name, const char *&pname) const {   \
      return m_application.getPropertyWorker(a_name, pname);
    }

    void Application::
    dumpDeployment(const char *appFile, const std::string &file) {
      return m_application.dumpDeployment(appFile, file);
    }

    void Application::
    dumpProperties(bool printParameters, bool printCached, const char *context) const {
      return m_application.dumpProperties(printParameters, printCached, context);
    }
    // Type-specific scalar property value setters.
    #define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)         \
    template <> void Application::                                         \
    setPropertyValue<run>(const char *w, const char *p, const run value, AccessList &l) const { \
      Property prop(*this, w, p);                                          \
      ocpiDebug("Application::setPropertyValue on %s %s->%s\n", prop.m_info.cname(),    \
                OU::baseTypeNames[OCPI_##pretty], OU::baseTypeNames[prop.m_info.m_baseType]); \
      prop.setValue<run>(value, l);                                     \
    }
    OCPI_PROPERTY_DATA_TYPES
    #undef OCPI_DATA_TYPE
    template <> void Application::
    setPropertyValue<std::string>(const char *w, const char *p, const std::string value,
                                  AccessList &l) const {
      Property prop(*this, w, p);
      prop.setValue<OA::String>(value.c_str(), l);
    }
    #undef OCPI_DATA_TYPE_S
    #define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)      \
    template <> run Application::                                       \
    getPropertyValue<run>(const char *w, const char *p, AccessList &l) const {  \
      Property prop(*this, w, p);                                       \
      return prop.getValue<run>(l);                                     \
    }
    #define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)    \
    template <> std::string Application::                               \
    getPropertyValue<std::string>(const char *w, const char *p, AccessList &l) const { \
      Property prop(*this, w, p);                                       \
      return prop.getValue<std::string>(l);                             \
    }
    OCPI_PROPERTY_DATA_TYPES

#if 1
#ifdef __APPLE__
    template <> long Application::
    getPropertyValue<long>(const char *w, const char *p, AccessList &l) const {
      Property prop(*this, w, p);
      return prop.getValue<long>(l);
    }
    template <> unsigned long Application::
    getPropertyValue<unsigned long>(const char *w, const char *p, AccessList &l) const {
      Property prop(*this, w, p);
      return prop.getValue<unsigned long>(l);
    }
#endif
#endif
  }
}
