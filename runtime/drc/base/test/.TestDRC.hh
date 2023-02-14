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

#ifndef _TEST_DRC_HH
#define _TEST_DRC_HH

#include "DRC.hh"
using namespace OCPI::DRC_PHASE_2;

// -----------------------------------------------------------------------------
// STEP 1 - DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

class TestDRCCSP : public CSPBase {
  public:
  TestDRCCSP() {
    define();
  }
  void define() {
    instance();
  }
  void instance() {
    define_x_d();
    define_c();
  }
  void define_x_d() {
    m_solver.add_var<int32_t>("dir_p1");
    m_solver.add_var<double>("fc_meghz_p1", dfp_tol);
    m_solver.add_var<double>("bw_meghz_p1", dfp_tol);
    m_solver.add_var<double>("fs_megsps_p1", dfp_tol);
    m_solver.add_var<int32_t>("samps_comp_p1");
    m_solver.add_var<int32_t>("gain_mode_p1");
    m_solver.add_var<double>("gain_db_p1", dfp_tol);
    m_solver.add_var<int32_t>("dir_p2");
    m_solver.add_var<double>("fc_meghz_p2", dfp_tol);
    m_solver.add_var<double>("bw_meghz_p2", dfp_tol);
    m_solver.add_var<double>("fs_megsps_p2", dfp_tol);
    m_solver.add_var<int32_t>("samps_comp_p2");
    m_solver.add_var<int32_t>("gain_mode_p2");
    m_solver.add_var<double>("gain_db_p2", dfp_tol);
  }
  void define_c() {
    /// port p1: tests basic value limiting including a variety of constraint
    //           types:
    //           rhs double inequality
    //           rhs int32_t inequality
    //           rhs int32_t equality
    //           rhs variable
    m_solver.add_constr("dir_p1", "=", (int32_t)RFPort::direction_t::rx); // rhs int32_t equality
    m_solver.add_constr("fc_meghz_p1"  , ">=",          1.); // rhs double inequality
    m_solver.add_constr("fc_meghz_p1"  , "<=",          2.); // rhs double inequality
    m_solver.add_constr("bw_meghz_p1"  , ">=",          3.);
    m_solver.add_constr("bw_meghz_p1"  , "<=",          4.);
    m_solver.add_constr("fs_megsps_p1" , ">=",          5.);
    m_solver.add_constr("fs_megsps_p1" , "<=",          6.);
    m_solver.add_constr("samps_comp_p1", "=" , (int32_t)1);
    m_solver.add_constr("gain_mode_p1" , ">=", (int32_t)0); // rhs int32_t inagc
    m_solver.add_constr("gain_mode_p1" , "<=", (int32_t)1); // manual
    m_solver.add_constr("gain_db_p1" , ">=", -10.);
    m_solver.add_constr("gain_db_p1" , "<=", 10.);
    /// port p2: must match all settings of p1 (tests constraint propagation)
    m_solver.add_constr("dir_p2", "="  , (int32_t)RFPort::direction_t::tx);
    m_solver.add_constr("fc_meghz_p2"  , "=", "fc_meghz_p1"  );
    m_solver.add_constr("bw_meghz_p2"  , "=", "bw_meghz_p1"  );
    m_solver.add_constr("fs_megsps_p2" , "=", "fs_megsps_p1" );
    m_solver.add_constr("samps_comp_p2", "=", "samps_comp_p1");
    m_solver.add_constr("gain_mode_p2" , "=", (int32_t)1     );
    m_solver.add_constr("gain_db_p2"   , "=", "gain_db_p1"   );
  }
}; // class TestDRCCSP

// -----------------------------------------------------------------------------
// STEP 2 - DEFINE CONFIGURATOR THAT UTILIZES THE CSP
// -----------------------------------------------------------------------------

