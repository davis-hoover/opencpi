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

// Process the tests.xml file.
#include <strings.h>
#include <sstream>
#include <set>
#include <limits>
#include <algorithm>
#include "OcpiOsDebugApi.h"
#include "OcpiOsFileSystem.h"
#include "OcpiUtilMisc.h"
#include "OcpiUtilEzxml.h"
#include "OcpiLibraryManager.h"
#include "wip.h"
#include "data.h"
#include "hdl-device.h"
#include "comp.h"
#include "input-output.h"
#include "cases.h"

#define TESTS "-tests.xml"
#define MS_CONFIG "bypass", "metadata", "throttle", "full"

namespace OL = OCPI::Library;

// Called for all workers globally acceptable workers and the one emulator if present
static void
addNonParameterProperties(Worker &w, ParamConfig &globals) {
  for (PropertiesIter pi = w.m_ctl.properties.begin(); pi != w.m_ctl.properties.end(); ++pi) {
    OU::Property &p = **pi;
    if (p.m_isParameter || !p.m_isWritable)
      continue;
    std::string name;
    Param::fullName(p, &w, name);
    bool found = false;
    for (unsigned n = 0; n < globals.params.size(); n++) {
      Param &param = globals.params[n];
      if (param.m_param && !strcasecmp(param.m_name.c_str(), name.c_str())) {
        found = true;
        break;
      }
    }
    if (found)
      continue;
    // New, non-parameter property never seen - could be worker-specific
    globals.params.resize(globals.params.size()+1);
    Param &param = globals.params.back();
    param.setProperty(&p, p.m_isImpl || w.m_emulate ? &w : NULL);
    if (p.m_default) {
      p.m_default->unparse(param.m_uValue);
      param.m_uValues.resize(1);
      param.m_attributes.resize(1);
      param.m_uValues[0] = param.m_uValue;
    }
  }
}
const char *
createTests(const char *file, const char *package, const char */*outDir*/, bool a_verbose) {
  verbose = a_verbose;
  const char *err;
  std::string parent, specFile;
  ezxml_t xml, xspec;
  if (!file || !file[0]) {
    static char x[] = "<tests/>";
    xml = ezxml_parse_str(x, strlen(x));
  } else if ((err = parseFile(file, parent, "tests", &xml, testFile, false, false, false)) ||
             (err = OE::checkAttrs(xml, "spec", "timeout", "duration","onlyWorkers",
                                   "excludeWorkers", "useHDLFileIo", "mode", "onlyPlatforms",
                                   "excludePlatforms", "finishPort", "doneWorkerIsUUT", NULL)) ||
             (err = OE::checkElements(xml, "property", "case", "input", "output", NULL)))
    return err;
  // This is a convenient way to specify XML include dirs in component libraries
  // This will be parsed again for build/Makefile purposes.
  // THIS MUST BE IN SYNC WITH THE gnumake VERSION in util.mk! Ugh.
  OrderedStringSet dirs;
  if ((err = getComponentLibraries(ezxml_cattr(xml, "componentlibraries"), NULL, true, dirs)))
    return err;
  for (auto it = dirs.begin(); it != dirs.end(); ++it)
    addInclude(*it);
  // ================= 1. Get the spec
  if ((err = getSpec(xml, testFile, package, xspec, specFile, specName)) ||
      (err = OE::getNumber(xml, "duration", &duration)) ||
      (err = OE::getNumber(xml, "timeout", &timeout)))
    return err;
  if (!duration && !timeout)
    // Set a default timeout value of 3600.  This value is
    // "unfortunate", and based on some of the "zed" tests.
    timeout = 3600;
  // ================= 2. Get/find/include/exclude the global workers
  // Parse global workers
  const char
    *excludeWorkersAttr = ezxml_cattr(xml, "excludeWorkers"),
    *onlyWorkersAttr = ezxml_cattr(xml, "onlyWorkers");
  if (onlyWorkersAttr) {
    // We will only look at workers mentioned here
    if (excludeWorkersAttr)
      return OU::esprintf("the onlyWorkers and excludeWorkers attributes cannot both occur");
    if ((err = OU::parseList(onlyWorkersAttr, addWorker)))
      return err;
  } else  if ((excludeWorkersAttr && (err = OU::parseList(excludeWorkersAttr, excludeWorker))) ||
              (err = findWorkers()))
    return err;
  if (excludeWorkersTmp.size() && verbose)
    for (StringsIter si = excludeWorkersTmp.begin(); si != excludeWorkersTmp.end(); ++si)
      fprintf(stderr, "Warning:  excluded worker \"%s\" never found.\n", si->c_str());
  // ================= 3. Get/collect the worker parameter configurations
  // Now "workers" has workers with parsed build files.
  // So next we globally enumerate PCs independent of them, that might be dependent on them.
  if (workers.empty()) { // AV-3369 (and possibly others)
    if (matchedWorkers) {
      const char *e =
        "Workers were found that matched the spec, but none were built, so no tests generated";
      if (verbose)
        fprintf(stderr, "%s\n", e);
      ocpiInfo("%s", e);
      return NULL;
    }
    return OU::esprintf("There are currently no valid workers implementing %s", specName.c_str());
  }
  // But first!... we create the first one from the defaults.
  wFirst = *workers.begin();
  for (WorkersIter wi = workers.begin(); wi != workers.end(); ++wi) {
    Worker &w = **wi;
    for (unsigned c = 0; c < w.m_paramConfigs.size(); ++c) {
      ocpiDebug("Inserting worker %s.%s/%p with new config %p/%zu", w.m_implName,
                w.m_modelString, &w, w.m_paramConfigs[c], w.m_paramConfigs[c]->nConfig);
      ocpiCheck(configs.insert(std::make_pair(w.m_paramConfigs[c], &w)).second);
    }
  }
  // ================= 4. Derive the union set of values from all configurations
  // Next, parse all global values into a special set for all tests that don't specify values.
  // This is different from the defaults and may have multiple values.
  ParamConfig globals(*wFirst);
  for (WorkerConfigsIter wci = configs.begin(); wci != configs.end(); ++wci) {
    ParamConfig &pc = *wci->first;
    ocpiDebug("Processing config %zu of worker %s.%s",
              pc.nConfig, pc.worker().cname(), pc.worker().m_modelString);
    for (unsigned n = 0; n < pc.params.size(); n++) {
      Param &p = pc.params[n];
      if (p.m_param == NULL)
        continue;
      assert(p.m_param->m_isParameter);
      size_t pn;
      assert(p.m_name.length());
      // See if the (implementation-qualified) name is in the globals yet
      unsigned nn;
      for (nn = 0; nn < globals.params.size(); nn++) {
        Param &gp = globals.params[nn];
        if (!gp.m_param)
          continue;
        assert(gp.m_name.length());
        if (!strcasecmp(p.m_name.c_str(), globals.params[nn].m_name.c_str())) {
          pn = nn;
          break;
        }
      }
      if (nn >= globals.params.size()) {
        pn = globals.params.size();
        globals.params.push_back(p); // add to end
        globals.params.back().m_worker = &pc.worker();// remember which worker it came from
      }
      Param &gp = globals.params[pn];
      if (!gp.m_param)
        gp.setProperty(p.m_param, p.m_worker);
      ocpiDebug("existing value for %s(%u) is %s(%zu)",
                p.m_param->cname(), n, p.m_uValue.c_str(), pn);
      for (nn = 0; nn < gp.m_uValues.size(); nn++)
        if (p.m_uValue == gp.m_uValues[nn])
          goto next;
      if (!gp.m_valuesType) {
        gp.m_valuesType = &p.m_param->sequenceType();
        gp.m_valuesType->m_default = new OU::Value(*gp.m_valuesType);
      }
      gp.m_valuesType->m_default->parse(p.m_uValue.c_str(), NULL, gp.m_uValues.size() != 0);
      gp.m_uValues.push_back(p.m_uValue);
      gp.m_attributes.push_back(Param::Attributes());
    next:;
    }
  }
  // ================= 4a. Parse and collect global non-parameter property values from workers
  for (WorkersIter wi = workers.begin(); wi != workers.end(); ++wi)
    addNonParameterProperties(**wi, globals);
  if (emulator)
    addNonParameterProperties(*emulator, globals);
  // ================= 4b. Add "empty" values for parameters that are not in all workers
  for (WorkerConfigsIter wci = configs.begin(); wci != configs.end(); ++wci) {
    ParamConfig &pc = *wci->first;
    // Check if any properties have no values.
    for (unsigned n = 0; n < globals.params.size(); n++) {
      Param &gparam = globals.params[n];
      if (!gparam.m_param)
        continue;
      for (unsigned nn = 0; nn < pc.params.size(); nn++) {
        Param &p = pc.params[nn];
        if (!p.m_param)
          continue;
        if (!strcasecmp(gparam.m_param->cname(), p.m_param->cname()))
          goto found;
      }
      // A globally defined property was not found in this worker config, so we must add
      // an empty value if there is not one already and there is no default
      {
        std::string defValue;
        if (gparam.m_param->m_default)
          gparam.m_param->m_default->unparse(defValue);
        for (auto it = gparam.m_uValues.begin(); it != gparam.m_uValues.end(); ++it)
          if (it->empty() || (*it) == defValue)
            goto found;
      }
      // AV-3372: We shouldn't do this if the property is generated, but we cannot tell at this point if it is.
      // gparam.m_generate is empty because it's from the worker XML. We will remove this later if needed.
      ocpiDebug("Adding empty value for property %s because it is not in worker %s.%s(%zu)",
                gparam.m_param->cname(), pc.worker().cname(), pc.worker().m_modelString,
                pc.nConfig);
      gparam.m_uValues.push_back("");
      gparam.m_attributes.push_back(Param::Attributes());
    found:;
    }
  }
  // ================= 5. Parse and collect global property values specified for all cases
  // Parse explicit/default property values to apply to all cases
#define TEST_ATTRS "generate", "add", "only", "exclude", "test"
  for (ezxml_t px = ezxml_cchild(xml, "property"); px; px = ezxml_cnext(px)) {
    std::string name;
    bool isTest;
    if ((err = OE::getRequiredString(px, name, "name")) ||
        (err = OE::getBoolean(px, "test", &isTest)) ||
        (err = (isTest ?
                OE::checkAttrs(px, PARAM_ATTRS, TEST_ATTRS, OCPI_UTIL_MEMBER_ATTRS, NULL) :
                OE::checkAttrs(px, PARAM_ATTRS, TEST_ATTRS, NULL))))
      return err;
    Param *found = NULL;
    // First pass, look for correctly scoped names in the Param (including worker.model.prop).
    for (unsigned n = 0; n < globals.params.size(); n++) {
      Param &p = globals.params[n];
      if (p.m_param && !strcasecmp(name.c_str(), p.m_name.c_str())) {
        if (isTest)
          return OU::esprintf("The test property \"%s\" is already a worker property",
                              name.c_str());
        found = &p;
        break;
      }
    }
    if (!found) {
      // Second pass for backward compatibility, with warnings, when a property name is not qualified
      for (unsigned n = 0; n < globals.params.size(); n++) {
        Param &p = globals.params[n];
        if (p.m_param && !strcasecmp(name.c_str(), p.m_param->cname())) {
          if (isTest)
            return OU::esprintf("The test property \"%s\" is already a worker property",
                                name.c_str());
          if (found)
            return OU::esprintf("Ambiguous property \"%s\" is worker-specific in multiple workers (%s and %s)",
                                p.m_param->cname(), p.m_worker->cname(), found->m_worker->cname());
          found = &p;
          break;
        }
      }
      if (found) {
        assert(found->m_param && found->m_param->m_isImpl);
        fprintf(stderr, "Warning:  property \"%s\" is worker-specific and should be identified as %s.%s.%s\n",
                found->m_param->cname(), found->m_worker->cname(), found->m_worker->m_modelString,
                found->m_param->cname());
      } else if (!isTest)
        return OU::esprintf("There is no property named \"%s\" for any worker", name.c_str());
    }
    if (isTest) {
      assert(!found);
      globals.params.resize(globals.params.size()+1);
      found = &globals.params.back();
      OU::Property &newp = *new OU::Property();
      found->m_isTest = true;
      char *copy = ezxml_toxml(px);
      // Make legal property definition XML out of this xml
      ezxml_t propx;
      if ((err = OE::ezxml_parse_str(copy, strlen(copy), propx)))
        return err;
      ezxml_set_attr(propx, "test", NULL);
      ezxml_set_attr(propx, "value", NULL);
      ezxml_set_attr(propx, "values", NULL);
      ezxml_set_attr(propx, "valuefile", NULL);
      ezxml_set_attr(propx, "valuesfile", NULL);
      ezxml_set_attr(propx, "initial", "1");
      if ((err = newp.Member::parse(propx, false, true, NULL, "property", 0)))
        return err;
      found->setProperty(&newp, NULL);
      // We allow a test property to be specified with no values (values only in cases)
      if (!ezxml_cattr(px, "value") &&
          !ezxml_cattr(px, "values") &&
          !ezxml_cattr(px, "valuefile") &&
          !ezxml_cattr(px, "valuesfile") &&
          !ezxml_cattr(px, "generate"))
        continue;
    }
    if ((err = found->parse(px, NULL, NULL, true)))
      return err;
  }
  // Check if any properties have no values.
  for (unsigned n = 0; n < globals.params.size(); n++) {
    Param &param = globals.params[n];
    if (!param.m_param)
      continue;
    const OU::Property &p = *param.m_param;
    if (!p.m_isParameter && p.m_isWritable && param.m_uValues.empty())
      fprintf(stderr,
              "Warning:  no values for writable property with no default: \"%s\" %zu %zu\n",
              p.cname(), param.m_uValues.size(), param.m_uValue.size());
  }
  // ================= 6. Parse and collect global platform and worker values
  finishPort = ezxml_cattr(xml, "finishPort");
  doneWorkerIsUUT = ezxml_cattr(xml, "doneWorkerIsUUT");
  // Parse global platforms
  const char
    *excludes = ezxml_cattr(xml, "excludePlatforms"),
    *onlys = ezxml_cattr(xml, "onlyPlatforms");
  if (!excludes)
    excludes = ezxml_cattr(xml, "exclude");
  if (!onlys)
    onlys = ezxml_cattr(xml, "only");
  if (onlys) {
    if (excludes)
      return OU::esprintf("the only and exclude attributes cannot both occur");
    if ((err = getPlatforms(onlys, onlyPlatforms)))
      return err;
  } else if (excludes && (err = getPlatforms(excludes, excludePlatforms)))
    return err;
  // ================= 7. Parse and collect global input/output specs
  // Parse global inputs and outputs
  if ((err = OE::ezxml_children(xml, "input", doInputOutput)) ||
      (err = OE::ezxml_children(xml, "output", doInputOutput)))
    return err;
  // ================= 8. Parse the specified cases (if any)
  if (!ezxml_cchild(xml, "case")) {
    static char c[] = "<case/>";
    ezxml_t x = ezxml_parse_str(c, strlen(c));
    if ((err = Case::doCase(x, &globals)))
      return err;
  } else if ((err = OE::ezxml_children(xml, "case", Case::doCase, &globals)))
    return err;
    std::cout << cases.size() << "Cases \n";
    std::cout << c[0] << "Cases \n";
  // ================= 9. Report what we found globally (not specific to any case)
  // So now we can generate cases based on existing configs and globals.
  if (OS::logGetLevel() >= OCPI_LOG_INFO) {
    fprintf(stderr,
            "Spec is %s, in file %s, %zu workers, %zu configs\n"
            "Configurations are:\n",
            specName.c_str(), specFile.c_str(), workers.size(), configs.size());
    unsigned c = 0;
    for (WorkerConfigsIter wci = configs.begin(); wci != configs.end(); ++wci, ++c) {
      ParamConfig &pc = *wci->first;
      fprintf(stderr, "  %2u: (from %s.%s)\n",
              c, pc.worker().cname(), pc.worker().m_modelString);
      for (unsigned n = 0; n < pc.params.size(); n++) {
        Param &p = pc.params[n];
        if (p.m_param == NULL)
          continue;
        fprintf(stderr, "      %s = %s%s\n", p.m_param->cname(), p.m_uValue.c_str(),
                p.m_isDefault ? " (default)" : "");
      }
    }
  }

  // ================= 10. Generate report in gen/cases.txt on all combinations of property values
  OS::FileSystem::mkdir("gen", true);
  std::string summary;
  OU::format(summary, "gen/cases.txt");
  if (verbose)
    fprintf(stderr, "Writing cases/subcases report in \"%s\"\n", summary.c_str());
  FILE *out = fopen(summary.c_str(), "w");
  fprintf(out,
          "Values common to all property combinations:\n"
          "===========================================\n");
  for (unsigned n = 0; n < globals.params.size(); n++) {
    Param &p = globals.params[n];
    if (p.m_param == NULL || p.m_uValues.size() != 1 || !p.m_generate.empty())
      continue;
    p.m_uValue = p.m_uValues[0];
    fprintf(out, "      %s = %s", p.m_param->cname(),
            p.m_uValues[0].empty() ? "<no value>" : p.m_uValues[0].c_str());
    if (p.m_param->m_isImpl && strncasecmp("ocpi_", p.m_param->cname(), 5)) {
      assert(p.m_worker);
      fprintf(out, " (specific to worker %s.%s)",
              p.m_worker->m_implName, p.m_worker->m_modelString);
    }
    fprintf(out, "\n");
  }
#if 0
  fprintf(out, "\n"
          "Property combinations/subcases that are default for all cases:\n"
          "==============================================================\n"
          "    ");
  for (unsigned n = 0; n < globals.params.size(); n++) {
    Param &p = globals.params[n];
    if (p.m_param && p.m_uValues.size() > 1)
      fprintf(out, "  %s", p.m_param->cname());
  }
  fprintf(out, "\n");
  bool first = true;
  doProp(globals, out, 0, 0, first);
#endif
  // ================= 11. Generate HDL assemblies in gen/assemblies
  if (verbose)
    fprintf(stderr, "Generating required HDL assemblies in gen/assemblies\n");
  bool hdlFileIO;
  if ((err = OE::getBoolean(xml, "UseHdlFileIO", &hdlFileIO)))
    return err;
  const char *env = getenv("OCPI_FORCE_HDL_FILE_IO");
  if (env)
    hdlFileIO = env[0] == '1';
  bool seenHDL = false;
  Strings assyDirs;
  std::string assemblies("gen/assemblies");
  for (WorkersIter wi = workers.begin(); wi != workers.end(); ++wi) {
    Worker &w = **wi;
    if (w.m_model == HdlModel) {
      ocpiInfo("Generating assemblies for worker: %s", w.m_implName);
      assert(w.m_paramConfigs.size());
      for (unsigned c = 0; c < w.m_paramConfigs.size(); ++c) {
        ParamConfig &pc = *w.m_paramConfigs[c];
        // Make sure the configuration is in the test matrix (e.g. globals)
        bool allOk = true;
        for (unsigned n = 0; allOk && n < pc.params.size(); n++) {
          Param &p = pc.params[n];
          bool isOk = false;
          if (p.m_param)
            for (unsigned nn = 0; nn < globals.params.size(); nn++) {
              Param &gp = globals.params[nn];
              if (gp.m_param && !strcasecmp(p.m_param->cname(), gp.m_param->cname()))
                for (unsigned v = 0; v < gp.m_uValues.size(); v++)
                  if (p.m_uValue == gp.m_uValues[v]) {
                    isOk = true;
                    break;
                  }
            }
          if (!isOk)
            allOk = false;
        }
        if (!allOk)
          continue; // skip this config - it is not in the test matrix
        if (!seenHDL) {
          OS::FileSystem::mkdir(assemblies, true);
          OU::string2File("include $(OCPI_CDK_DIR)/include/hdl/hdl-assemblies.mk\n",
                          (assemblies + "/Makefile").c_str(), true);
          seenHDL = true;
        }
        std::string name(w.m_implName);
        OU::formatAdd(name, "_%u", c);
        std::string dir(assemblies + "/" + name);
        ocpiInfo("Generating assembly: %s", dir.c_str());
        //there's always at least one case if there's a -test.xml
        if ((err = generateHdlAssembly(w, c, dir, name, false, assyDirs, cases[0]->m_ports)))
          return err;
        if (testingOptionalPorts) {
          for (unsigned n = 0; n < cases.size(); n++) {
            std::ostringstream temp; //can't use to_string
            temp << n;
            if ((err = generateHdlAssembly(w, c, dir + "_op_" + temp.str(), name + "_op_" + temp.str(), false, assyDirs, cases[n]->m_ports)))
              return err;
          }
        }
        if (hdlFileIO) {
          name += "_frw";
          dir += "_frw";
          if ((err = generateHdlAssembly(w, c, dir, name, true, assyDirs, cases[0]->m_ports)))
            return err;
          if (testingOptionalPorts) {
            for (unsigned n = 0; n < cases.size(); n++) {
              std::ostringstream temp; //can't use to_string
              temp << n;
              if ((err = generateHdlAssembly(w, c, dir + "_op_" + temp.str(), name + "_op_" + temp.str(), true, assyDirs, cases[n]->m_ports)))
                return err;
            }
          }
        }
      }
    }
  }
  // Cleanup any assemblies that were not just generated
  assyDirs.insert("Makefile");
  for (OS::FileIterator iter(assemblies, "*"); !iter.end(); iter.next())
    if (assyDirs.find(iter.relativeName()) == assyDirs.end() &&
        (err = remove(assemblies + "/" + iter.relativeName())))
      return err;

  // ================= 12. Generate subcases for each case, and generate outputs per subcase
  fprintf(out,
          "\n"
          "Descriptions of the %zu case%s and %s subcases:\n"
          "==============================================\n",
          cases.size(), cases.size() > 1 ? "s" : "", cases.size() > 1 ? "their" : "its");
  for (unsigned n = 0; n < cases.size(); n++) {
    cases[n]->m_subCases.push_back(new ParamConfig(cases[n]->m_settings));
    cases[n]->doProp(0);
    if ((err = cases[n]->pruneSubCases()))
      return err;
    cases[n]->print(out);
  }
  fclose(out);
  if (verbose)
    fprintf(stderr, "Generating required input and property value files in gen/inputs/ and "
            "gen/properties/\n");
  for (unsigned n = 0; n < cases.size(); n++)
    if ((err = cases[n]->generateInputs()))
      return err;
  std::string dir("gen/applications");
  if (verbose)
    fprintf(stderr, "Generating required application xml files in %s/\n", dir.c_str());
  Strings appFiles;
  for (unsigned n = 0; n < cases.size(); n++)
    if ((err = cases[n]->generateApplications(dir, appFiles)) ||
        (err = cases[n]->generateVerification(dir, appFiles)))
      return err;
  for (OS::FileIterator iter(dir, "*"); !iter.end(); iter.next())
    if (appFiles.find(iter.relativeName()) == appFiles.end() &&
        (err = remove(dir + "/" + iter.relativeName())))
      return err;
#if 1
  if ((err = openOutput("cases", "gen", "", "", ".xml", NULL, out)))
    return err;
#else
  out = fopen("gen/cases.xml", "w");
  if (!out)
    return OU::esprintf("Failed to open summary XML file gen/cases.xml");
#endif
  if (verbose)
    fprintf(stderr, "Generating summary gen/cases.xml file\n");
  fprintf(out, "<cases spec='%s'", wFirst->m_specName);
  if (emulator)
    fprintf(out, " emulator='%s'", emulatorName());
  fprintf(out, ">\n");
  if ((err = getPlatforms("*", allPlatforms)))
    return err;
  for (unsigned n = 0; n < cases.size(); n++)
    if ((err = cases[n]->generateCaseXml(out)))
      return err;
  fprintf(out, "</cases>\n");
  if (fclose(out))
    return OU::esprintf("Failed to write open summary XML file gen/cases.xml");
  return NULL;
}

