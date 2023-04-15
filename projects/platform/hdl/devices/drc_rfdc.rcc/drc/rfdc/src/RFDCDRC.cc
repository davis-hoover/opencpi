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
#include <stdexcept>
#include "xrfdc.h"

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

void
RFDCCSP::instance_rfdc() {
  define();
}

void
RFDCCSP::define() {
  define_x_d_rfdc();
  define_c_rfdc();
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

// with Xilinx RFSoC, the RCC container is only connected to a single RF Data
// Converter instance, so this is a single pointer instead of a vector of
// pointers as may exist in other DRCs
static DeviceCallBack* g_p_device_callback;

uint8_t get_uchar_prop(unsigned long offset,
    unsigned long prop_off) {
  return g_p_device_callback->get_uchar_prop(offset, prop_off);
}

uint16_t get_ushort_prop(unsigned long offset,
    unsigned long prop_off) {
  return g_p_device_callback->get_ushort_prop(offset, prop_off);
}

uint32_t get_ulong_prop(unsigned long offset,
    unsigned long prop_off) {
  return g_p_device_callback->get_ulong_prop(offset, prop_off);
}

uint64_t get_ulonglong_prop(unsigned long offset,
    unsigned long prop_off) {
  return g_p_device_callback->get_ulonglong_prop(offset, prop_off);
}

void set_uchar_prop(unsigned long offset, unsigned long prop_off, uint8_t val) {
  g_p_device_callback->set_uchar_prop(offset, prop_off, val);
}

void set_ushort_prop(unsigned long offset, unsigned long prop_off, uint16_t val) {
  g_p_device_callback->set_ushort_prop(offset, prop_off, val);
}

void set_ulong_prop(unsigned long offset, unsigned long prop_off, uint32_t val) {
  g_p_device_callback->set_ulong_prop(offset, prop_off, val);
}

void set_ulonglong_prop(unsigned long offset, unsigned long prop_off, uint64_t val) {
  g_p_device_callback->set_ulonglong_prop(offset, prop_off, val);
}

template<class cfgrtr_t>
RFDCDRC<cfgrtr_t>::RFDCDRC(DeviceCallBack &dev) : m_callback(dev) {
  // must "connect" this callback (reg interface) before init()
  g_p_device_callback = &m_callback;
  init();
}

template<class cfgrtr_t> bool
RFDCDRC<cfgrtr_t>::get_enabled(const std::string& rf_port_name) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  return true;
}

template<class cfgrtr_t>
RFPort::direction_t 
RFDCDRC<cfgrtr_t>::get_direction(const std::string& rf_port_name) {
  bool do_rx = get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  return do_rx ? RFPort::direction_t::rx : RFPort::direction_t::tx;
}

template<class cfgrtr_t> double 
RFDCDRC<cfgrtr_t>::get_tuning_freq_MHz(const std::string& rf_port_name) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  return 0.;
}

template<class cfgrtr_t> double 
RFDCDRC<cfgrtr_t>::get_bandwidth_3dB_MHz(const std::string& rf_port_name) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  return 100.;
}

template<class cfgrtr_t> double 
RFDCDRC<cfgrtr_t>::get_sampling_rate_Msps(const std::string& rf_port_name) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  return 100.;
}

template<class cfgrtr_t> bool
RFDCDRC<cfgrtr_t>::get_samples_are_complex(const std::string& rf_port_name) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  return true;
}

template<class cfgrtr_t> std::string
RFDCDRC<cfgrtr_t>::get_gain_mode(const std::string& rf_port_name) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  ///@TODO implement correctly
  return "manual";
}

template<class cfgrtr_t> double 
RFDCDRC<cfgrtr_t>::get_gain_dB(const std::string& rf_port_name) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  ///@TODO implement correctly
  return 0;
}

template<class cfgrtr_t> uint8_t
RFDCDRC<cfgrtr_t>::get_app_port_num(const std::string& rf_port_name) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
  ///@TODO investigate whether this is correct
  return 0;
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_direction(const std::string& rf_port_name,
    RFPort::direction_t /*val*/) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_tuning_freq_MHz(const std::string& rf_port_name, double /*val*/) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_bandwidth_3dB_MHz(const std::string& rf_port_name,
    double /*val*/) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_sampling_rate_Msps(const std::string& rf_port_name,
    double /*val*/) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_samples_are_complex(const std::string& rf_port_name,
    bool /*val*/) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_gain_mode(const std::string& rf_port_name, const std::string& /*val*/) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_gain_dB(const std::string& rf_port_name, double /*val*/) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::set_app_port_num(const std::string& rf_port_name, uint8_t /*val*/) {
  get_rx_and_throw_if_invalid_rf_port_name(rf_port_name);
}

