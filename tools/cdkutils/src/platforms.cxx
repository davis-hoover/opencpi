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

// Utility functions relating to available platforms.

#include <string.h>
#include <cstdlib>
#include <fnmatch.h>
#include "ocpi-config.h"
#include "OcpiOsFileIterator.h"
#include "OcpiOsFileSystem.h"
#include "OcpiUtilCppMacros.h"
#include "OcpiUtilMisc.h"
#include "cdkutils.h"

namespace OS = OCPI::OS;
namespace OU = OCPI::Util;
namespace OF = OCPI::OS::FileSystem;

namespace {

typedef std::vector<std::string> StringArray;
StringArray hdlPrimitivePath;
StringArray componentPath;
StringArray projectPath; // includes current project, OCPI_PROJECT_PATH, dependencies
StringSet oclPlatforms; bool oclPlatformsDone;
StringSet rccPlatforms; bool rccPlatformsDone;
StringSet hdlPlatforms; bool hdlPlatformsDone;
StringSet allPlatforms; bool allPlatformsDone;
StringSet oclTargets;
StringSet rccTargets;
StringSet hdlTargets;
StringSet allTargets; bool allTargetsDone;

// Add directories that must exist, based on an environment variable that contains
// one or more things that may require prefixes or suffixes
static const char *
addPlaces(const char *envname, const char *prefix, const char *suffix, bool check, StringArray &list) {
  const char *env = getenv(envname);
  ocpiInfo("Path %s is: %s", envname, env ? env : "<not set>");
  for (OU::TokenIter ti(env, ": "); ti.token(); ti.next()) {
    bool isDir;
    std::string whole = (prefix ? prefix : "");
    if (prefix && prefix[strlen(prefix)-1] != '/')
      whole += '/';
    whole += std::string(ti.token());
    if (suffix) {
      if (suffix[0] != '/')
	whole += '/';
      whole += suffix;
    }
    ocpiLog(10, "Adding: %s", whole.c_str());
    if (OF::exists(whole, &isDir) && isDir)
      list.push_back(whole);
    else if (check)
      return OU::esprintf("in %s, \"%s\" is not a directory", envname, whole.c_str());
  }
  return NULL;
}
const char *
addPlatform(const char *name, StringSet &platforms) {
  platforms.insert(name);
  allPlatforms.insert(name);
  return NULL;
}
const char *
addTarget(const char *name, StringSet &targets) {
  targets.insert(name);
  allTargets.insert(name);
  return NULL;
}
}

// The (localized) price of multiple error reporting models...
// FIXME: change OU::getCDK to use return strings or at least have an inner function that does.
static const char *
getCdkDir(std::string &cdk) {
  std::string err;
  try {
    cdk = OU::getCDK();
  } catch (std::string &e) {
    err = e;
  } catch (const char *e) {
    err = e;
  } catch (std::exception &e) {
    err = e.what();
  } catch (...) {
    err = "Unexpected exception";
  }
  return err.empty() ? NULL :
    OU::esprintf("Error finding CDK: %s", err.c_str());
}

const char *
getPrereqDir(std::string &dir) {
  const char *env = getenv("OCPI_PREREQUISITES_DIR");
  if (env)
    dir = env;
  else {
    std::string cdk;
    const char *err = getCdkDir(cdk);
    if (err)
      return err;
    dir = cdk + "/../prerequisites";
    if (!OF::exists(dir))
      dir = "/opt/opencpi/prerequisites";
  }
  bool isDir;
  if (OF::exists(dir, &isDir) && isDir) {
    ocpiDebug("OCPI_PREREQUISITES_DIR: %s", env);
    return NULL;
  }
  return
    OU::esprintf("OpenCPI prerequisites directory \"%s\" does not exist or is not a directory",
		 dir.c_str());
}

const char *
getRccPlatforms(const StringSet *&platforms) {
  platforms = &rccPlatforms;
  if (rccPlatformsDone)
    return NULL;
  const char *err;
  std::string dir;
  if ((err = getCdkDir(dir)))
    return err;
  // THIS IS BROKEN FIND OUT WHO NEEDS THIS AND FIX IT TO LOOK IN PROJECTS for rcc/platforms
  dir += "/platforms";
  for (OS::FileIterator it(dir, "*"); !it.end(); it.next())
    if (it.isDirectory()) {
      std::string abs, rel, target;
      OU::format(target, "%s/%s-target.mk", it.absoluteName(abs), it.relativeName(rel));
      if (OF::exists(target))
	addPlatform(rel.c_str(), rccPlatforms);
    }
  rccPlatformsDone = true;
  return NULL;
}

