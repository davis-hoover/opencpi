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

/**
   @file

   @brief
   The OCPI::Container::Container class as the base class for Container implementations.

   Revision History:

   06/15/09 - John Miller
   Added getLastControlError to interface.

   10/13/08 - John Miller
   Initial version.

************************************************************************** */

#ifndef CONTAINER_H_
#define CONTAINER_H_

#include <vector>

#include "OcpiContainerApi.hh"

#include "OsThreadManager.hh"
#include "UtilSelfMutex.hh"
#include "Transport.hh"
#include "LibraryManager.hh"
#include "ContainerPort.hh"

namespace OCPI {
  namespace Container {

    class Driver;
    class Artifact;
    class Launcher;

    // Container base class.
    class Container
      : public OCPI::API::Container,
	public OCPI::Library::Capabilities,
	public OCPI::Time::Emit,
	virtual public OCPI::Util::SelfMutex
    {
    public:
      typedef uint32_t CMap;
    protected:
      //!< Dispatch thread return codes
      enum DispatchRetCode {
        MoreWorkNeeded,   // Dispatch returned, but there is more work needed
        Spin,             // Dispatch completed it current tasks
        DispatchNoMore,   // No more dispatching required
        Stopped           // Container is stopped
      };
      typedef std::set<LocalPort *> BridgedPorts;
      typedef BridgedPorts::iterator BridgedPortsIter;
      static const unsigned maxContainer = sizeof(CMap) * 8;
      unsigned m_ordinal;
      // Start/Stop flag for this container
      bool m_enabled;
      bool m_ownThread;
      bool m_verbose;
      OCPI::OS::ThreadManager *m_thread;
      // This is not an embedded member to potentially control lifecycle better...
      OCPI::Transport::Transport &m_transport;
      // This vector will be filled in by derived classes
      Transports m_transports;  // terminology clash is unfortunate....
      BridgedPorts m_bridgedPorts;
      Container(const char *name, const ezxml_t config = NULL,
		const OCPI::Base::PValue* params = NULL);
    public:
      virtual ~Container();
    private:
      bool runInternal(uint32_t usecs = 0);
    public:
      bool enabled() const { return m_enabled; }
      virtual Driver &driver() = 0;
      virtual const std::string &name() const = 0;
      const char *cname() const { return name().c_str(); }
      const std::string &platform() const { return m_platform; }
      const std::string &model() const { return m_model; }
      const std::string &os() const { return m_os; }
      const std::string &osVersion() const { return m_osVersion; }
      const std::string &arch() const { return m_arch; }
      bool optimized() const { return m_optimized; }
      virtual bool portsInProcess() = 0;
      bool dynamic() const { return m_dynamic; }
      virtual Container *nextContainer() = 0;
      virtual bool supportsImplementation(OCPI::Metadata::Worker &);
      virtual OCPI::API::ContainerApplication *
      createApplication(const char *name = NULL, const OCPI::Base::PValue *props = NULL) = 0;
      virtual void dump(bool /*before*/, bool /*hex*/) {}
      OCPI::Base::PValue *getProperties();
      OCPI::Base::PValue *getProperty(const char *);

      /*
	This is the method that gets called by the creator to provide thread time to the
	container.  If this method returns "true" the caller must continue to call this
	method.  If the return is "false" the method no longer needs to be called.
	
	@param [ in ] event_manager
	Event Manager object that is associated with this container.  This parameter can be
	NULL if the container is being used in polled mode.
      */
      virtual DispatchRetCode dispatch(OCPI::Xfer::EventManager*);
      //      bool run(uint32_t usecs = 0);
      void thread();
      virtual bool needThread() = 0;
      // Load from url
      Artifact & loadArtifact(const char *url,
			      const OCPI::Base::PValue *artifactParams = NULL);
      // Load from library artifact
      Artifact & loadArtifact(OCPI::Library::Artifact &art,
			      const OCPI::Base::PValue *artifactParams = NULL);
      virtual Artifact *findLoadedArtifact(const char *url) = 0;
      virtual Artifact *findLoadedArtifact(const OCPI::Library::Artifact &a) = 0;
      virtual Artifact &createArtifact(OCPI::Library::Artifact &,
				       const OCPI::API::PValue *props = NULL) = 0;
      //      virtual void start(OCPI::Xfer::EventManager* event_manager);
      //      virtual void stop(OCPI::Xfer::EventManager* event_manager);
      virtual void stop();
      // FIXME: default start behavior is for software containers.
      virtual void start();
      //! get the event manager for this container
      virtual OCPI::Xfer::EventManager* getEventManager() { return NULL; }
      bool hasName(const char *name);
      inline unsigned ordinal() const { return m_ordinal; }
      static Container &nthContainer(unsigned n);
      // This is the container that external ports will be attached to
      static Container &baseContainer();
      // Launcher: default is to
      virtual Launcher &launcher() const;
      inline OCPI::Transport::Transport &getTransport() { return m_transport; }
      void registerBridgedPort(LocalPort &p);
      void unregisterBridgedPort(LocalPort &p);
      void addTransport(const char *name, const char *id, OCPI::Transport::PortRole roleIn,
			OCPI::Transport::PortRole roleOut, uint32_t inOptions, uint32_t outOptions);
      const Transports &transports() const { return m_transports; }
      // Return false if internal connection was not made
      virtual bool connectInside(BasicPort &/*in*/, BasicPort &/*out*/) { return false; }
    protected:
      void shutdown();
      virtual Application *firstApplication() const = 0; // Allow base class to see if there are apps
    };
  }
}

#endif

