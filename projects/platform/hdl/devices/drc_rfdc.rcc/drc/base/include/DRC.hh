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

#include "Math.hh" // Constraint Satisfaction Problem (CSP)

struct RFPort {
  public:
  enum class direction_t {rx, tx};
  enum class config_t {
      direction,
      tuning_freq_MHz,
      bandwidth_3dB_MHz,
      sampling_rate_Msps,
      samples_are_complex,
      gain_mode,
      gain_dB};
  RFPort::direction_t m_direction;
  double              m_tuning_freq_MHz;
  double              m_bandwidth_3dB_MHz;
  double              m_sampling_rate_Msps;
  bool                m_samples_are_complex;
  std::string         m_gain_mode;
  /// @brief ignore if m_gain_mode is not "manual"
  double              m_gain_dB;
  RFPort();
  RFPort(
    RFPort::direction_t direction,
    double              tuning_freq_MHz,
    double              bandwidth_3dB_MHz,
    double              sampling_rate_Msps,
    bool                samples_are_complex,
    const std::string&  gain_mode,
    double              gain_dB);
}; // struct RFPort

/*! @brief intentionally separate (does not inherit) from RFPort,
 *         m_rf_port_name is intended to point to a mapped RFPort entry
 ******************************************************************************/
struct RFPortConfigLock {
  std::string m_rf_port_name;
  uint8_t     m_rf_port_num;
  uint8_t     m_app_port_num;
  RFPortConfigLock(const std::string& rf_port_name, uint8_t rf_port_num,
      uint8_t app_port_num);
}; // struct RFPortConfigLock

typedef std::vector<RFPortConfigLock> ConfigLock;

/// @brief constructed once and never changes
class RFPortConfigLockRequest : protected RFPort, protected RFPortConfigLock {
  public:
  enum class config_t {
    rf_port_name, rf_port_num, app_port_num,
    tolerance_tuning_freq_MHz,
    tolerance_bandwidth_3dB_MHz,
    tolerance_sampling_rate_Msps,
    tolerance_gain_dB
  };
  /*! @param[in] gain_mode    "manual" or "agc" (or perhaps something
   *                          hardware-specific)
   *  @param[in] rf_port_name specify name to request by port, or leave as "" to
   *                          request by direction only
   ****************************************************************************/
  RFPortConfigLockRequest(
    RFPort::direction_t direction,
    double              tuning_freq_MHz,
    double              bandwidth_3dB_MHz,
    double              sampling_rate_Msps,
    bool                samples_are_complex,
    const std::string&  gain_mode,
    double              gain_dB,
    double              tolerance_tuning_freq_MHz,
    double              tolerance_bandwidth_3dB_MHz,
    double              tolerance_sampling_rate_Msps,
    double              tolerance_gain_dB,
    const std::string&  rf_port_name,
    uint8_t             rf_port_num,
    uint8_t             app_port_num);
  RFPort::direction_t get_direction() const;
  double              get_tuning_freq_MHz() const;
  double              get_bandwidth_3dB_MHz() const;
  double              get_sampling_rate_Msps() const;
  bool                get_samples_are_complex() const;
  const std::string&  get_gain_mode() const;
  double              get_gain_dB() const;
  double              get_tolerance_tuning_freq_MHz() const;
  double              get_tolerance_bandwidth_3dB_MHz() const;
  double              get_tolerance_sampling_rate_Msps() const;
  double              get_tolerance_gain_dB() const;
  const std::string&  get_rf_port_name() const;
  uint8_t             get_rf_port_num() const;
  uint8_t             get_app_port_num() const;
  protected:
  double m_tolerance_tuning_freq_MHz;
  double m_tolerance_bandwidth_3dB_MHz;
  double m_tolerance_sampling_rate_Msps;
  double m_tolerance_gain_dB;
}; // class RFPortConfigLockRequest

typedef std::vector<RFPortConfigLockRequest> ConfigLockRequest;
typedef ConfigLockRequest Configuration;

/* !@brief This is the base class for all CSP classes which will be radio
 *         specific. It has a CSPSolver which provides a way describing and
 *         enforcing radio-specific constraints,
 *         e.g. 70 <= rx1_tuning_freq_MHz <= 6000.
 ******************************************************************************/