// The arguments are platforms determined in the runtime environment
const char *
createCases(const char **platforms, const char */*package*/, const char */*outDir*/, bool a_verbose) {
  struct CallBack : public OL::ImplementationCallback {
    std::string m_spec, m_model, m_platform, m_component, m_dir, m_err;
    bool m_dynamic;
    ezxml_t m_xml;
    bool m_first;
    FILE *m_run, *m_verify;
    std::string m_outputArgs, m_verifyOutputs;
    const char *m_outputs;
    typedef std::map<std::string, std::string> Runs;
    typedef Runs::const_iterator RunsIter;
    typedef std::pair<std::string, std::string> RunsPair;
    Runs m_runs; // for this platform, what runs are done
    CallBack(const char *spec, const char *model, const char *platform, bool dynamic,
             ezxml_t xml)
      : m_spec(spec), m_model(model), m_platform(platform), m_dynamic(dynamic), m_xml(xml),
        m_first(true), m_run(NULL), m_verify(NULL), m_outputs(NULL) {
      const char *cp = strrchr(spec, '.');
      m_component = cp ? cp + 1 : spec;
    }
    ~CallBack() {
      if (m_run) {
        for (RunsIter ri = m_runs.begin(); ri != m_runs.end(); ++ri)
          fprintf(m_run, "%s", ri->second.c_str());
        fprintf(m_run, "exit $failed\n");
        fclose(m_run);
      }
      if (m_verify)
        fclose(m_verify);
    }
#if 0
    void doOutput(const char *output) {
      bool multiple = strchr(m_outputs, ',') != NULL;
      OU::formatAdd(m_outputArgs, " -pfile_write%s%s=fileName=$5.$6.$4.$3.%s.out",
                    multiple ? "_" : "", multiple ? output : "", output);
      OU::formatAdd(m_verifyOutputs, " %s", output);
    }
    static const char *doOutput(const char *output, void *me) {
      ((CallBack*)me)->doOutput(output);
      return NULL;
    }
#endif
    static bool found(const char *platform, const char *list) {
      size_t len = strlen(platform);
      const char *p = list ? strstr(list, platform) : NULL;
      return p && (!p[len] || isspace(p[len])) && (p == list || isspace(p[-1]));
    }
    static bool included(const char *platform, ezxml_t x) {
      const char
        *exclude = ezxml_cattr(x, "exclude"),
        *only = ezxml_cattr(x, "only");
      if (!exclude)
	exclude = ezxml_cattr(x, "excludeplatforms");
      if (!only)
	only = ezxml_cattr(x, "onlyplatforms");
      return
        (!exclude || !found(platform, exclude)) &&
        (!only || found(platform, only));
    }
    bool foundImplementation(const OL::Implementation &i, bool &accepted) {
      ocpiInfo("For platform %s, considering worker %s.%s from %s platform %s dynamic %u",
               m_platform.c_str(), i.m_metadataImpl.cname(), i.m_metadataImpl.model().c_str(),
               i.m_artifact.name().c_str(), i.m_artifact.platform().c_str(),
               i.m_artifact.dynamic());
      if (i.m_artifact.platform() == m_platform && i.m_metadataImpl.model() == m_model &&
          i.m_artifact.dynamic() == m_dynamic) {
        unsigned sn = 0;
        for (ezxml_t cx = ezxml_cchild(m_xml, "case"); cx; cx = ezxml_cnext(cx)) {
          const char *name = ezxml_cattr(cx, "name");
          for (ezxml_t sx = ezxml_cchild(cx, "subcase"); sx; sx = ezxml_cnext(sx), sn++)
            if (included(m_platform.c_str(), sx)) {
	      const char *id = ezxml_cattr(sx, "id");
	      size_t n;
	      ocpiCheck(id && !OE::getUNum(id, &n));
              for (ezxml_t wx = ezxml_cchild(sx, "worker"); wx; wx = ezxml_cnext(wx))
                if (!strcmp(i.m_metadataImpl.cname(), ezxml_cattr(wx, "name")) &&
                    i.m_metadataImpl.model() == ezxml_cattr(wx, "model")) {
                  ocpiInfo("Accepted for case %s subcase %zu from file: %s", name, n,
                           i.m_artifact.name().c_str());
                  if (m_first) {
                    m_first = false;
                    std::string dir("run/" + m_platform);
                    OS::FileSystem::mkdir(dir, true);
                    std::string file(dir + "/run.sh");
                    if (verbose)
                      fprintf(stderr, "  Generating run script for platform: %s\n",
                              m_platform.c_str());
                    if (!(m_run = fopen(file.c_str(), "w"))) {
                      OU::format(m_err, "Cannot open file \"%s\" for writing", file.c_str());
                      return true;
                    }
		    const char *em = ezxml_cattr(m_xml, "emulator");
		    fprintf(m_run,
                            "#!/bin/bash --noprofile\n" // no arg (at least to dash) to suppress reading .profile etc.
                            "# Note that this file runs on remote/embedded systems and thus\n"
                            "# may not have access to the full development host environment\n"
                            "failed=0\n"
                            ". $OCPI_CDK_DIR/scripts/testrun.sh %s %s \"%s\" $* - %s\n",
                            m_spec.c_str(), m_platform.c_str(), em ? em : "", ezxml_cattr(wx, "outputs"));
                  }
                  const char
                    *to = ezxml_cattr(sx, "timeout"),
                    *du = ezxml_cattr(sx, "duration"),
                    *w = ezxml_cattr(wx, "name"),
                    *o = ezxml_cattr(wx, "outputs");
                  std::string doit;
                  OU::format(doit, "docase %s %s %s %02zu %s %s %s\n", m_model.c_str(), w, name, n,
                             to ? to : "0", du ? du : "0", o);
                  std::string key;
                  OU::format(key, "%08u %s", sn, w);
                  m_runs.insert(RunsPair(key, doit));
                }
	    }
        }
        accepted = true;
      }
      return false;
    }
  };
  const char *err;
  std::string registry, path;
  if ((err = OU::getProjectRegistry(registry)))
    return err;
  OU::format(path, "../lib/rcc:../lib/ocl:gen/assemblies:%s/ocpi.core/artifacts",
             registry.c_str());
  setenv("OCPI_LIBRARY_PATH", path.c_str(), true);
  ocpiInfo("Initializing OCPI_LIBRARY_PATH to \"%s\"", path.c_str());
  verbose = a_verbose;
  ezxml_t xml;
  if ((err = OE::ezxml_parse_file("gen/cases.xml", xml)))
    return err;
  const char *spec = ezxml_cattr(xml, "spec");
  assert(spec);
  if (verbose)
    fprintf(stderr, "Generating execution scripts for each platform that can run.\n");
  OS::FileSystem::mkdir("run", true);
  for (const char **p = platforms; *p; p++) {
    ocpiDebug("Trying platform %s", *p);
    std::string model;
    const char *cp = strchr(*p, '-');
    assert(cp);
    model.assign(*p, OCPI_SIZE_T_DIFF(cp, *p));
    CallBack cb(spec, model.c_str(), cp + 3, cp[1] == '1', xml);
    OL::Manager::findImplementations(cb, ezxml_cattr(xml, "spec"));
    if (cb.m_err.size())
      return OU::esprintf("While processing platform %s: %s", cp + 1, cb.m_err.c_str());
  }
  return NULL;
}