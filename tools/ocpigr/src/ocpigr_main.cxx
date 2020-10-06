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


// OCPI headers
#include "ocpigr.h" // ocpigr class

// System headers
#include <algorithm> // assign() replace()
#include <cctype>    // toupper
#include <complex>   // abs()
#include <cstddef>   // NULL, size_t
#include <cstdint>   // uint32_t etc.
#include <cstdlib>   // getenv, setenv
#include <fstream>   // std::ofstream
#include <list>      // list<T>
#include <set>       // set<T>
#include <string>    // strings
#include <vector>    // std::vector 

// 3rd party headers
#include <yaml-cpp/yaml.h> // YAML

// OCPI headers
#include "OcpiDriverManager.h" // OCPI::Driver::ManagerManager::suppressDiscovery
#include "OcpiLibraryManager.h"  // OL::* stuff
#include "OcpiOsAssert.h"  // ocpiLog macros
#include "OcpiOsFileSystem.h"  // Filesystem ops like mkdir etc.
#include "OcpiUtilDataTypesApi.h"  // OA::OCPI_* types
#include "OcpiUtilException.h"  // OU::Error
#include "OcpiUtilMisc.h"  // OU::format, getProjectRegistry, string2File
#include "OcpiUtilPort.h"  // OU::Port
#include "OcpiUtilProperty.h"  // OU::Property
#include "OcpiUtilWorker.h"  // OU::Worker

#define AUTO_PLATFORM_COLOR "#afaf75"

// OpenCPI GNU Radio utility
// Generate blocks corresponding to available artifacts
// After options args are platforms to engage or "all"
#define OCPI_OPTIONS_HELP \
  "Usage syntax is: ocpigr [options]\n" \
  "At least one option must be specified\n" \

// Define command line options when running ocpigr
#define OCPI_OPTIONS \
  CMD_OPTION  (verbose,   v, Bool,   NULL, "Set verbosity to info level") \
  CMD_OPTION  (debug,     d, Bool,   NULL, "Set verbosity to debug level") \
  CMD_OPTION  (directory, D, String, ".",  "Specify the directory in which to put output generated files")
#include "CmdOption.h"

// Instantiate ocipgr object
static OcpigrObj ocpigr;

static void genWorkerBlocks(OU::Worker &w){
  ocpigr.genWorkerBlocks(w);
}

//////////
// mymain
// Description: calls main from with openCPI infrastructure.
//
// Input: none - however ocpigr command line options are used for verbosity and directory output
//
// Output: returns executible status code 0 - Ouputs block, domain, tree, and container yaml files for GRC
//////////
static int mymain(const char ** /*ap*/) {
  // Do not load system.xml
  setenv("OCPI_SYSTEM_CONFIG", "", 1);

  // Set verbosity level if user requested via CLI
  if (options.verbose()) {
    OS::logSetLevel(OCPI_LOG_INFO);
  }
  if (options.debug()) {
    OS::logSetLevel(OCPI_LOG_DEBUG);
  }

  // If OCPI_LIBRARY_PATH is not set, use project-registry
  if (getenv("OCPI_LIBRARY_PATH") == NULL) {
    std::string library_path;
    const char *err = OU::getProjectRegistry(library_path);
    if (err != NULL) {
      throw OU::Error("ERROR: OCPI_LIBRARY_PATH was not set and attempts to detect project registry failed. %s", err);
    }
    ocpiInfo("No OCPI_LIBRARY_PATH given. Setting to '%s'", library_path.c_str());
    setenv("OCPI_LIBRARY_PATH", library_path.c_str(), 1);
  }

  // Create output directory
  OS::FileSystem::mkdir(options.directory(), true);
  ocpiInfo("Created directory or already exist: %s", options.directory());

  // We only want to discover libraries
  OCPI::Driver::ManagerManager::suppressDiscovery();
  OL::getManager().enableDiscovery();

  // Discover and generate OpenCPI workers blocks
  // Note: This MUST be done before generating the block tree, domain blocks, and container blocks
  //       as it discovers all the blocks and fills the maps which are used to generated those items
  OL::getManager().doWorkers(genWorkerBlocks);

  // Generate block tree yaml
  ocpigr.genOcpiBlockTree();

  // Generate ocpi_container.block.yml
  ocpigr.genContainerBlock();
  
  return 0;
}

