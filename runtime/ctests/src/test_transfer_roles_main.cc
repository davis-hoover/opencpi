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
#include <test_utilities.h>
#include "UtilCommandLineConfiguration.hh"
#include <UtZeroCopyIOWorkers.h>
#include "TimeEmit.hh"
#include "UtilThread.hh"

using namespace OCPI::Container;
using namespace OCPI;
using namespace OCPI::CONTAINER_TEST;

static size_t OCPI_RCC_DATA_BUFFER_SIZE   = 512;
static int   OCPI_USE_POLLING            = 1;

static CWorker PRODUCER(0,1),  CONSUMER(1,0);

#define PRODUCER_OUTPUT_PORT  PORT_0
#define CONSUMER_INPUT_PORT   PORT_0

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


static void createWorkers(std::vector<CApp>& ca )
{
  try {
    PRODUCER.worker = OCPI::CONTAINER_TEST::createWorker(ca[PRODUCER.cid], &UTZCopyProducerWorkerDispatchTable );
    CONSUMER.worker = OCPI::CONTAINER_TEST::createWorker(ca[CONSUMER.cid], &UTZCopyConsumerWorkerDispatchTable );
  }
  CATCH_ALL_RETHROW( "creating workers" )

    }

static void createPorts( std::vector<CApp>& ca )
{
  ( void ) ca;
  try {
    PRODUCER.pdata[PRODUCER_OUTPUT_PORT].port = &
      PRODUCER.worker->createOutputPort(  PRODUCER_OUTPUT_PORT,
                                          PRODUCER.pdata[PRODUCER_OUTPUT_PORT].bufferCount,
                                          OCPI_RCC_DATA_BUFFER_SIZE,PRODUCER.pdata[PRODUCER_OUTPUT_PORT].props);
    PRODUCER.sPortCount++;

  }
  CATCH_ALL_RETHROW( "creating producer source port" )

    try {
      CONSUMER.pdata[CONSUMER_INPUT_PORT].port = &
        CONSUMER.worker->createInputPort( CONSUMER_INPUT_PORT,
                                          CONSUMER.pdata[CONSUMER_INPUT_PORT].bufferCount,
                                          OCPI_RCC_DATA_BUFFER_SIZE, CONSUMER.pdata[CONSUMER_INPUT_PORT].props);
      CONSUMER.tPortCount++;
    }
  CATCH_ALL_RETHROW("creating consumer target port")

}


static void connectWorkers(std::vector<CApp>& ca )
{
  ( void ) ca;
  PRODUCER.pdata[PRODUCER_OUTPUT_PORT].port->connect( *CONSUMER.pdata[CONSUMER_INPUT_PORT].port, NULL, NULL );
}


#define BUFFERS_2_PROCESS 1000;
static void initWorkerProperties(int mode, std::vector<CApp>& ca )
{
  ( void ) ca;
  ( void ) mode;
  int32_t  tprop[5];
  unsigned offset, nBytes;

  // Set the producer buffer run count property to 0
  offset = offsetof(ProducerWorkerProperties,run2BufferCount);
  nBytes = sizeof( uint32_t );
  tprop[0] = BUFFERS_2_PROCESS;
  PRODUCER.worker->write(  offset,
			   nBytes, &tprop[0]);
  PRODUCER.worker->afterConfigure();

  // Set the producer buffers processed count
  offset = offsetof(ProducerWorkerProperties,buffersProcessed);
  nBytes = sizeof( uint32_t );
  tprop[0] = 0;
  PRODUCER.worker->write(  offset, nBytes, &tprop[0]);
  PRODUCER.worker->afterConfigure();
  
  // Set the producer bytes processed count
  offset = offsetof(ProducerWorkerProperties,bytesProcessed);
  nBytes = sizeof( uint32_t );
  tprop[0] = 0;
  PRODUCER.worker->write(  offset, nBytes, &tprop[0]);
  PRODUCER.worker->afterConfigure();

  // Set the consumer passfail property to passed
  offset = offsetof(ConsumerWorkerProperties,passfail);
  nBytes = sizeof( uint32_t );
  tprop[0] = 1;
  CONSUMER.worker->write(  offset, nBytes, &tprop[0]);
  CONSUMER.worker->afterConfigure();

  // Set the consumer dropped buffers count
  offset = offsetof(ConsumerWorkerProperties,droppedBuffers);
  nBytes = sizeof( uint32_t );
  tprop[0] = 0;
  CONSUMER.worker->write(  offset, nBytes, &tprop[0]);
  CONSUMER.worker->afterConfigure();

  // Set the consumer buffer run count property to 0
  offset = offsetof(ConsumerWorkerProperties,run2BufferCount);
  nBytes = sizeof( uint32_t );
  tprop[0] = BUFFERS_2_PROCESS;
  CONSUMER.worker->write(  offset, nBytes, &tprop[0]);
  CONSUMER.worker->afterConfigure();

  // Set the consumer buffers processed count
  offset = offsetof(ConsumerWorkerProperties,buffersProcessed);
  nBytes = sizeof( uint32_t );
  tprop[0] = 0;
  CONSUMER.worker->write( offset, nBytes, &tprop[0]);
  CONSUMER.worker->afterConfigure();

  // Set the consumer buffers processed count
  offset = offsetof(ConsumerWorkerProperties,bytesProcessed);
  nBytes = sizeof( uint32_t );
  tprop[0] = 0;
  CONSUMER.worker->write(  offset, nBytes, &tprop[0]);
  CONSUMER.worker->afterConfigure();

  // Set the producer mode
  offset = offsetof(ProducerWorkerProperties, transferMode);
  nBytes = sizeof( uint32_t );
  tprop[0] = ProducerSend;
  PRODUCER.worker->write(  offset, nBytes, &tprop[0]);
  PRODUCER.worker->afterConfigure();

  // Set the consumer mode
  offset = offsetof(ConsumerWorkerProperties, transferMode);
  nBytes = sizeof( uint32_t );
  tprop[0] = ConsumerConsume;
  CONSUMER.worker->write(  offset, nBytes, &tprop[0]);
  CONSUMER.worker->afterConfigure();

}



