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

#include "lzma.h"                   // just for linkage hooks
#include "zlib.h"                   // just for linkage hooks
#include "pthread_workqueue.h"      // just for linkage hooks
#include "gpsd.h"                   // just for linkage hooks
#include "ocpi-config.h"
#include "OsSocket.hh"           // just for linkage hooks
#include "OsServerSocket.hh"     // just for linkage hooks
#include "OsSemaphore.hh"        // just for linkage hooks
#include "OcpiUuid.h"               // just for linkage hooks
#include "UtilThread.hh"             // just for linkage hooks
#include "UtilPci.hh"            // just for linkage hooks
#include "ContainerPort.hh"          // just for linkage hooks
#if 1
#include "UtilLogPrefix.hh"         // just for linkage hooks
#include "RadioCtrlr.hh"            // just for linkage hooks
#include "RadioCtrlrConfigurator.hh"// just for linkage hooks
#include "RadioCtrlrConfigurator.hh"// just for linkage hooks
#include "RadioCtrlrConfiguratorAD9361.hh"// just for linkage hooks
#include "RadioCtrlrNoOSTuneResamp.hh"// just for linkage hooks
#include "RadioCtrlrConfiguratorTuneResamp.hh"// just for linkage hooks
extern "C" {
#include "ad9361_platform.h"
}
#endif
#include "OcpiContainerRunConditionApi.hh"
#include "XferAccess.hh"
#include "XferManager.hh"

#include "ContainerManager.hh"
#include "ContainerLauncher.hh"
namespace OCPI {
  namespace Container {
    namespace OA = OCPI::API;
    namespace OP = OCPI::Base::Plugin;
    namespace OB = OCPI::Base;
    namespace OM = OCPI::Metadata;
    namespace OT = OCPI::Transport;
    namespace OU = OCPI::Util;
    namespace XF = OCPI::Xfer;
    const char *container = "container";

    unsigned Manager::s_nContainers = 0;
    // TODO: Move this to a vector to manage its own memory...?
    Container **Manager::s_containers;
    unsigned Manager::s_maxContainer;
    static OCPI::Base::Plugin::Registration<Manager> cm;
    Manager::Manager() : m_tpg_events(NULL), m_tpg_no_events(NULL) {
    }

    Manager::~Manager() {
      // Delete my children before the transportGlobals they depend on.
      delete LocalLauncher::singleton();
      deleteChildren();
      if ( m_tpg_no_events ) delete m_tpg_no_events;
      if ( m_tpg_events ) delete m_tpg_events;
      delete [] s_containers;
    }

