// This file is protected by Copyright. Please refer to the COPYRIGHT file
// distributed with this source distribution.
//
// This file is part of OpenCPI <http://www.opencpi.org>
//
// OpenCPI is free software: you can redistribute it and/or modify it under the
// terms of the GNU Lesser General Public License as published by the Free
// Software Foundation, either version 3 of the License, or (at your option) any
// later version.
//
// OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
// WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
// A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
// more details.
//
// You should have received a copy of the GNU Lesser General Public License
// along with this program. If not, see <http://www.gnu.org/licenses/>.

#include <iostream>
#include <sstream>  // std::istringstream
#include <string>
#include <unistd.h> //usleep
#include <getopt.h>
#include "OcpiApi.hh"

namespace OA = OCPI::API;

void cli_usage(const char* prog_name) {
  std::cout << "Usage: " << prog_name << " ";
  std::cout << "[-c] ";
  std::cout << "[-r] regval ";
  std::cout << "[-t] regval ";
  std::cout << "[-s] sample_rate_mhz ";
  std::cout << "[-h] ";
  std::cout << std::endl;
  std::cout << "  Where:" << std::endl;
  std::cout << "    -c, --cal : Run a delay calibration sweep." << std::endl;
  std::cout << "                When not set existing calibration is tested.";
  std::cout << std::endl;
  std::cout << "    -r, --rxclkreg regval : Override the rx_clock_data_delay register. E.g. 0xFF" << std::endl;
  std::cout << "    -t, --txclkreg regval : Override the tx_clock_data_delay register. E.g. 0xF0" << std::endl;
  std::cout << "    -s, --samplerate sample_rate_mhz : Sample rate in MHz." << std::endl;
  std::cout << "    -v, --verbose : Print debug infomation." << std::endl;
  std::cout << "    -h, --help : Print this help message." << std::endl;
  exit(2);  
}

static struct option long_options[] =
{
    {"cal", no_argument, NULL, 'c'},
    {"rxclkreg", required_argument, NULL, 'r'},
    {"txclkreg", required_argument, NULL, 't'},
    {"samplerate", required_argument, NULL, 's'},
    {"verbose", no_argument, NULL, 'v'},
    {"help", no_argument, NULL, 'h'},
    {NULL, 0, NULL, 0}
};

typedef enum BIST_MODE {BIST_NORMAL = 0, BIST_LOOPBACK = 1, BIST_RX_PRBS = 2, BIST_LOOPBACK_FIXED = 3} BIST_MODE;

void setBISTMode(OA::Application &app, BIST_MODE mode) {

  if (mode == BIST_RX_PRBS) {
    app.setProperty("drc.config.test_bist_config", "0x9");
    app.setProperty("drc.config.test_observe_config", "0x0");
    app.setProperty("ad9361_prbs_gen_xs.mode", "0x1");
  } else if (mode == BIST_LOOPBACK) {
    app.setProperty("drc.config.test_bist_config", "0x0");
    app.setProperty("drc.config.test_observe_config", "0x1");
    app.setProperty("ad9361_prbs_gen_xs.mode", "0x2");      
  } else if (mode == BIST_LOOPBACK_FIXED) {
    app.setProperty("drc.config.test_bist_config", "0x0");
    app.setProperty("drc.config.test_observe_config", "0x1");
    app.setProperty("ad9361_prbs_gen_xs.mode", "0x3");    
    app.setProperty("ad9361_prbs_gen_xs.set_value", "0xABC00000");    
  }
  else { // BIST_NORMAL
    app.setProperty("drc.config.test_bist_config", "0x0");
    app.setProperty("drc.config.test_observe_config", "0x0");
    app.setProperty("ad9361_prbs_gen_xs.mode", "0x1");
  }
}

bool checkCalibration(OA::Property &go, OA::Property &done, OA::Property &result, uint32_t pass_threshold) {
  // Let things settle
  usleep(50000);
  go.setBoolValue(true);
  while(1) {
    if (done.getBoolValue()) {
      uint32_t result_val = result.getULongValue();
      go.setBoolValue(false);
      return (result_val > pass_threshold);
    } else {
      usleep(50000);
    }
  }
  return false;
}

