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
 * This file contains driver-level code that does not know about the guts of the 
 * container class.
 */
#include <unistd.h> // alarm()
#include <cmath> // round
#include "ContainerManager.hh"
#include "HdlContainer.hh"
#include "HdlDriver.hh"
#include <gpsd.h>

bool OCPI::HDL::Driver::m_gpsdTimeout = false;

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

struct GPSDParams gpsdp;

static void gpsCallback(struct gps_device_t *device, gps_mask_t changed) {
  if (device) {
  }
  if (changed) {
  }
  static int packet_counter = 0;
  if (packet_counter++ >= 15) {
    OCPI::HDL::Driver::m_gpsdTimeout = true;
    alarm(0);
  }
}

namespace OCPI {
  namespace HDL {
    namespace OC = OCPI::Container;
    namespace OA = OCPI::API;
    namespace OU = OCPI::Util;
    namespace OB = OCPI::Base;
    namespace OS = OCPI::OS;
    namespace OP = OCPI::Base::Plugin;

    const char *hdl = "hdl";

    Driver::
    Driver() : m_gpsdp(&gpsdp), m_doGpsd(false) {
    }

    OCPI::HDL::Device *Driver::
    open(const char *a_name, bool discovery, bool forLoad, const OA::PValue *params,
	 std::string &err) {
      parent().parent().configureOnce();
      lock();
      // FIXME: obviously this should be registered and dispatched nicely..
      bool pci = false, ether = false, sim = false, bus = false, lsim = false;
      const char *which = a_name;
      if (!strncasecmp("PCI:", which, 4)) {
	pci = true;
	which += 4;
      } else if (!strncasecmp("pl:", which, 3)) {
	bus = true;
	which += 3;
      } else if (!strncasecmp("sim:", which, 4)) {
	sim = true;
	which += 4;
      } else if (!strncasecmp("lsim:", which, 5)) {
	lsim = true;
	which += 5;
      } else if (!strncasecmp("Ether:", which, 6)) {
	ether = true;
	which += 6;
      } else {
	unsigned n = 0;
	for (const char *cp = strchr(which, ':'); cp; n++, cp = strchr(cp+1, ':'))	  ;
	if (n == 5)
	  ether = true;
	else
	  pci = true;
      }
      if (!which[0]) {
	OU::format(err, "Missing device name after prefix \"%s\"", a_name);
	return NULL;
      }
      Device *dev =
	pci ? PCI::Driver::open(which, params, err) : 
	bus ? Zynq::Driver::open(which, forLoad, params, err) : 
	ether ? Ether::Driver::open(which, discovery, params, err) :
	sim ? Sim::Driver::open(which, discovery, params, err) : 
	lsim ? LSim::Driver::open(which, params, err) : NULL;
      ezxml_t config;
      if (forLoad && bus)
	return dev;
      if (dev && !setup(*dev, config, err))
	return dev;
      delete dev;
      return NULL;
    }

    void Driver::
    close() {
      closeAccess();
      unlock();
    }

    // A device has been found (and created).  Its ownership has been passed in to us,
    // so we will delete it here if there is any error.
    // Return true if error or if we otherwise discarded the device
    // Assuming we are called possibly multiple times from a give driver's search method,
    // record the first error seen.
    bool Driver::
    found(Device &dev, const char **excludes, bool discoveryOnly, std::string &error) {
      ezxml_t config;
      error.clear();
      if (excludes)
	for (const char **ap = excludes; *ap; ap++)
	  if (!strcasecmp(*ap, dev.name().c_str()))
	    goto out;
      if (!setup(dev, config, error)) {
	bool printOnly = false;
	if ((OB::findBool(m_params, "printOnly", printOnly) && printOnly))
	  dev.print(); // fall through to delete
	else {
#if 0
	  if (dev.m_verbose)
	    dev.print();
#endif
	  if (!discoveryOnly)
	    createContainer(dev, config, m_params); // no errors?
	  return false;
	}
      }
    out:
      delete &dev;
      return true;
    } 

