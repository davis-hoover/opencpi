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
#include "ContainerManager.h"
#include "HdlContainer.h"
#include "HdlDriver.h"

bool OCPI::HDL::Driver::m_gpsdTimeout = false;

namespace OCPI {
  namespace HDL {
    namespace OC = OCPI::Container;
    namespace OA = OCPI::API;
    namespace OU = OCPI::Util;
    namespace OP = OCPI::HDL::PCI;
    namespace OS = OCPI::OS;
    namespace OD = OCPI::Driver;

    const char *hdl = "hdl";

    OCPI::HDL::Device *Driver::
    open(const char *name, bool discovery, bool forLoad, const OA::PValue *params,
	 std::string &err) {
      parent().parent().configureOnce();
      lock();
      // FIXME: obviously this should be registered and dispatched nicely..
      bool pci = false, ether = false, sim = false, bus = false, lsim = false;
      const char *which = name;
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
	for (const char *cp = strchr(which, ':'); cp; n++, cp = strchr(cp+1, ':'))
	  ;
	if (n == 5)
	  ether = true;
	else
	  pci = true;
      }
      if (!which[0]) {
	OU::format(err, "Missing device name after prefix \"%s\"", name);
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
	if ((OU::findBool(m_params, "printOnly", printOnly) && printOnly))
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
    void Driver::
    configure_gpsd(struct GPSDParams& gpsd) {
      gps_context_init(&gpsd.m_context, "opencpi-gpsd");
      gpsd.m_context.errout.debug = LOG_INF;
      gpsd.m_session.context = &gpsd.m_context;
      if(gpsd.m_forceType) {
        const char* dd = gpsd.m_forceType->type_name;
        ocpiInfo("HDL Driver: assigning gpsd session device type to %s", dd);
	      gpsd.m_session.device_type = gpsd.m_forceType;
      }
      gpsd_init(&gpsd.m_session, &gpsd.m_context, gpsd.m_serialPort.c_str());
      if(gpsd_activate(&gpsd.m_session, O_PROBEONLY) >= 0) {
        gpsd.m_configured = true;
        FD_SET(gpsd.m_session.gpsdata.gps_fd, &gpsd.m_allFds);
        if(gpsd.m_session.gpsdata.gps_fd > gpsd.m_maxFd)
          gpsd.m_maxFd = gpsd.m_session.gpsdata.gps_fd;
        gpsd_time_init(&gpsd.m_context, time(NULL));
      }
    }
    /*void Driver::
    configure_gpsctl(ezxml_t xml) {
      ocpiInfo("HDL Driver: configure_gpsctl");
      GPSDParams gpsd;
      ezxml_t xdt = ezxml_cattr(xml, "devicetype");
      if(xdt) {
        std::string devt(xdt);
        ocpiInfo("HDL Driver: searching for gpsd driver %s", devt.c_str());
        unsigned matchcount = 0;
        const struct gps_type_t **dp;
        for (dp = gpsd_drivers; *dp; dp++)
          if (strstr((*dp)->type_name, devt.c_str()) != NULL) {
            gpsd.m_forceType = *dp;
            matchcount++;
          }
        if(matchcount != 1)
          gpsd.m_forceType = NULL;
        else {
          std::string driver(gpsd.m_forceType->type_name);
          ocpiInfo("HDL Driver: gpsd driver matches %s", driver.c_str());
        }
      }
      gpsd.m_serialPort.assign(ezxml_cattr(xml, "serialport"));
      //configure_gpsd(gpsd);
    }*/
    /*<!-- system XML -->
        <opencpi>
          <container>
            <hdl load='1'> <!-- hdl: optional,
                                load: mandatory -->
              <gpsd devicetype='' serialport=''> <!-- gpsd: optional,
                                                      devicetype: optional
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
      OD::Driver::configure(xml);
      bool do_gpsd = xml ? true : false;
      /*if (do_gpsd)
        for (ezxml_t x = ezxml_cchild(xml, "gpsctl"); x; x = ezxml_cnext(x))
          configure_gpsctl(x);*/
      ezxml_t xx;
      if (do_gpsd)
        do_gpsd = (xx = ezxml_cchild(xml, "gpsd")) ? true : false;
      if (do_gpsd) {
        m_gpsdp.m_serialPort.assign(ezxml_cattr(xx, "serialport")); // mandatory
        ocpiInfo("HDL Driver: gpsd: serialport: %s", m_gpsdp.m_serialPort.c_str());
        auto dtx = ezxml_cattr(xx, "devicetype"); // optional
        if(dtx) {
          std::string devt(dtx);
          ocpiInfo("HDL Driver: searching for gpsd devicetype %s", devt.c_str());
          unsigned matchcount = 0;
          const struct gps_type_t **dp;
          for (dp = gpsd_drivers; *dp; dp++)
            if (strstr((*dp)->type_name, devt.c_str()) != NULL) {
              m_gpsdp.m_forceType = *dp;
              matchcount++;
            }
          if(matchcount != 1)
            m_gpsdp.m_forceType = NULL;
          else {
            std::string driver(m_gpsdp.m_forceType->type_name);
            ocpiInfo("HDL Driver: gpsd: devicetype: %s", driver.c_str());
          }
        }
      }
      if (do_gpsd) {
        // control is optional
        for (ezxml_t x = ezxml_cchild(xx, "control"); x; x = ezxml_cnext(x)) {
          char bb[BUFSIZ];
          ssize_t len = 0;
          m_gpsdp.m_context.readonly = false;
          char* control = (char*) ezxml_cattr(x, "value"); // mandatory
          ocpiInfo("HDL Driver: gpsd: control: %s", control);
          if ((len = hex_escapes(bb, control)) <= 0)
            ocpiInfo("HDL Driver: gpsd error");
          else
            if (m_gpsdp.m_session.device_type->control_send(&m_gpsdp.m_session, bb, (size_t)len) == -1)
              ocpiInfo("HDL Driver: gpsd send error");
            else
              ocpiInfo("HDL Driver: gpsd: control: %s", control);
          m_gpsdp.m_context.readonly = true;
        }
      }
      if (do_gpsd) {
        configure_gpsd(m_gpsdp);
        bool isGps;
        (void)now(isGps); // sync time
      }
    }
    // Get the best current OS time, independent of any device.
    void Driver::
    gpsCallback(struct gps_device_t *device, gps_mask_t changed) {
      if (device) {
      }
      if (changed) {
      }
      static int packet_counter = 0;
      if (packet_counter++ >= 15) {
        m_gpsdTimeout = true;
        alarm(0);
      }
    }
    // Get the best current OS time, independent of any device.
    OS::Time Driver::
    now(bool &isGps) {
      isGps = true;
      if (!m_gpsdp.m_configured) {
        ocpiInfo("HDL Driver: GPS not configured");
        isGps = false;
        return OS::Time::now();
      }
      fd_set rfds;
      for (m_gpsdTimeout = false; !m_gpsdTimeout; ) {
        fd_set efds;
        switch (gpsd_await_data(&rfds, &efds, m_gpsdp.m_maxFd, &m_gpsdp.m_allFds, &m_gpsdp.m_context.errout)) {
          case AWAIT_GOT_INPUT:
            break;
          case AWAIT_NOT_READY:
            if(FD_ISSET(m_gpsdp.m_session.gpsdata.gps_fd, &efds)) {
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
        switch (gpsd_multipoll(FD_ISSET(m_gpsdp.m_session.gpsdata.gps_fd, &rfds), &m_gpsdp.m_session, gpsCallback, 0)) {
          case DEVICE_READY:
            FD_SET(m_gpsdp.m_session.gpsdata.gps_fd, &m_gpsdp.m_allFds);
          case DEVICE_UNREADY:
            FD_CLR(m_gpsdp.m_session.gpsdata.gps_fd, &m_gpsdp.m_allFds);
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
      if (m_gpsdp.m_session.gpsdata.fix.mode >= MODE_2D)
        return (OS::Time::TimeVal) m_gpsdp.m_session.gpsdata.fix.time;
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
