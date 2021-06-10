#include <cstddef>
#include <string>
#include <strings.h>
#include <cassert>
#include <vector>
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
#include "parameters.h"
#include "hdl-device.h"
#include "wip.h"
#include "data.h"
#include "comp.h"
#include "input-output.h"
#include "cases.h"

#define TESTS "-tests.xml"
#define MS_CONFIG "bypass", "metadata", "throttle", "full"

namespace OL = OCPI::Library;

struct Case;

const char *doExcludePlatform(const char *a_platform, void *arg) {
  Case &c = *(Case *)arg;
  OrderedStringSet platforms;
  const char *err;
  if ((err = getPlatforms(a_platform, platforms)))
    return err;
  for (auto pi = platforms.begin(); pi != platforms.end(); ++pi) {
    const char *platform = pi->c_str();
    if (excludePlatforms.find(platform) != excludePlatforms.end()) {
     fprintf(stderr, "Warning:  for case \"%s\", excluded platform \"%s\" is already "
        "globally excluded\n", c.m_name.c_str(), platform);
      return NULL;
      }
    if (onlyPlatforms.size() && onlyPlatforms.find(platform) == onlyPlatforms.end()) {
      //If there is a global onlyPlatforms list, only exclude things from that list
      fprintf(stderr, "Warning:  for case \"%s\", excluded platform \"%s\" is not in the "
        "global only platforms\n", c.m_name.c_str(), platform);
      return NULL;
      }
    if ((err = doPlatform(platform, c.m_excludePlatforms)))
      return err;
  }
  return NULL;
}

const char *doOnlyPlatform(const char *a_platform, void *arg) {
  Case &c = *(Case *)arg;
  OrderedStringSet platforms;
  const char *err;
  if ((err = getPlatforms(a_platform, platforms)))
    return err;
  for (auto pi = platforms.begin(); pi != platforms.end(); ++pi) {
    const char *platform = pi->c_str();
    if (excludePlatforms.find(platform) != excludePlatforms.end())
      return OU::esprintf("For case \"%s\", only platform \"%s\" is globally excluded",
        c.m_name.c_str(), platform);
    if (onlyPlatforms.size() && onlyPlatforms.find(platform) == onlyPlatforms.end())
        return OU::esprintf("For case \"%s\", only platform \"%s\" is not in global list",
          c.m_name.c_str(), platform);
    if ((err = doPlatform(platform, c.m_onlyPlatforms)))
      return err;
  }
  return NULL;
}

const char *doOnlyWorker(const char *worker, void *arg) {
  Case &c = *(Case *)arg;
  if (excludeWorkers.find(worker) != excludeWorkers.end())
    return
      OU::esprintf("For case \"%s\", only worker \"%s\" is globally excluded",
                    c.m_name.c_str(), worker);
  WorkersIter wi;
  if ((wi = findWorker(worker, workers)) == workers.end()) //checking against global worker list
    return OU::esprintf("For case \"%s\", only worker \"%s\" is not a known worker",
                        c.m_name.c_str(), worker);
  return doWorker(*wi, &c.m_workers);
}

const char *doExcludeWorker(const char *worker, void *arg) {
  Case &c = *(Case *)arg;
  if (excludeWorkers.find(worker) != excludeWorkers.end())
    return OU::esprintf("excluded worker \"%s\" is already globally excluded", worker);
  WorkersIter wi;
  if ((wi = findWorker(worker, c.m_workers)) == c.m_workers.end()) {
    fprintf(stderr, "Warning:  for case \"%s\", excluded worker \"%s\" is not a potential worker",
                  c.m_name.c_str(), worker);
    return NULL;
  }
  c.m_workers.erase(wi);
  return NULL;
}

const char *doCase(ezxml_t cx, void *globals) {
  Case *c = new Case(*(ParamConfig *)globals);
  const char *err;
  if ((err = c->parse(cx, cases.size()))) {
    delete c;
    return err;
  }
  cases.push_back(c);
  return NULL;
}

const char *doPorts(Worker &w, ezxml_t x) {
  for (unsigned n = 0; n < w.m_ports.size(); n++)
    if (w.m_ports[n]->isData()) {
      Port &p = *w.m_ports[n];
      DataPort &dp = *static_cast<DataPort *>(&p);
      const char *a, *err, *tag = dp.isDataProducer() ? "output" : "input";
      InputOutput *myIo = NULL;
      for (ezxml_t iox = ezxml_cchild(x, tag); iox; iox = ezxml_cnext(iox))
        if ((a = ezxml_cattr(iox, "port")) && !strcasecmp(p.pname(), a)) {
          // explicit io for port - either ref to global or complete one here.
          if ((a = ezxml_cattr(iox, "name"))) {
            InputOutput *ios = findIO(a, dp.isDataProducer() ? outputs : inputs);
            if (!ios)
              return OU::esprintf("No global %s defined with name: \"%s\"", tag, a);
            ios->m_port = &dp;
            m_ports.push_back(*ios);
            myIo = &m_ports.back();
          } else {
            m_ports.resize(m_ports.size() + 1);
            myIo = &m_ports.back();
            if ((err = myIo->parse(iox, NULL)))
              return err;
          }
          break;
        }
      if (!myIo) {
        // no explicit reference to global input and no locally defined input
        InputOutput *ios = findIO(p, dp.isDataProducer() ? outputs : inputs);
        if (!ios) {
          if (dp.isDataProducer()) {
            ios = new InputOutput;
            ios->m_port = &dp;
            fprintf(stderr, "Warning:  no output file or script defined for port \"%s\"\n",
                    dp.pname());
          } else
            return OU::esprintf("No global %s defined for port: \"%s\"", tag, p.pname());
        }
        m_ports.push_back(*ios);
      }
    }
  return NULL;
}

// FIXME: this code is redundant with the OcpiUtilAssembly.cxx
const char *parseDelay(ezxml_t sx, const OU::Property &p) {
  const char *err;
  if ((err = OE::checkAttrs(sx, "delay", "value", NULL)) ||
      (err = OE::checkElements(sx, NULL)))
    return err;
  if (p.m_isTest)
    return "delayed property settings are not allowed for test properties";
  // We are preparsing these delays to produce earlier errors, otherwise we could just
  // save the XML and attach it to the generated apps
  OU::ValueType vt(OA::OCPI_Double);
  OU::Value v(vt);
  const char
    *delay = ezxml_cattr(sx, "delay"),
    *value = ezxml_cattr(sx, "value");
    if (!delay || !value)
      return "<set> elements must contain both \"delay\" and \"value\" attributes";
  if ((err = v.parse(delay)))
    return err;
  v.m_Double *= 1e6;
  if (v.m_Double < 0 || v.m_Double >= std::numeric_limits<uint32_t>::max())
    return OU::esprintf("delay value \"%s\"(%g) out of range, 0 to %g", delay, v.m_Double/1e6,
                    (double)std::numeric_limits<uint32_t>::max()/1e6);
  v.setType(p);
  if ((err = v.parse(value)))
    return err;
  ocpiDebug("Adding delay for:  <property name='%s' delay='%s' value='%s'/>",
            p.cname(), delay, value);
  OU::formatAdd(m_delays, "    <property name='%s' delay='%s' value='%s'/>\n",
                p.cname(), delay, value);
  // add to some list
  return NULL;
}