//////////
// OcpigrObj::genWorkerBlocks
// Description: This function fills maps which are required to generate the tree yaml in addition
//              to actually generating the worker block yaml file. In general a block yaml file has
//              the following information: 
//              id, label, category, flags, parameters, inputs, outputs, templates (imports & callbacks), file_format
//              
//
// Input: w - is the ocpi worker object that we are building the yaml file for
//
// Output: none - write out a yaml file into the chosen directory
//////////
void OcpigrObj::genWorkerBlocks(OU::Worker &w) {
  assert(w.attributes().platform().length());

  // Only process each worker once
  if (!specs.insert(w.specName()).second) {
    ocpiDebug("This worker has already been processed, skipping: %s", w.specName().c_str());
    return;
  }

  // Count the number of workers processed
  ++numWorkers;
  ocpiDebug("This is worker number: %d", numWorkers);
  ocpiDebug("worker: %s | spec: %s | platform: %s | model: %s ",
        w.cname(), w.specName().c_str(), w.attributes().platform().c_str(), w.model().c_str());
  
  // Fill maps
  specToPlatforms[w.specName()].insert(w.attributes().platform()); // For each spec, which platforms are implemented
  platformToModel[w.attributes().platform()] = w.model(); // For each platform, which model does it support
  
  // Assign various strings for given worker
  const char *cp = strrchr(w.specName().c_str(), '.');
  std::string workerId(w.specName());
  std::string workerLabel = workerId.substr((size_t) ((cp - w.specName().c_str()) + 1));
  std::string workerPath(w.specName().c_str(), (size_t) (cp - w.specName().c_str()));
  std::string workerCategory("[OpenCPI]/" + workerPath);

  // Edit workerId replacing "." with "_" to form full worker block name
  std::replace(workerId.begin(), workerId.end(), '.', '_');

  // Declare yaml emitter, and put in what I'm calling the header
  YAML::Emitter workerEmitter;
  workerEmitter << YAML::BeginMap; // start worker_map
  workerEmitter << YAML::Key << "id"       << YAML::Value << workerId;
  workerEmitter << YAML::Key << "label"    << YAML::Value << workerLabel;
  workerEmitter << YAML::Key << "category" << YAML::Value << workerCategory;
  workerEmitter << YAML::Newline           << YAML::Newline; // blank line for the looks

  // Start parameters section
  workerEmitter << YAML::Key << "parameters" << YAML::Value;
  workerEmitter << YAML::BeginSeq; // start parameters_sequence

  // Add ocpi_spec section in parameters
  workerEmitter << YAML::BeginMap; // start ocpi_spec_map
  workerEmitter << YAML::Key << "id"      << YAML::Value << "ocpi_spec";
  workerEmitter << YAML::Key << "label"   << YAML::Value << "ocpi_spec";
  workerEmitter << YAML::Key << "default" << YAML::Value << w.specName().c_str();
  workerEmitter << YAML::Key << "dtype"   << YAML::Value << "string";
  workerEmitter << YAML::Key << "hide"    << YAML::Value << "part";
  workerEmitter << YAML::EndMap; // end ocpi_spec_map

  // Add platforms section in parameters
  StringSet &platforms = specToPlatforms[w.specName()];
  workerEmitter << YAML::BeginMap; // start container_map
  workerEmitter << YAML::Key << "id"      << YAML::Value << "container";
  workerEmitter << YAML::Key << "label"   << YAML::Value << "Container";
  workerEmitter << YAML::Key << "default" << YAML::Value << "auto";
  workerEmitter << YAML::Key << "dtype"   << YAML::Value << "enum";
  workerEmitter << YAML::Key << "hide"    << YAML::Value << "none";
  workerEmitter << YAML::Key << "options" << YAML::Value << YAML::Flow;
  workerEmitter << YAML::BeginSeq; // start options_seq
  workerEmitter << "auto";
  for(StringSetIter it = platforms.begin(); it != platforms.end(); ++it) {
    workerEmitter << it->c_str();
  }
  workerEmitter << YAML::EndSeq; // stop options_seq
  workerEmitter << YAML::Key << "option_labels" << YAML::Value << YAML::Flow;
  workerEmitter << YAML::BeginSeq; // start option_labels_seq
  workerEmitter << "auto";
  for(StringSetIter it = platforms.begin(); it != platforms.end(); ++it){
    workerEmitter << it->c_str();
  }
  workerEmitter << YAML::EndSeq; // stop option_labels_seq
  workerEmitter << YAML::EndMap; // stop container_map

  // Add slave section in parameters if needed
  if (!w.slaves().empty()) {
    workerEmitter << YAML::BeginMap; // start slave_map
    workerEmitter << YAML::Key << "id"       << YAML::Value << "slave";
    workerEmitter << YAML::Key << "label"    << YAML::Value << "Slave";
    workerEmitter << YAML::Key << "default"  << YAML::Value << "Null";
    workerEmitter << YAML::Key << "dtype"    << YAML::Value << "string";
    workerEmitter << YAML::Key << "hide"     << YAML::Value << "none";
    workerEmitter << YAML::Key << "required" << YAML::Value << "True"; // Not in the GRC YAML Standard?
    workerEmitter << YAML::EndMap; // end slave_map
  }

  // Add component specific properties in parameters
  uint32_t np = 0;
  OU::Property* p = w.properties(np);
  for (uint32_t n = 0; n < np; ++n, ++p) {
    if (!p->m_isImpl) {
      addProperty(workerEmitter, w, p);
    }
    else{
      // For each worker, add worker specific params
      workerSpecificProperties[w.specName()][w.cname()].insert(p);
    }
  }

  // Add properties specific to a particular worker
  std::map<std::string, std::set < OU::Property *>>::const_iterator wsp = workerSpecificProperties[w.specName()].begin();
  while (wsp != workerSpecificProperties[w.specName()].end()) {
    std::set<OU::Property *>::const_iterator prop = wsp->second.begin();
    while (prop != wsp->second.end()) {
      addProperty(workerEmitter, w, *prop);
      prop++;
    }
    wsp++;
  }
  workerEmitter << YAML::EndSeq; // end parameters_sequence
  workerEmitter << YAML::Newline <<YAML::Newline; // blank line for the looks

  // Add inputs and outputs sections to yaml emitter
  // Note: the use of inputs and outputs vectors were used because it seemed like a
  //       bad idea to assume that inputs and outputs would coming in order, aka all  
  //       inputs then all outputs
  std::vector<std::map<std::string, std::string>> inputsVector;
  std::vector<std::map<std::string, std::string>> outputsVector;
  np = 0; // reset np
  OU::Port *ports = w.ports(np);

  // Loop through ports and gather input and output information for the worker
  for (uint32_t n = 0; n < np; ++n, ++ports) {
    OU::Port &port = *ports;

    // Build portMap which contains the following information for a given input or output
    // label, domain, dtype, optional, protocol
    std::map<std::string, std::string> portMap;

    portMap["domain"]="message";
    portMap["dtype"]="ocpi";
    if(port.m_isOptional){
      portMap["optional"]="True";
    }

    // Fill inputs or outputs vector with the portMap information
    if(port.m_provider){
      inputsVector.push_back(portMap);
    } else{   
      outputsVector.push_back(portMap);
    }
  }

  // Put inputs into the yaml emitter
  if(!inputsVector.empty()){
    workerEmitter << YAML::Key << "inputs" << YAML::Value;
    workerEmitter << YAML::BeginSeq; // start inputs_sequence

    for(uint inputIndex = 0; inputIndex < inputsVector.size(); inputIndex++){
      workerEmitter   << YAML::BeginMap; // start input_map
      workerEmitter   << YAML::Key << "domain" << YAML::Value   << inputsVector[inputIndex].find("domain")->second;
      workerEmitter   << YAML::Key << "dtype" << YAML::Value    << inputsVector[inputIndex].find("dtype")->second;
      if(inputsVector[inputIndex].find("optional") != inputsVector[inputIndex].end()){
        workerEmitter << YAML::Key << "optional" << YAML::Value << inputsVector[inputIndex].find("optional")->second;
      }
      workerEmitter   << YAML::EndMap; // end input_map
    }
    workerEmitter << YAML::EndSeq; // end inputs_sequence
    workerEmitter << YAML::Newline <<YAML::Newline; // blank line for the looks
  }

  // Put outputs into the yaml emitter
  if(!outputsVector.empty()){
    workerEmitter << YAML::Key << "outputs" << YAML::Value;
    workerEmitter << YAML::BeginSeq; // start outputs_sequence

    for(uint outputIndex = 0; outputIndex < outputsVector.size(); outputIndex++){
      workerEmitter << YAML::BeginMap; // start outputs_map
      workerEmitter   << YAML::Key << "domain" << YAML::Value   << outputsVector[outputIndex].find("domain")->second;
      workerEmitter   << YAML::Key << "dtype" << YAML::Value    << outputsVector[outputIndex].find("dtype")->second;
      if(outputsVector[outputIndex].find("optional") != outputsVector[outputIndex].end()){
        workerEmitter << YAML::Key << "optional" << YAML::Value << outputsVector[outputIndex].find("optional")->second;
      }
      workerEmitter << YAML::EndMap; // end outputs_map
    }
    workerEmitter << YAML::EndSeq; // end outputs_sequence
    workerEmitter << YAML::Newline <<YAML::Newline; // blank line for the looks
  }

  // Add templates to yaml emitter
  workerEmitter << YAML::Key << "templates" << YAML::Value;
  workerEmitter << YAML::BeginMap; // start templates_map
  workerEmitter << YAML::Key << "import" << YAML::Value << "import ocpi";


  // reset worker properties pointer and add callback section to yaml emitter
  np = 0;
  p = w.properties(np);
  bool callbackInit = false;
  for (uint32_t n = 0; n < np; ++n, ++p) {
    if (p->m_isWritable && !p->m_isInitial) {
      // Only do this once, inside the loop and check such that callbacks map sequence isn't started
      // when not needed
      if(!callbackInit){
        workerEmitter << YAML::Key << "callbacks" << YAML::Value;
        workerEmitter << YAML::BeginSeq; // start callbacks_sequence
        callbackInit = true;
      }

      std::string callbackString("self._ocpi_application_internal_black_box_0.set_property(\"$(id)\", \"" 
                                  + p->m_name + "\", str($" + p->m_name + "))");
      workerEmitter << YAML::Value << callbackString;
    }
  }
  if(callbackInit){
    workerEmitter << YAML::EndSeq; // end callbacks_sequence
  }
  workerEmitter << YAML::EndMap; // end templates_map
  workerEmitter << YAML::Newline <<YAML::Newline; // blank line for the looks

  // Add file_format at the end of the yaml file
  workerEmitter << YAML::Key << "file_format" << YAML::Value << "1";
  workerEmitter << YAML::EndMap; // end worker_map

  //Check if there was an error while building the emitter
  if(!workerEmitter.GetLastError().empty()) {
    ocpiBad("YAML emitter silently errored when generating block tree: \n");
    ocpiBad("%s \n", workerEmitter.GetLastError().c_str());
  }

  // Output built emitter to yaml file
  std::string file;
  OU::format(file, "%s/%s.block.yml", options.directory(), workerId.c_str());
  std::ofstream fout(file);
  fout << workerEmitter.c_str();
}

