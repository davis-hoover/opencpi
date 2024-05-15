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

#include "test_drc-worker.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Test_drcWorkerTypes;

#include <iostream>
#define _LOG_INFO(fmt, ...) Test_drcWorkerBase::log(8, fmt, ##__VA_ARGS__)
#define _LOG_DEBUG(fmt, ...) Test_drcWorkerBase::log(10, fmt, ##__VA_ARGS__)
#include "TestDRC.hh"

size_t test_no;

struct test_config_t {
  uint16_t nconfig;
  unsigned multichan;
  unsigned name;
  unsigned recoverable;
  int tol_adjust;
};

class Test_drcWorker : public Test_drcWorkerBase {
  ConfigurationChannel get_default_configuration_channel(
      const std::string& rf_port_name, int tol_adjust = 0) {
    ConfigurationChannel ret;
    ret.rx = true;
    ret.tuning_freq_MHz = tol_adjust == 5 ? 2.05 : (tol_adjust == 1 ? 0.95 : 1.5);
    ret.bandwidth_3dB_MHz = tol_adjust == 6 ? 4.05 : (tol_adjust == 2 ? 2.95 : 3.5);
    ret.sampling_rate_Msps = tol_adjust == 7 ? 6.05 : (tol_adjust == 3 ? 4.95 : 5.5);
    ret.samples_are_complex = true;
    ret.gain_mode.assign("manual");
    ret.gain_dB = tol_adjust == 8 ? 10.05 : (tol_adjust == 4 ? -10.05 : 0.);
    ret.rf_port_name.assign(rf_port_name);
    ret.rf_port_num = 0;
    ret.app_port_num = 0;
    ret.tolerance_tuning_freq_MHz = 0.1;
    ret.tolerance_bandwidth_3dB_MHz = 0.1;
    ret.tolerance_sampling_rate_Msps = 0.1;
    ret.tolerance_gain_dB = 0.1;
    return ret;
  }
  Configuration set_config(TestDRC& uut, test_config_t test_config, bool good = true) {
    Configuration config;
    config.recoverable = test_config.recoverable == 1;
    std::string rf_port_name;
    if (test_config.name) {
      rf_port_name.assign("p1");
    }
    ConfigurationChannel chan;
    chan = get_default_configuration_channel(rf_port_name, test_config.tol_adjust);
    if (!good) {
      chan.tuning_freq_MHz = 2.2;
    }
    config.channels.emplace(0, chan);
    if (test_config.multichan) {
      if (test_config.name) {
        rf_port_name.assign("p2");
      }
      else {
        rf_port_name.clear();
      }
      chan = get_default_configuration_channel(rf_port_name, test_config.tol_adjust);
      chan.rx = false;
      if (test_config.nconfig == 1) {
        config.channels.emplace(1, chan);
      }
    }
    uint16_t configuration = 0;
    uut.set_configuration(configuration++, config);
    if (test_config.nconfig > 1) {
      if (test_config.name) {
        rf_port_name.assign("p2");
      }
      else {
        rf_port_name.clear();
      }
      chan = get_default_configuration_channel(rf_port_name, test_config.tol_adjust);
      if (!good) {
        chan.tuning_freq_MHz = 2.2;
      }
      chan.rx = false;
      config.channels[0] = chan;
      uut.set_configuration(configuration++, config);
    }
    uut.set_configuration_length(configuration);
    return config;
  }
  void test_prepare(TestDRC& uut, uint16_t nconfig, Configuration& config2, bool good = true) {
    for (uint16_t configuration = 0; configuration < nconfig; configuration++) {
      uut.set_prepare(configuration);
      auto status = uut.get_status();
      if (good) {
        if (status[configuration].state != state_t::prepared) {
          throw std::runtime_error("failure");
        }
      }
      else {
        if (config2.recoverable && (status[configuration].state != state_t::error)) {
          throw std::runtime_error("failure");
        }
      }
    }
  }
  void test_start(TestDRC& uut, uint16_t nconfig, Configuration& config2, bool good = true) {
    for (uint16_t configuration = 0; configuration < nconfig; configuration++) {
      uut.set_start(configuration);
      auto status = uut.get_status();
      if (good) {
        if (status[configuration].state != state_t::operating) {
          throw std::runtime_error("failure");
        }
        auto& schans = status[configuration].channels;
        if (status.size() != nconfig) {
          throw std::runtime_error("failure");
        }
        //uint16_t idx = 0;
        for (auto it = schans.begin(); it != schans.end(); ++it) {
          if ((it->second.tuning_freq_MHz - config2.channels[0].tuning_freq_MHz) > 0.1) {
            throw std::runtime_error("failure");
          }
          if ((it->second.bandwidth_3dB_MHz - config2.channels[0].bandwidth_3dB_MHz) > 0.1) {
            throw std::runtime_error("failure");
          }
          if ((it->second.sampling_rate_Msps - config2.channels[0].sampling_rate_Msps) > 0.1) {
            throw std::runtime_error("failure");
          }
          if (!it->second.samples_are_complex) {
            throw std::runtime_error("failure");
          }
          if (it->second.gain_mode.compare("manual")) {
            throw std::runtime_error("failure");
          }
          if ((it->second.gain_dB - config2.channels[0].gain_dB) > 0.1) {
            throw std::runtime_error("failure");
          }
        }
      }
      else {
        if (config2.recoverable && (status[configuration].state != state_t::error)) {
          throw std::runtime_error("failure");
        }
      }
    }
  }
  void test_stop(TestDRC& uut, uint16_t nconfig) {
    for (uint16_t configuration = 0; configuration < nconfig; configuration++) {
      uut.set_stop(configuration);
      auto status = uut.get_status();
      if (status[configuration].state != state_t::prepared) {
        throw std::runtime_error("failure");
      }
    }
  }
  void test_release(TestDRC& uut, uint16_t nconfig) {
    for (uint16_t configuration = 0; configuration < nconfig; configuration++) {
      uut.set_release(configuration);
      auto status = uut.get_status();
      if (status[configuration].state != state_t::inactive) {
        throw std::runtime_error("failure");
      }
    }
  }
  void test_constructor() {
    _LOG_INFO("test %zu ========== testing constructor", test_no);
    TestDRC uut;
    uut.initialize({}, {});
  }
  void test_set_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing set known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
  }
  void test_set_release_release_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing release, release known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_release(uut, config.nconfig);
    test_release(uut, config.nconfig);
  }
  void test_set_prepare_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_prepare(uut, config.nconfig, config2);
  }
  void test_set_prepare_release_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare, release known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_prepare(uut, config.nconfig, config2);
    test_release(uut, config.nconfig);
  }
  void test_set_prepare_release_release_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare, release, release known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_prepare(uut, config.nconfig, config2);
    test_release(uut, config.nconfig);
    test_release(uut, config.nconfig);
  }
  void test_set_prepare_start_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare, start known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_prepare(uut, config.nconfig, config2);
    test_start(uut, config.nconfig, config2);
  }
  void test_set_prepare_start_stop_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare, start, stop known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_prepare(uut, config.nconfig, config2);
    test_start(uut, config.nconfig, config2);
    test_stop(uut, config.nconfig);
  }
  void test_set_prepare_start_stop_release_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare, start, stop, release known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_prepare(uut, config.nconfig, config2);
    test_start(uut, config.nconfig, config2);
    test_stop(uut, config.nconfig);
    test_release(uut, config.nconfig);
  }
  void test_set_prepare_start_stop_release_release_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare, start, stop, release, release known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_prepare(uut, config.nconfig, config2);
    test_start(uut, config.nconfig, config2);
    test_stop(uut, config.nconfig);
    test_release(uut, config.nconfig);
    test_release(uut, config.nconfig);
  }
  void test_set_prepare_start_release_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare, start, release known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_prepare(uut, config.nconfig, config2);
    test_start(uut, config.nconfig, config2);
    test_release(uut, config.nconfig);
  }
  void test_set_prepare_start_release_release_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare, start, release, release known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_prepare(uut, config.nconfig, config2);
    test_start(uut, config.nconfig, config2);
    test_release(uut, config.nconfig);
    test_release(uut, config.nconfig);
  }
  void test_set_start_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing start known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_start(uut, config.nconfig, config2);
  }
  void test_set_start_stop_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing start and release known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_start(uut, config.nconfig, config2);
    test_stop(uut, config.nconfig);
  }
  void test_set_start_release_good(test_config_t config) {
    _LOG_INFO("test %zu ========== testing start and release known good configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config);
    test_start(uut, config.nconfig, config2);
    test_release(uut, config.nconfig);
  }
  void test_set_prepare_bad(test_config_t config) {
    _LOG_INFO("test %zu ========== testing prepare known bad configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config, false);
    test_prepare(uut, config.nconfig, config2, false);
  }
  void test_set_start_bad(test_config_t config) {
    _LOG_INFO("test %zu ========== testing start known bad configuration", test_no);
    TestDRC uut;
    uut.initialize({}, {});
    Configuration config2 = set_config(uut, config, false);
    test_start(uut, config.nconfig, config2, false);
  }
  int do_test() {
    int ret = 0;
    test_no = 0;
    try {
      test_constructor();
      test_no++;
      for (int tol_adjust = 0; tol_adjust <= 8; tol_adjust++) {
        for (uint16_t nconfig = 1; nconfig <= 2; nconfig++) {
          for (unsigned multichan = 0; multichan <= 1; multichan++) {
            for (unsigned name = 0; name <= 1; name++) {
              for (unsigned recoverable = 0; recoverable <= 1; recoverable++) {
                if (!((nconfig == 2) && (multichan == 1))) {
                  test_config_t config;
                  config.nconfig = nconfig;
                  config.multichan = multichan;
                  config.name = name;
                  config.recoverable = recoverable;
                  config.tol_adjust = tol_adjust;
                  test_set_good(config);
                  test_no++;
                  test_set_release_release_good(config);
                  test_no++;
                  test_set_prepare_good(config);
                  test_no++;
                  test_set_prepare_release_good(config);
                  test_no++;
                  test_set_prepare_release_release_good(config);
                  test_no++;
                  test_set_prepare_start_good(config);
                  test_no++;
                  test_set_prepare_start_stop_good(config);
                  test_no++;
                  test_set_prepare_start_stop_release_good(config);
                  test_no++;
                  test_set_prepare_start_stop_release_release_good(config);
                  test_no++;
                  test_set_prepare_start_release_good(config);
                  test_no++;
                  test_set_prepare_start_release_release_good(config);
                  test_no++;
                  test_set_start_good(config);
                  test_no++;
                  test_set_start_stop_good(config);
                  test_no++;
                  test_set_start_release_good(config);
                  test_no++;
                  if (recoverable) {
                    test_set_prepare_bad(config);
                    test_no++;
                    test_set_start_bad(config);
                    test_no++;
                  }
                }
              }
            }
          }
        }
      }
    }
    catch (std::string& err) {
      std::cout << "[INFO] FAIL";
      ret = 1;
    }
    _LOG_INFO("==================== ALL PASSED");
    return ret;
  }
  RCCResult run(bool /*timedout*/) {
    static bool first = true;
    if (first) {
      first = false;
      do_test();
    }
    return RCC_DONE;
  }
};

TEST_DRC_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case
TEST_DRC_END_INFO
