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
#include <string>
#include <vector>
#include <sstream>
#include <fstream>
#include <ios>
#include <unistd.h> // usleep
#include "OcpiApi.hh"

/// @TODO / FIXME move this functionality into a generic worker once component slaves (slave that is the drc spec, and not a hardware-specific worker) are supported

namespace OA = OCPI::API;

struct app_args_t {
  std::string oas_path;
  std::string test_cases_path;
};

struct drc_channel_t {
  bool        rx;
  double      tuning_freq_MHz;
  double      bandwidth_3dB_MHz;
  double      sampling_rate_Msps;
  bool        samples_are_complex;
  std::string gain_mode;
  double      gain_dB;
  double      tolerance_tuning_freq_MHz;
  double      tolerance_bandwidth_3dB_MHz;
  double      tolerance_sampling_rate_Msps;
  double      tolerance_gain_dB;
  std::string rf_port_name;
  drc_channel_t() :
    rx(true),
    tuning_freq_MHz(-1),
    bandwidth_3dB_MHz(-1),
    sampling_rate_Msps(-1),
    samples_are_complex(true),
    gain_dB(0),
    tolerance_tuning_freq_MHz(-1),
    tolerance_bandwidth_3dB_MHz(-1),
    tolerance_gain_dB(-1) {
  }
};

struct drc_configuration_t {
  std::vector<drc_channel_t> channels;
};

typedef std::vector<drc_configuration_t> drc_configurations_t;

/// @brief row is a single channel, multiple rows build up multi-chan test case
struct csv_row_t : public drc_channel_t {
  size_t       row_num;
  std::string  transition;
  unsigned     configuration;
  unsigned     channel;
  bool         fatal;
  std::string  comment;
  csv_row_t() : drc_channel_t(),
    row_num(0), configuration(0),channel(0),fatal(false) {
  }
};

/// @brief a test case can consist of multiple configurations and/or channels
typedef std::vector<csv_row_t>       csv_test_case_t;
typedef std::vector<csv_test_case_t> csv_test_cases_t;

app_args_t verify_and_return_app_args(int argc, char **argv) {
  app_args_t ret;
  bool success = argc == 5;
  bool argv1_good = false;
  bool argv3_good = false;
  if(success) {
    argv1_good = std::string(argv[1]).compare("-o") == 0;
    argv3_good = std::string(argv[3]).compare("-t") == 0;
  }
  if(success && argv1_good && argv3_good) {
    ret.oas_path.assign(argv[2]);
    ret.test_cases_path.assign(argv[4]);
  }
  if(!success) {
    std::cout << "Usage: drc_test -o [OAS_PATH] -t [TEST_CASES_PATH]\n";
    throw std::string("[ERROR] invalid args");
  }
  return ret;
}

/// @brief a csv file consists of multiple test cases
csv_test_cases_t read_csv_file(std::string filename) {
  csv_test_cases_t ret;
  csv_test_case_t test_case;
  std::ifstream fin;
  fin.open(filename);
  std::vector<std::string> row_str;
  std::string line, word, tmp;
  getline(fin,line); // header
  size_t row_num = 2;
  while(getline(fin,line)) {
    row_str.clear();
    std::stringstream ss(line);
    while(getline(ss,word,',')) {
      row_str.push_back(word);
    }
    size_t idx = 0;
    csv_row_t row;
    row.row_num       = row_num++;
    row.transition    = row_str[idx++];
    row.configuration = stoi(row_str[idx++]);
    if(row.transition.empty()) {
      row.channel     = stoi(row_str[idx]);
    }
    idx++;
    std::string::size_type sz;
    if(row.transition.empty()) {
      row.rx                           = !row_str[idx++].compare("true");
      row.tuning_freq_MHz              = stod(row_str[idx++],&sz);
      row.bandwidth_3dB_MHz            = stod(row_str[idx++],&sz);
      row.sampling_rate_Msps           = stod(row_str[idx++],&sz);
      row.samples_are_complex          = !row_str[idx++].compare("true");
      row.gain_mode                    = row_str[idx++];
      row.gain_dB                      = stod(row_str[idx++],&sz);
      row.tolerance_tuning_freq_MHz    = stod(row_str[idx++],&sz);
      row.tolerance_bandwidth_3dB_MHz  = stod(row_str[idx++],&sz);
      row.tolerance_sampling_rate_Msps = stod(row_str[idx++],&sz);
      row.tolerance_gain_dB            = stod(row_str[idx++],&sz);
      row.rf_port_name                 = row_str[idx++];
    }
    else {
      idx += 12;
      row.fatal                        = !row_str[idx++].compare("true");
    }
    test_case.push_back(row);
    bool terminate_test_case = !row.transition.compare("start");
    if(terminate_test_case) {
      ret.push_back(test_case);
      test_case.clear();
    }
  }
  return ret;
}