//////////
// OcpigrObj::addProperty
// Description: Function adds a given worker's properties under the parameters section of worker block yaml
//
// Input: emitter - yaml emitter that is being used to build a given worker's yaml file
//        w       - given worker that is have a yaml file build for GRC
//        p       - pointer to given property for the given worker that is being added
//
// Output: None - adds data to the yaml emitter
//////////
void OcpigrObj::addProperty(YAML::Emitter& emitter, OU::Worker &w, OU::Property *p) {
  // Add parameter id and label to yaml emitter
  emitter << YAML::BeginMap; // start parameter_map
  emitter << YAML::Key << "id" << YAML::Value << p->cname();
  emitter << YAML::Key << "label" << YAML::Value << p->pretty();

  std::string strval;
  if (p->m_default) {
    p->m_default->unparse(strval);
  }

  // Determine paramter dtype
  const char *type = NULL;
  const bool isVector = p->m_arrayRank || p->m_isSequence;
  switch (p->m_baseType) {
    case OA::OCPI_Bool:
      type = isVector ? incompatibleType(w, "property", p->cname()) : "bool";
      if (strval.length() > 1) {
        strval[0] = (char) toupper(strval[0]);
      }
      break;
    case OA::OCPI_Double:
      type = isVector ? "real_vector" : "real";
      break;
    case OA::OCPI_Float:
      type = isVector ? "float_vector" : "float";
      break;
    case OA::OCPI_Char:
    case OA::OCPI_Short:
    case OA::OCPI_Long:
    case OA::OCPI_UChar:
    case OA::OCPI_ULong:
    case OA::OCPI_UShort:
    case OA::OCPI_LongLong:
    case OA::OCPI_ULongLong:
      type = isVector ? "int_vector" : "int";
      break;
    case OA::OCPI_String:
      type = isVector ? incompatibleType(w, "property", p->cname()) : "string";
      break;
    case OA::OCPI_Enum:
      type = "enum";
      break;
    case OA::OCPI_Struct:
    case OA::OCPI_Type:
    default:
      type = incompatibleType(w, "property", p->cname());
      break;
  }

  // Add parameter default value to emitter if needed
  if (strval.length()) {
    emitter << YAML::Key << "default" << YAML::Value << strval.c_str();
  }

  // Add parameter dtype to emitter
  emitter << YAML::Key << "dtype" << YAML::Value << type;

  // Add parameter hide and build_param to emitter
  if ((!p->m_isWritable && !p->m_isInitial) || p->m_isParameter) {
    emitter << YAML::Key << "hide" << YAML::Value << "none";
    // Could not find build_param in GRC Yaml Standard
    emitter << YAML::Key << "build_param" << YAML::Value << "True"; 
  }

  // Add parameter options to emitter if needed
  if (p->m_baseType == OA::OCPI_Enum) {
    emitter << YAML::Key << "options" << YAML::Value << YAML::Flow;
    emitter << YAML::BeginSeq; // start options_sequence
    for (const char **ep = p->m_enums; *ep; ++ep) {
        emitter << *ep;
    }
    emitter << YAML::EndSeq; // end options_sequence
  }

  // Add parameter category to emitter if needed
  if (p->m_isParameter) {
    emitter << YAML::Key << "category" << YAML::Value << "Parameters";
  } else if (!p->m_isWritable && !p->m_isInitial) {
    emitter << YAML::Key << "category" << YAML::Value << "Read Only";
  }

  // Add parameter required to emitter if needed
  if (p->m_isInitial) {
    emitter << YAML::Key << "required" << YAML::Value << "True";
  }
  emitter << YAML::EndMap; // end parameter_map
}

