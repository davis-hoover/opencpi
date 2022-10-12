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

/*
 * Coverage test for data transfer roles.  The container is used as a test bench
 * for this test.
 *
 *    John Miller - 1/10/10
 *    Initial Version
 */

#include <vector>
#include <string>
#include <stdio.h>
#include <sstream>
#include <stdlib.h>
#include "OsMisc.hh"
#include "OsAssert.hh"
#include "TransportRDTInterface.hh"
#include "test_utilities.h"
#include "UtilCommandLineConfiguration.hh"
#include "UtZeroCopyIOWorkers.h"
#include "TimeEmit.hh"
#include "UtilThread.hh"
#include "OcpiApplicationApi.hh"

using namespace OCPI::Container;
using namespace OCPI;
using namespace OCPI::CONTAINER_TEST;
namespace OA=OCPI::API;


class OcpiRccBinderConfigurator
  : public OCPI::Util::CommandLineConfiguration
{
public:
  OcpiRccBinderConfigurator ();

public:
  bool help;
  bool verbose;
  MultiString  endpoints;

private:
  static CommandLineConfiguration::Option g_options[];
};

// Configuration
static  OcpiRccBinderConfigurator config;

OcpiRccBinderConfigurator::
OcpiRccBinderConfigurator ()
  : OCPI::Util::CommandLineConfiguration (g_options),
    help (false),
    verbose (false)
{
}

OCPI::Util::CommandLineConfiguration::Option
OcpiRccBinderConfigurator::g_options[] = {

  { OCPI::Util::CommandLineConfiguration::OptionType::MULTISTRING,
    "endpoints", "container endpoints",
    OCPI_CLC_OPT(&OcpiRccBinderConfigurator::endpoints), 0 },
  { OCPI::Util::CommandLineConfiguration::OptionType::BOOLEAN,
    "verbose", "Be verbose",
    OCPI_CLC_OPT(&OcpiRccBinderConfigurator::verbose), 0 },
  { OCPI::Util::CommandLineConfiguration::OptionType::NONE,
    "help", "This message",
    OCPI_CLC_OPT(&OcpiRccBinderConfigurator::help), 0 },
  { OCPI::Util::CommandLineConfiguration::OptionType::END, 0, 0, 0, 0 }
};

static
void
printUsage (OcpiRccBinderConfigurator & a_config,
            const char * argv0)
{
  std::cout << "usage: " << argv0 << " [options]" << std::endl
            << "  options: " << std::endl;
  a_config.printOptions (std::cout);
}

void sig_handler( int signum )
{ 
  ( void ) signum;
  exit(-1);
}


int  main(int argc, char** argv) {

  SignalHandler sh(sig_handler);

  int test_rc = 1;
  //  OCPI::Xfer::EventManager* event_manager;
  //int cmap[3];

  try {
    config.configure (argc, argv);
  }
  catch (const std::string & oops) {
    std::cerr << "Error: " << oops << std::endl;
    return 1;
  }
  if (config.help) {
    printUsage (config, argv[0]);
    return 1;
  }
  g_testUtilVerbose = config.verbose;
  //cmap[0] = 0; cmap[1] = 1; cmap[2] = 2;

  try {
    OA::Application app("<application>"
			"  <instance name='testProducer' component='ocpi.core.Producer' "
			"            connect='testConsumer'/>"
			"  <instance name='testConsumer' component='ocpi.core.Consumer'/>"
			"</application>");
    app.initialize();
    OCPI::API::Property
      doubleT(app, "testConsumer", "doubleT"),
      passFail(app, "testConsumer", "passfail"),
      boolT(app, "testConsumer", "boolT"),
      run2BufferCount(app, "testConsumer", "run2BufferCount"),
      longlongT(app, "testConsumer", "longlongT"),
      buffersProcessed(app, "testConsumer", "buffersProcessed"),
      floatST(app, "testConsumer", "floatST"),
      droppedBuffers(app, "testConsumer", "droppedBuffers"),
      bytesProcessed(app, "testConsumer", "bytesProcessed"),
      transferMode(app, "testConsumer", "transferMode"),
      Prun2BufferCount(app, "testProducer", "run2BufferCount"),
      PbuffersProcessed(app, "testProducer", "buffersProcessed"),
      PbytesProcessed(app, "testProducer", "bytesProcessed"),
      PtransferMode(app, "testProducer", "transferMode");

    // Extra for test case only
    doubleT.setDoubleValue( 167.82 );
    boolT.setBoolValue( 1 );
    longlongT.setLongLongValue( 1234567890 );
    float fv[] = {1.1f, 2.2f ,3.3f, 4.4f, 5.5f, 6.6f};
    floatST.setFloatSequenceValue( fv, 6 );

    // Set consumer properties
    passFail.setULongValue( 1 );
    droppedBuffers.setULongValue( 0 );
    run2BufferCount.setULongValue( 250  );
    buffersProcessed.setULongValue( 0 );
    bytesProcessed.setULongValue( 0 );
    transferMode.setULongValue( ConsumerConsume );

    // Set producer properties
    Prun2BufferCount.setULongValue( 250 );
    PbuffersProcessed.setULongValue( 0 );
    PbytesProcessed.setULongValue( 0 );

    app.start();

    // Let test run for a while
    int count = 5;
    do {
      uint32_t bp = buffersProcessed.getULongValue();
      if ( bp == 250 ) {
	printf(" Test: PASSED\n");
	break;
      }
      OCPI::OS::sleep( 1000 );
    } while ( count-- );

    uint32_t tbp = buffersProcessed.getULongValue();
    if ( tbp != 250 ) {
      printf("Test: FAILED!!, tried to process 250 buffers, only processed %d buffers\n", tbp );
    }
  } catch (std::string & oops) {
    std::cout << "Error: " << oops << std::endl;
    return 1;
  }
  return !test_rc;
}
