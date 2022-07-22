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

#include <unistd.h>
#include "ocpi-config.h"
#include "OsFileSystem.hh"
#include "OsLoadableModule.hh"
#include "UtilCppMacros.hh"
#include "UtilEzxml.hh"
#include "UtilAutoMutex.hh"
#include "UtilMisc.hh"
#include "BasePluginManager.hh"
#include "OcpiPluginApi.hh"
namespace OCPI {
namespace Base {
namespace Plugin {
    namespace OU = OCPI::Util;
    namespace OX = OCPI::Util::EzXml;
    void Registration_debug_hook() {} // easier static constructor debug
    Manager::~Manager(){}
    // If a manager has no configuration method, this is the default implementation.
    // The argument is the element for this manager.
    // We just look for driver-specific configuration info
    // FIXME:: check for elements that don't match..
    void Manager::configure(ezxml_t x) {
      for (Driver *d = firstDriverBase(); d; d = d->nextDriverBase()) {
	ezxml_t found = NULL;
	for (ezxml_t c = ezxml_cchild(x, d->name().c_str()); c; c = ezxml_cnext(c))
	  if (found)
	    throw OU::Error("Duplicate XML driver element for: \"%s\"", d->name().c_str());
	  else
	    found = c;
	ocpiDebug("Configuring the %s driver with %p/%s", d->name().c_str(), found,
		  ezxml_name(found));
	d->configure(found);
      }
    }
  unsigned Manager::discover(const PValue *params, bool discoveryOnly) {
      parent().configureOnce();
      unsigned found  = 0;
      if (!m_doNotDiscover)
	for (auto *dd = firstDriverBase(); dd; dd = dd->nextDriverBase())
	  found += dd->discover(params, discoveryOnly);
      return found;
    }
    unsigned Manager::cleanupPosition() { return 1; }
    // Get the singleton ManagerManager, possibly constructing it.
    ManagerManager &ManagerManager::getManagerManager() {
      return OU::Singleton<ManagerManager>::getSingleton();
    }
    ManagerManager::ManagerManager()
      : m_configured(false), m_xml(NULL)
    {}
    ManagerManager::~ManagerManager() {
      ezxml_free(m_xml);
    }
    // We suppress all Managers rather than setting a global so we can easily re-enable
    // individual managers after doing this.
    // This is a static method
    void ManagerManager::suppressDiscovery() {
      for (Manager *m = getManagerManager().firstChild(); m; m = m->nextChild())
	m->suppressDiscovery();
    }
    // This is the static API method
    void ManagerManager::configure(const char *file) {
      getManagerManager().configureOnce(file);
    }
    static bool
    checkLibPath(std::string &path, std::string &dir, const char *name, bool mode,
		 bool dynamic, bool debug) {
      OU::format(path, "%s%s%s%s/libocpi_%s%s.%s", dir.c_str(),
		 mode ? "/" : "", mode ? (dynamic ? "d" : "s") : "",
		 mode ? (debug ? "d" : "o") : "",
		 name, OCPI_DYNAMIC ? "" : "_s", OS::LoadableModule::suffix());
      ocpiDebug("Trying driver path: %s", path.c_str());
      return OS::FileSystem::exists(path.c_str());
    }

    Driver *ManagerManager::
    findDriver(const char *managerName, const char *driverName) {
      Manager *m = getManagerManager().findChildByName(managerName);
      if (!m) {
	ocpiBad("Manager \"%s\" when finding driver \"%s\"", managerName, driverName);
	return NULL;
      }
      return m->findDriver(driverName);
    }
    // Function for compatibility etc.
    static bool
    checkDriver(const char *driverName, std::string &libDir, std::string &lib) {
      // Search, in order:
      // 1. The driver built like we are built, if modes are available
      // 2. The driver built with modes that is not the way we were built
      // 3. The driver built without modes
      return
	!checkLibPath(lib, libDir, driverName, true, OCPI_DYNAMIC, OCPI_DEBUG) &&
	!checkLibPath(lib, libDir, driverName, true, OCPI_DYNAMIC, !OCPI_DEBUG) &&
	!checkLibPath(lib, libDir, driverName, false, OCPI_DYNAMIC, false) &&
	!checkLibPath(lib, libDir, driverName, false, false, false);
    }