class TestConfigurator : public Configurator<TestDRCCSP> {
  public:
  TestConfigurator() {
    init_rf_port_p1();
    init_rf_port_p2();
  }
  protected:
  void init_rf_port_p1() {
    CSPVarMap map;
    map.insert(std::make_pair(RFPort::config_t::direction,
        "dir_p1"));
    map.insert(std::make_pair(RFPort::config_t::tuning_freq_MHz,
        "fc_meghz_p1"));
    map.insert(std::make_pair(RFPort::config_t::bandwidth_3dB_MHz,
        "bw_meghz_p1"));
    map.insert(std::make_pair(RFPort::config_t::sampling_rate_Msps,
        "fs_megsps_p1"));
    map.insert(std::make_pair(RFPort::config_t::samples_are_complex,
        "samps_comp_p1"));
    map.insert(std::make_pair(RFPort::config_t::gain_mode,
        "gain_mode_p1"));
    map.insert(std::make_pair(RFPort::config_t::gain_dB,
        "gain_db_p1"));
    m_dict["p1"] = map;
  }
  void init_rf_port_p2() {
    CSPVarMap map;
    map.insert(std::make_pair(RFPort::config_t::direction,
        "dir_p2"));
    map.insert(std::make_pair(RFPort::config_t::tuning_freq_MHz,
        "fc_meghz_p2"));
    map.insert(std::make_pair(RFPort::config_t::bandwidth_3dB_MHz,
        "bw_meghz_p2"));
    map.insert(std::make_pair(RFPort::config_t::sampling_rate_Msps,
        "fs_megsps_p2"));
    map.insert(std::make_pair(RFPort::config_t::samples_are_complex,
        "samps_comp_p2"));
    map.insert(std::make_pair(RFPort::config_t::gain_mode,
        "gain_mode_p2"));
    map.insert(std::make_pair(RFPort::config_t::gain_dB,
        "gain_db_p2"));
    m_dict["p2"] = map;
  }
}; // class TestConfigurator

// -----------------------------------------------------------------------------
// STEP 3 - DEFINE DRC (get/set APIs)
// -----------------------------------------------------------------------------

// test:
//  - multiple rx channels
//  - multiple tx channels
//  - request_config_lock() does not invalidate previous locks
class TestDRC : public DRC<TestConfigurator> {
  public:
  bool get_enabled(const std::string& rf_port_name) {
    return true;
  }
  RFPort::direction_t get_direction(const std::string& rf_port_name) {
    return m_settings[rf_port_name].m_direction;
  }
  double get_tuning_freq_MHz(const std::string& rf_port_name) {
    return m_settings[rf_port_name].m_tuning_freq_MHz;
  }
  double get_bandwidth_3dB_MHz(const std::string& rf_port_name) {
    return m_settings[rf_port_name].m_bandwidth_3dB_MHz;
  }
  double get_sampling_rate_Msps(const std::string& rf_port_name) {
    return m_settings[rf_port_name].m_sampling_rate_Msps;
  }
  bool get_samples_are_complex(const std::string& rf_port_name) {
    return m_settings[rf_port_name].m_samples_are_complex;
  }
  std::string get_gain_mode(const std::string& rf_port_name) {
    return m_settings[rf_port_name].m_gain_mode;
  }
  double get_gain_dB(const std::string& rf_port_name) {
    return m_settings[rf_port_name].m_gain_dB;
  }
  uint8_t get_app_port_num(const std::string& rf_port_name) {
    return m_app_port_nums[rf_port_name];
  }
  void set_direction(const std::string& rf_port_name, RFPort::direction_t val) {
    m_settings[rf_port_name].m_direction = val;
  }
  void set_tuning_freq_MHz(const std::string& rf_port_name, double val) {
    m_settings[rf_port_name].m_tuning_freq_MHz = val;
  }
  void set_bandwidth_3dB_MHz(const std::string& rf_port_name, double val) {
    m_settings[rf_port_name].m_bandwidth_3dB_MHz = val;
  }
  void set_sampling_rate_Msps(const std::string& rf_port_name, double val) {
    m_settings[rf_port_name].m_sampling_rate_Msps = val;
  }
  void set_samples_are_complex(const std::string& rf_port_name, bool val) {
    m_settings[rf_port_name].m_samples_are_complex = val;
  }
  void set_gain_mode(const std::string& rf_port_name, const std::string& val) {
    m_settings[rf_port_name].m_gain_mode = val;
  }
  void set_gain_dB(const std::string& rf_port_name, double val) {
    m_settings[rf_port_name].m_gain_dB = val;
  }
  void set_app_port_num(const std::string& rf_port_name, uint8_t val) {
    m_app_port_nums[rf_port_name] = val;
  }
  protected:
  std::map<std::string,RFPort>  m_settings;
  std::map<std::string,uint8_t> m_app_port_nums;
};

#endif // _TEST_DRC_HH