// Parse a case
const char *parse(ezxml_t x, size_t ordinal) {
  const char *err, *a;
  if ((a = ezxml_cattr(x, "name")))
    m_name = a;
  else
    OU::format(m_name, "case%02zu", ordinal);
  if ((err = OE::checkAttrs(x, "duration", "timeout", "onlyplatforms", "excludeplatforms",
                            "onlyworkers", "excludeworkers", "doneWorkerIsUUT", NULL)) ||
      (err = OE::checkElements(x, "property", "input", "output", NULL)) ||
      (err = OE::getNumber(x, "duration", &m_duration, NULL, duration)) ||
      // (err = OE::getNumber(x, "timeout", &m_timeout, NULL, timeout)) ||
      (err = OE::getNumber(x, "timeout", &m_timeout)) ||
      (err = OE::getBoolean(x, "doneWorkerIsUUT", &m_doneWorkerIsUUT, false, false)))
    return err;
  if (!m_duration) {
    if (!m_timeout)
      m_timeout = timeout;
  }
  else if (m_timeout)
    return OU::esprintf("Specifying both duration and timeout is not supported");
  if ((err = doPorts(*wFirst, x)) || (emulator && (err = doPorts(*emulator, x))))
      return err;
  if ((a = ezxml_cattr(x, "onlyworkers"))) {
    if (ezxml_cattr(x, "excludeworkers"))
      return OU::esprintf("the onlyWorkers and excludeWorkers attributes cannot both occur");
    if ((err = OU::parseList(a, doOnlyWorker, this)))
      return err;
  } else {
    m_workers = workers;
    if ((a = ezxml_cattr(x, "excludeworkers")) && (err = OU::parseList(a, doExcludeWorker, this)))
      return err;
  }
  // The only time the onlyplatforms= or excludeplatforms= attributes have an effect in the gen/case.xml
  // is at the subcase level, not case or cases, so the global lists of only/excludedPlatforms
  // must be added to each case's individual lists (m_excludePlatforms and m_onlyPlatforms)
  // there's a check earlier to make sure both onlyPlatforms and excludePlatforms
  // aren't set at the same time
  // global level excludePlatforms is added to case level excludePlatforms here
  // onlyPlatforms is handled later
  if (excludePlatforms.size())
      m_excludePlatforms.insert(excludePlatforms.begin(), excludePlatforms.end());

  if ((a = ezxml_cattr(x, "onlyplatforms"))) {
    if (ezxml_cattr(x, "excludeplatforms"))
      return OU::esprintf("the onlyplatforms and excludeplatforms attributes cannot both occur");
    if ((err = OU::parseList(a, doOnlyPlatform, this)))
      return err;
  } else if ((a = ezxml_cattr(x, "excludeplatforms")) &&
              (err = OU::parseList(a, doExcludePlatform, this)))
    return err;
  // Parse explicit property values for this case, which will override
  for (ezxml_t px = ezxml_cchild(x, "property"); px; px = ezxml_cnext(px)) {
    if ((err = OE::checkAttrs(px, PARAM_ATTRS, "generate", "add", "only", "exclude", NULL)) ||
        (err = OE::checkElements(px, "set", NULL)))
      return err;
    std::string name;
    if ((err = OE::getRequiredString(px, name, "name")))
      return err;
// The input name can be worker-qualified or not.
    Param *found = NULL, *wfound = NULL;
bool qname = strchr(name.c_str(), '.') != NULL;
    for (unsigned n = 0; n < m_settings.params.size(); n++) {
      Param &sp = m_settings.params[n];
      if (sp.m_param) {
  const char *dot = strrchr(sp.m_name.c_str(), '.');
  // Note we are looking at the param name, not the property name, which allows us to
  // specifically name worker-specific properties (name.model.property)
  if (!strcasecmp(sp.m_name.c_str(), name.c_str())) { // whole (maybe qualified) name match
    if (qname) {
assert(!wfound && !found); // can't happen
wfound = &sp;
    } else { // found an unqualified name - we should only find one
assert(!wfound && !found && (sp.m_isTest || !sp.m_param->m_isImpl));
found = &sp;
    }
  } else if (!qname && dot && !strcasecmp(dot + 1, name.c_str())) { // matched the last part
    assert(!wfound);
    if (found && !sp.m_worker->m_emulate)
return OU::esprintf("Error:  Property name \"%s\" matches more than one worker-specific "
        "property and is ambiguous.  Worker-specific properties "
        "can be prefixed by worker name and model,"
        " e.g. wkr1.rcc.prop1", name.c_str());

    found = &sp;
  }
}
}
if (!found)
found = wfound;
    if (!found)
      return OU::esprintf("Property name \"%s\" not a spec or test property (worker-specific "
        "properties must be prefixed by worker name and model, e.g. wkr1.rcc.prop1)",
        name.c_str());
// poor man's: any xml attributes? e.g. if not only "set" element?
if (px->attr && px->attr[0] &&
  (strcasecmp(px->attr[0], "name") || (px->attr[2] && strcasecmp(px->attr[2], "name"))) &&
  (err = found->parse(px, NULL, NULL, true)))
return err;
    for (ezxml_t sx = ezxml_cchild(px, "set"); sx; sx = ezxml_cnext(sx))
      if ((err = parseDelay(sx, *found->m_param)))
        return err;
  }
  return NULL;
}

void
doProp(unsigned n) {
  ParamConfig &c = *m_subCases.back();
  while (n < c.params.size() && (!c.params[n].m_param || !c.params[n].m_generate.empty() ||
                                  c.params[n].m_uValues.empty()))
    n++;
  if (n >= c.params.size())
    return;
  Param &p = c.params[n];
  for (unsigned nn = 0; nn < p.m_uValues.size(); ++nn) {
    if (nn)
      m_subCases.push_back(new ParamConfig(c));
    m_subCases.back()->params[n].m_uValue = p.m_uValues[nn];
    doProp(n + 1);
  }
}

