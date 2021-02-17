#include <iostream>
#include <unistd.h>
#include <cstdio>
#include <cassert>
#include <string>
#include "OcpiApi.hh"
namespace OA = OCPI::API;
int main(/*int argc, char **argv*/) {
  // For an explanation of the ACI, see:
  // https://opencpi.gitlab.io/releases/develop/docs/OpenCPI_Application_Development_Guide.pdf
  //activemq::library::ActiveMQCPP::initializeLibrary();
  try {
    //initialize the application
    OA::Application app("empty_drc.xml" /* may specify additional options as second arg*/ );
    /* For example:
    {
        // Create Application parameter structure.
        OA::PValue params[] = { PVString("model",
                                "psd1=rcc"),
                                PVString("selection", "filter=snr<40"),
                                PVString("property",
                                "filter=mode=6"),
                                 PVEnd
                              };

        // Start the application empty_drc.xml with parameter structure.
        OA::Application app("empty_drc.xml", params);
        app.initialize(); // All resources allocated
        app.start();      // Start execution
        app.wait();       // Wait until app is “done”
        app.finish();     // Do end-of-run processing like dump properties
    }*/

    std::cout << "<<---------------- Initializing app ...\n";
    app.initialize(); // all resources have been allocated 
    app.dumpProperties(true, true, "initial");
    std::cout << "Starting app ...\n";
    app.start();      // execution is started
    

    // <--- Create the properties (think of them as "buttons" for the drc).
    OA::Property start(app, "drc", "start"), stop(app, "drc", "stop"), release(app, "drc", "release"), prepare(app, "drc", "prepare");
    OA::Property configs(app, "drc", "configurations");

    // 1) Initial Rx configuration is 2450 Mhz specified in empty_drc.xml
    start.setValue(0);
    app.dumpProperties(false, false, "final");

    // 2) Second Rx configuration
    configs.setProperty("rx true,"
                        "tuning_freq_mhz 2449.999,"
                        "bandwidth_3db_mhz 0.24,"
                        "sampling_rate_Msps 0.25,"
                        "samples_are_complex true,"
                        "gain_db -25,"
                        "tolerance_tuning_freq_mhz 0.01,"
                        "tolerance_sampling_rate_msps 0.01,"
                        "tolerance_gain_db 1",
                        { 0, "channels", 0});
    app.dumpProperties(false, false, "final");
    stop.setValue(0);
    start.setValue(0);

    // 3) Final Rx configuration
    configs.setProperty("rx true,"
                        "tuning_freq_mhz 2450.001,"
                        "bandwidth_3db_mhz 0.24,"
                        "sampling_rate_Msps 0.25,"
                        "samples_are_complex true,"
                        "gain_db -25,"
                        "tolerance_tuning_freq_mhz 0.01,"
                        "tolerance_sampling_rate_msps 0.01,"
                        "tolerance_gain_db 1",
                        { 0, "channels", 0});
    app.dumpProperties(false, false, "final");
    stop.setValue(0);
    start.setValue(0);

/*
    //prepare.setValue(0);

    //configs.setValue(2400.0,{0,"channels",0,"tuning_freq_MHz"});
    // ----

    //app.stop();       // execution is started
    //app.initialize(); // all resources have been allocated 
    //app.start();      // execution is started


    // Create the properties (think of them as "buttons" for start/stop of the drc).
    OA::Property start(app, "drc", "start"), stop(app, "drc", "stop");
    std::cout << "<<---------------- Start/Stop created ...\n";

    // // Dump configuration prior to execution for verification 
    // app.dump();

    // // Recall - this is equal to the line removed from the xml file ... Second thoughts, I'm not so sure ...
    // start.setValue(0);
    std::cout << "<<---------------- Start setValue(0) occurred ...\n";
    // At this point the radio is running with the initial params from xml
    // ... waiting for 5 seconds to let things settle.
    std::cout << "<<---------------- After 1st start, now waiting 5 seconds ...\n";
    app.wait( 5000000 ); // microseconds

    // ... next, we will update configuration(0)
    OA::Property configs(app, "drc", "configurations");
    std::cout << "<<---------------- OA::Property configs(app, drc, configurations) ... occurred ... \n";

    // Dump the initial application properties
    app.dumpProperties(true, false, "initial"); // true, true, "initial" <-
    std::cout << "<<---------------- Initial parameters printed \n";

    // ------------- freq | configuration-index | channel
    configs.setValue(2400,{0,"channels",0,"tuning_freq_MHz"});
    configs.setValue(2400,{0,"channels",1,"tuning_freq_MHz"});

    //app.stop();      //
    //app.start();     //

    // Stopping configuration to latch new setup
    stop.setValue(0);
    std::cout << "<<---------------- After 1st stop, waiting 5 second ...\n";
    app.wait( 5000000 ); // microseconds

    // Apply and start new configuration
    start.setValue(0);
    std::cout << "<<---------------- After 2nd start, waiting 5 second ...\n";
    app.wait( 5000000 ); // microseconds

    // stop.setValue(0);
    // app.wait( 1000000 ); // microseconds

    // // Dump configuration after to updating the Rx frequency for verification 
    // app.dump();
    // Dump the final application properties
    app.dumpProperties(true, false, "final"); // false, false, "final"
    start.setValue(0); // Remove
    start.setValue(0); // Remove

    std::cout << "<<---------------- Third dump ...\n";
    app.dumpProperties(true, false, "final"); // false, false, "final"

    // Test app complete!
    app.finish();     // do end-of-run processing like dump properties  
*/
    } catch (std::string &e) {
      std::cerr << "app failed: " << e << std::endl;
      return 1;
    }
    std::cout << "<<---------------- App completed without errors!!!\n";
  return 0;
}
