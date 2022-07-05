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

#ifndef _OCL_CONTAINER_H_
#define _OCL_CONTAINER_H_
#include <stdint.h>
#include <set>
#include <string>
#include "ContainerManager.hh"

namespace OCPI {
  namespace OCL {

    class Driver;
    class Port;
    class Artifact;
    class Application;
    class DeviceContext;
    class Device;
    class Container
      : public OCPI::Container::ContainerBase<Driver, Container, Application, Artifact> {
      friend class Port;
      friend class Driver;
      friend class Artifact;

    private:
      OCPI::OCL::Device& m_device; // owned by the container

    protected:
      Container(OCPI::OCL::Device &device, const ezxml_t config = NULL,
		const OCPI::Base::PValue *params = NULL);
    public:
      ~Container();

      bool supportsImplementation(OCPI::Metadata::Worker &i);
      OCPI::Container::Container::DispatchRetCode dispatch(OCPI::Xfer::EventManager* event_manager);

      OCPI::Container::Artifact &
	createArtifact(OCPI::Library::Artifact &lart, const OCPI::API::PValue *artifactParams);
      OCPI::Container::Application *
        createApplication(const char *name, const OCPI::Base::PValue *props);

      bool needThread() { return true; }
      bool portsInProcess() { return true; }
      OCPI::OCL::Device &device() { return m_device; }
#if 0
      void loadArtifact(const std::string &pathToArtifact,
			const OCPI::API::PValue* artifactParams);
      void unloadArtifact(const std::string& pathToArtifact);
#endif
    }; // End: class Container
    extern const char *ocl;
    class Driver : public OCPI::Container::DriverBase<Driver, Container, ocl> {

    public:
      Driver();
      static uint8_t s_logLevel;
      // This is the standard driver discovery routine
      unsigned search(const OCPI::API::PValue*, const char** exclude, bool discoveryOnly);
      // This is our special one that does some extra stuff...
      virtual unsigned search(const OCPI::API::PValue*, const char **exclude, bool discoveryOnly,
		      const char *type, Device **found, std::set<std::string> *targets);
      // Find a device of this type (for compilers)
      virtual Device &find(const char *target);
      OCPI::Container::Container* probeContainer(const char* which, std::string &error,
						 const OCPI::API::PValue* props);
      virtual Device *open(const char *name, bool verbose, bool print, std::string &error);
      virtual void compile(size_t nSources, const char **mapped_sources, off_t *sizes,
			   const char **includes, const char **defines, const char *output,
			   const char *target, bool verbose);
    };
  }
}

#endif