const char *
pruneSubCases() {
  ocpiDebug("Pruning subcases for case %s starting with %zu subcases",
            m_name.c_str(), m_subCases.size());
  for (unsigned s = 0; s < m_subCases.size(); s++) {
    ocpiDebug("Considering pruning subcase %s.%u",  m_name.c_str(), s);
    ParamConfig &pc = *m_subCases[s];
    // For each worker configuration, decide whether it can support the subcase.
    // Note worker configs only have *parameters*, while subcases can have runtime properties
    unsigned viableConfigs = 0;
    for (WorkerConfigsIter wci = configs.begin(); wci != configs.end(); ++wci) {
      ParamConfig &wcfg = *wci->first;
      ocpiDebug("--Considering worker %s.%s(%zu)", wci->second->cname(),
                wci->second->m_modelString, wci->first->nConfig);
      // For each property in the subcase, decide whether it conflicts with a *parameter*
      // in this worker config
      for (unsigned nn = 0; nn < pc.params.size(); nn++) {
        Param &sp = pc.params[nn];
        if (sp.m_param == NULL)
          continue;
        OU::Property *wprop = wci->second->findProperty(sp.m_param->cname());
        for (unsigned n = 0; n < wcfg.params.size(); n++) {
          Param &wparam = wcfg.params[n];
          if (wparam.m_param && !strcasecmp(sp.m_param->cname(), wparam.m_param->cname())) {
            if (sp.m_uValue == wparam.m_uValue)
              goto next;     // match - this subcase property is ok for this worker config
            ocpiDebug("--Skipping worker %s.%s(%zu) because its param %s is different",
                      wci->second->cname(), wci->second->m_modelString,
                      wci->first->nConfig, sp.m_param->cname());
            goto skip_worker_config; // mismatch - this worker config rejected from subcase
          }
        }
        // The subcase property was not found as a parameter in the worker config
        if (wprop) {
          // But it is a runtime property in the worker config so it is ok
          assert(!wprop->m_isParameter);
          continue; // do next subcase parameter/property
        }
        // The subcase property is for the emulator, which is ok
        if (sp.m_worker && sp.m_worker->m_emulate)
          continue;
        // The subcase property was not in this worker at all, so it must be
        // implementation specific or a test property or an emulator property
        if (sp.m_param->m_isImpl && sp.m_uValue.size()) {
          if (sp.m_param->m_default) {
            std::string uValue;
            sp.m_param->m_default->unparse(uValue);
            if (sp.m_uValue == uValue)
              // The subcase property is the default value so it is ok for the worker
              // to not have it at all.
              continue;
          }
          // The impl property is not the default so this worker config cannot be used
          ocpiDebug("Skipping worker %s.%s(%zu) because param %s(%s) is impl-specific and %s",
                    wci->second->cname(), wci->second->m_modelString, wci->first->nConfig,
                    sp.m_param->cname(), sp.m_uValue.c_str(),
                    sp.m_param->m_default ? " the value does not match the default" :
                    "there is no default to check");
          goto skip_worker_config;
        }
        // The property is a test property which is ok
      next:;
      }
      viableConfigs++;
    skip_worker_config:;
    }
    if (viableConfigs == 0) {
      ocpiDebug("Removing subcase %u since no workers implement it", s);
      m_subCases.erase(m_subCases.begin() + s);
      s--;
    }
  }
  return m_subCases.size() == 0 ?
    OU::esprintf("For case %s, there are no valid parameter combinations for any worker",
                  m_name.c_str()) : NULL;
}

void
print(FILE *out) {
  fprintf(out, "Case %s:\n", m_name.c_str());
  table(out);
  for (unsigned s = 0; s < m_subCases.size(); s++) {
    fprintf(out, "  Subcase %02u:\n",s);
    ParamConfig &pc = *m_subCases[s];
    for (unsigned n = 0; n < pc.params.size(); n++) {
      Param &p = pc.params[n];
      if (p.m_param) {
        if (p.m_generate.empty())
          fprintf(out, "    %s = %s\n", p.m_param->cname(), p.m_uValue.c_str());
        else
          fprintf(out, "    %s = generated in file: gen/properties/%s.%02u.%s\n",
                  p.m_param->cname(), m_name.c_str(), s, p.m_param->cname());
      }
    }
  }
}

void
table(FILE *out) {
  std::vector<size_t> sizes(m_settings.params.size(), 0);
  std::vector<const char *> last(m_settings.params.size(), NULL);
  bool first = true;
  for (unsigned n = 0; n < m_settings.params.size(); n++) {
    Param &p = m_settings.params[n];
    if (p.m_param && p.m_uValues.size() > 1) {
      sizes[n] = p.m_param->m_name.length() + 2;
      for (unsigned u = 0; u < p.m_uValues.size(); u++)
        sizes[n] = std::max(sizes[n], p.m_uValues[u].length());
      if (first) {
        fprintf(out, "  Summary of subcases\n");
        fprintf(out, "  Subcase # ");
        first = false;
      }
      fprintf(out, "  %-*s", (int)sizes[n], p.m_param->cname());
    }
  }
  if (first)
    return;
  fprintf(out, "\n  ---------");
  for (unsigned n = 0; n < m_settings.params.size(); n++) {
    Param &p = m_settings.params[n];
    if (p.m_param && p.m_uValues.size() > 1) {
      std::string dashes;
      dashes.assign(sizes[n], '-');
      fprintf(out, "  %s", dashes.c_str());
    }
  }
  fprintf(out, "\n");
  for (unsigned s = 0; s < m_subCases.size(); s++) {
    fprintf(out, "%6u:   ", s);
    ParamConfig &pc = *m_subCases[s];
    for (unsigned n = 0; n < pc.params.size(); n++) {
      Param &p = pc.params[n];
      if (p.m_param && p.m_uValues.size() > 1) {
        fprintf(out, "  %*s", (int)sizes[n],
                last[n] && !strcmp(last[n], p.m_uValue.c_str()) ? "" :
                p.m_uValue.empty() ? "-" : p.m_uValue.c_str());
        last[n] = p.m_uValue.c_str();
      }
    }
    fprintf(out, "\n");
  }
  fprintf(out, "\n");
}

const char *
generateFile(bool &first, const char *dir, const char *type, unsigned s,
              const std::string &name, const std::string &generate, const std::string &env,
              std::string &file) {
  if (verbose && first) {
    fprintf(stderr, "Generating for %s.%02u:\n", m_name.c_str(), s);
    first = false;
  }
  // We have an input port that has a script to generate the file
  file = "gen/";
  file += dir;
  OS::FileSystem::mkdir(file, true);
  OU::formatAdd(file, "/%s.%02u.%s", m_name.c_str(), s, name.c_str());
  // Allow executing from the target dir in case we created some C++ programs
  std::string cmd("PATH=.:$OCPI_TOOL_DIR:$OCPI_PROJECT_DIR/scripts:$PATH ");
  cmd += "PYTHONPATH=$OCPI_PROJECT_DIR/scripts:$PYTHONPATH ";
  cmd += env;
  size_t prefix = cmd.length();
  OU::formatAdd(cmd, " %s %s", generate.c_str(), file.c_str());
  ocpiInfo("For case %s.%02u, executing generator \"%s\" for %s %s: %s", m_name.c_str(), s,
            generate.c_str(), type, name.c_str(), cmd.c_str());
  if (verbose)
fprintf(stderr,
"  Generating %s \"%s\" file: \"%s\"\n"
"    Using command: %s\n",
type, name.c_str(), file.c_str(), cmd.c_str() + prefix);
  int r;
  if ((r = system(cmd.c_str())))
    return OU::esprintf("Error %d(0x%x) generating %s file \"%s\" from command:  %s",
                        r, r, type, file.c_str(), cmd.c_str());
  if (!OS::FileSystem::exists(file))
    return OU::esprintf("No output from generating %s file \"%s\" from command:  %s",
                        type, file.c_str(), cmd.c_str());
  const char *space = strchr(generate.c_str(), ' ');
  std::string path;
  path.assign(generate.c_str(),
  space ? OCPI_SIZE_T_DIFF(space, generate.c_str()) : generate.length());
  if (OS::FileSystem::exists(path))
    addDep(path.c_str(), true);
  return NULL;
}

