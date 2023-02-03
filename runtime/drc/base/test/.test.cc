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

#include ".TestDRC.hh"
#include <list>
#include <cassert>

using namespace OCPI::DRC_PHASE_2;
typedef RFPort::direction_t dir_t;
typedef RFPortConfigLockRequest PR; // "P"ort "R"equest
typedef Configuration Conf;

PR last_port_request = PR(dir_t::rx,1.7,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0);
PR last_port_request2 = PR(dir_t::rx,1.7,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0);
size_t last_num_port_requests;
bool last_expected_success = true;

void print_port_request(const PR& req) {
  std::cout << " " << to_string(req.get_direction());
  std::cout << " " << req.get_tuning_freq_MHz();
  std::cout << " " << req.get_bandwidth_3dB_MHz();
  std::cout << " " << req.get_sampling_rate_Msps();
  std::cout << " " << req.get_sampling_rate_Msps();
  std::cout << " " << (req.get_samples_are_complex() ? "true" : "false");
  std::cout << " " << req.get_gain_mode();
  std::cout << " " << req.get_gain_dB();
  std::cout << " " << req.get_rf_port_name();
}

enum class test_t {
  start,
  start_release,
  start_stop_start,
  start_stop_start_release,
  prepare_start,
  prepare_start_release,
  all_ending_in_release};

/*! @brief Test a test case using one of the following scenarios:
 *         1. ->operating (start only)
 *         2. ->operating->prepared->operating (start, stop, then re-start)
 *         3. ->operating->inactive (start followed by release)
 *         4. ->prepared->operating (prepare before start)
 *         5. ->prepared->operating->inactive (prepare, start, then release)
 *         The scenario(s) are tested for known good configurations
 *         (expected_success=true) or known bad ones.
 *         It is important to test all of these scenarios for better code
 *         coverage. The usual scenario is to test a particular known
 *         good-or-bad test case for all scenarios ending in inactive, so
 *         that follow-on test cases can start from a known inactive state
 *         (sometimes you WANT to test a case in an previous operating state,
 *         in which case you would use one of the other scenarios as needed)
 ******************************************************************************/
void test(TestDRC& uut, uint16_t config_idx, const Conf& conf,
    bool expected_success, test_t type = test_t::all_ending_in_release) {
  std::list<test_t> type_list;
  if (type == test_t::all_ending_in_release) {
    type_list.push_back(test_t::start_release);
    type_list.push_back(test_t::start_stop_start_release);
    type_list.push_back(test_t::prepare_start_release);
  }
  else {
    type_list.push_back(type);
  }
  assert(conf.size() <= 2);
  last_port_request = conf[0];
  last_num_port_requests = 1;
  if (conf.size() == 2) {
    last_port_request2 = conf[1];
    last_num_port_requests = 2;
  }
  last_expected_success = expected_success;
  uut.set_configuration(config_idx, conf);
  for (auto it = type_list.begin(); it != type_list.end(); ++it) {
    bool success = true;
    bool do_prepare = (*it == test_t::prepare_start);
    if (*it == test_t::prepare_start_release)
      do_prepare = true;
    if (do_prepare)
      success = uut.prepare(config_idx); // prepare
    if (do_prepare && (success != expected_success))
      throw std::runtime_error("fail prepare");
    bool start_success = uut.start(config_idx); // start
    success = start_success;
    if (success != expected_success)
      throw std::runtime_error("fail start");
    bool do_stop_restart = (*it == test_t::start_stop_start);
    if (*it == test_t::start_stop_start_release)
      do_stop_restart = true;
    if (expected_success && do_stop_restart) {
      success = uut.stop(config_idx); // stop
      if (success != expected_success)
        throw std::runtime_error("fail stop");
      success = uut.start(config_idx); // (re-)start
      if (success != expected_success)
        throw std::runtime_error("fail restart");
    }
    bool do_release = (*it == test_t::start_release);
    if (*it == test_t::start_stop_start_release)
      do_release = true;
    if (*it == test_t::prepare_start_release)
      do_release = true;
    if (do_release && success)
      success = uut.release(config_idx); // release
    if (success != expected_success)
      throw std::runtime_error("fail release");
  }
  std::cout << "[INFO] PASS";
  print_port_request(last_port_request);
  if (last_num_port_requests == 2) {
    std::cout << ",";
    print_port_request(last_port_request);
  }
  std::cout << " " << (last_expected_success ? "1" : "0") << "\n";
}