//////////
// OcpigrObj::incompatibleType
// Description: This is called when and OpenCPI property has an incompatible type for yaml GRC block
//
// Input: w   - given worker that is have a yaml file build for GRC
//        tag - this is the where the incompatible type is coming from mostly from a property
//        val - this is the name of the specific tag (property) name 
//
// Output: "raw" - raw is the catch all type in GRC yaml blocks
//////////
const char* OcpigrObj::incompatibleType(OU::Worker& w, const char* tag, const char* val) {
  ocpiInfo("Incompatible type in worker: %s - can't map %s %s\n", w.cname(), tag, val);
  return "raw";
}

//////////
// OcpigrObj::genOcpiBlockTree
// Description: Generates ocpi.tree.yml file which is the tree structure for the
//              worker blocks in GRC. Note: This approach assumes that the workers
//              sorted and ordered.
//
// Input: none - uses OcpigrObj::specs which is a std::set<std::string> containing the
//               path and name for the worker with '.' as a delimiter. std::set orders
//               the workers which is why this approach works, interating through specs and 
//               putting them in the file top to bottom.
//
// Output: none - writes out the yaml file using ofstream
//////////
void OcpigrObj::genOcpiBlockTree(void) {
  ocpiInfo("Generating OpenCPI block tree");

  //Start building yaml emitter
  YAML::Emitter emitter;
  emitter << YAML::BeginSeq;

  std::vector<std::string> prevBlockVector;
  int currTreeDepth = 0;

  for(StringSetIter it = specs.begin(); it != specs.end(); it++) {
    ocpiDebug("ocpiTreeBlocks: %s", it->c_str());
    ocpiDebug("Starting currTreeDepth: %d", currTreeDepth);

    // Pull block data and put into vector form split based on periods
    std::string blockString = it->c_str();
    std::vector<std::string> currBlockVector = splitString(blockString, ".");

    // Edit blockString replacing "." with "_" to form full block name
    std::replace(blockString.begin(), blockString.end(), '.', '_');

    // equalVectorLength is the length of the current vector that is equal to the prev vector
    int equalVectorLength = 0;
    equalVectorLength = compareBlockVectors(currBlockVector, prevBlockVector);
    ocpiDebug("equalVectorLengh: %d", equalVectorLength);
    
    // Close finished sequences and maps
    int treeDepthChange = equalVectorLength - currTreeDepth;
    endTreeSeq(emitter, treeDepthChange);
    currTreeDepth = equalVectorLength;
    ocpiDebug("treeDepthChange: %d", treeDepthChange);
    ocpiDebug("endTreeSeq currTreeDepth: %d", currTreeDepth);

    // Create needed sequences of maps for tree
    createTreeSeq(emitter, currBlockVector, equalVectorLength);
    currTreeDepth = static_cast<int>(currBlockVector.size()) - 1;
    ocpiDebug("createTreeSeq currTreeDepth: %d", currTreeDepth);

    // Insert block name
    ocpiDebug("Insert blockString: %s", blockString.c_str());
    emitter << blockString;

    // Store current block into prev block
    prevBlockVector.assign(currBlockVector.begin(), currBlockVector.end());
  }
  // Close any remaining open sequences
  ocpiDebug("Ending currTreeDepth: %d", currTreeDepth);
  endTreeSeq(emitter, currTreeDepth);
  emitter << YAML::EndSeq;

  //Check if there was an error while building the emitter
  if(!emitter.GetLastError().empty()) {
    ocpiBad("YAML emitter silently errored when generating block tree: \n");
    ocpiBad("%s \n", emitter.GetLastError().c_str());
  }

  // Setup output file
  std::string file;
  OU::format(file, "%s/ocpi.tree.yml", options.directory());
  std::ofstream fout(file);

  // Top of OpenCPI tree, this segregates opencpi from GRC core
  // Note: Couldn't use YAML:Emitter to get this to format properly
  //       this maybe a GRC thing not a YAML standard?
  fout << "'[OpenCPI]':\n";

  // Output built emitter to yaml file
  fout << emitter.c_str();
}