template<class cfgrtr_t> bool
RFDCDRC<cfgrtr_t>::get_rx_and_throw_if_invalid_rf_port_name(
    const std::string& rf_port_name) {
  bool do_rx = false;
  ///@TODO query configurator map entries instead of hardcoding port names
  if(rf_port_name == "rx1") {
    do_rx = true;
  }
  else if(rf_port_name == "rx2") {
    do_rx = true;
  }
  else if(rf_port_name == "tx1") {
    do_rx = false;
  }
  else if(rf_port_name == "tx2") {
    do_rx = false;
  }
  else {
    this->throw_invalid_rf_port_name(rf_port_name);
  }
  return do_rx;
}

template<class cfgrtr_t> rfdc_ip_version_t
RFDCDRC<cfgrtr_t>::get_fpga_rfdc_ip_version() {
  rfdc_ip_version_t ret;
  uint32_t reg_0 = get_ulong_prop(0, 0);
  ret.major = (reg_0 & 0xff000000) >> 24;
  ret.minor = (reg_0 & 0x00ff0000) >> 16;
  return ret;
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::throw_if_proof_of_life_reg_test_fails() {
  rfdc_ip_version_t version = get_fpga_rfdc_ip_version();
  // v2.5 is what's used in primitives/rfdc/vivado-gen-rfdc.tcl at time of
  // writing this
  bool match = (version.major == 2) && (version.minor == 5);
  std::ostringstream oss;
  oss << "proof of life version register (v" << version.major << ".";
  oss << version.minor << ") ";
  if (match) {
    oss << "indicated";
  }
  else {
    oss << "did not indicate";
  }
  oss << " the expected rfdc ip version v2.5";
  printf("%s", oss.str().c_str());
  if (!match) {
    throw std::runtime_error("proof of life version register test failed");
  }
}

template<class cfgrtr_t> void
RFDCDRC<cfgrtr_t>::init() {
  // ref https://github.com/Xilinx/embeddedsw/tree/xilinx_v2021.1/XilinxProcessorIPLib/drivers/rfdc
  // note we do NOT call XRFdc_LookupConfig() as is usually the case with this
  // library - this is because we are not looking up by sysfs/device, we simply
  // "register" the opencpi control plane interface as the libmetal io
  // interface and bypass sysfs altogether since opencpi hdl containers
  // won't have the device tree that corresponds to the sysfs entry
  struct metal_init_params metal_param = METAL_INIT_DEFAULTS;
  metal_param.log_level = METAL_LOG_DEBUG;
  if (metal_init(&metal_param)) {
    throw std::runtime_error("metal_init failed");
  }
  // checking proof of life here since the rfdc lib does not
  throw_if_proof_of_life_reg_test_fails();
  XRFdc_Config config;
  m_xrfdc.io = &metal_io_region_; // from modified libmetal linux layer
  if (XRFdc_CfgInitialize(&m_xrfdc, &config) != XRFDC_SUCCESS) {
    throw std::runtime_error("XRFdc_CfgInitialize failure");
  }
  u32 val;
  bool any_en = false;
  for (u32 type = 0; type <= 1; type ++) {
    for (u32 tl= 0; tl<= 3; tl++) {
      for (u32 bl= 0; bl<= 3; bl++) {
        XRFdc_BlockStatus status;
        val = XRFdc_GetBlockStatus(&m_xrfdc, type, tl, bl, &status);
        int en = (val == XRFDC_SUCCESS) ? 1 : 0;
        const char* is = en ? " " : " not ";
        const char* ad = type ? "dac" : "adc";
        printf("drc: rfdc %s tile %i block %i: en %i\n", ad, tl, bl, en);
        if (en) {
          any_en = true;
          /*double f1, f2;
          val = XRFdc_GetMinSampleRate(&m_xrfdc, type, tl, &f1);
          printf("drc: rfdc %s tile %i block %i: minfs %f\n", ad, tl, bl, f1);
          val = XRFdc_GetMaxSampleRate(&m_xrfdc, type, tl, &f2);
          printf("drc: rfdc %s tile %i block %i: maxfs %f\n", ad, tl, bl, f2);*/
          u32 fa;
          if (type) {
            val = XRFdc_GetDecimationFactor(&m_xrfdc, tl, bl, &fa);
            printf("drc: rfdc %s tile %i block %i: dec   %i\n", ad, tl, bl, fa);
          }
          else {
            val = XRFdc_GetInterpolationFactor(&m_xrfdc, tl, bl, &fa);
            printf("drc: rfdc %s tile %i block %i: int   %i\n", ad, tl, bl, fa);
          }
        }
      }
    }
  }
  if (!any_en) {
    printf("drc: rfdc NO TILES ENABLED!\n");
  }
}