std::map<std::string,RFPort::direction_t> get_rf_port_direction_dict() {
  std::map<std::string,RFPort::direction_t> ret;
  ret["p1"] = RFPort::direction_t::rx;
  ret["p2"] = RFPort::direction_t::tx;
  return ret;
}

void test_TestDRC_direction(TestDRC& uut) {
  // test successful request by direction only
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"",0,0)),true);
  test(uut,0,Conf(1,PR(dir_t::tx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"",0,0)),true);
  // test known good request by rf_port_name for all ports
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0)),true);
  test(uut,0,Conf(1,PR(dir_t::tx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0)),true);
  // test known bad request by rf_port_name for all ports
  test(uut,0,Conf(1,PR(dir_t::tx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0)),false);
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0)),false);
}

void test_TestDRC_tuning_freq_MHz(TestDRC& uut) {
  std::map<std::string,RFPort::direction_t> dir_dict = get_rf_port_direction_dict();
  for (auto it = dir_dict.begin(); it != dir_dict.end(); ++it) {
    test(uut,0,Conf(1,PR(it->second,0.8,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),false);
    test(uut,0,Conf(1,PR(it->second,1.0,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),true);
    test(uut,0,Conf(1,PR(it->second,2.0,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),true);
    test(uut,0,Conf(1,PR(it->second,2.2,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),false);
  }
}

void test_TestDRC_bandwidth_MHz(TestDRC& uut) {
  std::map<std::string,RFPort::direction_t> dir_dict = get_rf_port_direction_dict();
  for (auto it = dir_dict.begin(); it != dir_dict.end(); ++it) {
    test(uut,0,Conf(1,PR(it->second,1.5,2.8,5.5,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),false);
    test(uut,0,Conf(1,PR(it->second,1.5,3.0,5.5,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),true);
    test(uut,0,Conf(1,PR(it->second,1.5,4.0,5.5,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),true);
    test(uut,0,Conf(1,PR(it->second,1.5,4.2,5.5,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),false);
  }
}

void test_TestDRC_sampling_rate_Msps(TestDRC& uut) {
  std::map<std::string,RFPort::direction_t> dir_dict = get_rf_port_direction_dict();
  for (auto it = dir_dict.begin(); it != dir_dict.end(); ++it) {
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,4.8,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),false);
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,5.0,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),true);
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,6.0,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),true);
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,6.2,true,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),false);
  }
}

void test_TestDRC_samples_are_complex(TestDRC& uut) {
  std::map<std::string,RFPort::direction_t> dir_dict = get_rf_port_direction_dict();
  for (auto it = dir_dict.begin(); it != dir_dict.end(); ++it) {
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,5.5,true ,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),true);
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,5.5,false,"manual",0,0.1,0.1,0.1,0.1,it->first,0,0)),false);
  }
}

void test_TestDRC_gain_mode(TestDRC& uut) {
  // test all known good gain modes for all ports, including switching between them
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0)),true);
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"auto"  ,0,0.1,0.1,0.1,0.1,"p1",0,0)),true);
  test(uut,0,Conf(1,PR(dir_t::tx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0)),true);
  // test a few known bad gain modes for all ports (base classes must overload
  // attempt_rf_port_config_locks() to implement hardware-specific gain modes
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,""       ,0,0.1,0.1,0.1,0.1,"p1",0,0)),false);
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"MANUAL" ,0,0.1,0.1,0.1,0.1,"p1",0,0)),false);
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"slowagc",0,0.1,0.1,0.1,0.1,"p1",0,0)),false);
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,""       ,0,0.1,0.1,0.1,0.1,"p2",0,0)),false);
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"MANUAL" ,0,0.1,0.1,0.1,0.1,"p2",0,0)),false);
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"slowagc",0,0.1,0.1,0.1,0.1,"p2",0,0)),false);
}

void test_TestDRC_gain_dB(TestDRC& uut) {
  std::map<std::string,RFPort::direction_t> dir_dict = get_rf_port_direction_dict();
  for (auto it = dir_dict.begin(); it != dir_dict.end(); ++it) {
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,5.5,true,"manual",-11,0.1,0.1,0.1,0.1,it->first,0,0)),false);
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,5.5,true,"manual",-10,0.1,0.1,0.1,0.1,it->first,0,0)),true);
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,5.5,true,"manual", 10,0.1,0.1,0.1,0.1,it->first,0,0)),true);
    test(uut,0,Conf(1,PR(it->second,1.5,3.5,5.5,true,"manual", 11,0.1,0.1,0.1,0.1,it->first,0,0)),false);
  }
}