// Generate inputs: input files
const char *
generateInputs() {
  const char *err;
  for (unsigned s = 0; s < m_subCases.size(); s++) {
    bool first = true;
    ParamConfig &pc = *m_subCases[s];
    std::string env;
    for (unsigned n = 0; n < pc.params.size(); n++) {
      Param &p = pc.params[n];
      if (p.m_param && p.m_generate.empty()) {
        assert(!strchr(p.m_uValue.c_str(), '\''));
        OU::formatAdd(env, "OCPI_TEST_%s='%s' ", p.m_param->cname(), p.m_uValue.c_str());
      }
    }
    std::string file;
    for (unsigned n = 0; n < pc.params.size(); n++) {
      Param &p = pc.params[n];
      if (p.m_param && !p.m_generate.empty()) {
        //
        // Originally, if p.m_uValue was non-empty (due to the parameter
  // having a default value), it needed clearing before generating.
        // OU::file2String() now clears non-empty "out" arguments.
        //
        if ((err = generateFile(first, "properties", "property value", s, p.m_param->m_name,
                                p.m_generate, env, file)) ||
            (err = (p.m_param->needsNewLineBraces() ?
                    OU::file2String(p.m_uValue, file.c_str(), "{", "},{", "}") :
                    OU::file2String(p.m_uValue, file.c_str(), ','))))
          return err;
        //
        // Quick parse --> unparse trip.  This is particularly needed
        // for use of generated '0' and '1' as boolean initializers,
        // and doesn't hurt otherwise.  The parameter type is known.
        //
        p.m_param->parseValue(p.m_uValue.c_str(), p.m_value);
        p.m_value.unparse(p.m_uValue);
        OU::formatAdd(env, "OCPI_TEST_%s='%s' ", p.m_param->cname(), p.m_uValue.c_str());
        OU::formatAdd(env, "OCPI_TESTFILE_%s='%s' ", p.m_param->cname(), file.c_str());
      }
    }

    for (unsigned n = 0; n < m_ports.size(); n++) {
      InputOutput &io = m_ports[n];
      if (io.m_port) {
        if (!io.m_port->isDataProducer() && io.m_script.size()) {
          if ((err = generateFile(first, "inputs", "input port", s,
                                  io.m_port->OU::Port::m_name, io.m_script, env, file)))
            return err;
        }
      }
    }
  }
  return NULL;
}

void
generateAppInstance(Worker &w, ParamConfig &pc, unsigned nOut, unsigned nOutputs, unsigned s,
                    const DataPort *first, bool a_emulator, std::string &app, const char *dut, bool testingOptional) {
  OU::formatAdd(app, "  <instance component='%s' name='%s'", w.m_specName, dut);
  if (nOut == 1 && !testingOptional) {
    if (nOutputs == 1)
      OU::formatAdd(app, " connect='bp'");
    else
      OU::formatAdd(app, " connect='bp_%s_%s'", dut, first->pname());
  }
  bool any = false;
  for (unsigned n = 0; n < pc.params.size(); n++) {
    Param &p = pc.params[n];
    // FIXME: Should m_uValues hold the results of the generate? (AV-3114)
    if (p.m_param && !p.m_isTest &&
        ((p.m_uValues.size() && p.m_uValue.size()) || p.m_generate.size())) {
// If the property is specific to the emulator, don't apply it to the DUT
      if (p.m_worker && p.m_worker->m_emulate && !w.m_emulate)
        continue;
// The emulator should not get the dut's hidden properties
// FIXME: this is overly broad since users may use "hidden" and
// this might present things like "debug" applying to the emulator
      if (w.m_emulate && p.m_param->m_isHidden)
        continue;
      if (p.m_param->m_isImpl && p.m_param->m_default) {
        std::string uValue;
        p.m_param->m_default->unparse(uValue);
        if (uValue == p.m_uValue)
          continue;
      }
      assert(!strchr(p.m_uValue.c_str(), '\''));
      if (!any)
        app += ">\n";
      any = true;
      OU::formatAdd(app, "    <property name='%s' ", p.m_param->cname());
      if (p.m_generate.empty())
        OU::formatAdd(app, "value='%s'", p.m_uValue.c_str());
      else
        OU::formatAdd(app, "valueFile='../../gen/properties/%s.%02u.%s'",
                      m_name.c_str(), s, p.m_param->cname());
      app += "/>\n";
    }
  }
  if (!a_emulator)
    app += m_delays;
  app += any ? "  </instance>\n" : "/>\n";
}

