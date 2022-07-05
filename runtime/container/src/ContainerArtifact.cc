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

#include "ContainerWorker.hh"
#include "ContainerApplication.hh"
#include "ContainerArtifact.hh"

namespace OL = OCPI::Library;
namespace OA = OCPI::API;
namespace OU = OCPI::Util;
namespace OB = OCPI::Base;
namespace OC = OCPI::Container;

namespace OCPI {
  namespace Container {
    Artifact::Artifact(OL::Artifact &lart, const OB::PValue *) 
      : m_libArtifact(lart) {
      // FIXME: ref count loads from library artifact?
    }
    Artifact::~Artifact() {
    }

    Worker &Artifact::
    createWorker(Application &app, const OL::Implementation &impl, const char *appInstName,
		 const OC::Workers &slaves, bool hasMaster, size_t member, size_t crewSize,
		 const OCPI::Base::PValue *wParams) {
      // Call the method in the derived class
      Worker &w = app.createWorker(this, appInstName, impl.m_metadataImpl.m_xml, impl.m_staticInstance,
				   slaves, hasMaster, member, crewSize, wParams);
      m_workers.push_back(&w);
      w.initialize();
      return w;
    }
    void Artifact::removeWorker(Worker &w) {
      m_workers.remove(&w);
    }
    bool Artifact::hasArtifact(const void *art) {
      return (OL::Artifact *)(art) == &m_libArtifact;
      }
  }
}
