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

// Non worker asset parsing for non-worker assets that the build-engine needs for
// settings/attributes in the make environment
// Note that determining dirtype (asset type of directory) is done separately in python and not here.
// So here we do asset-specific parsing and error checking, and return make syntax assignments on stdout

#include "ezxml.h"
#include "OcpiUtilEzxml.h"
#include "OcpiUtilMisc.h"
#include "cdkutils.h"

namespace OE = OCPI::Util::EzXml;
namespace OU = OCPI::Util;

	  // These are documented, although they may be deprecated...
#define PROJECT_AND_LIBRARY_ATTRS \
	  "HdlTargets", "HdlPlatforms", "RccPlatforms", "RccHdlPlatforms",\
	  "ComponentLibraries", "HdlLibraries", "PackageID", "Package",\
	  "OnlyTargets", "OnlyPlatforms", "ExcludeTargets", "ExcludePlatforms",\
          "XmlIncludeDirs", "IncludeDirs", "ComponentLibraries"



#define PROJECT_ONLY_ATTRS "PackageName", "PackagePrefix", "ProjectDependencies"
static const char *
parseProject(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, PROJECT_ONLY_ATTRS, PROJECT_AND_LIBRARY_ATTRS, NULL)) ||
      (err = OE::checkElements(xml, NULL)))
    return err;
  return NULL;
}

#define LIBRARY_ONLY_ATTRS "Workers", "Tests", "ExcludeWorkers", "ExcludeTests"
static const char *
parseLibrary(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, LIBRARY_ONLY_ATTRS, PROJECT_AND_LIBRARY_ATTRS, NULL)) ||
      (err = OE::checkElements(xml, NULL)))
    return err;
  return NULL;
}

#define HDL_LIBRARY_AND_CORE_ATTRS \
  "SourceFiles","NameSpace", "Libraries", "HdlLibraries", "ExcludeTargets", "OnlyTargets", "HdlNoLibraries"
#define HDL_LIBRARY_ONLY_ATTRS "HdlNoElaboration"
static const char *
parseHdlLibrary(ezxml_t xml) {
  (void)xml;
  return NULL;
}

#define HDL_CORE_ONLY_ATTRS "Top"
static const char *
parseHdlCore(ezxml_t xml) {
  (void)xml;
  return NULL;
}

static const char *
parseHdlAssembly(ezxml_t xml) {
  (void)xml;
  return NULL;
}

#define ALL_ATTRS PROJECT_AND_LIBRARY_ATTRS, PROJECT_ONLY_ATTRS
// The argument is [<expected-asset-type>:]<xml-file>
const char *
parseAsset(const char *file, const char *topElement) {
  std::string parent, xfile;
  const char *err;
  ezxml_t xml;
  if ((err = parseFile(file, parent, topElement, &xml, xfile, true, false)) ||
      (err = 
       !strcasecmp(xml->name, "project") ? parseProject(xml) :
       !strcasecmp(xml->name, "library") ? parseLibrary(xml) :
       !strcasecmp(xml->name, "hdllibrary") ? parseHdlLibrary(xml) :
       !strcasecmp(xml->name, "hdlcore") ? parseHdlCore(xml) :
       !strcasecmp(xml->name, "hdlassembly") ? parseHdlAssembly(xml) :
       "Unknown asset type"))
    return OU::esprintf("For <%s> XML file %s:  %s", topElement, file, err);
  static const char *attrs[] = { ALL_ATTRS, NULL };
  const char *attr;
  for (const char **ap = attrs; *ap; ++ap)
    if ((attr = ezxml_cattr(xml, *ap)))
      printf("%s=%s\n", *ap, attr);
  return NULL;
}