// Generate application xml files, being careful not to write files that are
// not changing
const char *generateApplications(const std::string &dir, Strings &files) {
  const char *err;
  const char *dut = strrchr(wFirst->m_specName, '.');
  bool isOptional = false; // for compiler warning
  if (dut)
    dut++;
  else
    dut = wFirst->m_specName;
  const char *em = emulatorName();
  for (unsigned s = 0; s < m_subCases.size(); s++) {
    ParamConfig &pc = *m_subCases[s];
    OS::FileSystem::mkdir(dir, true);
    std::string name;
    OU::format(name, "%s.%02u.xml", m_name.c_str(), s);
    files.insert(name);
    std::string file(dir + "/" + name);;
    unsigned nOutputs = 0, nInputs = 0, nEmIn = 0, nEmOut = 0, nWIn = 0, nWOut = 0;
    const DataPort *first = NULL, *firstEm = NULL;
    for (unsigned n = 0; n < m_ports.size(); n++)
      if (m_ports[n].m_port) {
  const DataPort &p = *m_ports[n].m_port;
        if (p.isDataProducer()) {
          if (!first)
            first = &p;
          nOutputs++;
          if (&p.worker() == wFirst)
            nWOut++;
          else if (&p.worker() == emulator) {
            if (!firstEm)
              firstEm = &p;
            nEmOut++;
          } else
            assert("port is neither worker or emulator?" == 0);
        } else {
          nInputs++;
          if (&p.worker() == wFirst)
            nWIn++;
          else if (&p.worker() == emulator)
            nEmIn++;
          else
            assert("port is neither worker or emulator?" == 0);
        }
        isOptional = m_ports[n].m_testOptional;
      }
    std::string app("<application");

    // the testrun.sh script has the name "file_write_from..." or "file_write" hardcoded, so
    // the name of the file_write is limited to those options

    if ((optionals.size() >= nOutputs) && isOptional && !finishPort)
      OU::formatAdd(app, " done='%s'", dut);
    else if (doneWorkerIsUUT || m_doneWorkerIsUUT)
      OU::formatAdd(app, " done='%s'", dut);
    else if (nOutputs == 1)
      OU::formatAdd(app, " done='file_write'");
    else if (nOutputs > 1) {
      if (finishPort && wFirst->findPort(finishPort)) {
        OU::formatAdd(app, " done='file_write_from_%s'", finishPort);
      } else if (finishPort && emulator->findPort(finishPort)) {
        OU::formatAdd(app, " done='file_write_from_%s'", finishPort);
      } else {
        OU::formatAdd(app, " done='file_write_from_%s'", (firstEm ? firstEm : first)->pname());
      }
    }
    app += ">\n";
    if (nInputs)
      for (unsigned n = 0; n < m_ports.size(); n++)
        if (!m_ports[n].m_port->isDataProducer()) {
          InputOutput &io = m_ports[n];
          if (!io.m_testOptional) {
            if (&io.m_port->worker() == emulator ) {
              OU::formatAdd(app, "  <instance component='ocpi.core.file_read' connect='%s_ms_%s'", em, io.m_port->pname());
            } else {
              OU::formatAdd(app, "  <instance component='ocpi.core.file_read' connect='%s_ms_%s'", dut, io.m_port->pname());
            }
            if (io.m_messageSize)
              OU::formatAdd(app, " buffersize='%zu'", io.m_messageSize);
            app += ">\n";
            std::string l_file;
            if (io.m_file.size())
              OU::formatAdd(l_file, "%s%s", io.m_file[0] == '/' ? "" : "../../", io.m_file.c_str());
            else
              OU::formatAdd(l_file, "../../gen/inputs/%s.%02u.%s", m_name.c_str(), s, io.m_port->pname());
            OU::formatAdd(app, "    <property name='filename' value='%s'/>\n", l_file.c_str());
            if (io.m_messageSize)
              OU::formatAdd(app, "    <property name='messageSize' value='%zu'/>\n", io.m_messageSize);
            if (io.m_messagesInFile)
              OU::formatAdd(app, "    <property name='messagesInFile' value='true'/>\n");
            if (io.m_suppressEOF)
              OU::formatAdd(app, "    <property name='suppressEOF' value='true'/>\n");
            app += "  </instance>\n";
            if (&io.m_port->worker() == emulator ) {
              OU::formatAdd(app, "  <instance component='ocpi.core.metadata_stressor' name='%s_ms_%s' connect='%s'", em, io.m_port->pname(), em);
            } else {
              OU::formatAdd(app, "  <instance component='ocpi.core.metadata_stressor' name='%s_ms_%s' connect='%s'", dut, io.m_port->pname(), dut);
            }
            if (nInputs > 1)
              OU::formatAdd(app, " to='%s'",  io.m_port->pname());
            app += ">\n";
            if (io.m_msMode == full)
              app += "    <property name='mode' value='full'/>\n"
                      "    <property name='enable_give_lsfr' value='true'/>\n"
                      "    <property name='enable_take_lsfr' value='true'/>\n"
                      "    <property name='insert_nop' value='true'/>\n";
            else if (io.m_msMode == throttle)
              app += "    <property name='mode' value='data'/>\n"
                      "    <property name='enable_give_lsfr' value='true'/>\n"
                      "    <property name='enable_take_lsfr' value='true'/>\n";
            else if (io.m_msMode == metadata)
              app += "    <property name='mode' value='metadata'/>\n";
            app += "  </instance>\n";
          }
        }
    generateAppInstance(*wFirst, pc, nWOut, nOutputs, s, first, false, app, dut, isOptional);
    if (emulator)
      generateAppInstance(*emulator, pc, nEmOut, nOutputs, s, firstEm, true, app, em, false);
    if (nOutputs)
      for (unsigned n = 0; n < m_ports.size(); n++) {
        InputOutput &io = m_ports[n];
        const DataPort &p = *m_ports[n].m_port;
        if (io.m_port->isDataProducer()) {
          if (!io.m_testOptional) {
          OU::formatAdd(app, "  <instance component='ocpi.core.backpressure'");
          if (nOutputs > 1) {
            if (&p.worker() == emulator)
              OU::formatAdd(app, " name='bp_%s_%s' connect='file_write_from_%s'", em,
                            io.m_port->pname(),  io.m_port->pname());
            else
              OU::formatAdd(app, " name='bp_%s_%s' connect='file_write_from_%s'", dut,
                            io.m_port->pname(), io.m_port->pname());
          } else {
            OU::formatAdd(app, " name='bp' connect='file_write'");
          }
          app += ">\n";
          if (!io.m_disableBackpressure)
            OU::formatAdd(app, "    <property name='enable_select' value='true'/>\n");
          app += "  </instance>\n";
          OU::formatAdd(app, "  <instance component='ocpi.core.file_write'");
          // the testrun.sh script has the name "file_write_from..." or "file_write" hardcoded, so
          // the name of the file_write is limited to those options
          if (nOutputs > 1) {
            if (&p.worker() == emulator)
              OU::formatAdd(app, " name='file_write_from_%s'", io.m_port->pname());
            else
              OU::formatAdd(app, " name='file_write_from_%s'", io.m_port->pname());
          }
          if (!io.m_messagesInFile && io.m_stopOnEOF)
            app += "/>\n";
          else {
            app += ">\n";
            if (io.m_messagesInFile)
              OU::formatAdd(app, "    <property name='messagesInFile' value='true'/>\n");
            if (!io.m_stopOnEOF)
              OU::formatAdd(app, "    <property name='stopOnEOF' value='false'/>\n");
            app += "  </instance>\n";
          }
          if (&io.m_port->worker() == wFirst && nWOut > 1)
            OU::formatAdd(app,
                          "  <connection>\n"
                          "    <port instance='%s' name='%s'/>\n"
                          "    <port instance='bp_%s_%s' name='in'/>\n"
                          "  </connection>\n",
                          dut, io.m_port->pname(),
                          dut, io.m_port->pname());
          if (&io.m_port->worker() == emulator && nEmOut > 1)
            OU::formatAdd(app,
                          "  <connection>\n"
                          "    <port instance='%s' name='%s'/>\n"
                          "    <port instance='bp_%s_%s' name='in'/>\n"
                          "  </connection>\n",
                          em, io.m_port->pname(),
                          em, io.m_port->pname());
          }
        }
      }
    app += "</application>\n";
    ocpiDebug("Creating application file in %s containing:\n%s",
              file.c_str(), app.c_str());
    if ((err = OU::string2File(app.c_str(), file.c_str(), false, true)))
      return err;
  }
  return NULL;
}

