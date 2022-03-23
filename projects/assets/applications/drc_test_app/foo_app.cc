#include <iostream>
#include <sstream>
#include <unistd.h>
#include <cstdio>
#include <cassert>
#include <string>
#include "OcpiApi.hh"

namespace OA = OCPI::API;

class fmcomms2_3_args {
  public:
  std::string description;
  bool rx;
  double tuning_freq_MHz;
  double bandwidth_3dB_MHz;
  double sampling_rate_Msps;
  bool samples_are_complex;
  std::string gain_mode;
  double gain_dB;
  double tolerance_tuning_freq_MHz;
  double tolerance_bandwidth_3dB_MHz;
  double tolerance_sampling_rate_Msps;
  double tolerance_gain_dB;
  std::string rf_port_name;
  std::string rf_port_num;
  std::string app_port_num;
  // @TODO Add 'expected_pass' functionality
  //bool expected_pass;
  public:
  fmcomms2_3_args() {
    description = "des";
    rx = true;
    tuning_freq_MHz = 3000.;
    bandwidth_3dB_MHz = 30.;
    sampling_rate_Msps = 32.;
    samples_are_complex = true;
    gain_mode = "manual";
    gain_dB = 0.;
    tolerance_tuning_freq_MHz = 0.00001;
    tolerance_bandwidth_3dB_MHz = 0.00001;
    tolerance_sampling_rate_Msps = 0.00001;
    tolerance_gain_dB = 0.00001;
    rf_port_name = "";
    rf_port_num = "";
    app_port_num = "";
    // @TODO Add 'expected_pass' functionality
    //expected_pass = true;
  }
} args;

class fmcomms2_3_ddcduc_args : public fmcomms2_3_args {
  public:
  fmcomms2_3_ddcduc_args() {
    bandwidth_3dB_MHz = 10.;
    sampling_rate_Msps = 10.;
  }
} ddcduc_args;

std::string get_configurations_prop_string(fmcomms2_3_args args) {
  std::stringstream data_stream_ss;
  data_stream_ss << "\n{";
  data_stream_ss << "description des_here,";
  data_stream_ss << "recoverable true,";
  data_stream_ss << "channels ";
  data_stream_ss << "{{";
  data_stream_ss << "description " << args.description << ",";
  data_stream_ss << "rx " << args.rx << ",";
  data_stream_ss << "tuning_freq_MHz " << args.tuning_freq_MHz << ",";
  data_stream_ss << "bandwidth_3dB_MHz " << args.bandwidth_3dB_MHz << ",";
  data_stream_ss << "sampling_rate_Msps " << args.sampling_rate_Msps << ",";
  data_stream_ss << "samples_are_complex " << args.samples_are_complex << ",";
  data_stream_ss << "gain_mode " << args.gain_mode << ",";
  data_stream_ss << "gain_dB " << args.gain_dB << ",";
  data_stream_ss << "tolerance_tuning_freq_MHz " << args.tolerance_tuning_freq_MHz << ",";
  data_stream_ss << "tolerance_bandwidth_3dB_MHz " << args.tolerance_bandwidth_3dB_MHz << ",";
  data_stream_ss << "tolerance_sampling_rate_Msps " << args.tolerance_sampling_rate_Msps << ",";
  data_stream_ss << "tolerance_gain_dB " << args.tolerance_gain_dB << ",";
  data_stream_ss << "rf_port_name " << args.rf_port_name << ",";
  data_stream_ss << "rf_port_num " << args.rf_port_num << ",";
  data_stream_ss << "app_port_num " << args.rf_port_num/** << ","**/;
  // @TODO Add 'expected_pass' functionality
  //data_stream_ss << "expected_pass " << args.expected_pass << ",";
  data_stream_ss << "}}}\n";
  //std::cout << data_stream_ss.str();
  return data_stream_ss.str();
}