    Driver *ManagerManager::
    loadDriver(const char *managerName, const char *driverName, std::string &err) {
      const char *dash = strchr(driverName, '-');
      Driver *driver = findDriver(managerName, dash ? dash + 1 : driverName);
      if (driver)
	return driver;
      std::string file;
      if (dash) {
	file.assign(driverName, OCPI_SIZE_T_DIFF(dash, driverName));
	driverName = file.c_str();
      }
      std::string libDir, lib;
      OU::format(libDir, "%s/%s%s%s%s/lib", OU::getCDK().c_str(),
		 OCPI_CPP_STRINGIFY(OCPI_PLATFORM),
		 !OCPI_DEBUG || OCPI_DYNAMIC ? "-" : "",
		 OCPI_DYNAMIC ? "d" : "",
		 OCPI_DEBUG ? "" : "o");
      if (!OS::FileSystem::exists(libDir)) { // try the pre-1.4 library name FIXME: nuke this?
	std::string oldLibDir;
	OU::format(oldLibDir, "%s/lib/%s-%s-%s", OU::getCDK().c_str(),
		   &OCPI_CPP_STRINGIFY(OCPI_OS)[strlen("OCPI")],
		   OCPI_CPP_STRINGIFY(OCPI_OS_VERSION), OCPI_CPP_STRINGIFY(OCPI_ARCH));
	if (!OS::FileSystem::exists(oldLibDir)) {
	  OU::eformat(err,
		      "when loading the \"%s\" \"%s\" driver, directory \"%s\" does not exist",
		      driverName, managerName, libDir.c_str());
	  return NULL;
	}
	libDir = oldLibDir;
      }
      if (checkDriver(driverName, libDir, lib)) {
	OU::eformat(err,
		    "when loading the \"%s\" \"%s\" driver, no driver file was found in \"%s\"",
		    driverName, managerName, libDir.c_str());
	return NULL;
      }
      ocpiInfo("Loading the \"%s\" \"%s\" driver from \"%s\"",
	       driverName, managerName, lib.c_str());
      std::string lme;
      if (!OS::LoadableModule::load(lib.c_str(), true, lme))
	OU::format(err, "error loading the \"%s\" \"%s\" driver from \"%s\": %s",
		   driverName, managerName, lib.c_str(), lme.c_str());
      else if (!(driver = findDriver(managerName, dash ? dash + 1 : driverName)))
	OU::format(err,
		   "after loading the \"%s\" \"%s\" driver from \"%s\": driver wasn't found",
		   driverName, managerName, lib.c_str());
      return driver;
    }