static const char *
addLibs(const char *libs, OrderedStringSet &dirs, OrderedStringSet &nonSlashes) {
  for (OU::TokenIter ti(libs); ti.token(); ti.next())
    if (strchr(ti.token(), '/')) {
      std::string withLib(ti.token());
      withLib += "/lib";
      if (!OF::exists(withLib)) {
	if (OF::exists(ti.token()))
	  withLib = ti.token();
        else
	  return OU::esprintf("Component library at \"%s\" does not exist or is not built.", ti.token());
      }
      dirs.push_back(withLib);
    } else
      nonSlashes.push_back(ti.token());
  return NULL;
}
static const char
  PROJECT_MK[] = "Project.mk",
  PROJECT_XML[] = "Project.xml",
  PROJECT_REL_DIR_ENV[] = "OCPI_PROJECT_REL_DIR";
static const char *
getProjectRelDir(std::string &dir) {
  const char *env = getenv(PROJECT_REL_DIR_ENV);
  if (env)
    dir = env;
  else {
    OF::FileId dot, dotdot;
    std::string up;
    for (up = "./"; !OF::exists(up + PROJECT_MK) && !OF::exists(up + PROJECT_XML); up += "../")
      if (!OF::exists(up + ".", NULL, NULL, NULL, &dot) ||
	  !OF::exists(up + "..", NULL, NULL, NULL, &dotdot) ||
	  dot == dotdot) {
	return OU::esprintf("Could not find containing project directory (i.e. count not find \"%s\""
			    " nor \"%s\" in any parent directory", PROJECT_MK, PROJECT_XML);
      }
    env = up == "./" ? up.c_str() : up.c_str() + 2;
    ocpiCheck(setenv(PROJECT_REL_DIR_ENV, env, 1) == 0);
    dir = env;
  }
  return NULL;
}

// This implementation mirrors the one in util./mk for OcpiXmlComponentLibraries
// I.e. implements the same search rules
const char *
getComponentLibraries(const char *libs, const char *model, bool topSpecs, OrderedStringSet &places) {
  // First pass just take the slash-containing ones
  OrderedStringSet dirs, nonSlashes;
  const char *err;
  if ((err = addLibs(libs, dirs, nonSlashes)) ||
      (err = addLibs(getenv("OCPI_COMPONENT_LIBRARIES"), dirs, nonSlashes)))
    return err;
  if (projectPath.empty()) {
    std::string imports;
    if ((err = getProjectRelDir(imports)))
      return err;
    imports += "/imports/";
    if ((err = addPlaces(PROJECT_REL_DIR_ENV, NULL, NULL, true, projectPath)) ||
	(err = addPlaces("OCPI_PROJECT_PATH", NULL, NULL, true, projectPath)) ||
	(err = addPlaces("OCPI_PROJECT_DEPENDENCIES", imports.c_str(), NULL, true, projectPath)))
      return err;
  }
  StringSet found;
  for (auto pit = projectPath.begin(); pit != projectPath.end(); ++pit) {
    ocpiInfo("For component library search, considering project dir: %s", pit->c_str());
    std::string pDir(*pit);
    if (pit != projectPath.begin() && OF::exists(pDir + "/exports"))
      pDir += "/exports";
    for (auto it = nonSlashes.begin(); it != nonSlashes.end(); ++it) {
      std::string dir, &lib = *it;
      if (pit == projectPath.begin()) {
	if (lib == "devices" || lib == "cards" || lib == "adapters")
	  dir = pDir + "/hdl/" + lib;
	else if (lib == "components")
	  dir = pDir + "/components";
	else
	  dir = pDir + "/components/" + lib;
	dir += "/lib";
      } else
	dir = pDir + "/lib/" + lib;
      ocpiDebug("Trying DIR: %s", dir.c_str());
      if (OF::exists(dir)) {
	found.insert(lib);
	dirs.push_back(dir);
      }
    }
    std::string dir(pDir + "/specs");
    if (topSpecs && OF::exists(dir))
      dirs.push_back(dir);
  }
  for (auto it = nonSlashes.begin(); it != nonSlashes.end(); ++it)
    if (found.find(*it) == found.end())
      return OU::esprintf("component library \"%s\" not found in this project or any one it depends on",
			  it->c_str());
  for (auto it = dirs.begin(); it != dirs.end(); ++it) {
    ocpiDebug("Final dir: %s", it->c_str());
    const char *slash = strrchr(it->c_str(), '/');
    assert(slash);
    if (model && strcmp(slash + 1, "specs")) {
      places.push_back(*it + "/hdl");
      if (model)
	places.push_back(*it + "/" + model);
    }
    places.push_back(*it);
  }
  return NULL;
}

