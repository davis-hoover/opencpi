#include <iostream>
#include <unistd.h>
#include <cstdio>
#include <cassert>
#include <string>
#include "OcpiApi.hh"

namespace OA = OCPI::API;

int main(/*int argc, char **argv*/) {
  // Reference https://opencpi.github.io/OpenCPI_Application_Development.pdf for
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
