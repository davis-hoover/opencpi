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

#ifndef _PARAMETERS_H_
#define _PARAMETERS_H_
#include <vector>
#include <set>
#include <string>
#include <unordered_set>
#include "BaseValue.hh"
#include "MetadataProperty.hh"
#include "cdkutils.h"
#include "ocpigen.h"

// These structures capture what is in or will be put in
// the build configuration file.
// They are also used to dump the makefile fragment output

// This vector holds a sequence of alternative values for a given parameter
// It is held as a string because it can't be parsed until the other
// parameter values are known (e.g. the length of an array in another parameter).
typedef std::vector<std::string> Values;
typedef std::set<std::string> Strings;
typedef Strings::const_iterator StringsIter;

class Assembly;
#define PARAM_ATTRS "name", "value", "values", "valueFile", "valuesFile"
struct Param {
  std::string                 m_name;       // if spec, same as m_param->m_name, if impl worker.model.property
  OCPI::Base::Value           m_value;      // value for the current config, perhaps the default
  std::string                 m_uValue;     // unparsed value: the canonical value for comparison
  OCPI::Base::Member         *m_valuesType; // the type (a sequence of these values).
  Values                      m_uValues;    // *Either* parsed from XML or captured from raw
  const OCPI::Metadata::Property *m_param;      // the property that is a parameter
  bool                        m_isDefault;  // is m_value from property default?
  const Worker               *m_worker;     // worker of param when the paramconfig spans impls
  bool                        m_isTest;
  std::string                 m_generate;   // how to generate a value
  Strings                     m_explicitPlatforms; // platforms w/ all platform-specified values
  struct Attributes {            // these attributes are PER VALUE
    bool         m_onlyExcluded; // the value is only excluded, for platforms in m_excluded
                                 // which is only when exclusion happens before inclusion
    Strings      m_excluded;     // platforms this value is excluded for 
                                 // i.e. if platform is in set, don't use value
    Strings      m_included;     // the platforms this value is used for
                                 // i.e. if platform is not in set, don't use value
    Strings      m_only;         // the platforms it is explicitly set for using "only".
                                 // i.e. if the platform is explicit, val is used if in this set
    Attributes() : m_onlyExcluded(false) {}
  };
  std::vector<Attributes>     m_attributes;
  static void fullName(const OCPI::Metadata::Property &prop, const Worker *wkr, std::string &name);
  Param();
  void setProperty(const OCPI::Metadata::Property *prop, const Worker *w);
  const char 
    // only one of w and wkrs should be set
    *parseValue(const OCPI::Metadata::Property &prop, const char *value),
    *parse(ezxml_t px, const OCPI::Metadata::Property *prop, const Worker *w = NULL, bool global = false),
    *excludeValue(std::string &uValue, Attributes *&attrs, const char *platform),
    *addValue(std::string &uValue, Attributes *&attrs, const char *platform),
    *onlyValue(std::string &uValue, Attributes *&attrs, const char *platform);
};

class Worker;
class ParamConfig;
// This must be pointers since it has a reference member which can't be copied,
// and we're not using c++11 yet, with "emplace".
typedef std::vector<ParamConfig*> ParamConfigs;
class ParamConfig : public OCPI::Base::IdentResolver {
  Worker &m_worker;
 public:
  char *m_slavesString;
  ezxml_t m_slavesXml;
  Assembly *m_slavesAssembly; // per-config slave assembly if worker is a proxy with a slave assembly
  // map of slave worker objects mapped by a string of the name of the slave either from name
  // attribute or auto generated
  std::list<std::pair<std::string, Worker*>> m_slaves; // maintain order
  std::unordered_set<std::string> m_slaveNames; // for duplicate checking
  std::vector<std::string> m_slaveTypes; // type namespace per slave
  std::vector<const char **> m_slaveBaseTypes; // saved temporarily
  std::vector<Param> params;
  std::string id;
  size_t nConfig; // ordinal
  bool used;  // Is this config in the current set?
  ParamConfig(Worker &w);
  ParamConfig(const ParamConfig &);
  ParamConfig &operator=(const ParamConfig * p);
  void clone(const ParamConfig &other);
  ~ParamConfig();
  const char *addSlavesConfig(ezxml_t slaves);
  const char *parse(ezxml_t cx, const ParamConfigs &configs);
  const char *doDefaults(bool missingOK);
  void write(FILE *xf, FILE *mf);
  void writeConstants(FILE *gf, Language lang);
  // Is the given configuration the same as this one?
  bool equal(ParamConfig &other);
  // The callback when evaluating expressions for data types (e.g. array length).
  const char *getValue(const char *sym, OCPI::Base::ExprValue &val) const;
  const char *getParamValue(const char *sym, const OCPI::Base::Value *&v) const;
  const Worker &worker() const { return m_worker; }
};

// The build information that is not necessary for code generation.
// (except the actual explicit configs, which are in ParamConfigs).
// Many of the lists need to preserve the original XML ordering
struct Build {
  Worker             &m_worker;
  ParamConfig         m_globalParams;  // parameters set for all non-id'd build configurations
  OrderedStringSet    m_onlyPlatforms, m_excludePlatforms;
  OrderedStringSet    m_onlyTargets, m_excludeTargets;
  OrderedStringSet    m_sourceFiles;    // absolute or relative to the worker dir ORDERED
  OrderedStringSet    m_checkedLibraries; // primitive libraries, with path and hdl-library name colon separated
  OrderedStringSet    m_libraries;      // primitive libraries, slashes imply no search
  OrderedStringSet    m_xmlIncludeDirs; // include paths for XML files
  OrderedStringSet    m_includeDirs;    // include paths for source files
  OrderedStringSet    m_componentLibraries;
  // HDL-specific
  OrderedStringSet    m_cores;
  OrderedStringSet    m_configurations; // for platform configurations
  // RCC-specific
  OrderedStringSet    m_staticPrereqLibs;
  OrderedStringSet    m_dynamicPrereqLibs;
  OrderedStringSet    m_exactParts;  // list of <family>:<part> pairs
  OrderedStringSet    m_containers;
  OrderedStringSet    m_defaultContainers;
  bool                m_anyDefaultContainers;
  Build(Worker &w);
  const char *parse(ezxml_t x, const char *buildFile = NULL);
  void writeMakeVars(FILE *mkFile);
};
#endif
