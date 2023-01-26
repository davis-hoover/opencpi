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
#include "UtilLogPrefix.hh" // Util::LogPrefix

namespace OCPI {

/// @todo / FIXME - consolidate into DRC namespace
namespace DRC_PHASE_2 {

using namespace Math;

/// @brief Each RF port has an associated direction (either RX or TX).
enum class rf_port_direction_t {rx, tx};
/*! @brief We model many (all?) of the radio controller config values as
 *         doubles.
 ******************************************************************************/
//enum class std::string {agc, manual};
/*! @brief Each config lock has an associated ID by which it can be referred to
 *         (after a lock occurs you use this ID to keep track of that lock so
 *         that you can specifically delete that lock at a later time).
 ******************************************************************************/
// standard radio controller RF port configs
const std::string config_key_direction          ("direction"          );
const std::string config_key_tuning_freq_MHz    ("tuning_freq_MHz"    );
const std::string config_key_bandwidth_3dB_MHz  ("bandwidth_3dB_MHz"  );
const std::string config_key_sampling_rate_Msps ("sampling_rate_Msps" );
const std::string config_key_samples_are_complex("samples_are_complex");
const std::string config_key_gain_mode          ("gain_mode"          );
const std::string config_key_gain_dB            ("gain_dB"            );

class CSPBase {
  protected:
  /// @todo / FIXME - pull in these 2 from DRC definition
  double dfp_tol = 1e-12;
  public:
  /// @todo / FIXME make protected?
  CSPSolver m_solver;
  const CSPSolver::FeasibleRegionLimits& get_feasible_region_limits() const;
  double get_feasible_region_limits_min_double(
        const char* var) const;
}; // CSPBase

// map generic CSP variable names (const char *s) each to a std::string (one
// of config_key_<name>
// for all RF ports

class RFPort {
  public:
  typedef std::map<std::string, const char*> CSPVarMap;
  /// @todo / FIXME make protected?
  CSPVarMap   m_csp_map;
  RFPort(std::string name, bool supports_rx, bool supports_tx, CSPVarMap map);
  std::string get_name() const;
  bool        get_supports_rx() const;
  bool        get_supports_tx() const;
  protected:
  std::string m_name;
  bool        m_supports_rx;
  bool        m_supports_tx;
}; // class RFPort

/*! @brief Software-only emulator of a hardware configuration environment which
 *         provides an API for locking/unlocking range-constrained configs.
 ******************************************************************************/
template<class CSP>
class Configurator : public OCPI::Util::LogPrefix {
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
    double m_lock_val_double;
    bool           m_lock_val_is_int32;
    bool           m_lock_val_is_double;
  };
  std::vector<std::string>          m_rf_port_names;
  std::vector<RFPort>               m_rf_ports;
  std::map<const char*, LockParam>  m_locked_params;
  /// @brief a config is mapped to a variable (X) within the CSP <X,D,C>
  CSP                               m_solver;
  std::string                       m_error;
  public:
  const char* get_config(std::string rf_port_name, std::string cfg) const;
  double get_config_locked_value(std::string rf_port_name,
      std::string cfg) const;
  template<typename T> std::string get_lock_config_str(std::string rf_port_name,
      std::string cfg, T val, bool succeeded);
  const std::vector<std::string>& get_rf_port_names() const;
  const std::string& get_error() const;
  void add_rf_port(RFPort rf_port);
  bool lock_config(std::string ds_id, std::string cfg, int32_t val);
  bool lock_config(std::string ds_id, std::string cfg, double val,
      double tol);
  bool lock_config(const char* config, int32_t val);
  bool lock_config(const char* config, double val,
      double tolerance);
  void unlock_config(std::string ds_id, std::string config);
  void unlock_config(const char* config);
  void unlock_all();
  void find_rf_ports_which_support_direction(rf_port_direction_t dir,
       std::vector<std::string>& rf_ports) const;
  double get_locked_value(const char* config);
  bool get_config_is_locked(const char* config);
  const CSPSolver::FeasibleRegionLimits& get_feasible_region_limits() const;
  double get_feasible_region_limits_min_double(const char* var) const;
}; // class Configurator

/*! @brief Intended to represent requested config locks for individual RF
 *         ports, which may or may not succeed.
 ******************************************************************************/
class RFPortConfigLockRequest {
  protected:
  std::string         m_rf_port_name;
  rf_port_direction_t m_direction;
  std::string         m_routing_id;
  double              m_tuning_freq_MHz;
  double              m_bandwidth_3dB_MHz;
  double              m_sampling_rate_Msps;
  bool                m_samples_are_complex;
  std::string         m_gain_mode;
  double              m_gain_dB;
  double              m_tolerance_tuning_freq_MHz;
  double              m_tolerance_bandwidth_3dB_MHz;
  double              m_tolerance_sampling_rate_Msps;
  double              m_tolerance_gain_dB;
  bool                m_including_direction;
  bool                m_including_rf_port_name;
  bool                m_including_routing_id;
  bool                m_including_tuning_freq_MHz;
  bool                m_including_bandwidth_3dB_MHz;
  bool                m_including_sampling_rate_Msps;
  bool                m_including_samples_are_complex;
  bool                m_including_gain_mode;
  bool                m_including_gain_dB;
  public:
  RFPortConfigLockRequest();
  rf_port_direction_t get_direction() const;
  std::string         get_rf_port_name() const;
  std::string         get_routing_id() const;
  double              get_tuning_freq_MHz() const;
  double              get_bandwidth_3dB_MHz() const;
  double              get_sampling_rate_Msps() const;
  bool                get_samples_are_complex() const;
  std::string         get_gain_mode() const;
  double              get_gain_dB() const;
  double              get_tolerance_tuning_freq_MHz() const;
  double              get_tolerance_bandwidth_3dB_MHz() const;
  double              get_tolerance_sampling_rate_Msps() const;
  double              get_tolerance_gain_dB() const;
  bool                get_including_direction() const;
  bool                get_including_rf_port_name() const;
  bool                get_including_routing_id() const;
  bool                get_including_tuning_freq_MHz() const;
  bool                get_including_bandwidth_3dB_MHz() const;
  bool                get_including_sampling_rate_Msps() const;
  bool                get_including_samples_are_complex() const;
  bool                get_including_gain_mode() const;
  bool                get_including_gain_dB() const;
  /*! @brief This funciton must be called before sending a
   *         RFPortConfigLockRequest to ARC::request_config_lock or
   *         DRC::request_config_lock.
   ******************************************************************************/
  void include_direction(rf_port_direction_t val);
  /*! @brief This function is optionally called before sending a
   *         RFPortConfigLockRequest to ARC::request_config_lock or
   *         DRC::request_config_lock.
   ******************************************************************************/
  void include_rf_port_name(std::string val);
  /*! @brief This function is optionally called before sending a
   *         RFPortConfigLockRequest to DRC::request_config_lock.
   *  @param[in] routing_id Must be a string in the format "RX0", "TX0", "RX1",
   *                        etc...
   ******************************************************************************/
  void include_routing_id(std::string val);
  /*! @brief This function must be called before sending a
   *         RFPortConfigLockRequest to ARC::request_config_lock or
   *         DRC::request_config_lock.
   ******************************************************************************/
  void include_tuning_freq_MHz(double val, double tolerance);
  /*! @brief This function must be called before sending a
   *         RFPortConfigLockRequest to ARC::request_config_lock or
   *         DRC::request_config_lock.
   ******************************************************************************/
  void include_bandwidth_3dB_MHz(double val, double tolerance);
  /*! @brief This function must be called before sending a
   *         RFPortConfigLockRequest to DRC::request_config_lock.
   ******************************************************************************/
  void include_sampling_rate_Msps(double val, double tolerance);
  /*! @brief This function must be called before sending a
   *         RFPortConfigLockRequest to DRC::request_config_lock.
   ******************************************************************************/
  void include_samples_are_complex(bool val);
  /*! @brief This function is optionally called before sending a
   *         RFPortConfigLockRequest to  ARC::request_config_lock or
   *         DRC::request_config_lock. Call this only if request should
   *         include a desired gain mode value.
   ******************************************************************************/
  void include_gain_mode(std::string val);
  /*! @brief This function is optionally called before sending a
   *         RFPortConfigLockRequest to  ARC::request_config_lock or
   *         DRC::request_config_lock. Call this only if request should
   *         include desired manual gain value.
   ******************************************************************************/
  void include_gain_dB(double val, double tolerance);
  protected:
  void throw_for_invalid_get_call(const char* config) const;
}; // class RFPortConfigLockRequest

/*! @brief Intended to represent requested controller config locks.
 *         Locks may or may not succeed.
 ******************************************************************************/
struct ConfigLockRequest {
  std::vector<RFPortConfigLockRequest> m_rf_ports;
}; // struct ConfigLockRequest

/*! @brief Intended to represent an existing (already locked) lock of a group
 *         of radio controller configs for an individual RF port.
 ******************************************************************************/
struct RFPortConfigLock {
  /// @brief Each existing lock is always associated with an RF port
  std::string         m_rf_port_name;
  rf_port_direction_t m_direction;
  /// @todo /FIXME - add routing id and implement corresponding functionality?
  //std::string         m_routing_id;
  double              m_tuning_freq_MHz;
  double              m_bandwidth_3dB_MHz;
  double              m_sampling_rate_Msps;
  bool                m_samples_are_complex;
  std::string         m_gain_mode;
  double              m_gain_dB;
  bool                m_including_gain_mode;
  bool                m_including_gain_dB;
}; // struct RFPortConfigLock

/*! @brief Intended to represent an existing (already locked) lock of a group
 *         of digital radio controller configs.
 ******************************************************************************/
struct ConfigLock {
  std::string                       m_config_lock_id;
  std::vector<RFPortConfigLock> m_rf_ports;
}; // struct ConfigLock

/*! @brief Provides an API for controlling/locking analog configs of
 *         a radio. When requesting config locks, a Configurator object is
 *         queried for valid ranges before hardware actuation is performed.
 ******************************************************************************/
template<class configurator_t>
class ARC : public OCPI::Util::LogPrefix {
  public:
  ARC(const char* descriptor);
  const std::string&      get_descriptor() const;
  const std::vector<ConfigLock>& get_config_locks() const;
  // get_ API calls each retrieve a value as it exists on hardware.
  /// @brief Determine whether the RF port is powered on and fully active.
  virtual bool            get_enabled(          std::string rf_port_name) = 0;
  virtual rf_port_direction_t get_direction(    std::string rf_port_name) = 0;
  virtual double          get_tuning_freq_MHz(  std::string rf_port_name) = 0;
  virtual double          get_bandwidth_3dB_MHz(std::string rf_port_name) = 0;
  // set_ API calls each attempt to set on-hardware value w/ no guarantee of
  // success
  virtual void set_direction(std::string rf_port_name,
      rf_port_direction_t val) = 0;
  /*! @brief  Attempt to set on-hardware value with no guarantee of success.
   *  @todo / FIXME - for increased functionality, make public and throw
   *          exception if value is locked?
   ******************************************************************************/
  virtual void set_tuning_freq_MHz(std::string rf_port_name, double val) = 0;
  /*! @brief  Attempt to set on-hardware value with no guarantee of success.
   *  @todo / FIXME - for increased functionality, make public and throw
   *          exception if value is locked?
   ******************************************************************************/
  virtual void set_bandwidth_3dB_MHz(std::string rf_port_name, double val) = 0;
  //protected:
  virtual bool request_config_lock(std::string id, const ConfigLockRequest& req);
  virtual void unlock_config_lock(std::string id);
  virtual void unlock_all();
  protected:
  const char*                               m_descriptor;
  ///@brief child class is expected to have a member derived from Configurator
  configurator_t                            m_configurator;
  std::vector<ConfigLock>                   m_config_locks;
  bool                                      m_cache_initialized;
  std::map<std::string,rf_port_direction_t> m_cache_direction;
  std::map<std::string,double>              m_cache_tuning_freq_MHz;
  std::map<std::string,double>              m_cache_bandwidth_3dB_MHz;
  virtual void initialize_cache();
  bool lock_config(std::string rf_port_name, double val,
      std::string cfg, bool do_tol, double tol);
  void unlock_config(std::string rf_port_name, std::string cfg_key);
  /// @brief Performs the minimum config locks required per Rf port
  virtual bool do_min_rf_port_config_locks(std::string rf_port_name,
    const RFPortConfigLockRequest& req);
  bool config_val_is_within_tolerance(double expected_val,
      double tolerance, double val) const;
  void throw_if_rf_port_lock_request_malformed(
      const RFPortConfigLockRequest& req) const;
  void throw_invalid_rf_port_name(std::string rf_port_name) const;
}; // class ARC

/*! @brief Provides an API for controlling/locking analog and digital configs of
 *         a radio. When preparing (requesting "config locks"), a Configurator
 *         object is queried for allowable ranges before hardware actuation is
 *         performed.
 ******************************************************************************/
template<class configurator_t>
class DRC : public ARC<configurator_t> {
  public:
  DRC(const char* descriptor);
  virtual bool prepare(unsigned config, const ConfigLockRequest& req);
  virtual bool start(  unsigned config);
  virtual bool stop(   unsigned config);
  virtual bool release(unsigned config);
  const std::string& get_error() const;
  // get_ API calls each retrieve a value as it exists on hardware.
  virtual double get_sampling_rate_Msps( std::string rf_port_name) = 0;
  virtual bool   get_samples_are_complex(std::string rf_port_name) = 0;
  virtual std::string get_gain_mode(     std::string rf_port_name) = 0;
  // set_ API calls each attempt to set on-hardware value w/ no guarantee of
  // success
  virtual double get_gain_dB(            std::string rf_port_name) = 0;
  virtual void   set_sampling_rate_Msps( std::string rf_port_name,
      double val) = 0;
  virtual void   set_samples_are_complex(std::string rf_port_name,
      bool val) = 0;
  virtual void   set_gain_mode(          std::string rf_port_name,
      std::string val) = 0;
  /*! @brief  Exception is thrown if the gain mode for the requested RF port
   *          is auto ("agc").
   ******************************************************************************/
  virtual void   set_gain_dB(            std::string rf_port_name,
      double val) = 0;
  virtual void   set_routing_id(         std::string rf_port_name,
      std::string val) = 0;
  //protected:
  virtual bool request_config_lock(std::string rf_port_name,
      const ConfigLockRequest& req);
  virtual void unlock_config_lock(std::string rf_port_name);
  /*! @brief     Requests configurator lock, and if that succeeds, set
   *             on-hardware value to desired value.
   *  @param[in] rf_port_name RF port name for which to apply lock
   *  @param[in] cfg_key      Configuration to lock
   *  @param[in] val          Desired value to lock to
   *  @param[in] do_tol       Instructs usage of the tolerance
   *  @param[in] tol          Tolerance
   *  @return    Boolean      indicator of success.
   ******************************************************************************/
  bool lock_config(std::string rf_port_name, double val, std::string cfg,
      bool do_tol, double tolerance);
  /// @brief Performs the minimum config locks required per RF port
  virtual bool do_min_rf_port_config_locks(std::string id,
      const RFPortConfigLockRequest& req);
  void throw_if_rf_port_lock_request_malformed(
      const RFPortConfigLockRequest& req) const;
  protected:
  std::map<std::string,double>         m_cache_sampling_rate_Msps;
  std::map<std::string,bool>           m_cache_samples_are_complex;
  std::map<std::string,std::string>    m_cache_gain_mode;
  std::map<std::string,double>         m_cache_gain_dB;
  std::map<unsigned,ConfigLockRequest> m_requests;
  virtual void initialize_cache();
}; // class DRC

} // namespace DRC_PHASE_2

} // namespace OCPI

#include "../src/DRC.cct"

#endif // _DRC_HH
