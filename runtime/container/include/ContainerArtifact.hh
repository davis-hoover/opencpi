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
 * Abstract:
 *   This file contains the interface for the CPi Artifact class
 *
 * Revision History: 
 * 
 *    Author: Jim Kulp
 *    Date: 7/2009
 *    Revision Detail: Created
 *
 */

#ifndef CONTAINER_ARTIFACT_H
#define CONTAINER_ARTIFACT_H
#include <list>
#include "ezxml.h"
#include "LibraryManager.hh"

namespace OCPI {

  namespace Container {

    // An artifact loaded into the container.
    // The OCPI::Library::Artifact represents the artifact in a library whether or
    // not it is loaded.  This class represents that class actually loaded in this
    // container.
    class Interface;
    class Worker;
    class Artifact {
      friend class Application;
      friend class Interface;
      friend class Worker;
      // This map is to remember which workers (which are owned by their container apps),
      // are using the artifact, and mapping the worker object address to its ordinal in the artifact
      std::map<Worker *, unsigned> m_workers; // what workers exist created based on this loaded artifact
      OCPI::Library::Artifact &m_libArtifact;
      // Artifacts contain (maybe reentrant) implementations and static instances.
      // Most of these are dormant after artifact loading until they are used for app workers
      // Reentrant implementations can support multiple workers at a time.
      // Non-reentrant implementations can support only one worker at a time.
      // Static instances of implementations can support one worker at a time.
      // So we have both implementations and static instances.
      std::vector<size_t> m_instanceInUse; // record count of usage of instance
      std::vector<Worker *> m_loadTimeWorkers; // Workers that were established upon load
      Application *m_application; // a container app to own workers created at load time
    protected:
      Artifact(OCPI::Library::Artifact &lart, const OCPI::Base::PValue *props = NULL);
      void removeWorker(Worker &);
    public:
      // Make sure this is loaded and ready to execute in case it was unloaded
      virtual void ensureLoaded() {}
      virtual void unload(); // Any override must call this base class method too
      const OCPI::Library::Artifact &libArtifact() const { return m_libArtifact; }
      virtual const std::string &name() const = 0;
      bool hasArtifact(const void *art);
      virtual Container &container() = 0;
      Worker &createWorker(Application &app, const OCPI::Library::Implementation &impl,
			   const char *appInstName, const OCPI::Container::Workers &slaves,
			   bool hasMaster, size_t member, size_t crewSize,
			   const OCPI::Base::PValue *wparams = NULL);
      Worker &addWorker(Application &app, const char *instName,
			const OCPI::Library::Implementation &impl,
			const OCPI::Container::Workers &slaves, bool hasMaster, size_t member,
			size_t crewSize, const OCPI::Base::PValue *wParams);
      Worker &addLoadTimeWorker(const OCPI::Library::Implementation &i, unsigned n);
      virtual void configure();
    protected:
      virtual ~Artifact();
    };
  } // Container
} // OCPI
#endif