//////////
// OcpigrObj::splitString
// Description: 
//
// Input: str - string that begin broken up into a vector based on the delimiter
//        delimiter - delimiter being used to break up the string into vector of strings
//
// Output: strVector - return vector of strings after being split
//////////
std::vector<std::string> OcpigrObj::splitString(std::string str, std::string delimiter) {
    size_t posStart = 0, posEnd, delimLen = delimiter.length();
    std::string token;
    std::vector<std::string> strVector;

    while ((posEnd = str.find (delimiter, posStart)) != std::string::npos) {
        token = str.substr (posStart, posEnd - posStart);
        posStart = posEnd + delimLen;
        strVector.push_back (token);
    }

    strVector.push_back (str.substr (posStart));
    return strVector;
}

//////////
// OcpigrObj::compareBlockVectors
// Description: 
//
// Input: curr - current worker blocks path broken into a vector of strings
//        prev - previous worker blocks path broken into a vector of strings
//
// Output: ndx - number of similar strings between the two vectors
//////////
int OcpigrObj::compareBlockVectors(std::vector<std::string>& curr, std::vector<std::string>& prev){
    // Determine smallest block between prev and current
    
    int currBlockSize = static_cast<int>(curr.size());
    int prevBlockSize = static_cast<int>(prev.size());
    int smallestBlockSize = (currBlockSize < prevBlockSize) ? currBlockSize : prevBlockSize;

    // Sizes are minus one due to the last element being the name which is ignored
    smallestBlockSize -= 1;
    // Don't let the smallestBlockSize go negative, this occurs during the initial block in 
    // genOcpiBlockTree due to preBlockSize not being filled.
    if(smallestBlockSize < 0){ smallestBlockSize = 0; }

    int ndx = 0;
    // Compare the two vectors starting at the front but stop at the end of the shortest vector
    
    while(ndx < (smallestBlockSize)){
      if(curr.at(ndx) != prev.at(ndx)){
        ocpiDebug("curr and prev block vectors NOT equal at ndx: %d", ndx);
        break;
      }
      ocpiDebug("curr and prev block vectors equal at ndx: %d", ndx);
      ndx++;
    }

    return ndx;
}