class CSPBase {
  protected:
  /// @todo / FIXME - pull in these 2 from DRC definition
  /// @brief floating point tolerance used for value comparison
  double dfp_tol = 1e-12;
  public:
  /// @todo / FIXME make protected?
  CSPSolver m_solver;
  const CSPSolver::FeasibleRegionLimits& get_feasible_region_limits() const;
  double get_feasible_region_limits_min_double(const std::string& var) const;
  template<typename T> bool val_is_within_var_feasible_region(T val,
      const std::string& var_key) const;
}; // class CSPBase

/// @brief maps a RFPort::config_t entry to a CSP variable name (string)
typedef std::map<RFPort::config_t, std::string> CSPVarMap;

/*! @brief Software-only emulator of a hardware configuration environment,
 *         which provides API for locking/unlocking range-constrained
 *         descriptors of radio configs, templatized by radio-specific CSP
 ******************************************************************************/
template<class CSP>
class Configurator {
  public:
  /*! @brief dictionary to construct and then allow internal methods to look up:
   *         rf_port_name > tune freq/bandwidth etc  > CSP variable name
   *         (string)     > CSPVarMap 1st (config_t) > CSPVarMap 2nd (string)
   ****************************************************************************/
  std::map<std::string,CSPVarMap> m_dict;
  /// @brief this just retrieves entries from the dictionary
  const std::string& get_error() const;
  double get_config_locked_value(const std::string& rf_port_name,
      RFPort::config_t cfg, double attempted_val) const;
  template<typename T> std::string get_lock_config_str(
      const std::string& rf_port_name, RFPort::config_t cfg, T val,
      bool succeeded);
  bool get_csp_var_is_locked(const std::string& csp_var) const;
  const CSPSolver::FeasibleRegionLimits& get_feasible_region_limits() const;
  double get_feasible_region_limits_min_double(const std::string& var) const;
  double get_val_is_within_feasible_region(const std::string& rf_port_name,
      RFPort::config_t cfg, double val) const;
  bool val_is_within_var_feasible_region(double val,
      const std::string& var) const;
  bool lock_config(const std::string& rf_port_name, RFPort::config_t cfg,
      int32_t val);
  bool lock_config(const std::string& rf_port_name, RFPort::config_t cfg,
      double val, double tolerance);
  void unlock_config(const std::string& rf_port_name, RFPort::config_t cfg);
  void unlock_all();
  protected:
  /*! @brief This is used to keep track of internal CSP var "locks". CSP
   *  variables aren't exactly locked, but rather their feasible regions
   *  are manipulated (via constraints) as a result of config lock/unlock,
   *  and this is used to keep track of said manipulation (constraints)
   ****************************************************************************/
  struct CSPVarLockInfo {
    size_t  m_constr_lo_id;
    size_t  m_constr_hi_id;
    int32_t m_lock_val_int32;
    double  m_lock_val_double;
    /*! @brief if true, m_lock_val_int32 is ignored, otherwise
     *         m_lock_val_double ignored
     **************************************************************************/
    bool    m_lock_val_is_double;
  };
  /// @brief map by var name
  std::map<std::string,CSPVarLockInfo> m_locked_csp_vars;
  /// @brief a config is mapped to a variable (X) within the CSP <X,D,C>
  CSP                                  m_solver;
  std::string                          m_error;
  // lock_csp_var() and unlock_csp_var() methods are the primary mechanism
  // between Configurators and their CSPs
  bool lock_csp_var(  const std::string& csp_var, int32_t val);
  bool lock_csp_var(  const std::string& csp_var, double val, double tolerance);
  void unlock_csp_var(const std::string& csp_var);
}; // class Configurator

/*! @brief Provides an API for controlling/locking analog and digital configs of
 *         a radio. When preparing (requesting "config locks"), a Configurator
 *         object is queried for allowable ranges before hardware actuation is
 *         performed.
 ******************************************************************************/
