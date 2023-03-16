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

#include "RFDCDRC.hh"
extern "C" {
#include "xrfdc.h"
}

// -----------------------------------------------------------------------------
// STEP 1 - DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

void
RFDCCSP::define_x_d_rfdc() {
  m_solver.add_var<int32_t>("rfdc_dir_rx1");
  m_solver.add_var<int32_t>("rfdc_dir_rx2");
  m_solver.add_var<int32_t>("rfdc_dir_tx1");
  m_solver.add_var<int32_t>("rfdc_dir_tx2");
  m_solver.add_var<double>("rfdc_fc_meghz_rx1", dfp_tol);
  m_solver.add_var<double>("rfdc_fc_meghz_rx2", dfp_tol);
  m_solver.add_var<double>("rfdc_fc_meghz_tx1", dfp_tol);
  m_solver.add_var<double>("rfdc_fc_meghz_tx2", dfp_tol);
  m_solver.add_var<double>("rfdc_bw_meghz_rx1", dfp_tol);
  m_solver.add_var<double>("rfdc_bw_meghz_rx2", dfp_tol);
  m_solver.add_var<double>("rfdc_bw_meghz_tx1", dfp_tol);
  m_solver.add_var<double>("rfdc_bw_meghz_tx2", dfp_tol);
  m_solver.add_var<double>("rfdc_fs_megsps_rx1", dfp_tol);
  m_solver.add_var<double>("rfdc_fs_megsps_rx2", dfp_tol);
  m_solver.add_var<double>("rfdc_fs_megsps_tx1", dfp_tol);
  m_solver.add_var<double>("rfdc_fs_megsps_tx2", dfp_tol);
  m_solver.add_var<int32_t>("rfdc_samps_comp_rx1");
  m_solver.add_var<int32_t>("rfdc_samps_comp_rx2");
  m_solver.add_var<int32_t>("rfdc_samps_comp_tx1");
  m_solver.add_var<int32_t>("rfdc_samps_comp_tx2");
  m_solver.add_var<int32_t>("rfdc_gain_mode_rx1");
  m_solver.add_var<int32_t>("rfdc_gain_mode_rx2");
  m_solver.add_var<int32_t>("rfdc_gain_mode_tx1");
  m_solver.add_var<int32_t>("rfdc_gain_mode_tx2");
  m_solver.add_var<double>("rfdc_gain_db_rx1", dfp_tol);
  m_solver.add_var<double>("rfdc_gain_db_rx2", dfp_tol);
  m_solver.add_var<double>("rfdc_gain_db_tx1", dfp_tol);
  m_solver.add_var<double>("rfdc_gain_db_tx2", dfp_tol);
}

void
RFDCCSP::define_c_rfdc() {
  m_solver.add_constr("rfdc_dir_rx1", "=", (int32_t)RFPort::direction_t::rx);
  m_solver.add_constr("rfdc_dir_rx2", "=", (int32_t)RFPort::direction_t::rx);
  m_solver.add_constr("rfdc_dir_tx1", "=", (int32_t)RFPort::direction_t::tx);
  m_solver.add_constr("rfdc_dir_tx2", "=", (int32_t)RFPort::direction_t::tx);
  m_solver.add_constr("rfdc_fc_meghz_rx1", "=", 0.);
  m_solver.add_constr("rfdc_fc_meghz_rx2", "=", 0.);
  m_solver.add_constr("rfdc_fc_meghz_tx1", "=", 0.);
  m_solver.add_constr("rfdc_fc_meghz_tx2", "=", 0.);
  m_solver.add_constr("rfdc_bw_meghz_rx1", "=", 100.);
  m_solver.add_constr("rfdc_bw_meghz_rx2", "=", 100.);
  m_solver.add_constr("rfdc_bw_meghz_tx1", "=", 100.);
  m_solver.add_constr("rfdc_bw_meghz_tx2", "=", 100.);
  m_solver.add_constr("rfdc_fs_megsps_rx1", "=", 100.);
  m_solver.add_constr("rfdc_fs_megsps_rx2", "=", 100.);
  m_solver.add_constr("rfdc_fs_megsps_tx1", "=", 100.);
  m_solver.add_constr("rfdc_fs_megsps_tx2", "=", 100.);
  m_solver.add_constr("rfdc_samps_comp_rx1", "=", (int32_t)1);
  m_solver.add_constr("rfdc_samps_comp_rx2", "=", (int32_t)1);
  m_solver.add_constr("rfdc_samps_comp_tx1", "=", (int32_t)1);
  m_solver.add_constr("rfdc_samps_comp_tx2", "=", (int32_t)1);
  m_solver.add_constr("rfdc_gain_mode_rx1", "=", (int32_t)1); // manual
  m_solver.add_constr("rfdc_gain_mode_rx2", "=", (int32_t)1); // manual
  m_solver.add_constr("rfdc_gain_mode_tx1", "=", (int32_t)1); // manual
  m_solver.add_constr("rfdc_gain_mode_tx2", "=", (int32_t)1); // manual
  m_solver.add_constr("rfdc_gain_db_rx1", "=", 0.);
  m_solver.add_constr("rfdc_gain_db_rx2", "=", 0.);
  m_solver.add_constr("rfdc_gain_db_tx1", "=", 0);
  m_solver.add_constr("rfdc_gain_db_tx2", "=", 0.);
}