void runCalibration(OA::Application &app, bool rx, OA::Property &go, OA::Property &done, OA::Property &result, uint32_t pass_threshold) {
  
  std::cerr << "  0 1 2 3 4 5 6 7 8 9 A B C D E F  <- Data Delay" << std::endl;        
  
  if (rx) {
    setBISTMode(app, BIST_RX_PRBS);
  } else {
    setBISTMode(app, BIST_LOOPBACK);
  }
  
  for (int clkDelay = 0; clkDelay < 16; clkDelay++) {        
    std::cerr << std::hex << clkDelay << " " << std::dec;          
    for (int dataDelay = 0; dataDelay < 16; dataDelay++) {
      int delay = (clkDelay*16)+dataDelay;
      if (rx) {
        app.setProperty("drc.config.general_rx_clock_data_delay", std::to_string(delay).c_str());
      } else {
        app.setProperty("drc.config.general_tx_clock_data_delay", std::to_string(delay).c_str());
      }
      std::cout << (checkCalibration(go, done, result, pass_threshold) ? "o " : ". ") << std::flush;
    }
    std::cout << std::endl;  
  }
    
  std::cout << "^--- Clock Delay" << std::endl << std::endl;
  std::cout << "o = Test Pass" << std::endl;
  std::cout << ". = Test Fail" << std::endl << std::endl;
  std::cout << "The calibration process should be repeated at a range of sample rates." << std::endl;
  std::cout << "Delay values should be selected which pass the test regardless of sample rate." << std::endl;
  setBISTMode(app, BIST_NORMAL);
}