//////////
// OcpigrObj::createTreeSeq
// Description: This opens sequences and maps from desired starting depth to the end of the 
//              block vector minus the worker name (last element in vector)
//
// Input: YAML::Emitter - yaml emitter that is being used to build the yaml file
//        blockVector   - vector containing work block path which translates to the tree
//        startingDepth - index of the vector to start at when iterating through
//
// Output: none - edits emitter in place
//////////
void OcpigrObj::createTreeSeq(YAML::Emitter& emitter, std::vector<std::string>& blockVector, int& startingDepth){
  // Determine total sequence depth
  int totalSeqDepth = static_cast<int>(blockVector.size()) - 1;
  ocpiDebug("createTreeSeq totalSeqDepth: %d", totalSeqDepth);
  ocpiDebug("createTreeSeq startingDepth: %d", abs(startingDepth));
  
  for(int depth = abs(startingDepth); depth < totalSeqDepth; depth++){
    // Setup map for given depth
    emitter << YAML::BeginMap;

    // Insert sequence name and create sequence
    ocpiDebug("createTreeSeq current depth: %d", depth+1);
    ocpiDebug("createTreeSeq insert sequence name: %s", blockVector.at(depth).c_str());
    emitter << YAML::Key << blockVector.at(depth) << YAML::Value;
    emitter << YAML::BeginSeq;
  }
}