// Generate the verification script for this case
const char *
generateVerification(const std::string &dir, Strings &files) {
  std::string name;
  OU::format(name, "verify_%s.sh", m_name.c_str());
  files.insert(name);
  std::string file(dir + "/" + name);
  std::string verify;
  OU::format(verify,
              "#!/bin/bash --noprofile\n"
              "# Verification and/or viewing script for case: %s\n"
              "# Args are: <worker> <subcase> <verify> <view>\n"
              "# Act like a normal process if get this signal\n"
              "trap 'exit 130' SIGINT\n"
              "function isPresent {\n"
              "  local key=$1\n"
              "  shift\n"
              "  local vals=($*)\n"
              "  for i in $*; do if [ \"$key\" = \"$i\" ]; then return 0; fi; done\n"
              "  return 1\n"
              "}\n"
              "worker=$1; shift\n"
              "subcase=$1; shift\n"
              "! isPresent run $* || run=run\n"
              "! isPresent view $* || view=view\n"
              "! isPresent verify $* || verify=verify\n"
              "if [ -n \"$verify\" ]; then\n"
              "  if [ -n \"$view\" ]; then\n"
              "    msg=\"Viewing and verifying\"\n"
              "  else\n"
              "    msg=Verifying\n"
              "  fi\n"
              "elif [ -n \"$view\" ]; then\n"
              "  msg=Viewing\n"
              "else\n"
              "  exit 1\n"
              "fi\n"
              "eval export OCPI_TESTCASE=%s\n"
              "eval export OCPI_TESTSUBCASE=$subcase\n",
              m_name.c_str(), m_name.c_str());
  verify += "exitval=0\n";
  size_t len = verify.size();
  for (unsigned n = 0; n < m_ports.size(); n++) {
    InputOutput &io = m_ports[n];
    if (io.m_port->isDataProducer()) {
      if (io.m_script.size() || io.m_view.size() || io.m_file.size()) {
        OU::formatAdd(verify,
                      "echo '  '$msg case %s.$subcase for worker \"$worker\" using %s on"
                      " output file:  %s.$subcase.$worker.%s.out\n"
                      "while read comp name value; do\n"
                      "  [ $comp = \"%s\"%s%s%s ] && eval export OCPI_TEST_$name=\\\"$value\\\"\n"
                      "done < %s.$subcase.$worker.props\n",
                      m_name.c_str(), io.m_script.size() ? "script" : "file comparison",
                      m_name.c_str(), io.m_port->pname(),
                      strrchr(specName.c_str(), '.') + 1,
                      emulator ? " -o $comp = \"" : "",
                      emulator ? strrchr(emulator->m_specName, '.') + 1 : "",
                      emulator ? "\"" : "",
                      m_name.c_str());
        // Put the value of any test properties into the environment according to the subcase
        bool firstTest = true;
        for (unsigned s = 0; s < m_subCases.size(); s++) {
          bool firstSubCase = true;
          ParamConfig &pc = *m_subCases[s];
          for (unsigned nn = 0; nn < pc.params.size(); nn++) {
            Param &sp = pc.params[nn];
            if (sp.m_param && sp.m_isTest) {
              if (firstTest) {
                firstTest = false;
                OU::formatAdd(verify, "case $subcase in\n");
              }
              if (firstSubCase) {
                firstSubCase = false;
                OU::formatAdd(verify, "  (%02u)", s);
              } else
                verify += ";";
              OU::formatAdd(verify, " export OCPI_TEST_%s='%s'",
                            sp.m_param->cname(), sp.m_uValue.c_str());
            }
          }
          if (!firstSubCase)
            verify += ";;\n";
        }
        if (!firstTest)
          verify += "esac\n";
        std::string inArgs;
        for (unsigned nn = 0; nn < m_ports.size(); nn++) {
          InputOutput &in = m_ports[nn];
          if (!in.m_port->isDataProducer()) {
if (in.m_file.size())
  OU::formatAdd(inArgs, " %s%s",
    in.m_file[0] == '/' ? "" : "../../", in.m_file.c_str());
else
  OU::formatAdd(inArgs, " ../../gen/inputs/%s.$subcase.%s",
    m_name.c_str(), in.m_port->pname());
    }
        }
        if (io.m_view.size())
          OU::formatAdd(verify, "[ -z \"$view\" ] || %s%s %s.$subcase.$worker.%s.out %s\n",
                        io.m_view[0] == '/' ? "" : "../../",
                        io.m_view.c_str(), m_name.c_str(), io.m_port->pname(),
                        inArgs.c_str());
        if (io.m_script.size() || io.m_file.size()) {
          OU::formatAdd(verify, "[ -z \"$verify\" ] || {\n");
          std::string out;
          OU::format(out, "%s.$subcase.$worker.%s.out", m_name.c_str(), io.m_port->pname());
          if (io.m_script.size())
            OU::formatAdd(verify,
              "  PATH=../..:../../$OCPI_TOOL_DIR:$OCPI_PROJECT_DIR/scripts:$PATH %s %s %s %s\n",
              "PYTHONPATH=$OCPI_PROJECT_DIR/scripts:$PYTHONPATH ",
              io.m_script.c_str(), out.c_str(), inArgs.c_str());
          else
            OU::formatAdd(verify,
                          "  echo '    'Comparing output file to specified file: \"%s\"\n"
                          "  cmp %s %s%s\n",
                          io.m_file.c_str(), out.c_str(),
                          io.m_file[0] == '/' ? "" : "../../", io.m_file.c_str());
          OU::formatAdd(verify,
                        "  r=$?\n"
                        "  tput bold 2>/dev/null\n"
                        "  if [ $r = 0 ] ; then \n"
                        "    tput setaf 2 2>/dev/null\n"
                        "    echo '    Verification for port %s: PASSED'\n"
                        "  else\n"
                        "    tput setaf 1 2>/dev/null\n"
                        "    echo '    Verification for port %s: FAILED'\n"
                        "    failed=1\n"
                        "  fi\n"
                        "  tput sgr0 2>/dev/null\n"
                        "  [ $r = 0 ] || exitval=1\n"
                        "}\n", io.m_port->pname(), io.m_port->pname());
        } else
          OU::formatAdd(verify,
                        "echo  ***No actual verification is being done.  Output is: $*\n");
      }
    }
  }
  if (len == verify.size())
    verify += "echo '  Verification was not run since there are no output ports.'\n";
  verify += "exit $exitval\n";
  return OU::string2File(verify.c_str(), file.c_str(), false, true, true);
}

