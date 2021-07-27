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
#include <iostream>
#include <unistd.h>
#include <cstdio>
#include <cassert>
#include <string>
#include <cstring> // strerror()
#include <sstream>
#include "OcpiApi.hh"
#include "AD9361_BIST.h"

namespace OA = OCPI::API;

#define LOG_PROCESSED_ARG(x) std::cout << "INFO: processed arg: " << #x << "=" \
	                           << app_main_args.x << "\n"
#define SET_APP_MAIN_ARG(arg,val) app_main_args.arg=val; LOG_PROCESSED_ARG(arg)

struct app_main_args_t {
  bool do_timeout;
  unsigned long timeout;
  bool d; // dump properties
  std::string app_xml_filepath;
  app_main_args_t() : do_timeout(false), timeout(0), d(false) {
  }
};

app_main_args_t app_main_args;

/// @return name of this file (does not contain path) with the extension removed
std::string& get_app_name() {
  static std::string ret(__FILE__);
  size_t pos = ret.find_last_of('/');
  if (pos != std::string::npos)
    ret = ret.substr(pos+1, ret.size()-pos-1);
  pos = ret.find_first_of('.');
  if (pos != std::string::npos)
    ret = ret.substr(0, pos);
  return ret;
}

void version() {
  std::cout << get_app_name() << " develop\n";
}

void usage() {
  version();
  std::cout << "usage: " << get_app_name() << " [--version] [--help] [-d] <app-xml>\n\n";
  std::cout << " -t         duration (seconds) to run the application if not done\n";
  std::cout << "            first; exit status is zero in either case\n";
  std::cout << " -d         dump properties\n";
  std::cout << " <app-xml>  (always required)\n";
}

void throw_if_not_followed_by_value(int argc, char **argv, int ii) {
  if (ii+1 >= argc) {
    std::ostringstream oss;
    oss << argv[ii] << "must be followed by a value\n";
    throw oss.str();
  }
}

void execute_cmd(const char* cmd) {
  if (system(cmd) != 0) {
    std::string err("system call ");
    err += cmd;
    err += " failed";
    throw err;
  }
}

void execute_cmd(std::string cmd) {
  execute_cmd(cmd.c_str());
}

void throw_if_app_xml_filepath_empty() {
  if (app_main_args.app_xml_filepath == "")
    throw std::string("app XML filepath must be specified as the last argument");
}

int parse_args(int argc, char **argv) {
  int ii=1; // start parsing at arg 1 (ignore arg 0)
  while (ii < argc) {
    int num_args_processed;
    if (strcmp(argv[ii],"--version") == 0) {
      version();
      return 0;
    }
    else if (strcmp(argv[ii],"--help") == 0) {
      usage();
      return 0;
    }
    else if (strcmp(argv[ii],"-t") == 0) {
      throw_if_not_followed_by_value(argc, argv, ii);
      SET_APP_MAIN_ARG(do_timeout, true);
      SET_APP_MAIN_ARG(timeout, strtoul(argv[ii+1], NULL, 0));
      num_args_processed = 2;
    }
    else if (strcmp(argv[ii],"-d") == 0) {
      SET_APP_MAIN_ARG(d, true);
      num_args_processed = 1;
    }
    else if (ii == argc-1) {
      SET_APP_MAIN_ARG(app_xml_filepath, argv[ii]);
      num_args_processed = 1;
    }
    else {
      std::ostringstream oss;
      oss << "invalid argument: " << argv[ii];
      throw oss.str();
    }
    ii += num_args_processed;
  }
  throw_if_app_xml_filepath_empty();
  return 1;
}

void delete_expected_file_write_out_file(OA::Application& app) {
  std::string fname = app.getPropertyValue<std::string>("file_write", "fileName");
  execute_cmd("rm -rf " + fname); 
}

void throw_if_iqstream_max_calculator_has_no_valid(OA::Application& app,
                                                   const char* inst,
                                                   const char* descr) {
  bool max_i_is_valid = app.getPropertyValue<bool>(inst, "max_I_is_valid");
  bool max_q_is_valid = app.getPropertyValue<bool>(inst, "max_Q_is_valid");
  OA::Short max_i = app.getPropertyValue<OA::Short>(inst, "max_I");
  OA::Short max_q = app.getPropertyValue<OA::Short>(inst, "max_Q");
  if ((!max_i_is_valid) || (!max_q_is_valid))
    throw std::string("no data was received from ") + std::string(descr);
  if ((max_i == 0) || (max_q == 0))
    throw std::string("one or more bit errors were observed");
}

