#include <iostream>
#include <unistd.h>
#include <cstdio>
#include <cassert>
#include <string>
#include "OcpiApi.hh"

namespace OA = OCPI::API;

int main(/*int argc, char **argv*/) {
  // Reference opencpi.github.io/releases/latest/docs/OpenCPI_Application_Development_Guide.pdf for
  // an explanation of the ACI.

  std::string cmd("rm -rf case00.00.in case00.00.out");
  if(system(cmd.c_str()) != 0) {
    std::cerr << "ERROR: non-zero exit status from " << cmd << "\n";
    return 1;
  }
  if(system("OCPI_TEST_ocpi_max_bytes_in=16384 ./generate.py case00.00.in") != 0) {
    return 1;
  }

  try {
    // When run in a build environment that is suppressing HDL platforms, respect that.
    const char *env = getenv("HdlPlatforms");
    bool hdl = false;
    if (!env || env[0]) {
      OA::Container *c;
      for (unsigned n = 0; (c = OA::ContainerManager::get(n)); ++n) {
	if (c->model() == "hdl") {
	  hdl = true;
	  std::cout << "INIT: found HDL container " << c->name() << ", will run HDL tests" << std::endl;
	}
      }
    }
    if (!hdl) {
      std::cerr << "WARNING: this test could not be run because no HDL containers were found\n";
      return 0;
    }
    OA::Application app("case00.00.xml");
    app.initialize(); // all resources have been allocated
    app.start();      // execution is started

    // Do work here.

    // Must use either wait()/finish() or stop(). The finish() method must
    // always be called after wait(). The start() method can be called
    // again after stop().
    //app.wait();       // wait until app is "done"
    //app.finish();     // do end-of-run processing like dump properties
    sleep(60);
    app.stop();

    if(system("./verify.py") != 0) {
      return 1;
    }
  } catch (std::string &e) {
    std::cerr << "app failed: " << e << std::endl;
    return 1;
  }
  return 0;
}