    // Note this is not dependent on configuration.
    // It is currently used in lieu of a generic data transport shutdowm.
    OT::TransportManager &Manager::
    getTransportManagerInternal(const OB::PValue *params) {
      static unsigned event_range_start = 0;
      bool polled = true;
      OB::findBool(params, "polled", polled);
      OT::TransportManager **tpg = polled ? &m_tpg_no_events : &m_tpg_events;
      if (!*tpg)
	*tpg = new OT::TransportManager( event_range_start++, !polled );
      return **tpg;
    }

#if 0
    // The manager of all container drivers gets the "containers" element
    void Manager::configure(ezxml_t x, bool debug) {
      // So by this time all drivers will be loaded and registered.
      // Find elements that match the container types.
      for (ezxml_t dx = x->child; dx; dx = dx->sibling) {
	for (DriverBase *d = firstChild(); d; d = d->nextChild())
	  if (!strcasecmp(d->name(), dx->name))
	    break;
	if (d)
	  d->configure(dx);
	else
	  OP::ManagerManager::
	    configError(x, "element '%s' doesn't match any loaded container driver");
      }
    }
#endif
    // Make sure we cleanup first since we are "on top"
    unsigned Manager::cleanupPosition() { return 0; }
    // FIXME: allow the caller to get errors. Perhaps another overloaded version
    OCPI::API::Container *Manager::find(const char *model, const char *which,
					const OA::PValue *params) {
      parent().configureOnce();
      for (Driver *d = firstChild(); d; d = d->nextChild()) {
	if (!strcmp(model, d->name().c_str())) {
	  OA::Container *c = d->findContainer(which);
	  std::string error;
	  return c ? c : d->probeContainer(which, error, params);
	}
      }
      return NULL;
    }
    Container *Manager::
    findX(const char *which) {
      parent().configureOnce();
      for (Driver *d = firstChild(); d; d = d->nextChild()) {
	Container *c = d->findContainer(which);
	if (c)
	  return c;
      }
      return NULL;
    }
    void Manager::shutdown() {
      deleteChildren();
    }
    bool Manager::findContainersX(Callback &cb, OM::Worker &i, const char *a_name) {
      ocpiDebug("Finding containers for worker %s container name %s",
		i.cname(), a_name ? a_name : "<none specified>");
      parent().configureOnce();
      for (Driver *d = firstChild(); d; d = d->nextChild())
	for (Container *c = d->firstContainer(); c; c = c->nextContainer()) {
	  ocpiDebug("Trying container c->name: %s ord %u",
		    c->name().c_str(), c->ordinal());
	  bool decimal = a_name && a_name[strspn(a_name, "0123456789")] == '\0';
	  if ((!a_name ||
	       (decimal && (unsigned)atoi(a_name) == c->ordinal()) ||
	       (!decimal && a_name == c->name())) &&
	      c->supportsImplementation(i))
	    cb.foundContainer(*c);
	}
      return false;
    }
    bool Manager::
    dynamic() {
      return OCPI_DYNAMIC;
    }
    bool Manager::
    optimized() {
      return !OCPI_DEBUG;
    }
    void Manager::
    cleanForContextX(void *context) {
      for (Driver *d = firstChild(); d; d = d->nextChild())
	for (Container *c = d->firstContainer(); c; c = c->nextContainer())
	  c->getTransport().cleanForContext(context);
      XF::XferManager::getFactoryManager().cleanForContext(context);
    }
    Driver::Driver(const char *a_name) 
      : OP::DriverType<Manager,Driver>(a_name, *this) {
    }
    const char
      *application = "application",
      *artifact ="artifact",
      *worker = "worker",
      *portBase = "port", // named differently to avoid shadowing issues
      *externalPort = "externalPort";
  }
  namespace API {
    Container *ContainerManager::
    find(const char *model, const char *which, const PValue *props) {
      return OCPI::Container::Manager::getSingleton().find(model, which, props);
    }
    void ContainerManager::shutdown() {
      OCPI::Container::Manager::getSingleton().shutdown();
    }
    Container *ContainerManager::
    get(unsigned n) {
      ocpiDebug("ContainerManager::get(): Calling configureOnce");
      OCPI::Container::Manager::getSingleton().parent().configureOnce();
      ocpiDebug("ContainerManager::get(): Back with %d containers", OCPI::Container::Manager::s_nContainers);
      return
	n >= OCPI::Container::Manager::s_nContainers ? NULL : 
	&OCPI::Container::Container::nthContainer(n);
    }
    // List the containers available
    void ContainerManager::
    list(bool onlyPlatforms) {
      Container *c;
      if (onlyPlatforms) {
	std::set<std::string> plats;
	for (unsigned n = 0; (c = ContainerManager::get(n)); n++)
	  plats.insert(c->model() + "-" + (c->dynamic() ? "1" : "0") + "-" + c->platform());
	for (std::set<std::string>::const_iterator i = plats.begin(); i != plats.end(); ++i)
	  printf("%s\n", i->c_str());
      } else {
	printf("Available containers:\n"
	       " #  Model Platform            OS     OS-Version  Arch     Name\n");
	for (unsigned n = 0; (c = ContainerManager::get(n)); n++)
	  printf("%2u  %-5s %-19s %-6s %-11s %-8s %s\n",
		 n,  c->model().c_str(), c->platform().c_str(), c->os().c_str(),
		 c->osVersion().c_str(), c->arch().c_str(), c->name().c_str());
      }
      fflush(stdout);
    }



  }
  /*
   * This ensures the following functions are linked into the final ocpirun/ACI executables when
   * the functions are used by driver plugin(s) (which are dynamically loaded, but linked against
   * dynamic libraries that do not exist at runtime, e.g. uuid.so) but nowhere else in the
   * framework infrastructure, forcing them to be statically linked here:
   */
#if defined(__clang__)
#pragma clang optimize off
#else
#pragma GCC push_options
#pragma GCC optimize ("O0")
#endif
  namespace Container {
    intptr_t linkme() {
      ((XF::Access *)linkme)->closeAccess();
      ((OA::RunCondition *)linkme)->setPortMasks((OA::OcpiPortMask *)NULL);
      ((Container*)linkme)->start();
      ((XF::XferServices*)linkme)->XF::XferServices::send(0, NULL, 0);
      ((XF::EndPoint*)linkme)->XF::EndPoint::createResourceServices();
      ((OU::Thread*)linkme)->join();
      OU::Uuid uuid;
      OU::UuidString us;
      OU::uuid2string(uuid, us);
      std::string str;
      OU::searchPath(NULL, NULL, str, NULL, NULL);
      (void)OU::getCDK();
      size_t dum2;
      (void)((BasicPort*)linkme)->BasicPort::getOperationInfo(0, dum2);
      unsigned dum3;
      (void)OU::probePci(NULL, 0, 0, 0, 0, 0, NULL, dum3, str);
      // Msg::XferFactoryManager::getFactoryManager();
      OS::Socket s;
      OS::ServerSocket ss;
      OS::Semaphore sem;
      gzerror(NULL, (int*)0);
      // p.applyConnectParams(NULL, NULL);
      ((Application*)0)->createWorker(NULL, NULL, NULL, NULL, NULL, NULL);
      pthread_workqueue_create_np(NULL, NULL);
      pthread_workqueue_additem_np(NULL, NULL, NULL, NULL, NULL);
      // DRC support
#if 1
      ((OCPI::DRC::DataStreamConfigLockRequest *)linkme)->get_data_stream_type();
      ((OCPI::DRC::RadioCtrlrNoOSTuneResamp *)linkme)->init();
      ((OCPI::DRC::Configurator *)linkme)->unlock_all();
      OCPI::DRC::ConfiguratorAD9361 c(NULL, NULL, NULL, NULL);
      OCPI::DRC::ConfiguratorTuneResamp cc(1.0, 2.0);
      //      ((OCPI::DRC::ConfiguratorTuneResamp*)linkme)->impose_constraints_single_pass();
      ((OCPI::Util::LogPrefix *)linkme)->log_debug("hello");
      ad9361_opencpi.set_reset(0, 0);
#endif
      return (intptr_t)&lzma_stream_buffer_decode & (intptr_t)&gpsd_drivers;
    }
  }
#if defined(__clang__)
#pragma clang optimize on
#else
#pragma GCC pop_options
#endif
}