RFDCCSP::RFDCCSP() : CSPBase() {
  define();
}

// -----------------------------------------------------------------------------
// STEP 2 - DEFINE CONFIGURATOR THAT UTILIZES THE CSP
// -----------------------------------------------------------------------------

RFDCConfigurator::RFDCConfigurator() : Configurator<RFDCCSP>() {
  init_rf_port_rx1();
  init_rf_port_rx2();
  init_rf_port_tx1();
  init_rf_port_tx2();
}

void
RFDCConfigurator::init_rf_port_rx1() {
  // maps each of the DRC-specific RFPort::config_t types to their corresponding CSP
  // variables names which are specific to this DRC (a CSP is generic and knows
  // nothing about a DRC, this is what ties the two together)
  CSPVarMap map;
  map.insert(std::make_pair(RFPort::config_t::direction,
      "rfdc_dir_rx1"));
  map.insert(std::make_pair(RFPort::config_t::tuning_freq_MHz,
      "rfdc_fc_meghz_rx1"));
  map.insert(std::make_pair(RFPort::config_t::bandwidth_3dB_MHz,
      "rfdc_bw_meghz_rx1"));
  map.insert(std::make_pair(RFPort::config_t::sampling_rate_Msps,
      "rfdc_fs_megsps_rx1"));
  map.insert(std::make_pair(RFPort::config_t::samples_are_complex,
      "rfdc_samps_comp_rx1"));
  map.insert(std::make_pair(RFPort::config_t::gain_mode,
      "rfdc_gain_mode_rx1"));
  map.insert(std::make_pair(RFPort::config_t::gain_dB,
      "rfdc_gain_db_rx1"));
  // make a dictionary entry which ties the mapping to a particular rf_port_name
  m_dict["rx1"] = map;
}

void
RFDCConfigurator::init_rf_port_rx2() {
  // maps each of the DRC-specific RFPort::config_t types to their corresponding CSP
  // variables names which are specific to this DRC (a CSP is generic and knows
  // nothing about a DRC, this is what ties the two together)
  CSPVarMap map;
  map.insert(std::make_pair(RFPort::config_t::direction,
      "rfdc_dir_rx2"));
  map.insert(std::make_pair(RFPort::config_t::tuning_freq_MHz,
      "rfdc_fc_meghz_rx2"));
  map.insert(std::make_pair(RFPort::config_t::bandwidth_3dB_MHz,
      "rfdc_bw_meghz_rx2"));
  map.insert(std::make_pair(RFPort::config_t::sampling_rate_Msps,
      "rfdc_fs_megsps_rx2"));
  map.insert(std::make_pair(RFPort::config_t::samples_are_complex,
      "rfdc_samps_comp_rx2"));
  map.insert(std::make_pair(RFPort::config_t::gain_mode,
      "rfdc_gain_mode_rx2"));
  map.insert(std::make_pair(RFPort::config_t::gain_dB,
      "rfdc_gain_db_rx2"));
  // make a dictionary entry which ties the mapping to a particular rf_port_name
  m_dict["rx2"] = map;
}

void
RFDCConfigurator::init_rf_port_tx1() {
  // maps each of the DRC-specific RFPort::config_t types to their corresponding CSP
  // variables names which are specific to this DRC (a CSP is generic and knows
  // nothing about a DRC, this is what ties the two together)
  CSPVarMap map;
  map.insert(std::make_pair(RFPort::config_t::direction,
      "rfdc_dir_tx1"));
  map.insert(std::make_pair(RFPort::config_t::tuning_freq_MHz,
      "rfdc_fc_meghz_tx1"));
  map.insert(std::make_pair(RFPort::config_t::bandwidth_3dB_MHz,
      "rfdc_bw_meghz_tx1"));
  map.insert(std::make_pair(RFPort::config_t::sampling_rate_Msps,
      "rfdc_fs_megsps_tx1"));
  map.insert(std::make_pair(RFPort::config_t::samples_are_complex,
      "rfdc_samps_comp_tx1"));
  map.insert(std::make_pair(RFPort::config_t::gain_mode,
      "rfdc_gain_mode_tx1"));
  map.insert(std::make_pair(RFPort::config_t::gain_dB,
      "rfdc_gain_db_tx1"));
  // make a dictionary entry which ties the mapping to a particular rf_port_name
  m_dict["tx1"] = map;
}

