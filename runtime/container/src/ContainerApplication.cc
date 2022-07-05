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

#include "Container.hh"
#include "ContainerWorker.hh"
#include "ContainerArtifact.hh"
#include "ContainerApplication.hh"


namespace OA = OCPI::API;
namespace OL = OCPI::Library;
namespace OB = OCPI::Base;
namespace OM = OCPI::Metadata;

namespace OCPI {
  namespace Container {
    Application::Application(const OA::PValue *params)
      : m_apiApplication(NULL) {
      const char *package;
      if (OB::findString(params, "package", package))
	m_package = package;
      else
	m_package = "local";
      m_package += '.';
    }
    Application::~Application() {
      ocpiDebug("In  Container::Application::~Application()");
    }

    // If not master, then we ignore isSlave, so there are three cases
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
    // If not master, then we ignore isSlave, so there are three cases
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
    // If not master, then we ignore isSlave, so there are three cases
    void Application::
    release(bool isMaster, bool isSlave) {
      for (Worker *w = firstWorker(); w; w = w->nextWorker())
	if ((isMaster && w->slaves().size() &&
	     ((isSlave && w->hasMaster()) || (!isSlave && !w->hasMaster()))) ||
	    (!isMaster && w->slaves().empty())) {
	  ocpiInfo("Releasing worker: %s in container %s from %s/%s", w->name().c_str(),
		   container().name().c_str(), w->implTag().c_str(), w->instTag().c_str());
	  w->release();
	}
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
  }
}