const char *
generateCaseXml(FILE *out) {
  fprintf(out, "  <case name='%s'>\n", m_name.c_str());
  for (unsigned s = 0; s < m_subCases.size(); s++) {
    ParamConfig &pc = *m_subCases[s];
    // Figure out which platforms will not support this subcase
    assert(pc.params.size() == m_settings.params.size());
    Strings excludedPlatforms; // for the subcase
    Strings excludedPlatformsMerge; //need a temp variable when merging subcase and test platforms
    for (unsigned n = 0; n < pc.params.size(); n++) {
      Param
        &cp = m_settings.params[n], // case param
        &sp = pc.params[n];         // subcase param
      assert((cp.m_param && sp.m_param) || (!cp.m_param && !sp.m_param));
      // We now support unset values (e.g. raw config registers...)
      //      assert(!cp.m_param || cp.m_uValues.size() || cp.m_generate.size());
      // AV-3372: If cp is generated, there's likely an empty string sitting in cp.m_uValues.
      if (cp.m_generate.size() and (cp.m_uValues.size() == 1) and cp.m_uValues[0].empty() ) {
        ocpiDebug("Erasing false empty value for generated %s", cp.m_param->pretty());
        cp.m_uValues.clear();
      }
      if (!cp.m_param || cp.m_uValues.empty()) // empty is generated - no exclusions
        continue;
      Param::Attributes *attrs = NULL;
      for (unsigned i = 0; !attrs && i < cp.m_uValues.size(); i++) {
        if (sp.m_uValue == cp.m_uValues[i]) {
          attrs = &cp.m_attributes[i];
        }
      }
      assert(attrs);
      for (auto si = allPlatforms.begin(); si != allPlatforms.end(); ++si) {
        const char *p = si->c_str();
        // allowed platform for this test? if platform not in global onlyPlatforms
        // list it shouldn't be tested anyway
        if (onlyPlatforms.size() && onlyPlatforms.find(p) == onlyPlatforms.end())
          continue;
        // If all values for this platform are not explicit
        if (cp.m_explicitPlatforms.find(p) == cp.m_explicitPlatforms.end()) {
          if (attrs->m_excluded.find(p) != attrs->m_excluded.end() ||
              (attrs->m_included.size() && attrs->m_included.find(p) == attrs->m_included.end())) {
            excludedPlatformsMerge.insert(p);
          }
        } else if (attrs->m_only.find(p) == attrs->m_only.end()) {
          // This value is not specifically set for this platform.  Exclude the platform.
          excludedPlatformsMerge.insert(p);
        }
      }
    }
    // add per-case excluded platforms from the test xml to the list
    if (excludedPlatformsMerge.size() > 0) {
      excludedPlatforms.insert(excludedPlatformsMerge.begin(), excludedPlatformsMerge.end());
    }
    if (m_excludePlatforms.size() > 0){
      excludedPlatforms.insert(m_excludePlatforms.begin(), m_excludePlatforms.end());
    }

std::string hdr;
    // Now that all platforms exclusions have been collected, generate list
OU::format(hdr, "    <subcase id='%u'", s);
    if (excludedPlatforms.size() && !onlyPlatforms.size() && !m_onlyPlatforms.size()) {
      OU::formatAdd(hdr, " exclude='");
      for (auto si = excludedPlatforms.begin(); si != excludedPlatforms.end(); ++si) {
        OU::formatAdd(hdr, "%s%s", si == excludedPlatforms.begin() ? "" : " ", si->c_str());
      }
    OU::formatAdd(hdr, "'");
    }
    // Now we know which platforms should be included
    if (m_onlyPlatforms.size()) {
      OU::formatAdd(hdr, " only='");
      for (auto si = m_onlyPlatforms.begin(); si != m_onlyPlatforms.end(); ++si) {
        OU::formatAdd(hdr, "%s%s", si == m_onlyPlatforms.begin() ? "" : " ", si->c_str());
      }
      OU::formatAdd(hdr, "'");
    } else if (onlyPlatforms.size()) {
      OU::formatAdd(hdr, " only='");
      for (auto si = onlyPlatforms.begin(); si != onlyPlatforms.end(); ++si) {
        const char *p = si->c_str();
        if (m_excludePlatforms.size()  && m_excludePlatforms.find(p) != m_excludePlatforms.end())
          continue;
        OU::formatAdd(hdr, "%s%s", si == onlyPlatforms.begin() ? "" : " ", p);
      }
      OU::formatAdd(hdr, "'");
    }
    if (m_timeout)
      OU::formatAdd(hdr, " timeout='%zu'", m_timeout);
    if (m_duration)
      OU::formatAdd(hdr, " duration='%zu'", m_duration);
    OU::formatAdd(hdr, ">\n");
bool noConfigs = true;
    // For each worker configuration, decide whether it can support the subcase.
    // Note worker configs only have *parameters*, while subcases can have runtime properties
    for (WorkerConfigsIter wci = configs.begin(); wci != configs.end(); ++wci) {
      ocpiDebug("  For case xml for %s.%u worker %s.%s(%zu)", m_name.c_str(), s,
                wci->second->cname(), wci->second->m_modelString, wci->first->nConfig);
      ParamConfig &wcfg = *wci->first;
      // Only use worker configurations that make use of this case's workers
      if (std::find(m_workers.begin(), m_workers.end(), wci->second) == m_workers.end())
          goto skip_worker_config;
      // For each property in the subcase, decide whether it conflicts with a *parameter*
      // in this worker config
      for (unsigned nn = 0; nn < pc.params.size(); nn++) {
        Param &sp = pc.params[nn];
        if (sp.m_param == NULL)
          continue;
        OU::Property *wprop = wci->second->findProperty(sp.m_param->cname());
        for (unsigned n = 0; n < wcfg.params.size(); n++) {
          Param &wparam = wcfg.params[n];
          if (wparam.m_param && !strcasecmp(sp.m_param->cname(), wparam.m_param->cname())) {
            if (sp.m_uValue == wparam.m_uValue)
              goto next;     // match - this subcase property is ok for this worker config
            ocpiDebug("--Skipping worker %s.%s(%zu) because its param %s is different",
                      wci->second->cname(), wci->second->m_modelString,
                      wci->first->nConfig, sp.m_param->cname());
            goto skip_worker_config; // mismatch - this worker config rejected from subcase
          }
        }
        // The subcase property was not found as a parameter in the worker config
        if (wprop) {
          // But it is a runtime property in the worker config so it is ok
          assert(!wprop->m_isParameter);
          continue;
        }
        // The subcase property is for the emulator, which is ok
        if (sp.m_worker && sp.m_worker->m_emulate)
          continue;
        // The subcase property was not in this worker at all, so it must be
        // implementation specific or a test property
        if (sp.m_param->m_isImpl && sp.m_uValue.size()) {
          if (sp.m_param->m_default) {
            std::string uValue;
            sp.m_param->m_default->unparse(uValue);
            if (sp.m_uValue == uValue)
              // The subcase property is the default value so it is ok for the worker
              // to not have it at all.
              continue;
          }
          // The impl property is not the default so this worker config cannot be used
          ocpiDebug("--Skipping worker %s.%s(%zu) because param %s(%s) is impl-specific and %s",
                    wci->second->cname(), wci->second->m_modelString, wci->first->nConfig,
                    sp.m_param->cname(), sp.m_uValue.c_str(),
                    sp.m_param->m_default ? " the value does not match the default" :
                    "there is no default to check");
          goto skip_worker_config;
        }
        // The property is a test property which is ok
      next:;
      }
      {
        std::string name = wci->second->m_implName;
        if (wcfg.nConfig)
          OU::formatAdd(name, "-%zu", wcfg.nConfig);
        std::string ports;
        bool first = true;
        for (unsigned n = 0; n < m_ports.size(); n++)
          if (m_ports[n].m_port->isDataProducer() & !m_ports[n].m_testOptional) { //have to delete optional ports being tested
            OU::formatAdd(ports, "%s%s", first ? "" : " ", m_ports[n].m_port->pname());
            first = false;
          }
  if (noConfigs)
    fprintf(out, "%s", hdr.c_str());
  noConfigs = false;
        fprintf(out, "      <worker name='%s' model='%s' outputs='%s'/>\n",
                name.c_str(), wci->second->m_modelString, ports.c_str());
      }
    skip_worker_config:;
    }
if (!noConfigs)
fprintf(out, "    </subcase>\n");
  }
  // Output the workers and configurations that are ok to run on this case.
  fprintf(out, "  </case>\n");
  return NULL;
}
  // Explicitly included workers

const char *addWorker(const char *name, void *) {
  const char *dot = strrchr(name, '.'); // checked earlier
  // FIXME: support finding other workers in the project path
  std::string wdir;
  const char *slash = strrchr(name, '/');
  if (slash)
    wdir = name;
  else {
    wdir = "../";
    wdir += name;
  }
  bool isDir;
  if (!OS::FileSystem::exists(wdir, &isDir) || !isDir)
    return OU::esprintf("Worker \"%s\" doesn't exist or is not a directory", name);
  const char *wname = slash ? slash + 1 : name;
  std::string
    wkrName(wname, OCPI_SIZE_T_DIFF(dot, wname)),
    wOWD = wdir + "/" + wkrName + ".xml";
  if (!OS::FileSystem::exists(wOWD, &isDir) || isDir)
    return OU::esprintf("For worker \"%s\", \"%s\" doesn't exist or is a directory",
                        name, wOWD.c_str());
  return tryWorker(name, specName, true, true);
}

const char *excludeWorker(const char *name, void *) {
  const char *dot = strrchr(name, '.');
  if (!dot)
    return OU::esprintf("For worker name \"%s\": missing model suffix (e.g. \".rcc\")", name);
  std::string file("../");
  file += name;
  bool isDir;
  if (!OS::FileSystem::exists(file, &isDir) || !isDir)
    return OU::esprintf("Excluded worker \"%s\" does not exist in this library.", name);
  if (!excludeWorkers.insert(name).second)
    return OU::esprintf("Duplicate worker \"%s\" in excludeWorkers attribute.", name);
  excludeWorkersTmp.insert(name);
  return NULL;
}
const char *findWorkers() {
  if (verbose) {
    fprintf(stderr, "Looking for workers with the same spec: \"%s\"\n", specName.c_str());
    if (excludeWorkers.size())
      fprintf(stderr, "Skipping workers specifically mentioned for exclusion\n");
  }
  std::string workerNames;
  const char *err;
  if ((err = OU::file2String(workerNames, "../lib/workers", ' ')))
    return err;
  addDep("../lib/workers", false); // if we add or remove a worker from the library...
  for (OU::TokenIter ti(workerNames.c_str()); ti.token(); ti.next())
    if ((err = tryWorker(ti.token(), specName, true, false)))
      return err;
  return NULL;
}

