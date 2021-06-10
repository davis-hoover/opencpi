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
#define HDL_TARGET_ATTRS "HdlTargets", "HdlPlatforms"

#define TARGET_ATTRS "OnlyTargets", "OnlyPlatforms", "ExcludeTargets", "ExcludePlatforms"

#define PACKAGE_ATTRS "PackageID", "Package", "PackageName", "PackagePrefix"
#define PROJECT_AND_LIBRARY_ATTRS HDL_TARGET_ATTRS, TARGET_ATTRS, PACKAGE_ATTRS, \
	  "RccPlatforms", "RccHdlPlatforms",\
	  "ComponentLibraries", "HdlLibraries", \
          "XmlIncludeDirs", "IncludeDirs"

#define PROJECT_ONLY_ATTRS "ProjectDependencies"
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
static const char *
parseLibraries(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, PROJECT_AND_LIBRARY_ATTRS, NULL)) ||
      (err = OE::checkElements(xml, NULL)))
    return err;
  return NULL;
}
#define APPLICATION_OCPIRUN_ATTRS \
  "OcpiApp", "OcpiAppNoRun", "OcpiApps", \
  "OcpiRunArgs", "OcpiRunBefore", "OcpiRunAfter"

static const char *
parseApplication(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, APPLICATION_OCPIRUN_ATTRS, PROJECT_AND_LIBRARY_ATTRS, NULL)) ||
      (err = OE::checkElements(xml, NULL)))
    return err;
  return NULL;
}

#define APPLICATIONS_ONLY_ATTRS "Applications"
static const char *
parseApplications(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, APPLICATIONS_ONLY_ATTRS, APPLICATION_OCPIRUN_ATTRS, \
			    PACKAGE_ATTRS, NULL)) ||
      (err = OE::checkElements(xml, NULL)))
    return err;
  return NULL;
}

#define HDL_LIBRARY_AND_CORE_ATTRS \
  "SourceFiles","NameSpace", "Libraries", "HdlNoLibraries",  "HdlLibraries"

#define HDL_LIBRARY_ONLY_ATTRS "HdlNoElaboration"
static const char *
parseHdlLibrary(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, HDL_LIBRARY_AND_CORE_ATTRS, HDL_TARGET_ATTRS, TARGET_ATTRS,
			    HDL_LIBRARY_ONLY_ATTRS, NULL)) ||
      (err = OE::checkElements(xml, NULL)))
  return NULL;
}

#define HDL_CORE_ONLY_ATTRS "Top"
static const char *
parseHdlCore(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, HDL_LIBRARY_AND_CORE_ATTRS, HDL_TARGET_ATTRS, TARGET_ATTRS,
			    HDL_CORE_ONLY_ATTRS, NULL)) ||
      (err = OE::checkElements(xml, NULL)))
  return NULL;
}

#define HDL_PRIMITIVES_ONLY_ATTRS "cores"
static const char *
parseHdlPrimitives(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, HDL_TARGET_ATTRS, TARGET_ATTRS, HDL_PRIMITIVES_ONLY_ATTRS,
			    "Libraries", NULL)) ||
      (err = OE::checkElements(xml, NULL)))
    return err;
  return NULL;
}

static const char *
parseHdlPlatforms(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, HDL_TARGET_ATTRS, NULL)) ||
      (err = OE::checkElements(xml, NULL)))
    return err;
  return NULL;
}

#define HDL_ASSEMBLY_ATTRS  "Containers"
static const char *
parseHdlAssembly(ezxml_t xml) {
  const char *err;
  if ((err = OE::checkAttrs(xml, TARGET_ATTRS, HDL_ASSEMBLY_ATTRS, NULL)) ||
      (err = OE::checkElements(xml, "instance", "connection", "external", NULL)))
    return err;
  return NULL;
}

#define ALL_ATTRS \
  HDL_TARGET_ATTRS, TARGET_ATTRS, PACKAGE_ATTRS, PROJECT_AND_LIBRARY_ATTRS, PROJECT_ONLY_ATTRS, \
  LIBRARY_ONLY_ATTRS, APPLICATION_OCPIRUN_ATTRS, APPLICATIONS_ONLY_ATTRS, \
  HDL_LIBRARY_AND_CORE_ATTRS, HDL_LIBRARY_ONLY_ATTRS, HDL_CORE_ONLY_ATTRS, \
  HDL_PRIMITIVES_ONLY_ATTRS

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
       !strcasecmp(xml->name, "hdlprimitives") ? parseHdlPrimitives(xml) :
       !strcasecmp(xml->name, "hdlplatforms") ? parseHdlPlatforms(xml) :
       !strcasecmp(xml->name, "libraries") ? parseLibraries(xml) :
       !strcasecmp(xml->name, "applications") ? parseApplications(xml) :
       !strcasecmp(xml->name, "application") ? parseApplication(xml) :
       "Unknown asset type"))
    return OU::esprintf("For <%s> XML file %s:  %s", topElement, file, err);
  static const char *attrs[] = { ALL_ATTRS, NULL };
  const char *attr;
  for (const char **ap = attrs; *ap; ++ap)
    if ((attr = ezxml_cattr(xml, *ap)))
      printf("%s=%s\n", *ap, attr);
  return NULL;
}