//////////
// OcpigrObj::endTreeSeq
// Description: This is the counter part to OcpigrObj::createTreeSeq as it closes and sequences
//              and maps that are opened when building the yaml emitter
//
// Input: YAML::Emitter - yaml emitter that is being used to build the yaml file
//        closeDepth    - number of sequences and maps that need to be closed
//
// Output: none - edits emitter in place
//////////
void OcpigrObj::endTreeSeq(YAML::Emitter& emitter, int& closeDepth){
  ocpiDebug("endTreeSeq closeDepth: %d", abs(closeDepth));

  for(int ndx = 0; ndx < abs(closeDepth); ndx++){
    ocpiDebug("Closing sequence and map number: %d", ndx+1);
    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;
    
  }
}

//////////
// OcpigrObj::stringToColorHash
// Description: "Converts" an arbitrary string to some arbitrary color via hashing.
//              Note: The total set of platforms encountered during parsing on a given
//              system is dynamic as it is based on what the workers have been built for,
//              however, we do want the colors to be consistent from one user to the other,
//              from one run to the other. Indexing into a static list of colors would cause
//              each user to have different colors for their platforms, or even different
//              for a single user after running this script after building for a new
//              platform. We could use a static mapping of all known platforms to colors,
//              but it would be difficult to maintain. This hash function maps the ID of the
//              platform to a calculated color, so it is the same every time for every run
//              while supporting new platforms with minimal chances of collision.
//
// Input: str - arbitrary string
//
// Output: "raw" - raw is the catch all type in GRC yaml blocks
//////////
std::string OcpigrObj::stringToColorHash(std::string str) {
  uint32_t hash = 0;
  for (std::string::size_type i = 0; i < str.size(); ++i) {
    hash = ((hash << 5) - hash) + (uint32_t) str[i];
  }
  std::string color;
  OU::format(color, "#%02x%02x%02x", (hash & 0x0000FF), (hash & 0x00FF00) >> 8, (hash & 0xFF0000) >> 16);
  return color;
}

