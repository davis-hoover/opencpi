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
#include "dlfcn.h"
#include "ocpi-config.h"
#include "UtilCppMacros.hh"
#include "UtilMisc.hh"
#include "UtilException.hh"
#include "ContainerManager.hh"

namespace OU = OCPI::Util;

#define OCPI_OPTIONS_HELP "This program loads all plugins. Supply at least one dummy argument.\n"
#include "BaseOption.hh" // for convenient main program and exception handling

static int
mymain(const char **) {
  std::string path, list, name;
  // FIXME: add the "stubs" indicator to plugin-list to avoid special casing ofed/ocl
  OU::format(path, "%s/%s/lib", OU::getCDK().c_str(), OCPI_CPP_STRINGIFY(OCPI_PLATFORM));
  name = (path + "/plugin-list").c_str();
  const char *err;
  if ((err = (OU::file2String(list, name.c_str()))))
    throw OU::Error("Failed to open plugin-list file %s: %s\n", name.c_str(), err);
  OCPI::Container::Manager::getSingleton().suppressDiscovery();
  for (OU::TokenIter ti(list.c_str()); ti.token(); ti.next()) {
    OU::format(name, "%s/libocpi_%s%s%s", path.c_str(), ti.token(),
               OCPI_DYNAMIC ? "" : "_s",
               OCPI_CPP_STRINGIFY(OCPI_DYNAMIC_SUFFIX));
    bool now = strcmp(ti.token(), "ofed") && strcmp(ti.token(), "ocl");
    ocpiBad("Trying to load plugin %s from %s (%s)", ti.token(), name.c_str(), now ? "now" : "lazy");
#if defined(OCPI_OS_macos)
    if (!now && atoi(OCPI_CPP_STRINGIFY(OCPI_OS_VERSION)) >= 12) {
      // At least the error checking will happen better on linux....
      ocpiBad("Skipping loading plugin %s on MacOS 12 or later due to lack of lazy binding",
	      ti.token());
      continue;
    }
#endif
    if (!dlopen(name.c_str(), now ? RTLD_NOW : RTLD_LAZY))
      throw OU::Error("Failed to open plugin: %s", dlerror());
  }
  ocpiBad("All plugins succesfully loaded");
  return 0;
}
