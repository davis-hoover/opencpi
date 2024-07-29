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

using namespace OCPI::DRC;

class TestDRC : public DRC {
  public:
  TestDRC() {
    const std::string rf_port_names[2] = {"p1", "p2"};
    for (size_t idx = 0; idx < 2; idx++) {
      m_cache[rf_port_names[idx]].rx = rf_port_names[idx].compare("p1") == 0;
      m_cache[rf_port_names[idx]].tuning_freq_MHz = 1.5;
      m_cache[rf_port_names[idx]].bandwidth_3dB_MHz = 3.5;
      m_cache[rf_port_names[idx]].sampling_rate_Msps = 5.5;
      m_cache[rf_port_names[idx]].samples_are_complex = 1.;
      m_cache[rf_port_names[idx]].gain_mode.assign("manual");
      m_cache[rf_port_names[idx]].gain_dB = 0.;
      m_cache[rf_port_names[idx]].app_port_num = 0;
    }
  }
  protected:
  OperatingPlan get_operating_plan_for_rx(
      const ConfigurationChannel& /*chan*/, const std::string& rf_port_name,
      double val) {
    OperatingPlan ret;
    ret.val_to_set_to = val;
    if ((rf_port_name == "p1") && (val < 0.5)) {
      ret.error.assign("tx is not supported");
    }
    else if ((rf_port_name == "p2") && (val > 0.5)) {
      ret.error.assign("rx is not supported");
    }
    return ret;
  }
  OperatingPlan get_operating_plan_for_tuning_freq_MHz(
      const ConfigurationChannel& /*chan*/, const std::string& /*rf_port_name*/,
      double val, double tolerance) {
    return get_operating_plan_clamp(val, 1., 2., tolerance, 0);
  }
  OperatingPlan get_operating_plan_for_bandwidth_3dB_MHz(
      const ConfigurationChannel& /*chan*/, const std::string& /*rf_port_name*/,
      double val, double tolerance) {
    return get_operating_plan_clamp(val, 3., 4., tolerance, 1);
  }
  OperatingPlan get_operating_plan_for_sampling_rate_Msps(
      const ConfigurationChannel& /*chan*/, const std::string& /*rf_port_name*/,
      double val, double tolerance) {
    return get_operating_plan_clamp(val, 5., 6., tolerance, 2);
  }
  OperatingPlan get_operating_plan_for_samples_are_complex(
      const ConfigurationChannel& /*chan*/, const std::string& /*rf_port_name*/,
      double val) {
    return get_operating_plan_complex_samples_only(val);
  }
  OperatingPlan get_operating_plan_for_gain_mode(
      const ConfigurationChannel& /*chan*/, const std::string& rf_port_name,
      double val) {
    OperatingPlan ret;
    ret.val_to_set_to = val;
    if (rf_port_name == "p1" && (val > 1.5)) {
      ret.error.assign("only the standard gain modes of manual and auto are supported");
    }
    else if (rf_port_name == "p2" && (val < 0.5)) {
      ret.error.assign("only the auto gain mode is supported");
    }
    return ret;
  }
  OperatingPlan get_operating_plan_for_gain_dB(
      const ConfigurationChannel& /*chan*/, const std::string& /*rf_port_name*/,
      double val, double tolerance) {
    return get_operating_plan_clamp(val, -10., 10., tolerance, 3);
  }
  OperatingPlan get_operating_plan_clamp(
      double val, double min, double max, double tolerance, size_t type) {
    const auto& tol = tolerance;
    OperatingPlan ret = get_operating_plan_continuous_limits(val, min, max, tol);
    if (ret.error.empty()) {
      /// port p2: must match all settings of p1 (tests constraint propagation)
      for (auto it = m_status.begin(); it != m_status.end(); ++it) {
        if (it->second.state == state_t::operating) {
          const auto& chans = it->second.channels;
          for (auto it2 = chans.begin(); it2 != chans.end(); ++it2) {
            double d_val;
            if (type == 0) {
              d_val = it2->second.tuning_freq_MHz;
            }
            else if (type == 1) {
              d_val = it2->second.bandwidth_3dB_MHz;
            }
            else if (type == 2) {
              d_val = it2->second.sampling_rate_Msps;
            }
            else {
              d_val = it2->second.gain_dB;
            }
            ret = get_operating_plan_discrete_val(val, d_val, tol);
          }
        }
      }
    }
    return ret;
  }
  OperatingPlan get_operating_plan_for_app_port_num(
      const ConfigurationChannel& /*chan*/, const std::string& /*rf_port_name*/,
      double val) {
    OperatingPlan ret;
    ret.val_to_set_to = val;
    return ret;
  }
  bool get_rx(const std::string& rf_port_name) {
    return m_cache[rf_port_name].rx;
  }
  double get_tuning_freq_MHz(const std::string& rf_port_name) {
    return m_cache[rf_port_name].tuning_freq_MHz;
  }
  double get_bandwidth_3dB_MHz(const std::string& rf_port_name) {
    return m_cache[rf_port_name].bandwidth_3dB_MHz;
  }
  double get_sampling_rate_Msps(const std::string& rf_port_name) {
    return m_cache[rf_port_name].sampling_rate_Msps;
  }
  bool get_samples_are_complex(const std::string& rf_port_name) {
    return m_cache[rf_port_name].samples_are_complex;
  }
  std::string get_gain_mode(const std::string& rf_port_name) {
    return m_cache[rf_port_name].gain_mode;
  }
  double get_gain_dB(const std::string& rf_port_name) {
    return m_cache[rf_port_name].gain_dB;
  }
  uint8_t get_app_port_num(const std::string& rf_port_name) {
    return m_cache[rf_port_name].app_port_num;
  }
  void set_rx(const std::string& /*rf_port_name*/, bool /*val*/) {
  }
  void set_tuning_freq_MHz(const std::string& /*rf_port_name*/,
      double /*val*/) {
  }
  void set_bandwidth_3dB_MHz(const std::string& /*rf_port_name*/,
      double /*val*/) {
  }
  void set_sampling_rate_Msps(const std::string& /*rf_port_name*/,
      double /*val*/) {
  }
  void set_samples_are_complex(const std::string& /*rf_port_name*/,
      bool /*val*/) {
  }
  void set_gain_mode(const std::string& /*rf_port_name*/,
      const std::string& /*val*/) {
  }
  void set_gain_dB(const std::string& /*rf_port_name*/, double /*val*/) {
  }
  void set_app_port_num(const std::string& /*rf_port_name*/,
      uint8_t /*val*/) {
  }
}; // class TestDRC

#endif // _TEST_DRC_HH