    unsigned Driver::
    search(const OA::PValue *params, const char **exclude, bool discoveryOnly) {
      OU::SelfAutoMutex x(this); // protect m_params etc.
      unsigned count = 0;
      m_params = params;
      // Note that the default here is to DO discovery, i.e. to disablediscovery
      // the variable must be set and set to 0
      const char *env;
      if ((env = getenv("OCPI_ENABLE_HDL_DISCOVERY")) && env[0] == '0')
	return 0;
      std::string error;
      count += Zynq::Driver::search(params, exclude, discoveryOnly, error);
      if (error.size()) {
	ocpiBad("In HDL Container driver, got Zynq search error: %s", error.c_str());
	error.clear();
      }
      count += Ether::Driver::search(params, exclude, discoveryOnly, false, error);
      if (error.size()) {
	ocpiBad("In HDL Container driver, got ethernet search error: %s", error.c_str());
	error.clear();
      }
      count += PCI::Driver::search(params, exclude, discoveryOnly, error);
      if (error.size()) {
	ocpiBad("In HDL Container driver, got PCI search error: %s", error.c_str());
	error.clear();
      }
      count += Sim::Driver::search(params, exclude, discoveryOnly, true, error);
      if (error.size()) {
	ocpiBad("In HDL Container driver, got SIM/UDP search error: %s", error.c_str());
	error.clear();
      }
      count += LSim::Driver::search(params, exclude, discoveryOnly, error);
      if (error.size()) {
	ocpiBad("In HDL Container driver, got LSIM search error: %s", error.c_str());
	error.clear();
      }
      return count;
    }
    
