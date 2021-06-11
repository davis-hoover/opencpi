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
#ifndef _OCPI_CASES_H
#define _OCPI_CASES_H

#include <cstddef>
#include <string>
#include <strings.h>
#include <cassert>
#include <vector>
#include "comp.h"
#include "input-output.h"

#define TESTS "-tests.xml"
#define MS_CONFIG "bypass", "metadata", "throttle", "full"

namespace OL = OCPI::Library;
struct Case;
typedef std::vector<Case *> Cases;
Cases cases;
OrderedStringSet allPlatforms;
// A test case, which may apply against multiple configurations
// Default is:
//   cases generated from configurations and defined property values
//   inputs and outputs are global
//   no property results (why not global results?  why not expressions?)
//   globally only/exclude platforms
//   globally only/exluded workers
// Specific cases
// Top level attributes of <tests>     
struct Case {
    std::string m_name;
    Strings m_onlyPlatforms, m_excludePlatforms; // can only apply these at runtime
    Workers m_workers; // the inclusion/exclusion happens at parse time
    WorkerConfigs m_configs;
    ParamConfig m_settings;
    ParamConfig m_results; // what the resulting properties should be
    ParamConfigs m_subCases;
    InputOutputs m_ports;  // the actual inputs and outputs to use
    size_t m_timeout, m_duration;
    bool m_doneWorkerIsUUT;
    std::string m_delays;
    Case ();
    static const char *doExcludePlatform(const char *a_platform, void *arg);
    static const char *doOnlyPlatform(const char *a_platform, void *arg);
    static const char *doOnlyWorker(const char *worker, void *arg);
    static const char *doExcludeWorker(const char *worker, void *arg);
    static const char *doCase(ezxml_t cx, void *globals);
    const char *doPorts(Worker &w, ezxml_t x);
    const char *parseDelay(ezxml_t sx, const OU::Property &p);
    const char *parse(ezxml_t x, size_t ordinal);
    void doProp(unsigned n);
    const char *pruneSubCases();
    void print(FILE *out);
    void table(FILE *out);
    const char *
    generateFile(bool &first, const char *dir, const char *type, unsigned s,
                const std::string &name, const std::string &generate, const std::string &env,
                std::string &file);
    const char *generateInputs();
    void
    generateAppInstance(Worker &w, ParamConfig &pc, unsigned nOut, unsigned nOutputs, unsigned s,
                      const DataPort *first, bool a_emulator, std::string &app, const char *dut, bool testingOptional); 
    const char *generateApplications(const std::string &dir, Strings &files);
    const char *generateVerification(const std::string &dir, Strings &files);
    const char *generateCaseXml(FILE *out);

    
};    
static const char *addWorker(const char *name, void *);
static const char *excludeWorker(const char *name, void *);
static const char *findWorkers();
void *connectHdlFileIO(const Worker &w, std::string &assy, InputOutputs &ports);
void *connectHdlStressWorkers(const Worker &w, std::string &assy, bool hdlFileIO, InputOutputs &ports);
const char *generateHdlAssembly(const Worker &w, unsigned c, const std::string &dir, const
                                      std::string &name, bool hdlFileIO, Strings &assyDirs, InputOutputs &ports);
#endif