const char *
getHdlPrimitive(const char *primitive, const char */*type*/, OrderedStringSet &prims) {
  const char
    *dot = strrchr(primitive, '.'),
    *packageId = getenv("OCPI_PROJECT_PACKAGE"),
    *projectDir = getenv("OCPI_PROJECT_REL_DIR");
  std::string prim, dir;
  if (dot) {
    const char *lib = dot + 1;
    std::string project(primitive, OCPI_SIZE_T_DIFF(dot, primitive));
    if (project == packageId)
      OU::format(dir, "%s/hdl/primitives/lib/%s", projectDir, lib);
    else
      OU::format(dir, "%s/imports/%s/exports/lib/hdl/%s", projectDir, project.c_str(), lib);
    prim = dir + ":";
    for (const char *cp = primitive; *cp; ++cp)
      prim += *cp == '.' ? '_' : *cp;
    if (!OF::exists(dir)) { // not built
      if (project == packageId) {
	OU::format(dir, "%s/hdl/primitives/%s", projectDir, lib);
	OU::ewprintf("for primitive library \"%s\", it %s", primitive,
			  OF::exists(dir) ? "has not yet been built" : "does not exist in this project");
      } else
	OU::ewprintf("for primitive library \"%s\", it has not been built and exported from the %p project",
		     primitive, project.c_str());
    }
    // Note we cannot produce an error here since it is legitimate to "build" workers for no targets,
    // E.g. to simply generate the skeleton or even to simply export the OWD.
  } else {
    StringArray places;
    const char *err;
    OU::format(dir, "%s/hdl/primitives/lib", projectDir);
    places.push_back(dir);
    std::string imports;
    if ((err = getProjectRelDir(imports)))
      return err;
    imports += "/imports/";
    // It is ok if there are no primitives in these projects
    if ((err = addPlaces("OCPI_PROJECT_PATH", NULL, "/exports/lib/hdl", false, places)) ||
	(err = addPlaces("OCPI_PROJECT_DEPENDENCIES", imports.c_str(), "/exports/lib/hdl", false, places)))
      return err;
    for (auto it = places.begin(); prim.empty() && it != places.end(); ++it) {
      std::string file;
      OU::format(file, "%s/%s/%s.libs", it->c_str(), primitive, primitive);
      if (OF::exists(file)) {
	std::string libs;
	if ((err = OU::file2String(libs, file.c_str())))
	  return err;
	for (OU::TokenIter ti(libs, "\n"); ti.token(); ti.next()) {
	  const char *cp = ti.token();
	  while (isspace(*cp)) cp++;
	  if (*cp != '#') {
	    OU::format(prim, "%s/%s:", it->c_str(), primitive);
	    if (it == places.begin() && *cp == 'q') { // if local and qualified
	      for (cp = packageId; *cp; ++cp)
		prim += *cp == '.' ? '_' : *cp;
	      prim += '_';
	    }
	    prim += primitive;
	    break;
	  }
	}
      }
    }
    if (prim.empty()) {
      OU::format(dir, "%s/hdl/primitives/%s", projectDir, primitive);
      if (OF::exists(dir)) {
	OU::ewprintf("primitive library \"%s\" found in this project but not built", primitive);
	OU::format(prim, "%s/hdl/primitives/lib/%s:%s", projectDir, primitive, primitive);
      } else {
	OU::ewprintf("primitive library \"%s\" not found/built in this project or other "
			  "projects it depends on", primitive);
	OU::format(prim, "%s:%s", primitive, primitive);
      }
    }
  }
  prims.push_back(prim);
  return NULL;
}