template<class configurator_t>
class DRC {
  public:
  DRC(const std::string& descriptor = "");
  virtual void set_configuration(uint16_t config_idx,
    const Configuration& req);
  // child classes may override transition functions w/ hardware-specific
  // behavior, config_idx refers to a configuration already set via
  // set_configuration()
  virtual bool prepare(uint16_t config_idx);
  virtual bool start(  uint16_t config_idx);
  virtual bool stop(   uint16_t config_idx);
  virtual bool release(uint16_t config_idx);
  void release_all();
  const std::string&                    get_descriptor() const;
  /*! @return most recent error which caused config lock failure (empty
   *          string if there was never a failure)
   ****************************************************************************/
  const std::string&                    get_error() const;
  const std::map<uint16_t, ConfigLock>& get_locks() const;
  // get_ functions retrieve (by port name) a value as it exists on hardware.
  /// @brief Determine whether the RF port is powered on and fully active.
  virtual bool        get_enabled(            const std::string&
    rf_port_name) = 0;
  virtual RFPort::direction_t get_direction(  const std::string&
    rf_port_name) = 0;
  virtual double      get_tuning_freq_MHz(    const std::string&
    rf_port_name) = 0;
  virtual double      get_bandwidth_3dB_MHz(  const std::string&
    rf_port_name) = 0;
  virtual double      get_sampling_rate_Msps( const std::string&
    rf_port_name) = 0;
  virtual bool        get_samples_are_complex(const std::string&
    rf_port_name) = 0;
  virtual std::string get_gain_mode(          const std::string&
    rf_port_name) = 0;
  virtual double      get_gain_dB(            const std::string&
    rf_port_name) = 0;
  virtual uint8_t     get_app_port_num(       const std::string&
    rf_port_name) = 0;
  // set_ functions attempt to set (by port name) on-hardware value, with no
  // guarantee of success (prior calls to configurator are what make guarantees)
  virtual void set_direction(          const std::string& rf_port_name,
      RFPort::direction_t val) = 0;
  virtual void set_tuning_freq_MHz(    const std::string& rf_port_name,
      double val) = 0;
  virtual void set_bandwidth_3dB_MHz(  const std::string& rf_port_name,
      double val) = 0;
  virtual void set_sampling_rate_Msps( const std::string& rf_port_name,
      double val) = 0;
  virtual void set_samples_are_complex(const std::string& rf_port_name,
      bool val) = 0;
  virtual void set_gain_mode(          const std::string& rf_port_name,
      const std::string& val) = 0;
  /*! @brief  Exception is thrown if the gain mode for the requested RF port
   *          is currently "agc" (auto).
   ****************************************************************************/
  virtual void set_gain_dB(     const std::string& rf_port_name,
      double val) = 0;
  virtual void set_app_port_num(const std::string& rf_port_name,
      uint8_t val) = 0;
  //protected:
  /*! @param[in] id Zero-based configuration ordinal used to refer to the lock
   *                request (and the succesful lock, if it suceeds) going
   *                forward, e.g. for future calls to unlock_config_lock()
   *  @return       Boolean indicator of success
   ****************************************************************************/
  virtual bool request_config_lock(uint16_t config_idx);
  virtual void unlock_config_lock(uint16_t config_idx);
  virtual void unlock_all();
  protected:
  /// @brief mainly just for logging "who am I"
  std::string                          m_descriptor;
  std::string                          m_error;
  /*! @brief each DRC child class is expected to associate a configurator_t
   *         class which is expected to derive from Configurator
   ****************************************************************************/
  configurator_t                       m_configurator;
  /// @brief map locks by uint index from prepare/start/stop/release
  std::map<uint16_t,ConfigLock>        m_locks;
  /// @brief map lock requests by uint index from prepare/start/stop/release
  std::map<uint16_t,Configuration>     m_configurations;
  std::map<uint16_t,bool>              m_pending_configuration;
  /// @brief map cache of RF port settings by rf_port_name (string)
  std::map<std::string,RFPort>         m_cache;
  bool                                 m_cache_initialized;
  virtual void initialize_cache();
  bool lock_config(const std::string& rf_port_name, RFPort::config_t cfg,
    double val, bool do_tolerance, double tolerance);
  void unlock_config(const std::string& rf_port_name, RFPort::config_t cfg);
  void unlock_rf_port(const std::string& rf_port_name);
  virtual bool attempt_rf_port_config_locks(const std::string& rf_port_name,
      const RFPortConfigLockRequest& req);
  void throw_invalid_rf_port_name(const std::string& rf_port_name) const;
}; // class DRC

#include "DRC.cc"

#endif // _DRC_HH
