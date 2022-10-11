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

#ifndef _DRC_HH
#define _DRC_HH

#include "Math.hh"
#include "LogForwarder.hh"

namespace DRC {

using namespace Math;

/// @brief Each data stream has an associated type (either RX or TX).
enum class data_stream_direction_t {rx, tx};
/*! @brief We model many (all?) of the radio controller config values as
 *         doubles.
 ******************************************************************************/
typedef double config_value_t;
//enum class gain_mode_value_t {agc, manual};
typedef std::string gain_mode_value_t;
/// @brief Each data stream has an associated ID.
typedef std::string data_stream_id_t;
typedef std::string routing_id_t;
/*! @brief Each config lock has an associated ID by which it can be referred to
 *         (after a lock occurs you use this ID to keep track of that lock so
 *         that you can specifically delete that lock at a later time).
 ******************************************************************************/
typedef std::string config_lock_id_t;
typedef std::string config_key_t;
// "standard" radio controller data stream configs
const config_key_t config_key_direction          ("direction"          );
const config_key_t config_key_tuning_freq_MHz    ("tuning_freq_MHz"    );
const config_key_t config_key_bandwidth_3dB_MHz  ("bandwidth_3dB_MHz"  );
const config_key_t config_key_sampling_rate_Msps ("sampling_rate_Msps" );
const config_key_t config_key_samples_are_complex("samples_are_complex");
const config_key_t config_key_gain_mode          ("gain_mode"          );
const config_key_t config_key_gain_dB            ("gain_dB"            );

class CSPBase {
  protected:
  /// @TODO - pull in these 2 from DRC definition
  double dfp_tol = 1e-12;
  public:
  CSPSolver m_solver; /// @TODO make protected?
  const CSPSolver::FeasibleRegionLimits& get_feasible_region_limits() const;
  double get_feasible_region_limits_min_double(
        const char* var) const;
}; // CSPBase

// map generic CSP variable names (const char *s) each to a config_key_t (one
// of config_key_<name>
// for all streams

class DataStream {
  public:
  typedef std::map<config_key_t, const char*> CSPVarMap;
  protected:
  data_stream_id_t  m_data_stream_id;
  bool              m_supports_rx;
  bool              m_supports_tx;
  public:
  CSPVarMap         m_csp_map; /// @TODO make protected?
  data_stream_id_t get_data_stream_id() const;
  bool get_supports_rx() const;
  bool get_supports_tx() const;
  DataStream(data_stream_id_t id, bool supports_rx, bool supports_tx,
      CSPVarMap map);
}; // class DataStream

/*! @brief Software-only emulator of a hardware configuration environment which
 *         provides an API for locking/unlocking range-constrained configs.
 ******************************************************************************/
template<class CSP>
class Configurator {
  protected:
  struct LockParam {
    // intentionallity not reference, due to changing vector entry which this is referring to
    CSPSolver::Constr m_constr_lo;
    // intentionallity not reference, due to changing vector entry which this is referring to
    CSPSolver::Constr m_constr_hi;
    //int32_t m_lock_val_int32;
    //double  m_lock_val_double;
    //int32_t m_lock_val_is_int32;
    //double  m_lock_val_is_double;
    bool           m_constr_hi_used;
    int32_t        m_lock_val_int32;
    config_value_t m_lock_val_double;
    bool           m_lock_val_is_int32;
    bool           m_lock_val_is_double;
  };
  std::vector<DataStream>           m_data_streams;
  std::map<const char*, LockParam>  m_locked_params;
  /// @brief a config is mapped to a variable (X) within the CSP <X,D,C>
  CSP                               m_solver;
  public:
  const char*    get_config(data_stream_id_t id, config_key_t cfg) const;
  config_value_t get_config_locked_value(data_stream_id_t id,
      config_key_t cfg) const;
  void add_data_stream(DataStream data_stream);
  bool lock_config(data_stream_id_t ds_id, config_key_t cfg, int32_t val);
  bool lock_config(data_stream_id_t ds_id, config_key_t cfg, config_value_t val,
      config_value_t tol);
  bool lock_config(const char* config, int32_t val);
  bool lock_config(const char* config, config_value_t val,
      config_value_t tolerance);
  void unlock_config(data_stream_id_t ds_id, config_key_t config);
  void unlock_config(const char* config);
  void unlock_all();
  void find_data_streams_which_support_direction(data_stream_direction_t dir,
       std::vector<data_stream_id_t>& data_streams) const;
  config_value_t get_locked_value(const char* config);
  bool get_config_is_locked(const char* config);
  const CSPSolver::FeasibleRegionLimits& get_feasible_region_limits() const;
  double get_feasible_region_limits_min_double(const char* var) const;
}; // class Configurator

/*! @brief Intended to represent requested config locks for individual data
 *         streams, which may or may not succeed.
 *  @todo / FIXME - allow analog radio controllers to include gain/gain mode
 ******************************************************************************/
class DataStreamConfigLockRequest {
  protected:
  data_stream_id_t   m_data_stream_id;
  data_stream_direction_t m_data_stream_direction;
  routing_id_t       m_routing_id;
  config_value_t     m_tuning_freq_MHz;
  config_value_t     m_bandwidth_3dB_MHz;
  config_value_t     m_sampling_rate_Msps;
  bool               m_samples_are_complex;
  gain_mode_value_t  m_gain_mode;
  config_value_t     m_gain_dB;
  config_value_t     m_tolerance_tuning_freq_MHz;
  config_value_t     m_tolerance_bandwidth_3dB_MHz;
  config_value_t     m_tolerance_sampling_rate_Msps;
  config_value_t     m_tolerance_gain_dB;
  bool               m_including_data_stream_direction;
  bool               m_including_data_stream_id;
  bool               m_including_routing_id;
  bool               m_including_tuning_freq_MHz;
  bool               m_including_bandwidth_3dB_MHz;
  bool               m_including_sampling_rate_Msps;
  bool               m_including_samples_are_complex;
  bool               m_including_gain_mode;
  bool               m_including_gain_dB;
  public:
  DataStreamConfigLockRequest();
  data_stream_direction_t get_data_stream_direction() const;
  data_stream_id_t   get_data_stream_id() const;
  routing_id_t       get_routing_id() const;
  config_value_t     get_tuning_freq_MHz() const;
  config_value_t     get_bandwidth_3dB_MHz() const;
  config_value_t     get_sampling_rate_Msps() const;
  bool               get_samples_are_complex() const;
  gain_mode_value_t  get_gain_mode() const;
  config_value_t     get_gain_dB() const;
  config_value_t     get_tolerance_tuning_freq_MHz() const;
  config_value_t     get_tolerance_bandwidth_3dB_MHz() const;
  config_value_t     get_tolerance_sampling_rate_Msps() const;
  config_value_t     get_tolerance_gain_dB() const;
  bool               get_including_data_stream_direction() const;
  bool               get_including_data_stream_id() const;
  bool               get_including_routing_id() const;
  bool               get_including_tuning_freq_MHz() const;
  bool               get_including_bandwidth_3dB_MHz() const;
  bool               get_including_sampling_rate_Msps() const;
  bool               get_including_samples_are_complex() const;
  bool               get_including_gain_mode() const;
  bool               get_including_gain_dB() const;
  /*! @brief Either this function or include_data_stream_id()
   *         must be called before sending a
   *         DataStreamConfigLockRequest to ARC::request_config_lock or
   *         DRC::request_config_lock.
   ******************************************************************************/
  void include_data_stream_direction(data_stream_direction_t data_stream_direction);
  /*! @brief Either this function or include_data_stream_direction()
   *         must be called before sending a
   *         DataStreamConfigLockRequest to ARC::request_config_lock or
   *         DRC::request_config_lock.
   ******************************************************************************/
  void include_data_stream_id(data_stream_id_t data_stream_id);
  /*! @brief This function must be called before sending a
   *         DataStreamConfigLockRequest to ARC::request_config_lock or
   *         DRC::request_config_lock.
   *  @param[in] routing_id Must be a string in the format "RX0", "TX0", "RX1",
   *                        etc...
   ******************************************************************************/
  void include_routing_id(routing_id_t routing_id);
  /*! @brief This function must be called before sending a
   *         DataStreamConfigLockRequest to ARC::request_config_lock or
   *         DRC::request_config_lock.
   ******************************************************************************/
  void include_tuning_freq_MHz(
      config_value_t desired_tuning_freq_MHz,
      config_value_t tolerance_tuning_freq_MHz);
  /*! @brief This function must be called before sending a
   *         DataStreamConfigLockRequest to ARC::request_config_lock or
   *         DRC::request_config_lock.
   ******************************************************************************/
  void include_bandwidth_3dB_MHz(
      config_value_t desired_bandwidth_3dB_MHz,
      config_value_t tolerance_bandwidth_3dB_MHz);
  /*! @brief This function must be called before sending a
   *         DataStreamConfigLockRequest to DRC::request_config_lock.
   ******************************************************************************/
  void include_sampling_rate_Msps(
      config_value_t desired_sampling_rate_Msps,
      config_value_t tolerance_sampling_rate_Msps);
  /*! @brief This function must be called before sending a
   *         DataStreamConfigLockRequest to DRC::request_config_lock.
   ******************************************************************************/
  void include_samples_are_complex(bool desired_samples_are_complex);
  /*! @brief This function is optionally called before sending a
   *         DataStreamConfigLockRequest to  ARC::request_config_lock or
   *         DRC::request_config_lock. Call this only if request should
   *         include a desired gain mode value.
   ******************************************************************************/
  void include_gain_mode(gain_mode_value_t desired_gain_mode);
  /*! @brief This function is optionally called before sending a
   *         DataStreamConfigLockRequest to  ARC::request_config_lock or
   *         DRC::request_config_lock. Call this only if request should
   *         include desired manual gain value.
   ******************************************************************************/
  void include_gain_dB(
      config_value_t desired_gain_dB,
      config_value_t tolerance_gain_dB);
  protected:
  void throw_for_invalid_get_call(const char* config) const;
}; // class DataStreamConfigLockRequest

/*! @brief Intended to represent requested controller config locks.
 *         Locks may or may not succeed.
 ******************************************************************************/
struct ConfigLockRequest {
  std::vector<DataStreamConfigLockRequest> m_data_streams;
}; // struct ConfigLockRequest

/*! @brief Intended to represent an existing (already locked) lock of a group
 *         of radio controller configs for an individual data stream.
 ******************************************************************************/
struct DataStreamConfigLock {
  /// @brief Each existing lock is always associated with a data stream ID.
  data_stream_id_t  m_data_stream_id;
  //routing_id_t       m_routing_id; /// @todo /FIXME - add this member and implement corresponding functionality?
  config_value_t    m_tuning_freq_MHz;
  config_value_t    m_bandwidth_3dB_MHz;
  config_value_t    m_sampling_rate_Msps;
  bool              m_samples_are_complex;
  gain_mode_value_t m_gain_mode;
  config_value_t    m_gain_dB;
  bool              m_including_gain_mode;
  bool              m_including_gain_dB;
}; // struct DataStreamConfigLock

/*! @brief Intended to represent an existing (already locked) lock of a group
 *         of digital radio controller configs.
 ******************************************************************************/
struct ConfigLock {
  config_lock_id_t                  m_config_lock_ID;
  std::vector<DataStreamConfigLock> m_data_streams;
}; // struct ConfigLock

/*! @brief Provides an API for controlling/locking analog configs of
 *         a radio. When requesting config locks, a Configurator object is
 *         queried for valid ranges before hardware actuation is performed.
 ******************************************************************************/
template<class log_t, class configurator_t>
class ARC : public LogForwarder<log_t> {
  protected:
  using LogForwarder<log_t>::log_info;
  using LogForwarder<log_t>::log_debug;
  using LogForwarder<log_t>::log_trace;
  using LogForwarder<log_t>::log_warn;
  using LogForwarder<log_t>::log_error;
  const char*                   m_descriptor;
  ///@brief child class is expected to have a member derived from Configurator
  configurator_t                m_configurator;
  std::vector<ConfigLock>       m_config_locks;
  std::vector<data_stream_id_t> m_data_stream_ids;
  public:
  ARC(const char* descriptor);
  const std::string& get_descriptor() const;
  const std::vector<ConfigLock>& get_config_locks() const;
  /// @brief Determine whether the data stream is powered on and fully active.
  virtual bool get_data_stream_is_enabled(
      data_stream_id_t data_stream_id) = 0;
  virtual data_stream_direction_t get_data_stream_direction(
      data_stream_id_t data_stream_id) = 0;
  virtual config_value_t get_tuning_freq_MHz(
      data_stream_id_t data_stream_id) = 0;
  virtual config_value_t get_bandwidth_3dB_MHz(
      data_stream_id_t data_stream_id) = 0;
  virtual bool request_config_lock(
      config_lock_id_t         config_lock_ID,
      const ConfigLockRequest& config_lock_request);
  virtual void unlock_config_lock(config_lock_id_t config_lock_ID);
  virtual void unlock_all();
  void throw_if_data_stream_lock_request_malformed(
      const DataStreamConfigLockRequest& data_stream_config_lock_request) const;
  protected:
  bool lock_config(data_stream_id_t ds_id, config_value_t val,
      config_key_t cfg, config_value_t tol);
  virtual void set_data_stream_direction(data_stream_id_t id,
      data_stream_direction_t val) = 0;
  /*! @brief  Attempt to set on-hardware value with no guarantee of success.
   *  @todo / FIXME - for increased functionality, make public and throw
   *          exception if value is locked?
   ******************************************************************************/
  virtual void set_tuning_freq_MHz(
      data_stream_id_t data_stream_id, config_value_t tuning_freq_MHz) = 0;
  /*! @brief  Attempt to set on-hardware value with no guarantee of success.
   *  @todo / FIXME - for increased functionality, make public and throw
   *          exception if value is locked?
   ******************************************************************************/
  virtual void set_bandwidth_3dB_MHz(
      data_stream_id_t data_stream_id, config_value_t bandwidth_3dB_MHz) = 0;
  /// @brief Unlocks configurator lock (no hardware action is performed).
  void unlock_tuning_freq_MHz(data_stream_id_t data_stream_id);
  /// @brief Unlocks configurator lock (no hardware action is performed).
  void unlock_bandwidth_3dB_MHz(data_stream_id_t data_stream_id);
  /*! @param[in] ds_id Data stream ID for which to apply lock.
   *  @param[in] cfg_key  Config key string.
   ******************************************************************************/
  void unlock_config(data_stream_id_t ds_id, config_key_t cfg_key);
  /*! @brief Performs the minimum config locks required per data stream
   *         for an ARC.
   ******************************************************************************/
  virtual bool do_min_data_stream_config_locks(data_stream_id_t data_stream_id,
    const DataStreamConfigLockRequest& data_stream_config_lock_request);
  bool config_val_is_within_tolerance(config_value_t expected_val,
      config_value_t tolerance, config_value_t val) const;
  public:
  void throw_if_data_stream_disabled_for_read(const data_stream_id_t& ds_id,
      const char* config_description) const;
  void throw_if_data_stream_disabled_for_write(const data_stream_id_t& ds_id,
      const char* config_description) const;
  void throw_invalid_data_stream_id(data_stream_id_t data_stream_id) const;
}; // class ARC

/*! @brief Provides an API for controlling/locking analog and digital configs of
 *         a radio. When requesting config locks, a Configurator object is
 *         queried for valid ranges before hardware actuation is performed.
 ******************************************************************************/
template<class log_t, class configurator_t>
class DRC : public ARC<log_t, configurator_t> {
  public:
  DRC(const char* descriptor);
  /// @brief Measure value as it exists on hardware.
  virtual config_value_t    get_sampling_rate_Msps(
      data_stream_id_t data_stream_id) = 0;
  /// @brief Retrieve value as it exists on hardware.
  virtual bool              get_samples_are_complex(
      data_stream_id_t data_stream_id) = 0;
  /*! @brief Measure value as it exists on hardware.
   *         If hardware does not support a gain mode setting, the expectation
   *         is that an exception will be thrown.
   ******************************************************************************/
  virtual gain_mode_value_t get_gain_mode(
      data_stream_id_t data_stream_id) = 0;
  /*! @brief Measure value as it exists on hardware (should throw exception if
   *         gain mode is auto)
   ******************************************************************************/
  virtual config_value_t    get_gain_dB(
      data_stream_id_t data_stream_id) = 0;
  /*! @brief  Attempt to set on-hardware value with no guarantee of success.
   *  @todo / FIXME - for increased functionality, make public and throw
   *          exception if value is locked?
   ******************************************************************************/
  virtual void set_sampling_rate_Msps(
      data_stream_id_t data_stream_id, config_value_t sampling_rate_Msps) = 0;
  /*! @brief  Attempt to set on-hardware value with no guarantee of success.
   *  @todo / FIXME - for increased functionality, make public and throw
   *          exception if value is locked?
   ******************************************************************************/
  virtual void set_samples_are_complex(data_stream_id_t data_stream_id,
      bool samples_are_complex) = 0;
  /*! @brief  Attempt to set on-hardware value with no guarantee of success.
   *          If hardware does not support a gain mode setting, the expectation
   *          is that an exception will be thrown.
   *  @todo / FIXME - for increased functionality, make public and throw
   *          exception if value is locked?
   ******************************************************************************/
  virtual void set_gain_mode(data_stream_id_t data_stream_id,
      gain_mode_value_t gain_mode) = 0;
  /*! @brief  Attempt to set on-hardware value with no guarantee of success.
   *          Exception should be thrown if if the gain mode for the
   *          requested data stream is auto.
   *  @todo / FIXME - for increased functionality, make public and throw
   *          exception if value is locked?
   ******************************************************************************/
  virtual void set_gain_dB(data_stream_id_t data_stream_id,
      config_value_t gain_dB) = 0;
  virtual bool request_config_lock(config_lock_id_t config_lock_ID,
      const ConfigLockRequest& config_lock_request);
  virtual void unlock_config_lock(config_lock_id_t config_lock_ID);
  /*! @brief     Requests configurator lock, and if that succeeds, attempt to set
   *             on-hardware value to desired value.
   *  @param[in] ds_id  Data stream ID for which to apply lock.
   *  @param[in] val    Desired value to lock to.
   *  @param[in] do_tol Instructs usage of the tolerance
   *  @param[in] tol    Tolerance.
   *  @return    Boolean indicator of success.
   ******************************************************************************/
  bool lock_config(data_stream_id_t ds_id, config_value_t val, config_key_t cfg,
      bool do_tol, config_value_t tol);
  /// @brief Unlocks configurator lock (no hardware action is performed).
  void unlock_sampling_rate_Msps (data_stream_id_t data_stream_id);
  /// @brief Unlocks configurator lock (no hardware action is performed).
  /*! @brief Performs the minimum config locks required per data stream
   *         for a DRC.
   ******************************************************************************/
  virtual bool do_min_data_stream_config_locks(data_stream_id_t data_stream_id,
      const DataStreamConfigLockRequest& data_stream_config_lock_request);
  void throw_if_data_stream_lock_request_malformed(
      const DataStreamConfigLockRequest& req) const;
}; // class DRC

} // namespace DRC

#include "DRC.cc"

#endif // _DRC_HH