const char *
getHdlPlatforms(const StringSet *&platforms) {
  platforms = &hdlPlatforms;
  if (hdlPlatformsDone)
    return NULL;
#if 1
  const char *env = getenv("OCPI_ALL_HDL_PLATFORMS");
  if (!env)
    return "The environment variable OCPI_ALL_HDL_PLATFORMS is expected to be set internally";
  for (OU::TokenIter ti(env); ti.token(); ti.next())
    addPlatform(ti.token(), hdlPlatforms);
#else
  const char *err;
  std::string cdk;
  StringArray places;
  if ((err = getCdkDir(cdk)) ||
      (err = addPlaces("OCPI_HDL_PLATFORM_PATH", NULL, NULL, true, places)) ||
      (err = addPlaces("OCPI_PROJECT_PATH", NULL, "/hdl/platforms", false, places)))
    return err;
  places.push_back(cdk + "/lib/platforms"); // this must exist
  for (unsigned n = 0; n < places.size(); n++) {
    ocpiDebug("Looking for HDL platforms in: %s", places[n].c_str());
    const char *slash = strrchr(places[n].c_str(), '/');
    assert(slash);
    if (!strcmp(++slash, "platforms")) {
      std::string dir(slash);
      dir = places[n] + "/mk";
      if (OF::exists(dir))
	for (OS::FileIterator it(dir, "*.mk"); !it.end(); it.next()) {
	  std::string p(it.relativeName());
	  p.resize(p.size() - 3);
	  addPlatform(p.c_str(), hdlPlatforms);
	}
      else
	for (OS::FileIterator it(places[n], "*"); !it.end(); it.next()) {
	  std::string p(it.relativeName()), s, abs;
	  if (OF::exists(OU::format(s, "%s/%s.xml", it.absoluteName(abs), p.c_str())) ||
	      OF::exists(OU::format(s, "%s/lib/hdl/%s.xml", abs.c_str(), p.c_str())) ||
	      OF::exists(OU::format(s, "%s/hdl/%s.xml", abs.c_str(), p.c_str())))
	    if ((err = doHdlPlatform(abs)))
		return err;
	}
    } else if ((err = doHdlPlatform(places[n])))
      return err;
  }
#endif
  hdlPlatformsDone = true;
  return NULL;
}

const char *
getOclPlatforms(const StringSet *&platforms) {
  const char *err;
  platforms = &oclPlatforms;
  if (oclPlatformsDone)
    return NULL;
  std::string ocpiocl;
  if ((err = getCdkDir(ocpiocl)))
    return err;
  OU::formatAdd(ocpiocl, "/%s%s%s%s/bin/ocpiocl",
		OCPI_CPP_STRINGIFY(OCPI_PLATFORM),
		!OCPI_DEBUG || OCPI_DYNAMIC ? "-" : "",
		OCPI_DYNAMIC ? "d" : "",
		OCPI_DEBUG ? "" : "o");
  std::string cmd;
  OU::format(cmd, "%stest test && %s targets", ocpiocl.c_str(), ocpiocl.c_str());
  FILE *out;
  if ((out = popen(cmd.c_str(), "r")) == NULL)
    return OU::esprintf("Could not execute the \"ocpiocl targets\" command");
  std::string targets;
  for (int c; (c = fgetc(out)) != EOF; targets += (char)c)
    ;
  for (OU::TokenIter ti(targets.c_str()); ti.token(); ti.next()) {
    const char *eq = strchr(ti.token(), '=');
    if (!eq)
      return OU::esprintf("Invalid output from the \"ocpiocl targets\" command:  \"%s\"",
			  targets.c_str());
    std::string platform(ti.token(), OCPI_SIZE_T_DIFF(eq, ti.token()));
    oclPlatforms.insert(platform);
  }
  oclPlatformsDone = true;
  return NULL;
}

