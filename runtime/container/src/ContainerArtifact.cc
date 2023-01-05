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

#include "LibraryAssembly.hh"
#include "OcpiContainerApi.hh"
#include "ContainerWorker.hh"
#include "ContainerApplication.hh"
#include "ContainerArtifact.hh"
#include "Container.hh"

namespace OL = OCPI::Library;
namespace OA = OCPI::API;
namespace OU = OCPI::Util;
namespace OB = OCPI::Base;
namespace OC = OCPI::Container;
namespace OX = OCPI::Util::EzXml;

namespace OCPI {
  namespace Container {
    Artifact::Artifact(OL::Artifact &lart, const OB::PValue *)
      : m_libArtifact(lart), m_application(NULL) {
      m_instanceInUse.resize(lart.nWorkers(), 0);
      m_loadTimeWorkers.resize(lart.nWorkers(), NULL);
      // FIXME: ref count loads from library artifact?
    }
    Artifact::~Artifact() {
    }
    // This deletion is not done during overall shutdown so we know that the m_application is not
    // destroyed by the parent/child container/artifact shutdown process
    void Artifact::unload() {
      delete m_application; // will delete loadtime workers
      m_application = NULL;
    }

    // Shared method between load time and app time.  Construct and initialize
    Worker &Artifact::
    addWorker(Application &app, const char *instName, const OL::Implementation &impl,
	      const OC::Workers &slaves, bool hasMaster, size_t member, size_t crewSize,
	      const OCPI::Base::PValue *wParams) {
      if (impl.m_staticInstance && m_instanceInUse[impl.m_ordinal])
	throw OU::Error("Worker instance named \"%s\" for worker \"%s\" in artifact \"%s\" "
			"is already in use?",
			instName ? instName : "<dynamic>", impl.m_metadataImpl.cname(),
			impl.m_artifact.name().c_str());
      // Call the method in the derived class
      Worker &w = app.createWorker(this, instName, impl.m_metadataImpl.m_xml, impl.m_staticInstance,
				   slaves, hasMaster, member, crewSize, wParams);
      m_instanceInUse[impl.m_ordinal]++;
      w.initialize();
      m_workers[&w] = impl.m_ordinal;  // remember that this worker uses this artifact
      return w;
    }

    Worker &Artifact::
    addLoadTimeWorker(const OL::Implementation &impl, unsigned n) {
      if (!m_application)
	m_application = &container().createApplication("__whenLoaded")->containerApplication();
      std::string instName;
      OU::format(instName, "whenLoaded_%s_%s%s%u", impl.m_metadataImpl.cname(),
		 impl.m_staticInstance ? ezxml_cattr(impl.m_staticInstance, "name") : "",
		 impl.m_staticInstance ? "_" : "", n);
      static OC::Workers noSlaves;
      Worker &w = addWorker(*m_application, instName.c_str(), impl, noSlaves, false, 0, 1, NULL);
      m_loadTimeWorkers[n] = &w;
      return w;
    }

    void Artifact::
    configure() {
      // Create the loadtime workers
      const OL::Implementation *i;
      for (unsigned n = 0; (i = libArtifact().getImplementation(n)); n++) {
	bool loadTime = false;
	const char *err;
	if ((err = OX::getBoolean(i->m_staticInstance, "loadtime", &loadTime, true))) {
	  ocpiBad("Invalid \"loadTime\" attribute in system.xml for container \"%s\": %s",
		  container().cname(), err);
	  continue;
	}
	// Add adapters and devices, but not interconnects
	if (loadTime || (i->m_inserted && i->m_staticInstance &&
			 strcmp(i->m_staticInstance->name, "interconnect")))
	  addLoadTimeWorker(*i, n);
      }
      // Configure loadtime workers
      for (ezxml_t x = ezxml_cchild(container().configXml(), "instance"); x; x = ezxml_cnext(x)) {
	const char
	  *spec = ezxml_cattr(x, "component"),
	  *l_worker = ezxml_cattr(x, "worker"), // match the worker
	  *device = ezxml_cattr(x, "device"); // match the device (device instance)
	for (unsigned n = 0; (i = libArtifact().getImplementation(n)); n++) {
	  // for instances in the artifact
	  if (!m_loadTimeWorkers[n] ||
	      (spec && strcasecmp(spec, i->m_metadataImpl.specName().c_str())) ||
	      !OL::instanceMatchesImpl(i->m_metadataImpl, i->m_staticInstance, l_worker, device))
	    continue;
	  m_loadTimeWorkers[n]->configure(x);
	}
      }
      // Start loadtime workers whether configured or not
      for (auto it = m_loadTimeWorkers.begin(); it != m_loadTimeWorkers.end(); ++it)
	if (*it)
	  (*it)->start();
    }

    Worker &Artifact::
    createWorker(Application &app, const OL::Implementation &impl, const char *appInstName,
		 const OC::Workers &slaves, bool hasMaster, size_t member, size_t crewSize,
		 const OCPI::Base::PValue *wParams) {
      if (m_loadTimeWorkers[impl.m_ordinal])
	// This worker instance is a load-time one and will persist, and its parent is *not*
	// the app of the first argument.
	return *m_loadTimeWorkers[impl.m_ordinal];
      ezxml_t configXml = NULL;
      for (ezxml_t x = ezxml_cchild(container().configXml(), "instance"); x; x = ezxml_cnext(x)) {
	const char
	  *spec = ezxml_cattr(x, "component"),
	  *worker = ezxml_cattr(x, "worker"), // match the worker
	  *device = ezxml_cattr(x, "device"); // match the device (device instance)
	if (!(spec && strcasecmp(spec, impl.m_metadataImpl.specName().c_str())) &&
	    OL::instanceMatchesImpl(impl.m_metadataImpl, impl.m_staticInstance, worker, device)) {
	  configXml = x;
	  break;
	}
      }
      Worker &w = addWorker(app, appInstName, impl, slaves, hasMaster, member, crewSize, wParams);
      w.configure(configXml);
      return w;
    }

    // The (container) application is telling us that this worker is going away.
    void Artifact::removeWorker(Worker &w) {
      ocpiDebug("Removing worker %s instance %s from artifact %s",
		w.implTag().c_str(), w.instTag().c_str(), name().c_str());
      auto found = m_workers.find(&w);
      assert(found != m_workers.end());
      assert(m_instanceInUse[found->second]);
      if (!--m_instanceInUse[found->second] && !m_loadTimeWorkers[found->second])
	m_workers.erase(found);
    }
    bool Artifact::hasArtifact(const void *art) {
      return (OL::Artifact *)(art) == &m_libArtifact;
      }
  }
}