    OC::Container *Driver::
    probeContainer(const char *which, std::string &error, const OA::PValue *params) {
      Device *dev;
      ezxml_t config;
      if ((dev = open(which, false, false, params, error))) {
	if (setup(*dev, config, error))
	  delete dev;
	else
	  return createContainer(*dev, config, params);
      }
      if (error.size())
	ocpiBad("While probing %s: %s", which, error.c_str());
      return NULL;
    }      
    // use libgpsd interface to configure gps
    // (ref https://www.systutorials.com/docs/linux/man/3-libgpsd/)
    // see https://gitlab.com/gpsd/gpsd/blob/release-3.14/gpsctl.c
    // for example libgpsd usage
    bool Driver::
    configure_gpsd_if_enabled() {
      if (!m_doGpsd)
        return false;
      if (m_gpsdp->m_configured)
        return true;
      gps_context_init(&m_gpsdp->m_context, "opencpi-gpsd");
      if (OS::logWillLog(OCPI_LOG_INFO))
        m_gpsdp->m_context.errout.debug = LOG_IO;
      else
        m_gpsdp->m_context.errout.debug = LOG_ERROR;
      m_gpsdp->m_session.context = &m_gpsdp->m_context;
      gpsd_init(&m_gpsdp->m_session, &m_gpsdp->m_context, m_gpsdp->m_serialPort.c_str());
      if (gpsd_activate(&m_gpsdp->m_session, O_PROBEONLY) >= 0) {
        FD_SET(m_gpsdp->m_session.gpsdata.gps_fd, &m_gpsdp->m_allFds);
        if(m_gpsdp->m_session.gpsdata.gps_fd > m_gpsdp->m_maxFd)
          m_gpsdp->m_maxFd = m_gpsdp->m_session.gpsdata.gps_fd;
        gpsd_time_init(&m_gpsdp->m_context, time(NULL));
        m_gpsdp->m_configured = true;
      }
      if (m_gpsdp->m_forceType) {
        m_gpsdp->m_session.device_type = m_gpsdp->m_forceType;
        ocpiInfo("HDL Driver: gpsd: devicetype: %s", m_gpsdp->m_session.device_type->type_name);
      }
      for (auto it = m_gpsd_xml.begin(); it != m_gpsd_xml.end(); ++it) {
        char bb[BUFSIZ];
        ssize_t len = 0;
        m_gpsdp->m_context.readonly = false;
        len = hex_escapes(bb, *it);
        if (len <= 0)
          ocpiInfo("HDL Driver: gpsd: error, len = %zu", len);
        else
          if (m_gpsdp->m_session.device_type) {
            if (m_gpsdp->m_session.device_type->control_send(&m_gpsdp->m_session, bb, (size_t)len) == -1)
              throw std::string("HDL Driver: gpsd: control_send error");
          }
          else
            throw std::string("HDL Driver: system.xml: malformed - gpsd element must contain a valid devicetype attribute if control sub-element is used");
        m_gpsdp->m_context.readonly = true;
      }
      return m_gpsdp->m_configured;
    }
    /*<!-- system XML -->
        <opencpi>
          <container>
            <hdl load='1'> <!-- hdl: optional,
                                load: mandatory -->
              <gpsd devicetype='' serialport=''> <!-- gpsd: optional,
                                                      devicetype: mandatory only when using control
                                                      serialport: mandatory -->
                <control value=''/> <!-- control: optional, value: mandatory -->
                <control value=''/> <!-- control: optional, value: mandatory -->
              </gpsd>
            </hdl>
          </container>
        </opencpi>
    */
    void Driver::
    configure(ezxml_t xml) {
      // First, do the generic configuration, which configures discovered devices for this driver
      OP::Driver::configure(xml);
      ezxml_t xx;
      if (!xml || !(xx = ezxml_cchild(xml, "gpsd"))) return;
      m_doGpsd = true;
      auto sp = ezxml_cattr(xx, "serialport"); // mandatory
      if (sp)
        m_gpsdp->m_serialPort.assign(sp);
      else
        throw std::string("HDL Driver: system.xml: malformed - gpsd element must contain serialport attribute");
      ocpiInfo("HDL Driver: gpsd: system.xml: serialport=%s", m_gpsdp->m_serialPort.c_str());
      auto dtx = ezxml_cattr(xx, "devicetype"); // optional
      if(dtx) {
        ocpiInfo("HDL Driver: gpsd: system.xml: devicetype=%s", dtx);
        unsigned matchcount = 0;
        const struct gps_type_t **dp;
        for (dp = gpsd_drivers; *dp; dp++)
          if (strstr((*dp)->type_name, dtx) != NULL) {
            m_gpsdp->m_forceType = *dp;
            matchcount++;
          }
        if(matchcount != 1)
          m_gpsdp->m_forceType = NULL;
      }
      // control is optional
      for (ezxml_t xxc = ezxml_cchild(xx, "control"); xxc; xxc = ezxml_cnext(xxc)) {
        const char* control = ezxml_cattr(xxc, "value"); // mandatory
        m_gpsd_xml.push_back(control);
        ocpiInfo("HDL Driver: gpsd: system.xml: control value='%s'", control);
      }
    }
    // Get the best current OS time, independent of any device.
    OS::Time Driver::
    now(bool &isGps) {
      isGps = true;
      if (!m_gpsdp->m_configured) {
        configure_gpsd_if_enabled();
        ocpiInfo("HDL Driver: GPS not configured");
        isGps = false;
        return OS::Time::now();
      }
      fd_set rfds;
      for (m_gpsdTimeout = false; !m_gpsdTimeout; ) {
        fd_set efds;
        switch (gpsd_await_data(&rfds, &efds, m_gpsdp->m_maxFd, &m_gpsdp->m_allFds, &m_gpsdp->m_context.errout)) {
          case AWAIT_GOT_INPUT:
            break;
          case AWAIT_NOT_READY:
            if(FD_ISSET(m_gpsdp->m_session.gpsdata.gps_fd, &efds)) {
              ocpiInfo("HDL Driver: gpsd: bad file descriptor");
              isGps = false;
              return OS::Time::now();
            }
            continue;
          case AWAIT_FAILED:
            ocpiInfo("HDL Driver: gpsd: gpsd_await_data() returned DEVICE_ERROR");
            isGps = false;
            return OS::Time::now();
        }
        switch (gpsd_multipoll(FD_ISSET(m_gpsdp->m_session.gpsdata.gps_fd, &rfds), &m_gpsdp->m_session, gpsCallback, 0)) {
          case DEVICE_READY:
            FD_SET(m_gpsdp->m_session.gpsdata.gps_fd, &m_gpsdp->m_allFds);
            break;
          case DEVICE_UNREADY:
            FD_CLR(m_gpsdp->m_session.gpsdata.gps_fd, &m_gpsdp->m_allFds);
            break;
          case DEVICE_ERROR:
            ocpiInfo("HDL Driver: gpsd: gpsd_multipoll() returned DEVICE_ERROR");
            isGps = false;
            return OS::Time::now();
          case DEVICE_EOF:
            ocpiInfo("HDL Driver: gpsd: gpsd_multipoll() returned DEVICE_EOF");
            isGps = false;
            return OS::Time::now();
          default:
            break;
        }
      }
      if (m_gpsdp->m_session.gpsdata.fix.mode >= MODE_2D)
	// Only use seconds
        return OS::Time((uint32_t)lround(m_gpsdp->m_session.gpsdata.fix.time), 0);
      else
        isGps = false;
      ocpiInfo("HDL Driver: GPS fix not acquired");
      return OS::Time::now();
    }
    // Internal method common to "open" and "found"
    // Return true on error
    bool Driver::
    setup(Device &dev, ezxml_t &config, std::string &err) {
      // Get any specific configuration information for this device
      const char *l_name = dev.name().c_str();
      config = getDeviceConfig(l_name);
      if (!config && !strncmp("PCI:", l_name, 4)) // compatibility
	config = getDeviceConfig(l_name + 4);
      // Configure the device
      return dev.configure(config, err);
    }
    void Driver::initAdmin(OccpAdminRegisters &admin, const char *platform, HdlUUID &hdlUuid,
			   OU::UuidString *uuidString) {
      Device::initAdmin(admin, platform, hdlUuid, uuidString);
    }
    DirectWorker *Driver::
    createDirectWorker(Device &dev, const Access &cAccess, Access &wAccess, ezxml_t impl,
		       ezxml_t inst, const char *idx, unsigned timeout) {
      return new DirectWorker(dev, cAccess, wAccess, impl, inst, idx, timeout);
    }

    OC::RegisterContainerDriver<Driver> driver;
  }
}