// Get it two ways.  If OCPI_ALL_PLATFORMS is provided we use it.  Otherwise we look around.
const char *
getAllPlatforms(const StringSet *&platforms, Model m) {
  if (!allPlatformsDone) {
    const char *env = getenv("OCPI_ALL_PLATFORMS");
    if (env)
      for (const char *ep; *env; env = ep) {
	while (isspace(*env)) env++;
	for (ep = env; *ep && !isspace(*ep); ep++)
	  ;
	if ((ep - env) < 5)
	  return OU::esprintf("the environment variable OCPI_ALL_PLATFORMS (\"%s\") is invalid",
			      env);
	std::string p;
	p.assign(env, OCPI_SIZE_T_DIFF((ep - 4), env));
	if (!strncmp(ep - 4, ".rcc", 4))
	  addPlatform(p.c_str(), rccPlatforms);
	else if (!strncmp(ep - 4, ".hdl", 4))
	  addPlatform(p.c_str(), hdlPlatforms);
	else if (!strncmp(ep - 4, ".ocl", 4))
	  addPlatform(p.c_str(), oclPlatforms);
	else
	  return OU::esprintf("the environment variable OCPI_ALL_PLATFORMS (\"%s\") is invalid",
			      env);
      }
    else {
      const char *err;
      const StringSet *dummy;
      if ((err = getRccPlatforms(dummy)) ||
	  (err = getHdlPlatforms(dummy)) ||
	  (err = getOclPlatforms(dummy)))
	return err;
    }
    allPlatformsDone = true;
  }
  switch (m) {
  case NoModel: platforms = &allPlatforms; break;
  case RccModel: platforms = &rccPlatforms; break;
  case OclModel: platforms = &oclPlatforms; break;
  case HdlModel: platforms = &hdlPlatforms; break;
  default:
    return "unsupported model for platforms";
  }
  return NULL;
}

// Parse the attribute value, validating it, and expanding it if wildcard
// Do not bother to determine whether each platform is valid unless
// 'onlyValidPlatforms' is set to true
const char *
getPlatforms(const char *attr, OrderedStringSet &platforms, Model m, bool onlyValidPlatforms) {
  if (!attr)
    return NULL;
  const char *err;
  const StringSet *universe;
  if ((err = getAllPlatforms(universe, m)))
    return err;
  for (OU::TokenIter ti(attr); ti.token(); ti.next()) {
    bool found;
    for (StringSetIter si = universe->begin(); si != universe->end(); ++si)
      if (fnmatch(ti.token(), (*si).c_str(), FNM_CASEFOLD) == 0) {
	found = true;
	platforms.push_back(*si);
      }
    if (!found && onlyValidPlatforms)
      return OU::esprintf("the string \"%s\" does not indicate or match any known platforms",
			    ti.token());
  }
  return NULL;
}

// Get it two ways.  If OCPI_ALL_TARGETS is provided we use it.  Otherwise we look around.
const char *
getAllTargets(const StringSet *&targets, Model m) {
  if (!allTargetsDone) {
    const char *env;
    if ((env = getenv("OCPI_ALL_HDL_TARGETS")))
      for (OU::TokenIter ti(env); ti.token(); ti.next())
	addTarget(ti.token(), hdlTargets);
    else
      ocpiInfo("the environment variable OCPI_ALL_HDL_TARGETS is not set");
    if ((env = getenv("OCPI_ALL_RCC_TARGETS")))
      for (OU::TokenIter ti(env); ti.token(); ti.next())
	addTarget(ti.token(), rccTargets);
    else
      ocpiInfo("the environment variable OCPI_ALL_RCC_TARGETS is not set");
    allTargetsDone = true;
  }
  switch (m) {
  case NoModel: targets = &allTargets; break;
  case RccModel: targets = &rccTargets; break;
  case HdlModel: targets = &hdlTargets; break;
  default:
    return "unsupported model for targets";
  }
  return NULL;
}

// Parse the attribute value, validating it, and expanding it if wildcard
const char *
getTargets(const char *attr, OrderedStringSet &targets, Model m) {
  if (!attr)
    return NULL;
  const char *err;
  const StringSet *universe;
  if ((err = getAllTargets(universe, m)))
    return err;
  for (OU::TokenIter ti(attr); ti.token(); ti.next()) {
    bool found;
    for (StringSetIter si = universe->begin(); si != universe->end(); ++si)
      if (fnmatch(ti.token(), (*si).c_str(), FNM_CASEFOLD) == 0) {
	found = true;
	targets.push_back(*si);
      }
    if (!found)
      return OU::esprintf("the string \"%s\" does not indicate or match any targets", ti.token());
  }
  return NULL;
}
std::list<std::string>::iterator OrderedStringSet::
find(const std::string &s) {
  for (auto si = begin(); si != end(); ++si)
    if (s == *si)
      return si;
  return end();
}
void OrderedStringSet::push_back(const std::string &s) {
  if (find(s) == end())
    std::list<std::string>::push_back(s);
}
