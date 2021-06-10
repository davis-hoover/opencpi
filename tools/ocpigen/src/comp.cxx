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


#include "comp.h"
#define TESTS "-tests.xml"
#define MS_CONFIG "bypass", "metadata", "throttle", "full"

namespace OL = OCPI::Library;
struct comp;
unsigned matchedWorkers = 0; // count them even if they are not built or usable

const char *
findPackage(ezxml_t spec, const char *package, const char *specName,
            const std::string &parent, const std::string &specFile, std::string &package_out) {
  if (!package)
    package = ezxml_cattr(spec, "package");
  if (package)
    package_out = package;
  else {
    std::string packageFileDir;
    // If the spec name already has a package, we don't use the package file name
    // to determine the package.
    const char *base =
      !strchr(specName, '.') && !specFile.empty() ? specFile.c_str() : parent.c_str();
    const char *cp = strrchr(base, '/');
    const char *err;
    // If the specfile (first) or the implfile (second) has a dir,
    // look there for package name file.  If not, look in the CWD (the worker dir).
    if (cp)
      packageFileDir.assign(base, OCPI_SIZE_T_DIFF(cp + 1, base));

    // FIXME: Fix this using the include path maybe?
    std::string packageFileName = packageFileDir + "package-id";
    if ((err = OU::file2String(package_out, packageFileName.c_str()))) {
      // If that fails, try going up a level (e.g. the top level of a library)
      packageFileName = packageFileDir + "../package-id";
      if ((err = OU::file2String(package_out, packageFileName.c_str()))) {
        // If that fails, try going up a level and into "lib" where it may be generated
        packageFileName = packageFileDir + "../lib/package-id";
        if ((err = OU::file2String(package_out, packageFileName.c_str())))
          return OU::esprintf("Missing package-id file: %s", err);
      }
    }
    for (cp = package_out.c_str(); *cp && isspace(*cp); cp++)
      ;
    package_out.erase(0, OCPI_SIZE_T_DIFF(cp, package_out.c_str()));
    for (cp = package_out.c_str(); *cp && !isspace(*cp); cp++)
      ;
    package_out.resize(OCPI_SIZE_T_DIFF(cp, package_out.c_str()));
  }
  return NULL;
}

