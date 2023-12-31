#ifndef OCPIGR_H
#define OCPIGR_H

// System headers
#include <string>          // std::string
#include <vector>          // std::vector

// 3rd party headers
#include <yaml-cpp/yaml.h> // YAML::Emitter

// OCPI headers
#include "BasePluginManager.hh"   // OCPI::Driver::ManagerManager::suppressDiscovery
#include "LibraryManager.hh"  // OL::* stuff


namespace OA = OCPI::API;
namespace OL = OCPI::Library;
namespace OS = OCPI::OS;
namespace OU = OCPI::Util;
namespace OM = OCPI::Metadata;

typedef std::set<std::string> StringSet;
typedef StringSet::const_iterator StringSetIter;

//////////
// OcpigrObj
// Description: Top level class which contains all fucntions needed for ocpigr tool
//
// Input: None 
//
// Output: None
//////////
class OcpigrObj {
  private:
    // Private members and data structures
    int numWorkers;
    std::map<std::string, StringSet> specToPlatforms;
    std::map<std::string, std::string> platformToModel;
    std::map<std::string, std::map<std::string, std::set<OM::Property *>>> workerSpecificProperties;
    StringSet specs;

    // Private functions for genPlatformBlocks
    std::string stringToColorHash(std::string);
  
    // Private functions for genOcpiBlockTree
    std::vector<std::string> splitString(std::string, std::string);
    size_t compareBlockVectors(std::vector<std::string>&, std::vector<std::string>&);
    void createTreeSeq(YAML::Emitter&, std::vector<std::string>&, size_t&);
    void endTreeSeq(YAML::Emitter&, size_t&);

    // Private functions for genWorkerBlocks
    void addProperty(YAML::Emitter&, OM::Worker&, OM::Property*);
    const char* incompatibleType(OM::Worker&, const char*, const char*);

  public:
    // Constructor
    OcpigrObj():
      numWorkers(0), 
      specToPlatforms(), 
      platformToModel(), 
      workerSpecificProperties(), 
      specs()
    { }

    // Public Functions for mymain
    void genWorkerBlocks(OM::Worker&);
    void genOcpiBlockTree(void);
    void genContainerBlock(void);  
};


#endif //OCPIGR_H