void test_TestDRC_p1_must_match_p2(TestDRC& uut) {
  // ----------------------------------------------------------------------------------
  // P1 followed by P2 test
  // ----------------------------------------------------------------------------------
  // start with known good setting for rf_port_name=p1, as a config "0" left in operating state
  test_t type = test_t::prepare_start; // this leaves things in an operating state
  test(uut,0,Conf(1,PR(dir_t::rx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0)),true,type);
  // attempt a setting for rf_port_name=p2, as a config "1" that is incompatible
  // with currently operating config "0" (incompatible since p1 is locked and p2 must follow p1)
  test(uut,1,Conf(1,PR(dir_t::tx,1.8,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0)),false,type);
  test(uut,1,Conf(1,PR(dir_t::tx,1.5,3.8,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0)),false,type);
  test(uut,1,Conf(1,PR(dir_t::tx,1.5,3.5,5.8,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0)),false,type);
  uut.release_all(); // cleanup by putting all configs in inactive state
  // ----------------------------------------------------------------------------------
  // P2 followed by P1 test
  // ----------------------------------------------------------------------------------
  // start with known good setting for rf_port_name=p2, as a config "0" left in operating state
  test(uut,0,Conf(1,PR(dir_t::tx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0)),true,type);
  // attempt a setting for rf_port_name=p1, as a config "1" that is incompatible
  // with currently operating config "0" (incompatible since p2 is locked and p1 must follow p2)
  test(uut,1,Conf(1,PR(dir_t::rx,1.8,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0)),false,type);
  test(uut,1,Conf(1,PR(dir_t::rx,1.5,3.8,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0)),false,type);
  test(uut,1,Conf(1,PR(dir_t::rx,1.5,3.5,5.8,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0)),false,type);
  uut.release_all(); // cleanup by putting all configs in inactive state
  // ----------------------------------------------------------------------------------
  // P1, P2 together test
  // ----------------------------------------------------------------------------------
  // attempt a setting for p1 and p2, all as a part of the same config "0",
  // that is incompatible since p1 and p2 are different (similar test as before,
  // now just all a part of the same config instead of separate ones)
  Conf conf;
  conf.push_back(PR(dir_t::rx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0));
  conf.push_back(PR(dir_t::tx,1.8,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0));
  test(uut,0,conf,false);
  conf.clear();
  conf.push_back(PR(dir_t::rx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0));
  conf.push_back(PR(dir_t::tx,1.5,3.8,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0));
  test(uut,0,conf,false);
  conf.clear();
  conf.push_back(PR(dir_t::rx,1.5,3.5,5.5,true,"manual",0,0.1,0.1,0.1,0.1,"p1",0,0));
  conf.push_back(PR(dir_t::tx,1.5,3.5,5.8,true,"manual",0,0.1,0.1,0.1,0.1,"p2",0,0));
  uut.release_all(); // cleanup by putting all configs in inactive state
}

int test_TestDRC() {
  int ret = 0;
  try {
    TestDRC uut;
    test_TestDRC_direction(uut);
    test_TestDRC_tuning_freq_MHz(uut);
    test_TestDRC_bandwidth_MHz(uut);
    test_TestDRC_sampling_rate_Msps(uut);
    test_TestDRC_samples_are_complex(uut);
    test_TestDRC_gain_mode(uut);
    test_TestDRC_gain_dB(uut);
    test_TestDRC_p1_must_match_p2(uut);
    uut.release_all();
    uut.get_direction("p1");
    uut.get_tuning_freq_MHz("p1");
    uut.get_bandwidth_3dB_MHz("p1");
    uut.get_sampling_rate_Msps("p1");
    uut.get_gain_mode("p1");
    uut.get_gain_dB("p1");
    uut.get_direction("p2");
    uut.get_tuning_freq_MHz("p2");
    uut.get_bandwidth_3dB_MHz("p2");
    uut.get_sampling_rate_Msps("p2");
    uut.get_gain_mode("p2");
    uut.get_gain_dB("p2");
    TestDRC uut2;
    uut2.release_all();
    std::cout << "[INFO] PASS\n";
  } catch (std::string& err) {
    std::cout << "[INFO] FAIL";
    print_port_request(last_port_request);
    std::cout << " " << (last_expected_success ? "1" : "0") << "\n";
    ret = 1;
  }
  return ret;
}

int main() {
  return test_TestDRC();
}