//////////
// OcpigrObj::genContainerBlocks
// Description: Generates container yaml file
//
// Input: none - uses OcpigrObj::platformToModel to determine the platforms it needs
//               to include in container yaml.
//
// Output: none - writes out the yaml file using ofstream
//////////
void OcpigrObj::genContainerBlock(void) {

  ocpiInfo("Generating container block");
  
  YAML::Emitter emitter;
  emitter << YAML::BeginMap; // Top level map
  emitter << YAML::Key << "id"    << YAML::Value << "variable_ocpi_container";
  emitter << YAML::Key << "label" << YAML::Value << "OpenCPI Container";
  emitter << YAML::Key << "category" << YAML::Value << "[OpenCPI]/Container";
  emitter << YAML::Newline << YAML::Newline; // blank line just to be consistent with GRC yaml examples
  
  emitter << YAML::Key << "parameters" << YAML::Value;
  emitter << YAML::BeginSeq; // Starting Sequence
  
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "id"    << YAML::Value << "type";
    emitter << YAML::Key << "label" << YAML::Value << "ocpi_spec";
    emitter << YAML::Key << "dtype" << YAML::Value << "string";
    emitter << YAML::Key << "hide"  << YAML::Value << "all";
    emitter << YAML::EndMap;

    emitter << YAML::BeginMap;
    emitter << YAML::Key << "id"    << YAML::Value << "value";
    emitter << YAML::Key << "label" << YAML::Value << "Platform";
    emitter << YAML::Key << "dtype" << YAML::Value << "enum";
    emitter << YAML::Key << "options" << YAML::Value << YAML::Flow;
    emitter << YAML::BeginSeq;

    // Iterate throught platforms and add them to emitter
    for (auto pi = platformToModel.begin(); pi != platformToModel.end(); ++pi) {
      emitter << pi->first.c_str();
    }
    emitter << YAML::EndSeq;
    emitter << YAML::EndMap;
    
    emitter << YAML::BeginMap;
    emitter << YAML::Key << "id"      << YAML::Value << "container";
    emitter << YAML::Key << "label"   << YAML::Value << "value";
    emitter << YAML::Key << "dtype"   << YAML::Value << "string";
    emitter << YAML::Key << "default" << YAML::Value << "${value}";
    emitter << YAML::Key << "hide"    << YAML::Value << "all";
    emitter << YAML::EndMap;
    
  emitter << YAML::EndSeq; // End Sequence

  // Add file_format at the end of the yaml file
  emitter << YAML::Newline << YAML::Newline; // blank line just to be consistent with GRC yaml examples
  emitter << YAML::Key << "file_format" << YAML::Value << "1";
  emitter << YAML::EndMap; // Top level map

  //Check if there was an error while building the emitter
  if(!emitter.GetLastError().empty()) {
    ocpiBad("YAML emitter silently errored when generating container block: \n");
    ocpiBad("%s \n", emitter.GetLastError().c_str());
  }

  // Output built emitter to yaml file
  std::string file;
  OU::format(file, "%s/ocpi_container.block.yml", options.directory());
  std::ofstream fout(file);
  fout << emitter.c_str();
}