static bool run_ap_test(std::vector<CApp>& ca, std::vector<CWorker*>& workers, int mode)
{
  ( void ) mode;
  bool passed = true;
  enableWorkers(ca, workers);
  ConsumerWorkerProperties cprops;
  ProducerWorkerProperties pprops;

  int count = 6;
  while ( count > 0 ) {

    //    OCPI::OS::sleep( 2000 );

    // Read the consumer properties to monitor progress
    CONSUMER.worker->read(   0, sizeof(ConsumerWorkerProperties), &cprops);

    if ( cprops.buffersProcessed == cprops.run2BufferCount  ) {

      if ( cprops.droppedBuffers ) {
        printf("\nConsumer dropped %d buffers\n", cprops.droppedBuffers );
        passed = false;
        break;
      }

      // Make sure that the consumer got the same data
      PRODUCER.worker->read(   0,
			       sizeof(ProducerWorkerProperties),
			       &pprops);

      if ( cprops.bytesProcessed != pprops.bytesProcessed ) {
        printf("Producer produced %d bytes of data, consumer got %d bytes of data\n",
               pprops.bytesProcessed, cprops.bytesProcessed );
        passed = false;
        break;
      }
      else {
        break;
      }

    }
    OCPI::OS::sleep( 1000 );
    count--;
  }

  if ( count == 0 ) {
    printf("\nTest timed out\n");
    passed = false;
  }

  if ( ! passed ) {
    PRODUCER.worker->read(   0,
			     sizeof(ProducerWorkerProperties),
			     &pprops);
    printf("\nTest failed results:\n");
    printf("   Producer produced %d buffers, consumer received %d buffers\n",
           pprops.buffersProcessed, cprops.buffersProcessed );
  }

  disableWorkers(ca, workers );
  return passed;
}

int run_ab_test( const char* test_name, std::vector<CApp>& ca, std::vector<CWorker*>& workers)
{
  bool test_rc;
  int testPassed = 1;

  test_rc = run_ap_test(ca, workers, LBSendOnly);
  if ( test_rc == false ) testPassed = 0;
  printf("\n%s Send Only:       %s\n",  test_name, test_rc ? "PASSED" : "FAILED" );

  disconnectPorts( ca, workers );
  destroyWorkers( ca, workers );

  return testPassed;

}