void *connectHdlFileIO(const Worker &w, std::string &assy, InputOutputs &ports) {
//Case cases;
for (PortsIter pi = w.m_ports.begin(); pi != w.m_ports.end(); ++pi) {
  Port &p = **pi;
  bool optional = false;
  InputOutput *ios = findIO(p, ports);
  if (ios)
    optional = ios->m_testOptional;
  if (p.isData() && !optional) {
      OU::formatAdd(assy,
                    "  <Instance name='%s_%s' Worker='file_%s'/>\n"
                    "  <Connection>\n"
                    "    <port instance='%s_%s' %s='%s'/>\n"
                    "    <port instance='%s%s%s' %s='%s'/>\n"
                    "  </Connection>\n",
                    w.m_implName, p.pname(), p.isDataProducer() ? "write" : "read",
                    w.m_implName, p.pname(), p.isDataProducer() ? "to" : "from",
                    p.isDataProducer() ? "in" : "out", w.m_implName,
                    p.isDataProducer() ? "_backpressure_" : "_ms_", p.pname(),
        p.isDataProducer() ? "from" : "to", p.isDataProducer() ? "out" : "in");
  }
}
}

void *connectHdlStressWorkers(const Worker &w, std::string &assy, bool hdlFileIO, InputOutputs &ports) {
for (PortsIter pi = w.m_ports.begin(); pi != w.m_ports.end(); ++pi) {
  Port &p = **pi;
  bool optional = false;
  InputOutput *ios = findIO(p, ports);
  if (ios)
    optional = ios->m_testOptional;
  if (p.isData() && !optional) {
    if (p.isDataProducer()) {
      OU::formatAdd(assy,
                    "  <Instance Name='%s_backpressure_%s' Worker='backpressure'/>\n",
                    w.m_implName, p.pname());
      OU::formatAdd(assy,
                    "  <Connection>\n"
                    "    <port instance='uut_%s' name='%s'/>\n"
                    "    <port instance='%s_backpressure_%s' name='in'/>\n"
                    "  </Connection>\n", w.m_implName, p.pname(), w.m_implName, p.pname());
      if (!hdlFileIO) {
        OU::formatAdd(assy,
                      "  <Connection Name='%s_backpressure_%s' External='producer'>\n"
                      "    <port Instance='%s_backpressure_%s' Name='out'/>\n"
                      "  </Connection>\n", p.pname(), w.m_implName, w.m_implName, p.pname());
      }
    } else {
      OU::formatAdd(assy,
                    "  <Instance Name='%s_ms_%s' Worker='metadata_stressor'/>\n",
                    w.m_implName, p.pname());
      OU::formatAdd(assy,
                    "  <Connection>\n"
                    "    <port instance='%s_ms_%s' name='out'/>\n"
                    "    <port instance='uut_%s' name='%s'/>\n"
                    "  </Connection>\n", w.m_implName, p.pname(), w.m_implName, p.pname());
      if (!hdlFileIO) {
        OU::formatAdd(assy,
                      "  <Connection Name='%s_ms_%s' External='consumer'>\n"
                      "    <port Instance='%s_ms_%s' Name='in'/>\n"
                      "  </Connection>\n",  p.pname(),  w.m_implName, w.m_implName, p.pname());
      }
    }
  }
}
}

const char *generateHdlAssembly(const Worker &w, unsigned c, const std::string &dir, const
                                std::string &name, bool hdlFileIO, Strings &assyDirs, InputOutputs &ports) {
OS::FileSystem::mkdir(dir, true);
assyDirs.insert(name);
const char *err;
ocpiInfo("Generating assembly for worker: %s in file %s filename %s spec %s",
    w.cname(), w.m_file.c_str(), w.m_fileName.c_str(), w.m_specFile.c_str());
std::string makeFile;
// Only build for sim targets if using vhdlfileio
if (hdlFileIO)
  makeFile +=
"override HdlPlatform:=$(filter %sim,$(HdlPlatform))\n"
"override HdlPlatforms:=$(filter %sim,$(HdlPlatforms))\n";
// Only build the assembly for targets that are built
std::string targets;
// Only build for targets for which the worker is built
// Note the worker may have been build for "no targets", and thus exist in the "lib" directory
// of the library, without having been built for.
for (OS::FileIterator iter("../lib/hdl", "*"); !iter.end(); iter.next()) {
  std::string
target = iter.relativeName(),
targetDir = "../lib/hdl/" + target;
  bool isDir;
  if (OS::FileSystem::exists(targetDir, &isDir) && isDir) {
if (OS::FileSystem::exists(targetDir + "/" + w.m_implName + ".vhd")) {
ocpiInfo("Found that worker was built for target: %s", target.c_str());
targets += " " + target;
}
  }
}
if (targets.empty()) // don't build for anything since worker was not built for anything
  makeFile += "override HdlPlatforms:=\noverride HdlPlatform:=\n";
else
  makeFile += "OnlyTargets=" + targets + "\n";
makeFile += "\ninclude $(OCPI_CDK_DIR)/include/hdl/hdl-assembly.mk\n";
#if 1
if ((err = OU::string2File(makeFile, dir + "/Makefile", false, true)))
  return err;
#else
if ((err = OU::string2File(hdlFileIO ?
                  "override HdlPlatform:=$(filter %sim,$(HdlPlatform))\n"
                  "override HdlPlatforms:=$(filter %sim,$(HdlPlatforms))\n"
                  "include $(OCPI_CDK_DIR)/include/hdl/hdl-assembly.mk\n" :
                  "include $(OCPI_CDK_DIR)/include/hdl/hdl-assembly.mk\n",
                  dir + "/Makefile", false, true)))
    return err;
#endif
std::string assy;
OU::format(assy,
            "<HdlAssembly%s>\n"
            "  <Instance Worker='%s' Name='uut_%s' ParamConfig='%u'/>\n",
            emulator ? " language='vhdl'" : "", w.m_implName, w.m_implName, c);
  if (emulator) {
    OU::formatAdd(assy, "  <Instance Worker='%s' Name='uut_%s' ParamConfig='%u'/>\n",
                emulator->m_implName, emulator->m_implName, c);
    for (unsigned n = 0; n < w.m_ports.size(); n++) {
      Port &p = *w.m_ports[n];
      if (p.m_type == DevSigPort || p.m_type == PropPort)
        OU::formatAdd(assy,
                    "  <Connection>\n"
                    "    <port instance='uut_%s' name='%s'/>\n"
                    "    <port instance='uut_%s' name='%s'/>\n"
                    "  </Connection>\n",
                    w.m_implName, p.pname(), emulator->m_implName, p.pname());
    }
}
  connectHdlStressWorkers(w, assy, hdlFileIO, ports);
  if(emulator)
    connectHdlStressWorkers(*emulator, assy, hdlFileIO, ports);
  if (hdlFileIO) {
    connectHdlFileIO(w, assy, ports);
    if (emulator)
      connectHdlFileIO(*emulator, assy, ports);
  }
  assy += "</HdlAssembly>\n";
  return OU::string2File(assy, dir + "/" + name + ".xml", false, true);
} 

