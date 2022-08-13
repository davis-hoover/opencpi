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

#include "RccContainer.hh"
#include "RccDriver.hh"
// This is the "driver" for RCC containers, which finds them, constructs them, and 
// in general manages them.  It is an object manages by the Container::Manager class.
// It acts as the factory for RCC containers.

namespace OC = OCPI::Container;
namespace OU = OCPI::Util;
namespace OX = OCPI::Util::EzXml;
namespace OA = OCPI::API;
namespace OP = OCPI::Base::Plugin;
namespace OCPI {
  namespace RCC {
    const char *rcc = "rcc";
    Driver::
    Driver()
      //:      m_tpg_events(NULL), m_tpg_no_events(NULL), m_count(0)
    {
      ocpiCheck(pthread_key_create(&s_threadKey, NULL) == 0);
      ocpiDebug("Registering the RCC Container driver");
    }
    pthread_key_t Driver::s_threadKey;
    // Look for a container that doesn't exist yet.
    OC::Container *Driver::
    probeContainer(const char *which, std::string &/*error*/, const OA::PValue *params) {
      return new Container(which, params);
    }
    // Per driver discovery routine to create devices
    unsigned Driver::
    search(const OA::PValue* /* params */, const char **/* exclude */, bool /* discoveryOnly */) {
      std::string error;
      ocpiInfo("Searching for RCC containers, and implicitly finding one.");
      return probeContainer("rcc0", error, NULL) ? 1 : 0;
    }
    Driver::
    ~Driver() {
      // Force containers to shutdown before we remove transport globals.
      OU::Parent<Container>::deleteChildren();
      //      if ( m_tpg_no_events ) delete m_tpg_no_events;
      //      if ( m_tpg_events ) delete m_tpg_events;
      ocpiCheck(pthread_key_delete(s_threadKey) == 0);
    }
    void Driver::
    configure(ezxml_t x) {
      OP::Driver::configure(x);
      OX::getOptionalString(x, m_platform, "platform");
      if (m_platform.size())
	ocpiDebug("RCC Driver platform set to %s", m_platform.c_str());
    }
    // Register this driver
    OC::RegisterContainerDriver<Driver> driver;
  }
}