// @TODO Add 'expected_pass' functionality
template<typename T>
void run_test(OA::Application& app, bool rx, std::string config, T val, double tolerance, std::string rf_port_name/**, bool expected_pass**/) {
  // fc = tuning_freq_MHz
  // bw = bandwidth_3dB_MHz
  // fs = sampling_rate_Msps
  // gn = gain_dB
  fmcomms2_3_args args;
  args.rf_port_name = rf_port_name;
  fmcomms2_3_ddcduc_args ddcduc_args;
  ddcduc_args.rf_port_name = rf_port_name;
  if(args.rf_port_name == "rx1a" || args.rf_port_name == "tx2a") {
    args.rx = rx;
    if(config == "fc") {
      args.tuning_freq_MHz = val;
      args.tolerance_tuning_freq_MHz = tolerance;
    }
    if(config == "bw") {
      args.bandwidth_3dB_MHz = val;
      args.tolerance_bandwidth_3dB_MHz = tolerance;
    }
    if(config == "fs") {
      args.sampling_rate_Msps = val;
      args.tolerance_sampling_rate_Msps = tolerance;
    }
    if(config == "gn") {
      args.gain_dB = val;
      args.tolerance_gain_dB = tolerance;
    }
    if(config == "sc") {
      args.samples_are_complex = val;
    }
    if(config == "gm") {
      args.gain_mode = val;
    }
    // @TODO Add 'expected_pass' functionality
    //args.expected_pass = expected_pass;
    std::string prop_string = get_configurations_prop_string(args);
    app.setProperty("foo_drc","configurations",prop_string.c_str());
  }
  else if(args.rf_port_name == "rx2a" || args.rf_port_name == "tx1a") {
    ddcduc_args.rx = rx;
    if(config == "fc") {
      ddcduc_args.tuning_freq_MHz = val;
      ddcduc_args.tolerance_tuning_freq_MHz = tolerance;
    }
    if(config == "bw") {
      ddcduc_args.bandwidth_3dB_MHz = val;
      ddcduc_args.tolerance_bandwidth_3dB_MHz = tolerance;
    }
    if(config == "fs") {
      ddcduc_args.sampling_rate_Msps = val;
      ddcduc_args.tolerance_sampling_rate_Msps = tolerance;
    }
    if(config == "gn") {
      ddcduc_args.gain_dB = val;
      ddcduc_args.tolerance_gain_dB = tolerance;
    }
    if(config == "sc") {
      ddcduc_args.samples_are_complex = val;
    }
    if(config == "gm") {
      ddcduc_args.gain_mode = val;
    }
    // @TODO Add 'expected_pass' functionality
    //ddcduc_args.expected_pass = expected_pass;
    std::string prop_string = get_configurations_prop_string(ddcduc_args);
    app.setProperty("foo_drc","configurations",prop_string.c_str());
  }
  std::cout << "[INFO] PASS";
  std::cout << " rf_port_name,cfg,val,tol=";
  std::cout << rf_port_name << "," << config << "," << val << "," << "," << tolerance << "\n";
  //if(res != expected) {
  //  throw std::string("[ERROR] FAIL\n");
  //}
  //else {/*ERROR incompatable rf_port_name (rx1a,rx2a,tx1a,tx2a)*/}
}

