#include <iostream>
#include <string>
#include "OcpiApi.hh"

namespace OA = OCPI::API;

int main(/*int argc, char **argv*/) {
  // For an explanation of the ACI, see:
  // https://opencpi.gitlab.io/releases/develop/docs/OpenCPI_Application_Development_Guide.pdf

  try {
    OA::Application app("raw2axi_lite32_test_app.xml");
    app.initialize(); // all resources have been allocated

    app.start();      // execution is started
    // test read access 
    uint32_t idValue = app.getPropertyValue<uint32_t>("register_map", "id");
    std::cout << "Expected ID Value = 0x1234567" << std::endl; 
    std::cout << "reading id reg: 0x" << std::hex << idValue << std::endl;

    // test write access 
    uint32_t scratchValue = app.getPropertyValue<uint32_t>("register_map", "scratch");
    std::cout << "reading scratch reg: 0x" << scratchValue << std::endl;
    std::cout << "setting scratch reg to 0x90000000" << std::endl; 
    app.setPropertyValue("register_map", "scratch", 0x90000000);
    scratchValue = app.getPropertyValue<uint32_t>("register_map", "scratch");
    std::cout << "reading scratch reg: 0x" << scratchValue << std::endl;

    app.finish();     // do end-of-run processing like dump properties
    app.stop();

  } catch (std::string &e) {
    std::cerr << "app failed: " << e << std::endl;
    return 1;
  }
  return 0;
}