    // This is NOT a static method
    void ManagerManager::configureOnce(const char *file, const PValue *params) {
      if (m_configured)
	return;
      OCPI::Util::AutoMutex guard(m_mutex);
      if (m_configured)
	return;
      m_configured = true;
      std::string configFile;
      if (!file)
	file = getenv("OCPI_SYSTEM_CONFIG");
      if (!file) {
	OU::format(configFile, "%s/system.xml", OU::getOpenCPI().c_str());
	if (!OS::FileSystem::exists(configFile)) {
	  OU::format(configFile, "%s/../system.xml", OU::getCDK().c_str());
	  if (!OS::FileSystem::exists(configFile))
	    OU::format(configFile, "%s/default-system.xml", OU::getCDK().c_str());
	}
      } else
	configFile = file;
      std::string err;
      if (configFile.empty())
	ocpiInfo("Skipping XML system configuration due to explicitly empty config file name");
      else {
	ocpiInfo("Processing XML system configuration file: \"%s\"", configFile.c_str());
	if (OS::FileSystem::exists(configFile)) {
	  const char *e = OX::ezxml_parse_file(configFile.c_str(), m_xml);
	  if (e)
	    err = e;
	} else
	  err = "file does not exist";
      }
      if (err.empty() && m_xml) {
	for (Manager *m = firstChild(); m; m = m->nextChild())
	  ocpiDebug("Found a \"%s\" manager", m->name().c_str());
	for (ezxml_t x = OX::ezxml_firstChild(m_xml);
	     err.empty() && x; x = OX::ezxml_nextChild(x)) {
	  ocpiDebug("Processing \"%s\" element in system config file", ezxml_name(x));
	  if (!strcasecmp(ezxml_name(x), "load")) {
	    const char *file_attr = ezxml_cattr(x, "file");
	    if (!file_attr)
	      err = "missing \"file\" attribute in \"load\" element";
	    else {
	      ocpiInfo("Loading module requested in system config file: \"%s\"", file_attr);
	      OS::LoadableModule::load(file_attr, true, err);
	    }
	    continue;
	  } else if (!strcasecmp(ezxml_name(x), "applications"))
	    continue;
	  Manager *m;
	  for (m = firstChild(); m; m = m->nextChild())
	    if (!strcasecmp(m->name().c_str(), ezxml_name(x)))
	      break;
	  if (!m) {
	    OU::format(err, "unknown/unsupported system config file element \"%s\"",
		       ezxml_name(x));
	    break;
	  }
	  for (ezxml_t d = OX::ezxml_firstChild(x); d; d = OX::ezxml_nextChild(d)) {
	    bool load;
	    const char *e = OX::getBoolean(d, "load", &load);
	    if (e) {
	      err = e;
	      break;
	    }
	    if (load && !loadDriver(m->name().c_str(), d->name, err))
	      break;
	  }
	}
      }
      if (!err.empty())
	throw OU::Error("Error processing system configuration file \"%s\": %s",
			configFile.c_str(), err.c_str());
      // Now perform the configuration process, where managers and their children can do
      // things they would not do earlier, at static construction time.
      // Note that configuring a manager configures its drivers, but not its devices.
      ocpiInfo("Configuring the plugin managers");
      for (Manager *m = firstChild(); m; m = m->nextChild()) {
	ocpiInfo("Configuring the %s manager", m->name().c_str());
	m->configure(m_xml ? ezxml_cchild(m_xml, m->name().c_str()) : NULL);
      }
      // The discovery happens in a second pass to make sure everything is configured before
      // anything is discovered so that one driver's discovery can depend on another type of
      // driver's configuration.
      for (Manager *m = firstChild(); m; m = m->nextChild())
	if (m->shouldDiscover()) {
	  ocpiInfo("Performing discovery for the %s manager using all its drivers", m->name().c_str());
	  m->discover(params);
	}
    }
    // Cleanup all managers
    bool ManagerManager::s_exiting = false;
    void ManagerManager::cleanup() {
      assert(!s_exiting);
      s_exiting = true;
      OU::g_exiting = true; // for exception handling
      ManagerManager *mm = &OU::Singleton<ManagerManager>::getSingleton();
      // Before simply deleting the managermanager, we delete the
      // managers in order of their "cleanupPosition()"
      for (unsigned i = 0; i < 10; i++)
	for (Manager *m = mm->firstChild(); m; ) {
	  Manager *d = m;
	  m = m->nextChild();
	  if (d->cleanupPosition() == i)
	    delete d;
	}
      delete mm;
    }
    OCPI_NORETURN
    static void exitbad(const char *e) {
      // We are in a very primitive mode here. No error checking.
      static const char msg[] = "\n*********During shutdown********\n";
      ocpiIgnore(write(2, e, strlen(e)));
      ocpiIgnore(write(2, msg, sizeof(msg)));
      _exit(1);
    }
    // A static-destructor hook to perform manager cleanup.
    static class cleanup {
    public:
      ~cleanup() {
	try {
	  ManagerManager::cleanup();
	} catch (std::string &e) {
	  exitbad(e.c_str());
	} catch (const char *e) {
	  exitbad(e);
	} catch (...) {
	  exitbad("Unexpected exception");
	}
      }
    } staticCleanup;
    Driver::Driver() : m_config(NULL), m_discovery(ALL) {}
    Driver::~Driver(){}