/// @todo / FIXME - REMOVE THIS HARDWARE-SPECIFIC METHOD
size_t get_ad9361_bist_num_bit_errors(const std::string& rx_filename) {
  long long max_num_samps_to_process = 0;
  bool log_debug = false;
  // TODO - FIXME replace this "magic number" with something more logical - I manually observed raw
  // binary output to see 0x01ff existed in the file for one of I or Q, and the bit-reverse of that
  // is 0xff80, then octave hex2dec('01ffff80') yields the number below
  long long reg_sync_val = -1; // 4294967295; or 33554304;

  double estimated_ber;
  size_t num_lfsr_bits;
  size_t num_bits_in_file;
  size_t num_procd_bits;
  non_errno_failure_t non_errno_failure;
  int ret_errno = calculate_BIST_PRBS_RX_BER(rx_filename, estimated_ber,
                                             num_lfsr_bits,
                                             num_bits_in_file,
                                             num_procd_bits,
                                             max_num_samps_to_process,
                                             reg_sync_val, non_errno_failure,
                                             log_debug);
  if (!((ret_errno == 0) && (non_errno_failure == ERROR_NONE))) {
    if (ret_errno != 0) {
      print_error(strerror(ret_errno), false);
      if ((ret_errno == ENOENT) || (ret_errno == EISDIR))
        std::cout << " (attempted to open filename: '" << rx_filename << "')";
      std::cout << "\n";
      std::cout << "\n";
    }
    else if (non_errno_failure == ERROR_FILE_WAS_EMPTY) {
      if (reg_sync_val == -1) {
        print_error("file was empty", false);
        std::cout << " (file read was " << rx_filename << ")";
        std::cout << "\n";
      }
      else {
        print_error("reg sync val could not be found", false);
        std::cout << " (file read was " << rx_filename << ")";
        std::cout << "\n";
      }
    }
    else if (non_errno_failure == ERROR_FILE_ENDED_IN_MIDDLE_OF_AN_IQ_SAMPLE) {
      print_error("file ended in the middle of an I/Q sample", false);
      std::cout << " (file read was " << rx_filename << ")";
      std::cout << "\n";
    }
    throw std::string("error");
  }
  const size_t num_bit_errors = (size_t)(((double)num_procd_bits)*
                                estimated_ber);
  std::cout << "filename : " << rx_filename << "\n";
  std::cout << "number_of_processed_bits_shifted_through_LFSR : " \
            << num_lfsr_bits << "\n";
  std::cout << "number_of_total_bits_in_file : " << num_bits_in_file << "\n";
  std::cout << "number_of_processed_bits_in_file : " << num_procd_bits << "\n";
  std::cout << "estimated_number_of_bit_errors : " << num_bit_errors << "\n";
  std::cout << "estimated_BER : " << (estimated_ber*100.) << "%" << "\n";
  return num_bit_errors;
}

size_t get_num_bit_errors(OA::Application& app) {
  std::string fname = app.getPropertyValue<std::string>("file_write", "fileName");
  return get_ad9361_bist_num_bit_errors(fname); /// @todo / FIXME - MAKE THIS HARDWARE-PORTABLE (it is currently AD9361-specific)
}

void throw_if_num_bit_errors_not_zero(OA::Application& app) {
  size_t num_bit_errors = get_num_bit_errors(app);
  if (num_bit_errors == 0)
    std::cout << "SUCCESS: all data received without bit error\n";
  else {
    std::ostringstream oss;
    oss << "num_bit_errors was " << num_bit_errors \
        <<  " instead of the expected 0";
    throw oss.str();
  }
}

int main(int argc, char **argv) {
  try {
    if (parse_args(argc, argv) == 0)
      return 0;
    OA::Application app(app_main_args.app_xml_filepath);
    app.initialize(); // all resources have been allocated
    delete_expected_file_write_out_file(app);
    app.start();      // execution is started
    // Must use either wait()/finish() or stop(). The finish() method must
    // always be called after wait(). The start() method can be called
    // again after stop().
    if (app_main_args.do_timeout)
      for (unsigned nsec_rem = app_main_args.timeout; nsec_rem>0; nsec_rem--)
        sleep(1);
    else {
      app.wait(); // behave like ocpirun in absence of -t argument
      app.finish();
    }
    if (app_main_args.do_timeout)
      app.stop();
    if (app_main_args.d) {
      bool print_parameters = true;
      bool print_cached = false;
      app.dumpProperties(print_parameters, print_cached, NULL);
    }
    if (app_main_args.do_timeout) {
      throw_if_iqstream_max_calculator_has_no_valid(app,
          "iqstream_max_calculator_dac", "DAC data path");
      throw_if_iqstream_max_calculator_has_no_valid(app,
          "iqstream_max_calculator_adc", "ADC data path");
      throw_if_num_bit_errors_not_zero(app);
    }
  }
  catch (std::string &err) {
    std::cerr << "ERROR: " << err << "\n";
    return 1;
  }
  return 0;
}