int config_and_run_ap_container_test1(std::vector<CApp>& ca, std::vector<CWorker*>& workers,
                                      unsigned cmap[], unsigned bcmap[] )
{
  char tnamebuf[256];

  PRODUCER = cmap[0];
  PRODUCER.pdata[PRODUCER_OUTPUT_PORT].bufferCount = bcmap[1];
  CONSUMER = cmap[2];
  CONSUMER.pdata[CONSUMER_INPUT_PORT].bufferCount  = bcmap[1];

  createWorkers( ca );
  createPorts( ca );
  connectWorkers( ca );
  initWorkerProperties(LBSendOnly, ca);

  int32_t  tprop[5];
  size_t offset, nBytes;

  // Set the consumer mode
  offset = offsetof(ConsumerWorkerProperties, transferMode);
  nBytes = sizeof( uint32_t );
  tprop[0] = ConsumerConsume;
  CONSUMER.worker->write(  offset, nBytes, &tprop[0]);
  CONSUMER.worker->afterConfigure();

  // Set the producer mode
  offset = offsetof(ProducerWorkerProperties, transferMode);
  nBytes = sizeof( uint32_t );
  tprop[0] = ProducerSend;
  PRODUCER.worker->write(  offset, nBytes, &tprop[0]);
  PRODUCER.worker->afterConfigure();

  sprintf(tnamebuf, "Advanced port managment test (using send): container map %d,%d,%d buffer map %d,%d,%d,%d\n Test:  ",
          cmap[0], cmap[1], cmap[2], bcmap[0], bcmap[1], bcmap[2], bcmap[3] );


  return run_ab_test( tnamebuf, ca, workers );
}


static unsigned bcmap[][4] = {
  { 4,5,10,1 },
  { 1,1,1,1 },
  { 2,2,2,2 },
  { 1,2,3,4 },
  { 4,5,1,14 },
  { 1,1,10,5 },
  { 10,1,1,5 },
  { 1,10,10,15 },
  { 15,1,1,1 }
};



void sig_handler( int signum )
{
  ( void ) signum;
  exit(-1);
}


#ifdef NO_MAIN
int test_ap_main( int argc, char** argv)
#else
int  main( int argc, char** argv)
#endif
{
  SignalHandler sh(sig_handler);

  int test_rc = 1;
  OCPI::Xfer::EventManager* event_manager;
  unsigned cmap[3];

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
  cmap[0] = 0; cmap[1] = 1; cmap[2] = 2;

  std::vector<const char*> endpoints;
  std::vector<CApp> ca;
  try {
    ca =
      createContainers(endpoints, event_manager, (bool)OCPI_USE_POLLING);
  }
  catch( OCPI::Util::EmbeddedException& ex ) {
    printf("Create containers failed with exception. errorno = %d, aux = %s\n",
           ex.getErrorCode(), ex.getAuxInfo() );
    exit(-1);
  }
  catch( std::string& err ) {
    printf("Got a string exception while creating containers = %s\n", err.c_str() );
    exit(-1);
  }
  catch( ... ) {
    printf("Got an unknown exception while creating containers\n");
    exit(-1);
  }

#if 0
  // Create a dispatch thread
  DThreadData tdata;
  tdata.run =1;
  tdata.containers = ca;
  tdata.event_manager = event_manager;
  OCPI::Util::Thread* t = runTestDispatch(tdata);
#endif

  std::vector<CWorker*> workers;
  workers.push_back( &PRODUCER );
  workers.push_back( &CONSUMER );

  // Run test with default settings of active only roles
  //  test_rc &= config_and_run_ap_container_test1(ca,workers,cmap, bcmap[1] );

  // Run test with producer role of ActiveFlowControl
  static OCPI::Base::PValue t2props[] = {OCPI::Base::PVString("role","ActiveOnly"),
                                        OCPI::Base::PVEnd };
  PRODUCER.pdata[PRODUCER_OUTPUT_PORT].props = t2props;

  //  static OCPI::Base::PValue c_port_props[] = {OCPI::Base::PVString("protocol","ocpi-socket-rdma"),
  static OCPI::Base::PValue c_port_props[] = {OCPI::Base::PVString("protocol","ocpi-smb-pio"),
  //  static OCPI::Base::PValue c_port_props[] = {OCPI::Base::PVString("protocol","ocpi-ofed-rdma"),
                                                                                  OCPI::Base::PVEnd };
  CONSUMER.pdata[CONSUMER_INPUT_PORT].props = c_port_props;


  test_rc &= config_and_run_ap_container_test1(ca,workers,cmap, bcmap[1] );
  PRODUCER.pdata[PRODUCER_OUTPUT_PORT].props = NULL;

#if 0
  tdata.run=0;
  t->join();
  delete t;
#endif
  destroyContainers( ca, workers );

  //  OCPI::Time::EmitFormatter tfb(OCPI::Time::EmitFormatter::VCDFormat);
  //  std::cout << tfb;

  return !test_rc;
}


