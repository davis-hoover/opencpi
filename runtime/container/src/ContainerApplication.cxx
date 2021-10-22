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

#include "Container.h"
#include "ContainerWorker.h"
#include "ContainerArtifact.h"
#include "ContainerApplication.h"


namespace OA = OCPI::API;
namespace OL = OCPI::Library;
namespace OU = OCPI::Util;
namespace OM = OCPI::Metadata;

namespace OCPI {
  namespace Container {
    Application::Application(const OA::PValue *params)
      : m_apiApplication(NULL) {
      const char *package;
      if (OU::findString(params, "package", package))
	m_package = package;
      else
	m_package = "local";
      m_package += '.';
    }
    Application::~Application() {
      ocpiDebug("In  Container::Application::~Application()");
    }

    OA::Worker &Application::
    createWorker(const char *url, const OA::PValue *aParams, const char *instName,
		 const char *implName, const char *preInstName,
		 const OA::PValue *wProps, const OA::PValue *wParams,
		 const char * /* selectCriteria */ ) {
      if (url)
	return container().loadArtifact(url, aParams).createWorker(*this, instName,
								   implName, preInstName,
								   wProps, wParams);
      // This is for passing in a dispatch table for RCC workers.
      else {
	Worker &w = createWorker(NULL, instName, (ezxml_t)NULL, (ezxml_t)NULL, NoWorkers, false,
				 0, 1, aParams);
	w.initialize();
	return w;
      }
    }
    OA::Worker &Application::
    createWorker(const char *instName, const char *specName,
		 const OA::PValue *wProps,
		 const OA::PValue *wParams,
		 const char *selectCriteria, 
		 const OA::Connection *connections) {
      // Find an artifact (and instance within the artifact), for this worker
      std::string spec;
      const char *dot = strchr(specName, '.');
      if (dot)
	spec = specName;
      else {
	spec = m_package;
	spec += specName;
      }
      const char *artInst = NULL;
      OL::Artifact &a =
	OL::Manager::findArtifact(container(), spec.c_str(), wParams, selectCriteria,  connections, artInst);
      // Load the artifact and create the worker
      return
	container().loadArtifact(a).createWorker(*this, instName, spec.c_str(), artInst, wProps, wParams);
    }
    Worker &Application::
    createWorker(OCPI::Library::Artifact &art, const char *appInstName, 
		 ezxml_t impl, ezxml_t inst, const Workers &slaves, bool hasMaster,
		 size_t member, size_t crewSize, const OCPI::Util::PValue *wParams) {
      // Load the artifact and create the worker
      return
	container().loadArtifact(art).createWorker(*this, appInstName, impl, inst, slaves,
						   hasMaster, member, crewSize, wParams);
    }
    // If not master, then we ignore slave, so there are three cases
    void Application::
    startMasterSlave(bool isMaster, bool isSlave, bool isSource) {
      for (Worker *w = firstWorker(); w; w = w->nextWorker())
	if (isSource == w->isSource() &&
	    isMaster == (w->slaves().size() != 0 || w->isEmulator()) &&
	    isSlave == w->hasMaster()) {
	  assert(w->getState() == OM::Worker::INITIALIZED || 
		 w->getState() == OM::Worker::SUSPENDED);
	  ocpiInfo("Starting worker: %s in container %s from %s/%s", w->name().c_str(),
		   container().name().c_str(), w->implTag().c_str(), w->instTag().c_str());
	  w->start();
	}
    }
    // If not master, then we ignore slave, so there are three cases
    void Application::
    stop(bool isMaster, bool isSlave) {
      for (Worker *w = firstWorker(); w; w = w->nextWorker())
	if ((isMaster && w->slaves().size() &&
	     ((isSlave && w->hasMaster()) || (!isSlave && !w->hasMaster()))) ||
	    (!isMaster && w->slaves().empty())) {
	  ocpiInfo("Stopping worker: %s in container %s from %s/%s", w->name().c_str(),
		   container().name().c_str(), w->implTag().c_str(), w->instTag().c_str());
	  w->stop();
	}
    }
    // If not master, then we ignore slave, so there are three cases
    void Application::
    release(bool isMaster, bool isSlave) {
      for (Worker *w = firstWorker(); w; w = w->nextWorker())
	if ((isMaster && w->slaves().size() &&
	     ((isSlave && w->hasMaster()) || (!isSlave && !w->hasMaster()))) ||
	    (!isMaster && w->slaves().empty()))
	w->release();
    }
    bool Application::
    isDone() {
      for (Worker *w = firstWorker(); w; w = w->nextWorker())
	if (!w->isDone())
	  return false;
      return true;
    }
    bool Application::
    wait(OS::Timer *timer) {
      for (Worker *w = firstWorker(); w; w = w->nextWorker())
	if (w->wait(timer))
	  return true;
      return false;
    }
#if 0 // let's see if anyone uses this
    void Application::
    start() {
      startMasterSlave(true, false); // start masters that are not slaves
      startMasterSlave(true, true);  // start masters that are slaves
      startMasterSlave(false, false); // start non-masters
    }
#endif
  }
  namespace API {
    ContainerApplication::~ContainerApplication(){}
  }
}
