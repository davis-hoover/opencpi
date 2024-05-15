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

/// @author Davis Hoover (git@davishoover.com)

#include "DRC.hh"
#include <cmath> // std::abs
#include <sstream>
#include <iomanip> // setprecision
#include "OcpiDebugApi.hh" // OS::Log::print

namespace OCPI {

namespace DRC {

std::string
to_string(const Channel::config_t& rhs) {
  std::string ret;
  if (rhs == Channel::config_t::rx) {
    ret.assign("rx");
  }
  if (rhs == Channel::config_t::tuning_freq_MHz) {
    ret.assign("tuning_freq_MHz");
  }
  if (rhs == Channel::config_t::bandwidth_3dB_MHz) {
    ret.assign("bandwidth_3dB_MHz");
  }
  if (rhs == Channel::config_t::sampling_rate_Msps) {
    ret.assign("sampling_rate_Msps");
  }
  if (rhs == Channel::config_t::samples_are_complex) {
    ret.assign("samples_are_complex");
  }
  if (rhs == Channel::config_t::gain_mode) {
    ret.assign("gain_mode");
  }
  if (rhs == Channel::config_t::gain_dB) {
    ret.assign("gain_dB");
  }
  if (rhs == Channel::config_t::app_port_num) {
    ret.assign("app_port_num");
  }
  return ret;
}

std::ostream&
operator<<(std::ostream& os, const Channel::config_t& rhs) {
  os << to_string(rhs);
  return os;
}

DRC::DRC() : m_initialized(false) {
}

const Status&
DRC::get_status() const {
  throw_if_not_initialized();
  return m_status;
}

void
DRC::set_configuration(const uint16_t idx, const Configuration& config,
    bool force_set) {
  throw_if_not_initialized();
  const bool in_prep = m_status[idx].state == state_t::prepared;
  const bool in_oper = m_status[idx].state == state_t::operating;
  if ((in_prep || in_oper) && (!force_set)) {
    const char* m1 = "drc: deferring setting of configuration ";
    OS::Log::print(OCPI_LOG_INFO, "%s%i", m1, idx);
    m_deferred_configurations.emplace(idx, config);
  }
  else {
    OS::Log::print(OCPI_LOG_INFO, "drc: setting configuration %i", idx);
    if (m_configurations.find(idx) != m_configurations.end()) {
      m_configurations[idx] = config;
    }
    else {
      m_configurations.emplace(idx, config);
    }
    StatusConfiguration config2;
    config2.state = state_t::inactive;
    if (m_configurations.find(idx) != m_configurations.end()) {
      auto it = config.channels.begin();
      for (; it != config.channels.end(); ++it) {
        config2.channels.emplace(it->first, (Channel)it->second);
      }
    }
    if (m_status.find(idx) == m_status.end()) {
      m_status.emplace(idx, config2);
    }
    else {
      m_status.at(idx) = config2;
    }
  }
}

void
DRC::set_configuration_length(size_t val) {
  throw_if_not_initialized();
  for (size_t idx = m_configurations.size(); idx > val; idx--) {
    m_configurations.erase(idx);
  }
}

void
DRC::set_prepare(uint16_t val) {
  throw_if_not_initialized();
  throw_if_configuration_undefined(val);
  if (m_status[val].state != state_t::inactive) {
    if (m_status[val].state != state_t::error) {
      throw std::runtime_error("invalid state transition");
    }
  }
  check_and_handle_deferred_configuration(val);
  OS::Log::print(OCPI_LOG_INFO, "drc: preparing configuration %i", val);
  auto& config = m_configurations[val];
  std::string error;
  for (auto it = config.channels.begin(); it != config.channels.end(); ++it) {
    error.clear();
    for (auto itp = m_cache.begin(); itp != m_cache.end(); ++itp) {
      if (!it->second.rf_port_name.empty()) { // requesting by name
        if (itp->first.compare(it->second.rf_port_name)) {
          continue;
        }
      }
      error.assign(prepare_channel(val, it->first, itp->first, it->second));
      if (error.empty()) {
        break;
      }
    }
    auto name = it->second.rf_port_name.c_str();
    std::string msg = error.empty() ? "succeeded" : "failed";
    const char* m1 = "drc: preparing configuration ";
    const auto m2 = val;
    const char* m3 = " rf_port_name ";
    const auto DB = OCPI_LOG_DEBUG;
    OS::Log::print(DB, "%s%i%s%s %s", m1, m2, m3, name, msg.c_str());
    if (!error.empty()) {
      error = "no rf ports satisfy configuration (last fail: " + error + ")";
      if (m_configurations[val].recoverable) {
        m_status[val].error.assign(error);
        m_status[val].state = state_t::error;
        break;
      }
      else {
        throw std::runtime_error(error);
      }
    }
  }
  std::string msg = error.empty() ? "succeeded" : "failed";
  const char* m1 = "drc: preparing configuration ";
  OS::Log::print(OCPI_LOG_INFO, "%s%i %s", m1, val, msg.c_str());
  if (error.empty()) {
    m_status[val].state = state_t::prepared;
  }
}

void
DRC::set_start(uint16_t val) {
  throw_if_not_initialized();
  throw_if_configuration_undefined(val);
  check_and_handle_deferred_configuration(val);
  if (m_status[val].state != state_t::prepared) {
    set_prepare(val);
  }
  const char* m1 = "drc: starting configuration ";
  if (m_status[val].error.empty()) {
    OS::Log::print(OCPI_LOG_INFO, "%s%i", m1, val);
    auto& config = m_status.at(val);
    auto it = config.channels.begin();
    for (; it != config.channels.end(); ++it) {
      auto& channel = m_configurations[val].channels[it->first];
      start_channel(val, it->second.rf_port_name, it->second, channel);
    }
    m_status[val].state = state_t::operating;
    OS::Log::print(OCPI_LOG_INFO, "%s%i succeeded", m1, val);
  }
}

void
DRC::set_stop(uint16_t val) {
  throw_if_not_initialized();
  throw_if_configuration_undefined(val);
  if (m_status[val].state != state_t::operating) {
    throw std::runtime_error("invalid state transition");
  }
  OS::Log::print(OCPI_LOG_INFO, "drc: stopping configuration %i", val);
  m_status[val].state = state_t::prepared;
}

void
DRC::set_release(uint16_t val) {
  throw_if_not_initialized();
  throw_if_configuration_undefined(val);
  OS::Log::print(OCPI_LOG_INFO, "drc: releasing configuration %i", val);
  m_status[val].state = state_t::inactive;
}

void
DRC::initialize(const std::vector<std::string>& rf_ports_rx,
    const std::vector<std::string>& rf_ports_tx) {
  const auto& de = m_description;
  const auto LI = OCPI_LOG_INFO;
  for (auto it = rf_ports_rx.begin(); it != rf_ports_rx.end(); ++it) {
    m_cache.emplace(*it, Channel());
    const char* m1 = "drc: setting rf ";
    const char* m4 = " to allow rx";
    OS::Log::print(LI, "%s%s port named %s%s", m1, de.c_str(), it->c_str(), m4);
  }
  for (auto it = rf_ports_tx.begin(); it != rf_ports_tx.end(); ++it) {
    m_cache.emplace(*it, Channel());
    const char* m1 = "drc: setting rf ";
    const char* m4 = " to allow tx";
    OS::Log::print(LI, "%s%s port named %s%s", m1, de.c_str(), it->c_str(), m4);
  }
  OS::Log::print(OCPI_LOG_INFO, "drc: initializing rf port cache");
  // initialize the correct number (and names) of cached RF ports
  for (auto it = m_cache.begin(); it != m_cache.end(); ++it) {
    it->second.rx = get_rx(it->first);
    it->second.tuning_freq_MHz = get_tuning_freq_MHz(it->first);
    it->second.bandwidth_3dB_MHz = get_bandwidth_3dB_MHz(it->first);
    it->second.sampling_rate_Msps = get_sampling_rate_Msps(it->first);
    it->second.samples_are_complex = get_samples_are_complex(it->first);
    it->second.gain_mode = get_gain_mode(it->first);
    it->second.gain_dB = get_gain_dB(it->first);
    const char* port = it->first.c_str();
    const char* xx = (it->second.rx ? "1" : "0");
    const char* m1 = "drc: cache[";
    OS::Log::print(LI, "%s%s][rx]                  = %s", m1, port, xx);
    double val = it->second.tuning_freq_MHz;
    OS::Log::print(LI, "%s%s][tuning_freq_MHz]     = %f", m1, port, val);
    val = it->second.bandwidth_3dB_MHz;
    OS::Log::print(LI, "%s%s][bandwidth_3dB_MHz]   = %f", m1, port, val);
    val = it->second.sampling_rate_Msps;
    OS::Log::print(LI, "%s%s][sampling_rate_Msps]  = %f", m1, port, val);
    std::string sval = (it->second.samples_are_complex ? "true" : "false");
    OS::Log::print(LI, "%s%s][samples_are_complex] = %s", m1, port, sval.c_str());
    std::string& gm = it->second.gain_mode;
    OS::Log::print(LI, "%s%s][gain_mode]           = %s", m1, port, gm.c_str());
    val = it->second.gain_dB;
    OS::Log::print(LI, "%s%s][gain_dB]             = %f", m1, port, val);
    //const char* yy = (it->second.app_port_num ? "1" : "0");
    //OS::Log::print(LI, "drc: cache[%s][app_port_num]        = %s", port, yy);
  }
  m_initialized = true;
}

void
DRC::check_and_handle_deferred_configuration(uint16_t val) {
  if (m_deferred_configurations.find(val) != m_deferred_configurations.end()) {
    set_configuration(val, m_deferred_configurations[val], true);
    m_deferred_configurations.erase(val);
  }
}

void
DRC::start_rf_port(uint16_t config_idx, const std::string& rf_port,
    Channel::config_t cfg, double val, double tol) {
  const char* m1 = "drc: starting configuration ";
  const auto& m2 = config_idx;
  const char* m3 = m_description.c_str();
  const char* m4 = " rf_port_name ";
  const char* m5 = rf_port.c_str();
  auto cfgs = to_string(cfg);
  const char* m6 = cfgs.c_str();
  const char* m7 = " with value ";
  const auto DB = OCPI_LOG_DEBUG;
  OS::Log::print(DB, "%s%i %s%s%s %s%s%f", m1, m2, m3, m4, m5, m6, m7, val);
  if (cfg == Channel::config_t::rx) {
    if (m_cache[rf_port].rx != (val > 0.5)) {
      set_rx(rf_port, val > 0.5);
      m_cache[rf_port].rx = (val > 0.5);
    }
  }
  else if (cfg == Channel::config_t::tuning_freq_MHz) {
    if (std::abs(m_cache[rf_port].tuning_freq_MHz-val) > tol) {
      set_tuning_freq_MHz(rf_port, val);
      m_cache[rf_port].tuning_freq_MHz = val;
    }
  }
  else if (cfg == Channel::config_t::bandwidth_3dB_MHz) {
    if (std::abs(m_cache[rf_port].bandwidth_3dB_MHz-val) > tol) {
      set_bandwidth_3dB_MHz(rf_port, val);
      m_cache[rf_port].bandwidth_3dB_MHz = val;
    }
  }
  else if (cfg == Channel::config_t::sampling_rate_Msps) {
    if (std::abs(m_cache[rf_port].sampling_rate_Msps-val) > tol) {
      set_sampling_rate_Msps(rf_port, val);
      m_cache[rf_port].sampling_rate_Msps = val;
    }
  }
  else if (cfg == Channel::config_t::samples_are_complex) {
    const bool tmp = val > 0.5;
    if (m_cache[rf_port].samples_are_complex != tmp) {
      set_samples_are_complex(rf_port, tmp);
      m_cache[rf_port].samples_are_complex = tmp;
    }
  }
  else if (cfg == Channel::config_t::gain_mode) {
    std::string mode= (val < 0.5 ? "auto" : "manual");
    if (m_cache[rf_port].gain_mode != mode) {
      set_gain_mode(rf_port, mode);
      m_cache[rf_port].gain_mode = mode;
    }
  }
  else if (cfg == Channel::config_t::gain_dB) {
    if (std::abs(m_cache[rf_port].gain_dB-val) > tol) {
      set_gain_dB(rf_port, val);
      m_cache[rf_port].gain_dB = val;
    }
  }
}

/*! @param[in]    rf_port_name port being considered for the requested
 *                chan (chan.rf_port_name is allowed to be empty)
 *  @param[inout] channel configuration channel that is adjusted according to
 *                the tolerance and achievable operating plans
 *  @return string indicating error (empty if none) */
std::string
DRC::prepare_channel(uint16_t config_idx, uint16_t chan_idx,
    const std::string& rf_port_name, ConfigurationChannel& chan) {
  const auto& name = rf_port_name;
  auto& status_chan = m_status[config_idx].channels[chan_idx];
  OperatingPlan plan;
  for (auto it = m_status.begin(); it != m_status.end(); ++it) {
    const bool prep = it->second.state == state_t::prepared;
    const bool oper = it->second.state == state_t::operating;
    if (prep or oper) {
      auto it2 = it->second.channels.begin();
      for (; it2 != it->second.channels.end(); ++it2) {
        if (!(it2->second.rf_port_name.compare(rf_port_name))) {
          if (prep) {
            plan.error.assign("rf port is already prepared");
          }
          else {
            plan.error.assign("rf port is already operating");
          }
        }
      }
    }
  }
  const char* m1 = "drc: preparing configuration ";
  const auto& m2 = config_idx;
  const char* m3 = m_description.c_str();
  const char* m4 = " rf_port_name ";
  auto m5 = rf_port_name.c_str();
  const auto DB = OCPI_LOG_DEBUG;
  if (plan.error.empty()) {
    const double val = chan.rx ? 1. : 0.;
    const char* m6 = " rx with value ";
    OS::Log::print(DB, "%s%i %s%s%s%s%f", m1, m2, m3, m4, m5, m6, val);
    plan = get_operating_plan_for_rx(chan, name, val);
    status_chan.rx = plan.val_to_set_to > 0.5;
  }
  if (plan.error.empty()) {
    const auto val = chan.tuning_freq_MHz;
    const auto tol = chan.tolerance_tuning_freq_MHz;
    const char* m6 = " tuning_freq_MHz with value ";
    OS::Log::print(DB, "%s%i %s%s%s%s%f", m1, m2, m3, m4, m5, m6, val);
    plan = get_operating_plan_for_tuning_freq_MHz(chan, name, val, tol);
    status_chan.tuning_freq_MHz = plan.val_to_set_to;
  }
  if (plan.error.empty()) {
    const auto val = chan.bandwidth_3dB_MHz;
    const auto tol = chan.tolerance_bandwidth_3dB_MHz;
    const char* m6 = " bandwidth_3dB_MHz with value ";
    OS::Log::print(DB, "%s%i %s%s%s%s%f", m1, m2, m3, m4, m5, m6, val);
    plan = get_operating_plan_for_bandwidth_3dB_MHz(chan, name, val, tol);
    status_chan.bandwidth_3dB_MHz = plan.val_to_set_to;
  }
  if (plan.error.empty()) {
    const auto val = chan.sampling_rate_Msps;
    const auto tol = chan.tolerance_sampling_rate_Msps;
    const char* m6 = " sampling_rate_Msps with value ";
    OS::Log::print(DB, "%s%i %s%s%s%s%f", m1, m2, m3, m4, m5, m6, val);
    plan = get_operating_plan_for_sampling_rate_Msps(chan, name, val, tol);
    status_chan.sampling_rate_Msps = plan.val_to_set_to;
  }
  if (plan.error.empty()) {
    const double val = chan.samples_are_complex ? 1. : 0.;
    const char* m6 = " samples_are_complex with value ";
    OS::Log::print(DB, "%s%i %s%s%s%s%f", m1, m2, m3, m4, m5, m6, val);
    plan = get_operating_plan_for_samples_are_complex(chan, name, val);
    status_chan.samples_are_complex = plan.val_to_set_to > 0.5;
  }
  if (plan.error.empty()) {
    if (chan.gain_mode.compare("auto") && chan.gain_mode.compare("manual")) {
      plan.error.assign("requested unsupported gain mode");
      if (!m_configurations[config_idx].recoverable) {
        throw std::runtime_error(plan.error);
      }
    }
    else {
      const double val = chan.gain_mode == "auto" ? 0. : 1.;
      const char* m6 = " gain_mode with value ";
      OS::Log::print(DB, "%s%i %s%s%s%s%f", m1, m2, m3, m4, m5, m6, val);
      plan = get_operating_plan_for_gain_mode(chan, name, val);
      status_chan.gain_mode = plan.val_to_set_to > 0.5 ? "manual" : "auto";
    }
  }
  if (plan.error.empty() && (chan.gain_mode == "manual")) {
    const auto val = chan.gain_dB;
    const auto tol = chan.tolerance_gain_dB;
    const char* m6 = " gain_dB with value ";
    OS::Log::print(DB, "%s%i %s%s%s%s%f", m1, m2, m3, m4, m5, m6, val);
    plan = get_operating_plan_for_gain_dB(chan, name, val, tol);
    status_chan.gain_dB = plan.val_to_set_to;
  }
  if (plan.error.empty()) {
    const auto val = chan.app_port_num;
    const char* m6 = " app_port_num with value ";
    OS::Log::print(DB, "%s%i %s%s%s%s%f", m1, m2, m3, m4, m5, m6, (double)val);
    plan = get_operating_plan_for_app_port_num(chan, name, val);
    status_chan.app_port_num = (uint8_t)plan.val_to_set_to;
  }
  if (plan.error.empty()) {
    chan.rf_port_name = rf_port_name; // very important (request by name vs dir)
  }
  else {
    auto err = plan.error.c_str();
    OS::Log::print(DB, "%s%i %s%s%s failed (%s)", m1, m2, m3, m4, m5, err);
  }
  return plan.error;
}

void
DRC::start_channel(uint16_t config_idx, const std::string& rf_port_name,
    const Channel& chan, const ConfigurationChannel& chan_for_tol) {
  const auto& idx = config_idx;
  const auto& name = rf_port_name;
  typedef Channel::config_t cfg_t;
  start_rf_port(idx, name, cfg_t::rx, chan.rx, 0.);
  double tol = chan_for_tol.tolerance_tuning_freq_MHz;
  start_rf_port(idx, name, cfg_t::tuning_freq_MHz, chan.tuning_freq_MHz, tol);
  tol = chan_for_tol.tolerance_bandwidth_3dB_MHz;
  const auto& bw = chan.bandwidth_3dB_MHz;
  start_rf_port(idx, name, cfg_t::bandwidth_3dB_MHz, bw, tol);
  tol = chan_for_tol.tolerance_sampling_rate_Msps;
  const auto& fs = chan.sampling_rate_Msps;
  start_rf_port(idx, name, cfg_t::sampling_rate_Msps, fs, tol);
  tol = chan_for_tol.tolerance_sampling_rate_Msps;
  const auto& sc = chan.samples_are_complex;
  start_rf_port(idx, name, cfg_t::samples_are_complex, sc, 0.);
  double gm = chan.gain_mode == "auto" ? 0. : 1.;
  start_rf_port(idx, name, cfg_t::gain_mode, gm, 0.);
  tol = chan_for_tol.tolerance_gain_dB;
  start_rf_port(idx, name, cfg_t::gain_dB, chan.gain_dB, tol);
  start_rf_port(idx, name, cfg_t::app_port_num, chan.app_port_num, 0.);
}

void
DRC::throw_invalid_rf_port_name(const std::string& rf_port_name) const {
  throw std::runtime_error(std::string("invalid rf_port_name: ")+rf_port_name);
}

/* @param[in] val       val to consider setting to, that could be adjusted
 *                      up to the tolerance amount
 * @param[in] low_limit absolute lower limit to be used for
 *                      val_to_set_to in the final plan (below this limit
 *                      results in an unachievable plan)
 * @param[in] hi_limit  absolute upper limit to be considered for
 *                      val_to_set_to in the final plan (above this limit
 *                      results in an unachievable plan)
 * @param[in] tolerance maximum value which is allowed to be subtracted
 *                      from or added to the considered plan's val_to_set_to
 *                      (outside this tolerance results in an unachievable
 *                      plan)
 * @return              final lock plan after limits are enforced */
OperatingPlan
DRC::get_operating_plan_continuous_limits(double val,
    double low_limit, double hi_limit, double tolerance) {
  std::ostringstream oss;
  OperatingPlan ret;
  ret.val_to_set_to = val;
  if ((val+tolerance) < low_limit) {
    oss << val << " below threshold of " << std::setprecision(10) << low_limit;
    ret.error.assign(oss.str());
  }
  else if ((val-tolerance) > hi_limit) {
    oss << val << " above threshold of " << std::setprecision(10) << hi_limit;
    ret.error.assign(oss.str());
  }
  else {
    double val = ret.val_to_set_to;
    ret.val_to_set_to = (val < low_limit) ? low_limit : val;
    val = ret.val_to_set_to;
    ret.val_to_set_to = (val > hi_limit) ? hi_limit : val;
  }
  return ret;
}

OperatingPlan
DRC::get_operating_plan_discrete_val(double val,
    double achievable_val, double tolerance) {
  const auto& tol = tolerance;
  OperatingPlan ret;
  ret.val_to_set_to = val;
  if ((achievable_val > (val-tol)) && (achievable_val < (val+tol))) {
    ret.val_to_set_to = achievable_val;
  }
  else {
    std::ostringstream oss;
    oss << std::setprecision(10) << val << " with tolerance " << tolerance;
    oss << " is not achievable but " << achievable_val << " is";
    ret.error.assign(oss.str());
  }
  return ret;
}

/* @param[in] val            val to consider setting to, that could be adjusted
 *                           up to the tolerance amount
 * @param[in] achievable_low lowest of 2 discrete possible values to be allowed
 *                           for val_to_set_to in the final plan (anything
 *                           other than the 2 results in an unachievable plan)
 * @param[in] achievable_hi  highest of 2 discrete possible values to be allowed
 *                           for val_to_set_to in the final plan (anything
 *                           other than the 2 results in an unachievable plan)
 * @param[in] tolerance      maximum value which is allowed to be subtracted
 *                           from or added to the considered plan's val_to_set_to
 *                           (outside this tolerance results in an unachievable
 *                           plan)
 * @return                   final operating plan after clamps are enforced */
OperatingPlan
DRC::get_operating_plan_discrete_limits(double val,
    double achievable_low, double achievable_hi, double tolerance) {
  const auto& tol = tolerance;
  OperatingPlan ret;
  ret.val_to_set_to = val;
  if ((achievable_low > (val-tolerance)) && (achievable_low < (val+tol))) {
    ret.val_to_set_to = achievable_low;
  }
  else if ((achievable_hi > (val-tolerance)) && (achievable_hi < (val+tol))) {
    ret.val_to_set_to = achievable_hi;
  }
  else {
    std::ostringstream oss;
    oss << val << " with tolerance " << tolerance << " is not achievable but ";
    oss << std::setprecision(10) << achievable_low << " and " << achievable_hi;
    oss << " are";
    ret.error.assign(oss.str());
  }
  return ret;
}

OperatingPlan
DRC::get_operating_plan_complex_samples_only(double val) {
  OperatingPlan ret;
  ret.val_to_set_to = val;
  if (val < 0.5) {
    ret.error.assign("real samples are not supported");
  }
  return ret;
}

OperatingPlan
DRC::get_operating_plan_manual_gain_mode_only(double val) {
  OperatingPlan ret;
  ret.val_to_set_to = val;
  if (val < 0.5) {
    ret.error.assign("only the manual gain mode is supported");
  }
  return ret;
}

void
DRC::throw_if_configuration_undefined(uint16_t val) {
  if (m_status.find(val) == m_status.end()) {
    throw std::runtime_error("undefined configuration");
  }
}

void
DRC::throw_if_not_initialized() const {
  if (!m_initialized) {
    const char* m1 = "drc get... or set... method called before initialize()";
    throw std::runtime_error(m1);
  }
}

} // namespace DRC

} // namespace OCPI