const char *
remove(const std::string &name) {
  ocpiInfo("Trying to remove %s", name.c_str());
  int rv = ::system(std::string("rm -r -f " + name).c_str());
  return rv ?
    OU::esprintf("Error removing \"%s\" directory: %d", name.c_str(), rv) :
    NULL;
}
WorkersIter findWorker(const char *name, Workers &ws) {
  for (auto wi = ws.begin(); wi != ws.end(); ++wi) {
      std::string workername; //need the worker name and the model in order to make comparison
      OU::formatAdd(workername, "%s.%s",(*wi)->cname(), (*wi)->m_modelString);
if (!strcasecmp(name, workername.c_str()))
        return wi;
  }
  return ws.end();
}
// If the spec in/out arg may be set in advance if it is inline or xi:included
// FIXME: share this with the one in parse.cxx
const char *getSpec(ezxml_t xml, const std::string &parent, const char *a_package, ezxml_t &spec,
        std::string &specFile, std::string &a_specName) {
  // xi:includes at this level are component specs, nothing else can be included
  spec = NULL;
  std::string name, file;
  const char *err;
  if ((err = tryOneChildInclude(xml, parent, "ComponentSpec", &spec, specFile, true)))
    return err;
  const char *specAttr = ezxml_cattr(xml, "spec");
  if (specAttr) {
    if (spec)
      return "Can't have both ComponentSpec element (maybe xi:included) and a 'spec' attribute";
    size_t len = strlen(specAttr);
    file = specAttr;
    // If the file is suffixed, try it as is.
    if (!strcasecmp(specAttr + len - 4, ".xml") ||
        !strcasecmp(specAttr + len - 5, "-spec") ||
        !strcasecmp(specAttr + len - 5, "_spec"))
      err = parseFile(specAttr, parent, "ComponentSpec", &spec, specFile, false);
    else {
      // If not suffixed, try it, and then with suffixes.
      if ((err = parseFile(specAttr, parent, "ComponentSpec", &spec, specFile, false))) {
        file = specAttr;
        // Try the two suffixes
        file += "-spec";
        if ((err = parseFile(file.c_str(), parent, "ComponentSpec", &spec, specFile, false))) {
          file = specAttr;
          file += "_spec";
          if ((err = parseFile(file.c_str(), parent, "ComponentSpec", &spec, specFile, false)))
            return OU::esprintf("After trying \"-spec\" and \"_spec\" suffixes: %s", err);
        }
      }
    }
  } else {
    if (parent.size()) {
      // No spec mentioned at all, try using the name of the parent file with suffixes
      OU::baseName(parent.c_str(), name);
      const char *dash = strrchr(name.c_str(), '-');
      if (dash)
        name.resize(OCPI_SIZE_T_DIFF(dash, name.c_str()));
    } else {
      OU::baseName(OS::FileSystem::cwd().c_str(), name);
      const char *dot = strrchr(name.c_str(), '.');
      if (dot)
        name.resize(OCPI_SIZE_T_DIFF(dot, name.c_str()));
    }
    // Try the two suffixes
    file = name + "-spec";
    if ((err = parseFile(file.c_str(), parent, "ComponentSpec", &spec, specFile, false))) {
      file =  name + "_spec";
      const char *err1 = parseFile(file.c_str(), parent, "ComponentSpec", &spec, specFile, false);
      if (err1) {
        // No spec files are found, how about a worker with the same name?
        // (if no spec, must be a single worker with embedded spec?)
        bool found = false;
        for (OS::FileIterator iter("../", name + ".*"); !iter.end(); iter.next()) {
          std::string wname;
          const char *suffix = strrchr(iter.relativeName(wname), '.') + 1;
          if (strcmp(suffix, "test")) {
            OU::format(file, "../%s/%s.xml", wname.c_str(), name.c_str());
            if ((err1 =
                  parseFile(file.c_str(), parent, NULL, &spec, specFile, false, false, false))) {
              ocpiInfo("When trying to open and parse \"%s\":  %s", file.c_str(), err1);
              continue;
            }
            if (!ezxml_cchild(spec, "componentspec")) {
              ocpiInfo("When trying to parse \"%s\":  no embedded ComponentSpec element found",
                        file.c_str());
              continue;
            }
            if (found)
              return OU::esprintf("When looking for workers matching \"%s\" with embedded "
                                  "specs, found more than one", name.c_str());
            found = true;
            specName = name; // package?
          }
        }
        if (!found)
          return OU::esprintf("After trying \"-spec\" and \"_spec\" suffixes, no spec found");
      }
    }
  }
  std::string fileName;
  // This is a component spec file or a worker OWD that contains a componentspec element
  if ((err = getNames(spec, specFile.c_str(), NULL, name, fileName)))
    return err;
  // If name is file name, strip suffixes for name.
  if (name == fileName) {
    size_t len = name.length();
    if (len > 5 && (!strcasecmp(name.c_str() + len - 5, "-spec") ||
                    !strcasecmp(name.c_str() + len - 5, "_spec")))
      name.resize(len - 5);
  }
  // Find the package even though the spec package might be specified already
  argPackage = a_package;
  if (strchr(name.c_str(), '.'))
    a_specName = name;
  else {
    if ((err = findPackage(spec, a_package, a_specName.c_str(), parent, specFile, specPackage)))
      return err;
    a_specName = specPackage + "." + name;
  }
  if (verbose)
    fprintf(stderr, "Spec is \"%s\" in file \"%s\"\n",
            a_specName.c_str(), specFile.c_str());
  return NULL;
}

inline bool comp::operator() (const WorkerConfig &lhs, const WorkerConfig &rhs) const {
  // Are all the non-impl parameter values the same?
  // Since they are all from the same spec the order will be the same
    if (lhs.second < rhs.second)
      return false;
    if (lhs.second > rhs.second)
      return true;
      for (unsigned p = 0; p < lhs.first->params.size(); ++p) {
      //      if (lhs.first->params[p].m_param->m_isImpl)
      //        break;
      int c = lhs.first->params[p].m_uValue.compare(rhs.first->params[p].m_uValue);
      if (c < 0)
        return true;
      if (c > 0)
        break;
      }
      return false;
  }