std::string get_cfgs_str(drc_configurations_t cfgs) {
  std::ostringstream oss;
  for(auto itcfgs=cfgs.begin(); itcfgs!=cfgs.end(); ++itcfgs) {
    oss << "{"; // start of configuration
    //oss << "description LOCK_DRC_TEST_APP,";
    oss << "recoverable false,";
    oss << "channels {"; // start of all channels
    for(auto it=itcfgs->channels.begin(); it!=itcfgs->channels.end(); ++it) {
      oss << "{"; // start of channel
      oss << "rx "                            << it->rx;
      oss << ",tuning_freq_MHz "              << it->tuning_freq_MHz;
      oss << ",bandwidth_3dB_MHz "            << it->bandwidth_3dB_MHz;
      oss << ",sampling_rate_Msps "           << it->sampling_rate_Msps;
      oss << ",samples_are_complex "          << it->samples_are_complex;
      oss << ",gain_mode "                    << it->gain_mode;
      oss << ",gain_dB "                      << it->gain_dB;
      oss << ",tolerance_tuning_freq_MHz "    << it->tolerance_tuning_freq_MHz;
      oss << ",tolerance_bandwidth_3dB_MHz "  << it->tolerance_bandwidth_3dB_MHz;
      oss << ",tolerance_sampling_rate_Msps " << it->tolerance_sampling_rate_Msps;
      oss << ",tolerance_gain_dB "            << it->tolerance_gain_dB;
      oss << ",rf_port_name "                 << it->rf_port_name;
      oss << "}"; // end of channel
      if((itcfgs->channels.size() > 1) && (it+1 != itcfgs->channels.end())) {
        oss << ",";
      }
    }
    oss << "}"; // end of all channels
    if((cfgs.size() > 1) && (itcfgs+1 != cfgs.end())) {
      oss << ",";
    }
    oss << "}"; // end of configuration
  }
  return oss.str();
}

void print_info_configuration_channel(csv_row_t test) {
  std::cout << "[INFO]     : csv_line " << test.row_num << ":   \t\t";
  std::cout << "cfg="  << test.configuration;
  std::cout << ",ch="  << test.channel;
  std::cout << ",rx="  << (test.rx ? "1" : "0");
  std::cout << ",fc="  << test.tuning_freq_MHz;
  std::cout << ",bw="  << test.bandwidth_3dB_MHz;
  std::cout << ",fs="  << test.sampling_rate_Msps;
  std::cout << ",sc="  << (test.samples_are_complex ? "1" : "0");
  std::cout << ",gm="  << test.gain_mode.substr(0,3);
  std::cout << ",gn="  << test.gain_dB;
  std::cout << ",fct=" << test.tolerance_tuning_freq_MHz;
  std::cout << ",bwt=" << test.tolerance_bandwidth_3dB_MHz;
  std::cout << ",fst=" << test.tolerance_sampling_rate_Msps;
  std::cout << ",gnt=" << test.tolerance_gain_dB;
  std::cout << ",rf="  << test.rf_port_name;
  //std::cout << ",fatal=" << (test.fatal ? "1" : "0");
  std::cout << "\n";
}

int main(int argc, char **argv) {
  int ret = 0;
  static bool first = true;
  app_args_t app_args;
  try {
    app_args = verify_and_return_app_args(argc,argv);
  } catch (std::string &err) {
    std::cout << err << "\n";
    ret = 1;
  }
  if(!ret) {
    OA::Application app(app_args.oas_path.c_str());
    try {
      app.initialize();
      app.start();

    } catch (std::string &err) {
      std::cout << err << "\n";
      ret = 1;
    }
    csv_test_cases_t test_cases = read_csv_file(app_args.test_cases_path);
    for(auto it1=test_cases.begin(); it1!=test_cases.end(); ++it1) {
      drc_configurations_t cfgs;
      for(auto it=it1->begin(); it!=it1->end(); ++it) { // channels
        if(ret) {
          break;
        }
        else {
          bool expected = !it->fatal;
          if(it->transition.empty()) {
            while(cfgs.size() < it->configuration+1) {
              cfgs.push_back(drc_configuration_t());
            }
            drc_configuration_t& configuration = cfgs[it->configuration];
            if(it->channel > 15) {
              std::cout << "[WARN] channel seen above 15 - check CSV...\n";
            }
            while(configuration.channels.size() < it->channel+1) {
              configuration.channels.push_back(drc_channel_t());
            }
            configuration.channels[it->channel] = (drc_channel_t)(*it);
            if(it->configuration > 15) {
              std::cout << "[WARN] configuration seen above 15 - check CSV...\n";
            }
            std::string cfgsstr = get_cfgs_str(cfgs);
            if(it->tuning_freq_MHz < 0) {
              std::cout << "ERR\n";
            }
            app.setProperty("drc","configurations",cfgsstr.c_str());
            //std::cout << "setting property: configurations: " << cfgsstr << "\n";
            print_info_configuration_channel(*it);
          }
          else {
            try {
              std::string configuration = std::to_string(it->configuration);
              app.setProperty("drc",it->transition.c_str(),configuration.c_str());
              if(first){
                usleep(3000000); // give certain hardware a time to startup
                first = false;
              }
              if(it->transition.compare("start")) {
                std::cout << "[INFO]     ";
              }
              else {
                std::cout << (expected ? "[INFO] PASS" : "[INFO] FAIL");
                if(!expected) {
                  ret = 1;
                }
              }
            }
            catch (std::string err) {
              std::cout << (expected ? "[INFO] FAIL" : "[INFO] PASS");
              if(expected) {
                ret = 1;
              }
            }
            std::cout << ": csv_line " << it->row_num << ":";
            std::cout << " " << it->transition;
            std::cout << ":\tcfg=" << it->configuration;
            std::cout << ",fatal=" << (it->fatal ? "1" : "0") << "\n";
          }
        }
      }
    }
    try {
      app.stop();
    } catch (std::string &e) {
      std::cout << e << "\n";
      ret = 1;
    }
    std::cout << "[INFO] " << (ret ? "FAIL" : "PASS") << "\n";
  }
  return ret;
}
