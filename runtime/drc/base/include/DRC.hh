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

#ifndef _DRC_HH
#define _DRC_HH

// https://opencpi.gitlab.io/releases/develop/docs/briefings/Briefing_14_Digital_Radio_Controller.pdf

#include <map>
#include <string>
#include <vector>

namespace OCPI {

namespace DRC {

struct RFPort {
  /// @brief false indicates tx
  bool rx;
  double tuning_freq_MHz;
  double bandwidth_3dB_MHz;
  double sampling_rate_Msps;
  bool samples_are_complex;
  /// @brief "manual" or "agc" (or perhaps something hardware specific)
  std::string gain_mode;
  /// @brief ignore if m_gain_mode is not "manual"
  double gain_dB;
}; // struct RFPort

struct Channel : RFPort {
  enum class config_t {
    rx,
    tuning_freq_MHz,
    bandwidth_3dB_MHz,
    sampling_rate_Msps,
    samples_are_complex,
    gain_mode,
    gain_dB,
    rf_port_name,
    rf_port_num,
    app_port_num
  };
  /* @brief when used in m_configurations, defines requested port if
   *        requesting by name (can be empty to request by direction only), and
   *        when used in m_status, non-empty
   *        indicates achievable configuration */
  std::string rf_port_name;
  uint8_t rf_port_num;
  uint8_t app_port_num;
}; // struct Channel

struct ConfigurationChannel : Channel {
  std::string description;
  double tolerance_tuning_freq_MHz;
  double tolerance_bandwidth_3dB_MHz;
  double tolerance_sampling_rate_Msps;
  double tolerance_gain_dB;
}; // struct ConfigurationChannel

struct Configuration {
  std::string description;
  bool recoverable;
  std::map<uint16_t, ConfigurationChannel> channels;
}; // struct Configuration

typedef std::map<uint16_t, Configuration> Configurations;

enum class state_t {inactive, prepared, operating, error};

struct StatusConfiguration {
  state_t state;
  std::string error;
  std::map<uint16_t, Channel> channels;
}; // struct StatusConfiguration

typedef std::map<uint16_t, StatusConfiguration> Status;

struct OperatingPlan {
  /* @brief conveys whether the specific radio can move to the state with the
   *        specified value (empty string if so), and if non-empty, indicates a
   *        description why the state transition cannot be achieved */
  std::string error;
  /// @brief val to set when moving to operate (can be adjusted by tolerance)
  double val_to_set_to;
}; // struct OperatingPlan

/*! @brief Provides an API for controlling analog and digital configs of
 *         a radio. When preparing to move to an operating state,
 *         get_operating_plan are called to consider allowable ranges and
 *         tolerances before hardware actuation is performed. */
class DRC {
  public:
  DRC();
  const Status& get_status() const;
  virtual void set_configuration(const uint16_t idx,
      const Configuration& config, bool force_set = false);
  virtual void set_configuration_length(size_t val);
  // child classes may override transition functions w/ hardware-specific
  // behavior
  virtual void set_prepare(uint16_t val);
  virtual void set_start(uint16_t val);
  virtual void set_stop(uint16_t val);
  virtual void set_release(uint16_t val);
  /// @brief IMPORTANT get/set not allowed until initialize() called
  void initialize(const std::vector<std::string>& rf_ports_rx,
      const std::vector<std::string>& rf_ports_tx);
  protected:
  /// @brief implies initialize() was called and cache was initialized
  bool m_initialized;
  Configurations m_configurations;
  Configurations m_deferred_configurations;
  std::string m_description;
  Status m_status;
  /// @brief caches RF port settings by rf_port_name
  std::map<std::string, Channel> m_cache;
  // get, by port name, a value as it exists on hardware.
  virtual bool get_rx(const std::string&
      rf_port_name) = 0;
  virtual double get_tuning_freq_MHz(const std::string&
      rf_port_name) = 0;
  virtual double get_bandwidth_3dB_MHz(const std::string&
      rf_port_name) = 0;
  virtual double get_sampling_rate_Msps(const std::string&
      rf_port_name) = 0;
  virtual bool get_samples_are_complex(const std::string&
      rf_port_name) = 0;
  virtual std::string get_gain_mode(const std::string&
      rf_port_name) = 0;
  virtual double get_gain_dB(const std::string&
      rf_port_name) = 0;
  virtual uint8_t get_app_port_num(const std::string& rf_port_name) = 0;
  /// @brief get hardware-specific operational plan, called 1st
  virtual OperatingPlan get_operating_plan_for_rx(
      const ConfigurationChannel& chan, const std::string& rf_port_name,
      double val) = 0;
  /// @brief called after get_operating_plan_for_rx
  virtual OperatingPlan get_operating_plan_for_tuning_freq_MHz(
      const ConfigurationChannel& chan, const std::string& rf_port_name,
      double val, double tolerance) = 0;
  /// @brief called after get_operating_plan_for_tuning_freq_MHz
  virtual OperatingPlan get_operating_plan_for_bandwidth_3dB_MHz(
      const ConfigurationChannel& chan, const std::string& rf_port_name,
      double val, double tolerance) = 0;
  /// @brief called after get_operating_plan_for_bandwidth_3dB_MHz
  virtual OperatingPlan get_operating_plan_for_sampling_rate_Msps(
      const ConfigurationChannel& chan, const std::string& rf_port_name,
      double val, double tolerance) = 0;
  /// @brief called after get_operating_plan_for_sampling_rate_Msps
  virtual OperatingPlan get_operating_plan_for_samples_are_complex(
      const ConfigurationChannel& chan, const std::string& rf_port_name,
      double val) = 0;
  /// @brief called after get_operating_plan_for_samples_are_complex
  virtual OperatingPlan get_operating_plan_for_gain_mode(
      const ConfigurationChannel& chan, const std::string& rf_port_name,
      double val) = 0;
  /// @brief called after get_operating_plan_for_gain_mode
  virtual OperatingPlan get_operating_plan_for_gain_dB(
      const ConfigurationChannel& chan, const std::string& rf_port_name,
      double val, double tolerance) = 0;
  /// @brief called after get_operating_plan_for_gain_dB
  virtual OperatingPlan get_operating_plan_for_app_port_num(
      const ConfigurationChannel& chan, const std::string& rf_port_name,
      double val) = 0;
  // set, by port name, on-hardware value
  virtual void set_rx(const std::string& rf_port_name, bool val) = 0;
  virtual void set_tuning_freq_MHz(const std::string& rf_port_name,
      double val) = 0;
  virtual void set_bandwidth_3dB_MHz(const std::string& rf_port_name,
      double val) = 0;
  virtual void set_sampling_rate_Msps(const std::string& rf_port_name,
      double val) = 0;
  virtual void set_samples_are_complex(const std::string& rf_port_name,
      bool val) = 0;
  virtual void set_gain_mode(const std::string& rf_port_name,
      const std::string& val) = 0;
  /*! @brief  Exception is thrown if the gain mode for the requested RF port
   *          is currently "agc" (auto). */
  virtual void set_gain_dB(const std::string& rf_port_name, double val) = 0;
  virtual void set_app_port_num(const std::string& rf_port_name,
      uint8_t val) = 0;
  void check_and_handle_deferred_configuration(uint16_t val);
  virtual void start_rf_port(uint16_t config_idx,
      const std::string& rf_port, Channel::config_t cfg,
      double val, double tol);
  virtual std::string prepare_channel(uint16_t config_idx, uint16_t chan_idx,
      const std::string& rf_port_name, ConfigurationChannel& chan);
  virtual void start_channel(uint16_t config_idx,
      const std::string& rf_port_name, const Channel& chan,
      const ConfigurationChannel& chan_for_tol);
  void throw_invalid_rf_port_name(const std::string& rf_port_name) const;
  OperatingPlan get_operating_plan_continuous_limits(double val,
      double low_limit, double hi_limit, double tolerance);
  OperatingPlan get_operating_plan_discrete_val(double val,
    double achievable_val, double tolerance);
  OperatingPlan get_operating_plan_discrete_limits(double val,
      double low_limit, double hi_limit, double tolerance);
  OperatingPlan get_operating_plan_complex_samples_only(double val);
  OperatingPlan get_operating_plan_manual_gain_mode_only(double val);
  void throw_if_configuration_undefined(uint16_t val);
  void throw_if_not_initialized() const;
}; // class DRC

} // namespace DRC

} // namespace OCPI

#endif // _DRC_HH
