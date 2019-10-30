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

#ifndef HdlDriver_H
#define HdlDriver_H

#include <string>
#include "HdlSimDriver.h"
#include "HdlLSimDriver.h"
#include "HdlBusDriver.h"
#include "HdlEtherDriver.h"
#include "HdlPciDriver.h"
#include "ContainerManager.h"
#include <gpsd.h>

namespace OCPI {
  namespace HDL {
    extern const char *hdl;

    struct GPSDParams {
      struct gps_context_t     m_context;
      const struct gps_type_t* m_forceType;
      struct gps_device_t      m_session;
      std::string              m_serialPort; // e.g. /dev/ttyPS1
      bool                     m_configured;
      fd_set                   m_allFds;
      int                      m_maxFd;
      GPSDParams() : m_forceType(NULL), m_configured(false), m_maxFd(0) {
      }
    };

    class Container;
    class Driver
      // Note DriverBase must be destructed before the specific Driver destructors
      // In particular, destructors of specific devices (destroyed by DriverBase)
      // can know that their specific drivers (which are not strictly parents) still exist
      : OCPI::HDL::PCI::Driver,
	OCPI::HDL::Ether::Driver,
	OCPI::HDL::Sim::Driver,
	public OCPI::HDL::LSim::Driver,
	OCPI::HDL::Zynq::Driver,
        public OCPI::Container::DriverBase<Driver, Container, hdl>,
      Access, // for temporary probing
	virtual protected OCPI::Util::SelfMutex
    {
      const OCPI::Util::PValue *m_params; // a temporary during discovery
      bool setup(Device &dev, ezxml_t &config, std::string &err);
    protected:
      static bool m_gpsdTimeout;
      bool m_doGpsd;
      std::vector<const char*> m_gpsd_xml;
      GPSDParams  m_gpsdp;
      void configure_gpsd(struct GPSDParams& gpsd);
      void loop_gpsctl(ezxml_t xml);
      void configure(ezxml_t xml);
    public:
      Driver();
      static void gpsCallback(struct gps_device_t *device, gps_mask_t changed);
      void configure_gpsd();
      OCPI::OS::Time now(bool &isGps);
      void print(const char *name, Access &access);
      // This driver method is called when container-discovery happens, to see if there
      // are any container devices supported by this driver
      // It uses a generic PCI scanner to find candidates, and when found, calls the
      // "found" method.
      unsigned search(const OCPI::API::PValue*, const char **exclude, bool discoveryOnly);
      bool found(Device &dev, const char **excludes, bool discoveryOnly, std::string &error);
      // Probe a specific container
      OCPI::Container::Container *probeContainer(const char *which, std::string &error,
						 const OCPI::API::PValue *props);
      virtual OCPI::HDL::Device * open(const char *which, bool discovery, bool forLoad,
				       const OCPI::API::PValue *params, std::string &err);
      void close();

      // Create an actual container.
      static OCPI::Container::Container *
      createContainer(Device &dev, ezxml_t config = NULL,
		      const OCPI::Util::PValue *params = NULL);
      // Create a dummy worker. - virtual due to driver access
      virtual DirectWorker *
      createDirectWorker(Device &dev, const Access &cAccess, Access &wAccess, ezxml_t impl,
			 ezxml_t inst, const char *idx, unsigned timeout);
      virtual void initAdmin(OccpAdminRegisters &admin, const char *platform, HdlUUID &hdlUuid,
			     OU::UuidString *uuidString);
    };
  }
}
#endif