void
RFDCConfigurator::init_rf_port_tx2() {
  // maps each of the DRC-specific RFPort::config_t types to their corresponding CSP
  // variables names which are specific to this DRC (a CSP is generic and knows
  // nothing about a DRC, this is what ties the two together)
  CSPVarMap map;
  map.insert(std::make_pair(RFPort::config_t::direction,
      "rfdc_dir_tx2"));
  map.insert(std::make_pair(RFPort::config_t::tuning_freq_MHz,
      "rfdc_fc_meghz_tx2"));
  map.insert(std::make_pair(RFPort::config_t::bandwidth_3dB_MHz,
      "rfdc_bw_meghz_tx2"));
  map.insert(std::make_pair(RFPort::config_t::sampling_rate_Msps,
      "rfdc_fs_megsps_tx2"));
  map.insert(std::make_pair(RFPort::config_t::samples_are_complex,
      "rfdc_samps_comp_tx2"));
  map.insert(std::make_pair(RFPort::config_t::gain_mode,
      "rfdc_gain_mode_tx2"));
  map.insert(std::make_pair(RFPort::config_t::gain_dB,
      "rfdc_gain_db_tx2"));
  // make a dictionary entry which ties the mapping to a particular rf_port_name
  m_dict["tx2"] = map;
}

// -----------------------------------------------------------------------------
// STEP 3 - DEFINE DRC (get/set APIs)
// -----------------------------------------------------------------------------

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::RFDCDRC() {
  init();
}

template<class cfgrtr_t> bool
RFDCDRC<cfgrtr_t>::get_enabled(const std::string& rf_port_name) {
}

template<class cfgrtr_t>
RFPort::direction_t 
RFDCDRC<cfgrtr_t>::get_direction(const std::string& rf_port_name) {
  bool do_rx = get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  return do_rx ? RFPort::direction_t::rx : RFPort::direction_t::tx;
}

template<class cfgrtr_t> double 
RFDCDRC<cfgrtr_t>::get_tuning_freq_MHz(const std::string& rf_port_name) {
  return 0.;
}

template<class cfgrtr_t> double 
RFDCDRC<cfgrtr_t>::get_bandwidth_3dB_MHz(const std::string& rf_port_name) {
  return 100.;
}

template<class cfgrtr_t> double 
RFDCDRC<cfgrtr_t>::get_sampling_rate_Msps(const std::string& rf_port_name) {
  return 100.;
}

template<class cfgrtr_t> bool
RFDCDRC<cfgrtr_t>::get_samples_are_complex(const std::string& rf_port_name) {
  return true;
}

template<class cfgrtr_t> std::string
RFDCDRC<cfgrtr_t>::get_gain_mode(const std::string& rf_port_name) {
  ///@TODO implement correctly
  return "manual";
}

template<class cfgrtr_t> double 
RFDCDRC<cfgrtr_t>::get_gain_dB(const std::string& rf_port) {
  ///@TODO implement correctly
  return 0;
}

template<class cfgrtr_t> uint8_t
RFDCDRC<cfgrtr_t>::get_app_port_num(const std::string& rf_port_name) {
  ///@TODO investigate whether this is correct
  return 0;
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_direction(const std::string& /*rf_port_name*/,
    RFPort::direction_t /*val*/) {
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_tuning_freq_MHz(const std::string& /*rf_port_name*/, double /*val*/) {
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_bandwidth_3dB_MHz(const std::string& /*rf_port_name*/,
    double /*val*/) {
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_sampling_rate_Msps(const std::string& /*rf_port_name*/,
    double /*val*/) {
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_samples_are_complex(const std::string& /*rf_port_name*/,
    bool /*val*/) {
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_gain_mode(const std::string& /*rf_port_name*/, const std::string& /*val*/) {
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_gain_dB(const std::string& /*rf_port_name*/, double /*val*/) {
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_app_port_num(const std::string& /*rf_port_name*/, uint8_t /*val*/) {
}

template<class cfgrtr_t>
RFDCDRC<cfgrtr_t>::init() {
  ///@TODO implement correctly
  u16 device_id = 0;
  XRFdc_Config* p_config = XRFdc_LookupConfig(device_id);
  u32 XRFdc_CfgInitialize(&m_xrfdc, XRFdc_Config *ConfigPtr);
}