int main(int argc, char **argv) {
  // Returns 0 On success, 1 on failed calibration, 2 on error
  int retval = 0;

  // Parse CLI arguments
  bool run_calibration(false);
  bool configure_sample_rate(false);
  bool configure_rxclkreg(false);
  bool configure_txclkreg(false);  
  bool verbose(false);
  double sample_rate_mhz(0.0);
  std::string rx_clock_data_delay("0x00");
  std::string tx_clock_data_delay("0x00");
  
  int opt;
  while((opt = getopt_long(argc, argv, "cr:t:s:vh", long_options, NULL)) != -1) {
    switch(opt) {
      case 'c':
        run_calibration = true;
        break;
      case 'r':
          configure_rxclkreg = true;
          rx_clock_data_delay = optarg;
        break;
      case 't':
          configure_txclkreg = true;
          tx_clock_data_delay = optarg;
        break;
      case 's':
        {
          configure_sample_rate = true;
          std::istringstream iss(optarg);
          iss >> sample_rate_mhz;
        }
        break;
      case 'v':
        verbose = true;
        break;
      default:
        cli_usage(argv[0]);
    }
  }

  try {
    OA::Application app("ad9361_interface_test_app.xml");
    app.initialize(); // all resources have been allocated
    
    // Get access to DRC configs
    OA::Property drc_configs(app, "drc.configurations");   

    if (configure_sample_rate) {
      drc_configs.setValue(sample_rate_mhz,     {0, "channels", 0, "sampling_rate_Msps"});
      drc_configs.setValue(sample_rate_mhz*0.1, {0, "channels", 0, "bandwidth_3dB_MHz"});      
      drc_configs.setValue(sample_rate_mhz,     {0, "channels", 1, "sampling_rate_Msps"});
      drc_configs.setValue(sample_rate_mhz*0.1, {0, "channels", 1, "bandwidth_3dB_MHz"});
    } else {
      sample_rate_mhz = app.getPropertyValue<double>("drc.configurations", {0, "channels", 0, "sampling_rate_Msps"});
    }

    if (verbose) {
      for (unsigned char chan = 0; chan < app.getPropertyValue<unsigned char>("drc.MAX_CHANNELS_p"); chan++) {
        bool rx_tx = app.getPropertyValue<bool>("drc.configurations", {0, "channels", chan, "rx"});
        double frequency = app.getPropertyValue<double>("drc.configurations", {0, "channels", chan, "tuning_freq_MHz"});
        double sample_rate = app.getPropertyValue<double>("drc.configurations", {0, "channels", chan, "sampling_rate_Msps"});
        double bandwidth = app.getPropertyValue<double>("drc.configurations", {0, "channels", chan, "bandwidth_3dB_MHz"});
        std::cout << "Channel " << int(chan) << " [" << (rx_tx ? "RX" : "TX") << "]" << std::endl;
        std::cout << "Frequency: " << frequency << " MHz" << std::endl;
        std::cout << "Sample rate: " << sample_rate << " MHz" << std::endl;
        std::cout << "Bandwidth: " << bandwidth << " MHz" << std::endl;            
      }
    }    
    
    app.start();
        
    // Set clock / data register settings
    if (configure_rxclkreg) {
      if (verbose) {
        std::string val;
        std::cout << "Changing rx_clock_data_delay from ";
        std::cout << app.getProperty("drc.config.general_rx_clock_data_delay", val, {}, {OA::HEX});
        std::cout << " to " << rx_clock_data_delay << std::endl;
      }
      app.setProperty("drc.config.general_rx_clock_data_delay", rx_clock_data_delay.c_str());
      
    }
        
    if (configure_txclkreg) {
      if (verbose) {
        std::string val;
        std::cout << "Changing tx_clock_data_delay from ";
        std::cout << app.getProperty("drc.config.general_tx_clock_data_delay", val, {}, {OA::HEX});
        std::cout << " to " << tx_clock_data_delay << std::endl;
      }
      app.setProperty("drc.config.general_tx_clock_data_delay", tx_clock_data_delay.c_str());
    }    

    // Get access to test properties
    OA::Property go(app, "ad9361_prbs_test_xs.go");
    OA::Property done(app, "ad9361_prbs_test_xs.done");
    OA::Property result(app, "ad9361_prbs_test_xs.result");

    // Allow up to 5 errors compared with the test length
    // This gives a bit of time to lock to the PRBS (should only take 1 cycle)
    uint32_t pass_threshold = app.getPropertyValue<uint32_t>("ad9361_prbs_test_xs.test_length") - 5;

    usleep(1000000);  // Wait 1 second after starting to let everything settle    

    if (!run_calibration) {

      // Don't run full calibration, just check if the current delays values work
      setBISTMode(app, BIST_RX_PRBS);
      bool rx_test_result = checkCalibration(go, done, result, pass_threshold);
      if (verbose) {
std::string val1;
        std::cout << "Checking RX calibration: ";
        std::cout << (rx_test_result ? "PASS" : "FAIL") << std::endl;
        std::cout << "DRC Using TWO R "<< app.getProperty("drc.config.config_is_two_r", val1) << val1 << std::endl;
      }
      
      setBISTMode(app, BIST_LOOPBACK);
      bool tx_test_result = checkCalibration(go, done, result, pass_threshold);
      if (verbose) {
        std::cout << "Checking TX calibration: ";
        std::cout << (tx_test_result ? "PASS" : "FAIL") << std::endl;
      }
      
      setBISTMode(app, BIST_NORMAL);
      retval = (tx_test_result & rx_test_result) ? 0 : 1;
      if (verbose) {
        std::cout << "Result: " << (retval ? "FAIL" : "PASS") << std::endl;
      }
    }
    else {
      // Save RX reg    
      std::string saved_rx_reg;
      app.getProperty("drc.config.general_rx_clock_data_delay", saved_rx_reg, {}, {OA::HEX});
      
      // RX Calibration      
      std::cerr << std::endl << "Receiver data interface calibration" << std::endl;
      std::cerr << "Sample Rate: " << sample_rate_mhz << " MHz" << std::endl;
      runCalibration(app, true, go, done, result, pass_threshold);
      
      // Restore original RX clock / data register as the TX calibration needs
      // the RX interface to be working in order to be successful.
      app.setProperty("drc.config.general_rx_clock_data_delay", saved_rx_reg.c_str());
      
      // TX Calibration
      std::cerr << std::endl << "Transmitter data interface calibration" << std::endl;
      std::cerr << "Sample Rate: " << sample_rate_mhz << " MHz" << std::endl;
      runCalibration(app, false, go, done, result, pass_threshold);
    }
    
    app.stop();
    app.finish();
    app.stop();

  } catch (std::string &e) {
    std::cerr << "Error: " << e << std::endl;
    return 2;
  }
  return retval;
}