    // Default implementation for a driver is to configure devices that exist
    // at configuration time.
    void Driver::configure(ezxml_t xml) {
      if (xml) {
	m_config = xml;
	const char *l_discovery = ezxml_cattr(xml, "discovery");
	if (!l_discovery || !strcasecmp(l_discovery, "all"))
	  m_discovery = ALL;
	else if (!strcasecmp(l_discovery, "none"))
	  m_discovery = NONE;
	else if (!strcasecmp(l_discovery, "static"))
	  m_discovery = STATIC;
	else if (!strcasecmp(l_discovery, "dynamic"))
	  m_discovery = DYNAMIC;
	else
	  ocpiBad("Invalid \"discovery\" attribute for the %s driver \"%s\":  %s.  "
		  "Valid values are:  all, none, static, dynamic",
		  managerBase().name().c_str(), name().c_str(), l_discovery);
	for (ezxml_t dx = ezxml_cchild(xml, "device"); dx; dx = ezxml_cnext(dx))
	  for (Device *d = firstDeviceBase(); d; d = d->nextDeviceBase())
	    if (d->name() == ezxml_name(dx))
	      d->configure(dx);
      }
    }
    ezxml_t Driver::getDeviceConfig(const char *argName) {
      ocpiDebug("getDeviceConfig driver '%s' for device '%s' m_config %p", name().c_str(), argName, m_config);
      for (ezxml_t dx = ezxml_cchild(m_config, "device"); dx; dx = ezxml_cnext(dx)) {
	const char *devName = ezxml_cattr(dx, "name");
	if (devName && !strcmp(argName, devName))
	  return dx;
      }
      return NULL;
    }
    // This non-virtual method is for doing what "search" would do for devices that are not
    // discoverable and thus statically defined in system.xml.
    unsigned Driver::
    createStaticDevices(const PValue *params, std::vector<const char *> &excludes,
                        bool discoveryOnly, Discovery discoveryMode) {
      unsigned found = 0;
      for (ezxml_t x = ezxml_cchild(m_config, "device"); x; x = ezxml_cnext(x)) {
	bool isStatic, isDisabled;
	const char *err;
	if ((err = OX::getBoolean(x, "static", &isStatic, true, true)) ||
	    (err = OX::getBoolean(x, "disable", &isDisabled, false, true)))
	  throw OU::Error("Error in system configuration file for \"static\" or \"disable\""
			  " attributes:  %s", err);
	if (discoveryMode != DYNAMIC && isStatic && !isDisabled) {
	  std::string l_name;
	  if ((err = OX::getRequiredString(x, l_name, "name")))
	    throw OU::Error("Error processing system configuration file:  %s", err);
	  for (auto ei = excludes.begin(); ei != excludes.end(); ++ei)
	    if (!strcasecmp(*ei, l_name.c_str()))
	      goto cont2;
	  // There is nothing more we can do generically here.  The driver can look at
	  // device's name and  XML.
	  createStaticDevice(l_name.c_str(), x, params, discoveryOnly);
	  found++;
	cont2:;
	}
	if (isStatic)
	  excludes.push_back(ezxml_cattr(x, "name"));
      }
      return found;
    }
    void Driver::
    createStaticDevice(const char *a_name, ezxml_t /*x*/, const PValue */*params*/,
                       bool /*discoveryOnly*/) {
      throw OU::Error("Error in system configuration file, driver %s does not support static "
                      "device(s): %s", name().c_str(), a_name);
    }

    // Per driver discovery routine to create devices that are dynamically found,
    // excluding the ones named in the "exclude" list.
    unsigned Driver::
    search(const PValue */*props*/, const char **/*exclude*/, bool /*discoveryOnly*/) {
      return 0;
    }
    // Probe for a particular device and return it if found, and creating it
    // if not yet created. Return NULL if it is not found.
    // This would typically be called by something that had a configuration file
    // and didn't want "discovery" via search.
    // If "which" is null, return any one that matches props, otherwise
    // request a specific one.
    Device *Driver::
    probe(const char */*which*/, bool /*verbose*/, bool /*discovery*/, const char **/*exclude*/,
          const PValue */*params*/, std::string &/*err*/) {
      return NULL;
    }

    // Non-virtual driver discovery
    unsigned Driver::
    discover(const PValue *params, bool discoveryOnly) {
      // e.g. when drivers are specifically discovers like ocpihdl search
      ManagerManager::getManagerManager().configureOnce();
      unsigned found = 0;
      if (m_discovery != Discovery::NONE) {
	ocpiInfo("Performing discovery for the \"%s\" \"%s\" driver",
		 name().c_str(), managerBase().name().c_str());
	std::vector<const char *> excludes;
	found += createStaticDevices(params, excludes, discoveryOnly, m_discovery);
	if (m_discovery != Discovery::STATIC) {
	  excludes.push_back(NULL);
	  found += search(params, &excludes[0], discoveryOnly);
	}
      } else
	ocpiDebug("Discovery for %s driver %s suppressed",
		  managerBase().name().c_str(), name().c_str());
      return found;
    }

    const char *device = "device"; // template argument
    void Device::configure(ezxml_t xml) { (void)xml;}
    Device::~Device(){}

} // Plugin
} // Base
  namespace API {
    void PluginManager::configure(const char *cf) {
      OCPI::Base::Plugin::ManagerManager::configure(cf);
    }
  }
} // OCPI