int main(/*int argc, char **argv*/) {
  try{
    OA::Application app("foo_app.xml");
    app.initialize(); // all resources have been allocated
    app.start(); // execution is started
    // RX1A CHANNEL
    // Tuning Freq for FMCOMMS2 [2400 - 2500 MHz]
    // @TODO Add FMCOMMS2 vs FMCOMMS3 funcationality
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "fc", 2399.99 , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 2400.   , 0.000001, "rx1a"/**, true**/ );
    //// MEDIAN BOUNDS
    run_test<double>(app, true, "fc", 2000.   , 0.000001, "rx1a"/**, true**/ );
    //// UPPER BOUNDS
    run_test<double>(app, true, "fc", 2500.   , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 2500.99 , 0.000001, "rx1a"/**, false**/);
    // Tuning Freq for FMCOMMS2 [70 - 6000 MHz]
    // LOWER BOUNDS
    run_test<double>(app, true, "fc", 69.99   , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 70.     , 0.000001, "rx1a"/**, true**/ );
    //// MEDIAN BOUNDS
    run_test<double>(app, true, "fc", 3000.   , 0.000001, "rx1a"/**, true**/ );
    //// UPPER BOUNDS
    run_test<double>(app, true, "fc", 6000.   , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 6000.01 , 0.000001, "rx1a"/**, false**/);
    // Bandwidth [0.2 - 56 MHz]
    // ================================================
    //  LOWER BOUNDS
    run_test<double>(app, true, "bw", 0.19    , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "bw", 0.2     , 0.000001, "rx1a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "bw", 30.     , 0.000001, "rx1a"/**, true**/);
    // UPPER BOUNDS
    run_test<double>(app, true, "bw", 56.     , 0.000001, "rx1a"/**, true**/);
    run_test<double>(app, true, "bw", 56.01   , 0.000001, "rx1a"/**, false**/);
    // Sampling rate [2.083334 - 61.44 Msps]
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "fs", 2.08    , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fs", 2.083334, 0.000001, "rx1a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "fs", 32.     , 0.000001, "rx1a"/**, true**/ );
    // UPPER BOUND
    run_test<double>(app, true, "fs", 61.44   , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fs", 61.45   , 0.000001, "rx1a"/**, false**/);
    // Samples are complex
    // ================================================
    run_test<bool>(app, true, "sc", false     , 0.000001, "rx1a"/**, false**/ );
    run_test<bool>(app, true, "sc", true      , 0.000001, "rx1a"/**, true**/  );
    // Gain Mode
    // ================================================
    run_test<bool>(app, true, "gm", "manual"     , 0.000001, "rx1a"/**, false**/ );
    run_test<bool>(app, true, "gm", "automatic"  , 0.000001, "rx1a"/**, true**/  );
    // Gain dB
    // ================================================
    // Unconditional Constraints
    // ------------------------------------------------
    run_test<double>(app, true, "gn", -11.    , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "gn", -10.    , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -3.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -1.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 0.      , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 62.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 71.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 73.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 74.     , 0.000001, "rx1a"/**, false**/);
    // @TODO Create the ability to change 2 or more configs
    // Conditional Constraints
    // ================================================
    // If fc [70 - 1300 MHz]; Possible Gain: -1 - 73 dB
    // LOWER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -2.     , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -2.     , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -1.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -1.     , 0.000001, "rx1a"/**, true**/ );
    // MEDIAN BOUND
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx1a"/**, true**/ );
    // UPPER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 73.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 73.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 74.     , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 74.     , 0.000001, "rx1a"/**, false**/);
    // If fc [1300 - 4000 MHz); Possible Gain: -3 - 71 dB
    // LOWER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -4.     , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -4.     , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -3.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -3.     , 0.000001, "rx1a"/**, true**/ );
    // MEDIAN BOUND
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx1a"/**, true**/ );
    // UPPER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 71.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 71.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 72.     , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 72.     , 0.000001, "rx1a"/**, false**/);
    // If fc [4000 - 6000 MHz); Possible Gain: -10 - 62 dB
    // LOWER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -11.    , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -11.    , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -10.    , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", -10.    , 0.000001, "rx1a"/**, true**/ );
    // MEDIAN BOUND
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx1a"/**, true**/ );
    // UPPER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 62.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 62.     , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 63.     , 0.000001, "rx1a"/**, false**/);
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 63.     , 0.000001, "rx1a"/**, false**/);

    // RX2A DDCDUC CHANNEL
    // Tuning Freq for FMCOMMS2 [2369.28 - 2530.72 MHz]
    // @TODO Add FMCOMMS2 vs FMCOMMS3 funcationality
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "fc", 2369.27 , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 2369.28 , 0.000001, "rx2a"/**, true**/ );
    //// MEDIAN BOUNDS
    run_test<double>(app, true, "fc", 3000.   , 0.000001, "rx2a"/**, true**/ );
    //// UPPER BOUNDS
    run_test<double>(app, true, "fc", 2530.72 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 2530.73 , 0.000001, "rx2a"/**, false**/);
    // Tuning Freq for FMCOMMS2 [39.28 - 6000 MHz]
    // LOWER BOUNDS
    run_test<double>(app, true, "fc", 39.27   , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 39.28   , 0.000001, "rx2a"/**, true**/ );
    //// MEDIAN BOUNDS
    run_test<double>(app, true, "fc", 3000.   , 0.000001, "rx2a"/**, true**/ );
    //// UPPER BOUNDS
    run_test<double>(app, true, "fc", 6030.7190625, 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 6039.71907, 0.000001, "rx2a"/**, false**/);
    // Bandwidth [0.000024140625 - 14 MHz]
    // ================================================
    //  LOWER BOUNDS
    run_test<double>(app, true, "bw", 0.000023, 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "bw", 0.000024140625, 0.000001, "rx2a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "bw", 10.     , 0.000001, "rx2a"/**, true**/);
    // UPPER BOUNDS
    run_test<double>(app, true, "bw", 14.     , 0.000001, "rx2a"/**, true**/);
    run_test<double>(app, true, "bw", 14.01   , 0.000001, "rx2a"/**, false**/);
    // Sampling rate [~0.000255 - 15.36 Msps]
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "fs", 0.000253, 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fs", 0.000255, 0.000001, "rx2a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "fs", 10.     , 0.000001, "rx2a"/**, true**/ );
    // UPPER BOUND
    run_test<double>(app, true, "fs", 15.36   , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fs", 15.37   , 0.000001, "rx2a"/**, false**/);
    // Samples are complex
    // ================================================
    run_test<bool>(app, true, "sc", false     , 0.000001, "rx2a"/**, false**/ );
    run_test<bool>(app, true, "sc", true      , 0.000001, "rx2a"/**, true**/  );
    // Gain Mode
    // ================================================
    run_test<bool>(app, true, "gm", "manual"     , 0.000001, "rx2a"/**, false**/ );
    run_test<bool>(app, true, "gm", "automatic"  , 0.000001, "rx2a"/**, true**/  );
    // Gain dB
    // ================================================
    // Unconditional Constraints
    // ------------------------------------------------
    run_test<double>(app, true, "gn", -11.    , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "gn", -10.    , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -3.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -1.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 0.      , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 62.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 71.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 73.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 74.     , 0.000001, "rx2a"/**, false**/);
    // @TODO Create the ability to change 2 or more configs
    // Conditional Constraints
    // ================================================
    // If fc [70 - 1300 MHz]; Possible Gain: -1 - 73 dB
    // LOWER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -2.     , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -2.     , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -1.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -1.     , 0.000001, "rx2a"/**, true**/ );
    // MEDIAN BOUND
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx2a"/**, true**/ );
    // UPPER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 73.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 73.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 70.01   , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 74.     , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 1299.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 74.     , 0.000001, "rx2a"/**, false**/);
    // If fc [1300 - 4000 MHz); Possible Gain: -3 - 71 dB
    // LOWER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -4.     , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -4.     , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -3.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -3.     , 0.000001, "rx2a"/**, true**/ );
    // MEDIAN BOUND
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx2a"/**, true**/ );
    // UPPER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 71.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 71.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 1300.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 72.     , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 3999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 72.     , 0.000001, "rx2a"/**, false**/);
    // If fc [4000 - 6000 MHz); Possible Gain: -10 - 62 dB
    // LOWER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -11.    , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -11.    , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -10.    , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", -10.    , 0.000001, "rx2a"/**, true**/ );
    // MEDIAN BOUND
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 50.     , 0.000001, "rx2a"/**, true**/ );
    // UPPER BOUNDS
    // ------------------------------------------------
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 62.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 62.     , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 4000.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 63.     , 0.000001, "rx2a"/**, false**/);
    run_test<double>(app, true, "fc", 5999.01 , 0.000001, "rx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 63.     , 0.000001, "rx2a"/**, false**/);

    // TX1A DDCDUC CHANNEL
    // Tuning Freq for FMCOMMS2 [2400 - 2500 MHz]
    // @TODO Add FMCOMMS2 vs FMCOMMS3 funcationality
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "fc", 2399.99 , 0.000001, "tx1a"/**, false**/);
    run_test<double>(app, true, "fc", 2400.   , 0.000001, "tx1a"/**, true**/ );
    //// MEDIAN BOUNDS
    run_test<double>(app, true, "fc", 2000.   , 0.000001, "tx1a"/**, true**/ );
    //// UPPER BOUNDS
    run_test<double>(app, true, "fc", 2500.   , 0.000001, "tx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 2500.99 , 0.000001, "tx1a"/**, false**/);
    // Tuning Freq for FMCOMMS2 [70 - 6000 MHz]
    // LOWER BOUNDS
    run_test<double>(app, true, "fc", 69.99   , 0.000001, "tx1a"/**, false**/);
    run_test<double>(app, true, "fc", 70.     , 0.000001, "tx1a"/**, true**/ );
    //// MEDIAN BOUNDS
    run_test<double>(app, true, "fc", 3000.   , 0.000001, "tx1a"/**, true**/ );
    //// UPPER BOUNDS
    run_test<double>(app, true, "fc", 6000.   , 0.000001, "tx1a"/**, true**/ );
    run_test<double>(app, true, "fc", 6000.01 , 0.000001, "tx1a"/**, false**/);
    // Bandwidth [0.000024140625 - 14 MHz]
    // ================================================
    //  LOWER BOUNDS
    run_test<double>(app, true, "bw", 0.000023, 0.000001, "tx1a"/**, false**/);
    run_test<double>(app, true, "bw", 0.000024140625, 0.000001, "tx1a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "bw", 10.     , 0.000001, "tx1a"/**, true**/);
    // UPPER BOUNDS
    run_test<double>(app, true, "bw", 14.     , 0.000001, "tx1a"/**, true**/);
    run_test<double>(app, true, "bw", 14.01   , 0.000001, "tx1a"/**, false**/);
    // Sampling rate [~0.000255 - 15.36 Msps]
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "fs", 0.000253, 0.000001, "tx1a"/**, false**/);
    run_test<double>(app, true, "fs", 0.000255, 0.000001, "tx1a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "fs", 10.     , 0.000001, "tx1a"/**, true**/ );
    // UPPER BOUND
    run_test<double>(app, true, "fs", 15.36   , 0.000001, "tx1a"/**, true**/ );
    run_test<double>(app, true, "fs", 15.37   , 0.000001, "tx1a"/**, false**/);
    // Samples are complex
    // ================================================
    run_test<bool>(app, true, "sc", false     , 0.000001, "tx1a"/**, false**/ );
    run_test<bool>(app, true, "sc", true      , 0.000001, "tx1a"/**, true**/  );
    // Gain Mode
    // ================================================
    run_test<bool>(app, true, "gm", "manual"     , 0.000001, "tx1a"/**, false**/ );
    run_test<bool>(app, true, "gm", "automatic"  , 0.000001, "tx1a"/**, true**/  );
    // Gain (-89.25 - 0 dB)
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "gn", -89.76  , 0.000001, "tx1a"/**, false**/);
    run_test<double>(app, true, "gn", -89.75  , 0.000001, "tx1a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "gn", -40.00  , 0.000001, "tx1a"/**, true**/ );
    // UPPER BOUND
    run_test<double>(app, true, "gn", 0.      , 0.000001, "tx1a"/**, true**/ );
    run_test<double>(app, true, "gn", 0.01    , 0.000001, "tx1a"/**, false**/);


    // TX2A CHANNEL
    // Tuning Freq for FMCOMMS2 [2400 - 2500 MHz]
    // @TODO Add FMCOMMS2 vs FMCOMMS3 funcationality
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "fc", 2399.99 , 0.000001, "tx2a"/**, false**/);
    run_test<double>(app, true, "fc", 2400.   , 0.000001, "tx2a"/**, true**/ );
    //// MEDIAN BOUNDS
    run_test<double>(app, true, "fc", 2000.   , 0.000001, "tx2a"/**, true**/ );
    //// UPPER BOUNDS
    run_test<double>(app, true, "fc", 2500.   , 0.000001, "tx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 2500.99 , 0.000001, "tx2a"/**, false**/);
    // Tuning Freq for FMCOMMS2 [70 - 6000 MHz]
    // LOWER BOUNDS
    run_test<double>(app, true, "fc", 69.99   , 0.000001, "tx2a"/**, false**/);
    run_test<double>(app, true, "fc", 70.     , 0.000001, "tx2a"/**, true**/ );
    //// MEDIAN BOUNDS
    run_test<double>(app, true, "fc", 3000.   , 0.000001, "tx2a"/**, true**/ );
    //// UPPER BOUNDS
    run_test<double>(app, true, "fc", 6000.   , 0.000001, "tx2a"/**, true**/ );
    run_test<double>(app, true, "fc", 6000.01 , 0.000001, "tx2a"/**, false**/);
    // Bandwidth [0.2 - 56 MHz]
    // ================================================
    //  LOWER BOUNDS
    run_test<double>(app, true, "bw", 0.19    , 0.000001, "tx2a"/**, false**/);
    run_test<double>(app, true, "bw", 0.2     , 0.000001, "tx2a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "bw", 30.     , 0.000001, "tx2a"/**, true**/);
    // UPPER BOUNDS
    run_test<double>(app, true, "bw", 56.     , 0.000001, "tx2a"/**, true**/);
    run_test<double>(app, true, "bw", 56.01   , 0.000001, "tx2a"/**, false**/);
    // Sampling rate [2.083334 - 61.44 Msps]
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "fs", 2.08    , 0.000001, "tx2a"/**, false**/);
    run_test<double>(app, true, "fs", 2.083334, 0.000001, "tx2a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "fs", 32.     , 0.000001, "tx2a"/**, true**/ );
    // UPPER BOUND
    run_test<double>(app, true, "fs", 61.44   , 0.000001, "tx2a"/**, true**/ );
    run_test<double>(app, true, "fs", 61.45   , 0.000001, "tx2a"/**, false**/);
    // Samples are complex
    // ================================================
    run_test<bool>(app, true, "sc", false     , 0.000001, "tx2a"/**, false**/ );
    run_test<bool>(app, true, "sc", true      , 0.000001, "tx2a"/**, true**/  );
    // Gain Mode
    // ================================================
    run_test<bool>(app, true, "gm", "manual"     , 0.000001, "tx1a"/**, false**/ );
    run_test<bool>(app, true, "gm", "automatic"  , 0.000001, "tx1a"/**, true**/  );
    // Gain (-89.25 - 0 dB)
    // ================================================
    // LOWER BOUNDS
    run_test<double>(app, true, "gn", -89.76  , 0.000001, "tx2a"/**, false**/);
    run_test<double>(app, true, "gn", -89.75  , 0.000001, "tx2a"/**, true**/ );
    // MEDIAN BOUND
    run_test<double>(app, true, "gn", -40.00  , 0.000001, "tx2a"/**, true**/ );
    // UPPER BOUND
    run_test<double>(app, true, "gn", 0.      , 0.000001, "tx2a"/**, true**/ );
    run_test<double>(app, true, "gn", 0.01    , 0.000001, "tx2a"/**, false**/);


    //run_test<std:string>(app, true, "gm", "manual"   , 0.000001, "tx2a"/**, false**/);
    //run_test<bool>(app, true, "sc", true , 0.000001, "tx2a"/**, false**/);

    app.wait();       // wait until app is "done"
    app.finish();     // do end-of-run processing like dump properties
    // app.stop();
  } catch (std::string &e) {
    std::cerr << "app failed: " << e << std::endl;
    return 1;
  }
  return 0;
}


