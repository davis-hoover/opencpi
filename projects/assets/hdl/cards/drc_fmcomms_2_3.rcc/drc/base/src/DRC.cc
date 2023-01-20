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

#include <vector>   // std::vector
#include <string>   // std::string
#include <sstream>  // std::ostringstream
#include <cmath>    // std::abs
#include "DRC.hh"
///@TODO / FIXME address whether to remove
#define IS_LOCKING

namespace DRC {

const CSPSolver::FeasibleRegionLimits&
CSPBase::get_feasible_region_limits() const {
  return m_solver.get_feasible_region_limits();
}

double
CSPBase::get_feasible_region_limits_min_double(const char* var) const {
  return m_solver.get_feasible_region_limits_min_double(var);
}

DataStream::DataStream(data_stream_id_t id, bool supports_rx, bool supports_tx,
      CSPVarMap map) : m_data_stream_id(id), m_supports_rx(supports_rx),
      m_supports_tx(supports_tx), m_csp_map(map) {
}

data_stream_id_t
DataStream::get_data_stream_id() const {
  return m_data_stream_id;
}

bool
DataStream::get_supports_rx() const {
  return m_supports_rx;
}

bool
DataStream::get_supports_tx() const {
  return m_supports_tx;
}

template<class CSP> void
Configurator<CSP>::add_data_stream(DataStream data_stream) {
  m_data_streams.push_back(data_stream);
  m_data_stream_ids.push_back(data_stream.get_data_stream_id());
}

template<class CSP> const std::vector<data_stream_id_t>&
Configurator<CSP>::get_data_stream_ids() const {
  return m_data_stream_ids;
}

template<class CSP> const char*
Configurator<CSP>::get_config(data_stream_id_t id, config_key_t cfg) const {
  for(auto it=m_data_streams.begin(); it!=m_data_streams.end(); ++it) {
    if(it->get_data_stream_id() == id) {
      return it->m_csp_map.at(cfg);
    }
  }
  throw std::string("data stream id not found ")+id.c_str();
}

template<class CSP> config_value_t
Configurator<CSP>::get_config_locked_value(data_stream_id_t id,
    config_key_t cfg) const {
  auto var = get_config(id, cfg);
  return m_solver.get_feasible_region_limits_min_double(var);
}

template<class CSP> template<typename T> std::string
Configurator<CSP>::get_lock_config_str(data_stream_id_t id, config_key_t cfg,
    T val, bool succeeded) {
  std::ostringstream oss;
  oss << "lock " << (succeeded ? "SUCCEEDED " : "FAILED ");
  oss << "for data stream: " << id << " for config: " << cfg << " ";
  oss << "for requested value: " << val;
  return oss.str();
}

template<class CSP> bool
Configurator<CSP>::lock_config(data_stream_id_t id, config_key_t cfg,
    int32_t val) {
  //std::cout << "drc: Configurator: lock_config: " << id << " " << cfg << " " << val << "\n";
  bool ret = lock_config(get_config(id,cfg),val);
  //std::cout << "[DEBUG] " << m_solver.m_solver << "\n";
  //std::cout << "[DEBUG] " << m_solver.get_feasible_region_limits() << "\n";
  std::ostringstream oss;
  oss << get_lock_config_str<int32_t>(id,cfg,val,ret) << "\n";
  printf("%s", oss.str().c_str());
  return ret;
}

template<class CSP> bool
Configurator<CSP>::lock_config(data_stream_id_t id, config_key_t cfg,
    config_value_t val, config_value_t tol) {
  bool ret = lock_config(get_config(id,cfg),val,tol);
  //std::cout << "[DEBUG] " << m_solver.get_feasible_region_limits() << "\n";
  std::ostringstream oss;
  oss << get_lock_config_str<config_value_t>(id,cfg,val,ret);
  oss << " w/ tolerance: +/- " << tol << "\n";
  printf("%s", oss.str().c_str());
  return ret;
}

template<class CSP> bool
Configurator<CSP>::lock_config(const char* config, int32_t val) {
  bool successful = false;
  // attempt a lock
  if(!get_config_is_locked(config)) {
    CSPSolver::Constr& clo = m_solver.m_solver.add_constr(config, "=", val);
    //std::cout << "attempt a lock: add constraint " << config << "=" << val << "\n";
    //std::cout << "solver is now: " << m_solver.m_solver << "\n";
    successful = not m_solver.m_solver.feasible_region_limits_is_empty_for_var(config);
    if(successful) {
      Configurator<CSP>::LockParam param = {clo, clo, false, val, 0, true, false};
      m_locked_params.insert(std::pair<const char*, LockParam>(config, param));
    }
    else { // unroll
      //std::cout << "[DEBUG] " << get_feasible_region_limits() << "\n";
      m_solver.m_solver.remove_constr(clo);
      //m_solver.m_solver.remove_constr(clo);
    }
  }
  return successful;
}

template<class CSP> bool
Configurator<CSP>::lock_config(const char* config, config_value_t val,
    config_value_t tolerance) {
  // attempt a lock
  const CSPSolver::Constr& clo = m_solver.m_solver.add_constr(config, ">=", val-tolerance);
  //std::cout << "[DEBUG] lock " << config << get_feasible_region_limits() << "\n";
  const CSPSolver::Constr& chi = m_solver.m_solver.add_constr(config, "<=", val+tolerance);
  //std::cout << "[DEBUG] lock " << config << get_feasible_region_limits() << "\n";
  //std::cout << "attempt a lock: add constraint " << config << ">=" << val-tolerance << "\n";
  //std::cout << "solver is now: " << m_solver.m_solver << "\n";
  //std::cout << "attempt a lock: add constraint " << config << "<=" << val+tolerance << "\n";
  //std::cout << "solver is now: " << m_solver.m_solver << "\n";
  // test whether the lock was successful:
  // if we overconstrained such the feasible region contains an empty set for
  // the variable (config), the lock was unsuccessful we roll back (remove)
  // the constraints to their original values
  /*if(not m_solver.m_solver.feasible_region_limits_is_empty_for_var(config)) {
    CSPSolver::Constr& cmi = m_solver.m_solver.add_constr(config, "=", val);
    if(m_solver.m_solver.feasible_region_limits_is_empty_for_var(config)) {
      m_solver.m_solver.remove_constr(cmi);
    }
  }*/
  bool successful = not m_solver.m_solver.feasible_region_limits_is_empty_for_var(config);
  if(successful) {
    Configurator<CSP>::LockParam param = {clo, chi, true, 0, val, false, true};
    m_locked_params.insert(std::pair<const char*, LockParam>(config, param));
  }
  else { // unroll
    m_solver.m_solver.remove_constr(clo);
    m_solver.m_solver.remove_constr(chi);
  }
  return successful;
}

template<class CSP> void
Configurator<CSP>::unlock_config(data_stream_id_t ds_id, config_key_t config) {
  //std::cout << "drc: Configurator: unlock_config: " << ds_id << " " << config << "\n";
  unlock_config(get_config(ds_id, config));
}

template<class CSP> void
Configurator<CSP>::unlock_config(const char* config) {
  if(get_config_is_locked(config)) {
    auto& tmp = m_locked_params.at(config);
    // intentionallity not reference, due to changing vector entry which this is referring to
    auto chi = tmp.m_constr_hi;
    m_solver.m_solver.remove_constr(m_locked_params.at(config).m_constr_lo);
    if(m_locked_params.at(config).m_constr_hi_used) {
      m_solver.m_solver.remove_constr(chi);
    }
    m_locked_params.erase(m_locked_params.find(config));
  }
  else {
    throw std::string("attempted unlock for config not locked");
  }
  //std::cout << "[DEBUG] unlock " << m_solver.get_feasible_region_limits() << "\n";
}

template<class CSP> void
Configurator<CSP>::unlock_all() {
  auto it = m_locked_params.begin();
  while(it != m_locked_params.end()) {
    unlock_config(it->first);
    it = m_locked_params.begin();
  }
  //std::cout << "[DEBUG] " << m_solver.get_feasible_region_limits() << "\n";
  //std::cout << "solver is now (unlock): " << m_solver.m_solver << "\n";
}

template<class CSP> void
Configurator<CSP>::find_data_streams_which_support_direction(
    const data_stream_direction_t       dir,
    std::vector<data_stream_id_t>& data_streams) const {
  auto it=m_data_streams.begin();
  for(; it != m_data_streams.end(); it++) {
    if((dir == data_stream_direction_t::rx and it->get_supports_rx()) or
        (dir == data_stream_direction_t::tx and it->get_supports_tx())) {
      data_streams.push_back(it->get_data_stream_id());
    }
  }
}

template<class CSP> config_value_t 
Configurator<CSP>::get_locked_value(const char* config) {
  if(not get_config_is_locked(config)) {
    throw std::string("invalid config");
  }
  return m_locked_params.at(config).m_lock_val;
}

template<class CSP> bool
Configurator<CSP>::get_config_is_locked(const char* config) {
  bool ret = false;
  if(m_locked_params.find(config) != m_locked_params.end()) {
    ret = true;
  }
  return ret;
}

template<class CSP> const CSPSolver::FeasibleRegionLimits&
Configurator<CSP>::get_feasible_region_limits() const {
  return m_solver.get_feasible_region_limits();
}

template<class CSP> double
Configurator<CSP>::get_feasible_region_limits_min_double(const char* var) const {
  return m_solver.get_feasible_region_limits_min_double(var);
}

DataStreamConfigLockRequest::DataStreamConfigLockRequest() :
  m_including_direction          (false),
  m_including_data_stream_id     (false),
  m_including_routing_id         (false),
  m_including_tuning_freq_MHz    (false),
  m_including_bandwidth_3dB_MHz  (false),
  m_including_sampling_rate_Msps (false),
  m_including_samples_are_complex(false),
  m_including_gain_mode          (false),
  m_including_gain_dB            (false) {
}

data_stream_direction_t
DataStreamConfigLockRequest::get_direction() const {
  if(not m_including_direction) {
    throw_for_invalid_get_call("data_stream_direction");
  }
  return m_direction;
}

data_stream_id_t
DataStreamConfigLockRequest::get_data_stream_id() const {
  if(not m_including_data_stream_id) {
    throw_for_invalid_get_call("data_stream_ID");
  }
  return m_data_stream_id;
}

routing_id_t
DataStreamConfigLockRequest::get_routing_id() const {
  if(not m_including_routing_id) {
    throw_for_invalid_get_call("routing_id");
  }
  return m_routing_id;
}

config_value_t
DataStreamConfigLockRequest::get_tuning_freq_MHz() const {
  if(not m_including_tuning_freq_MHz) {
    throw_for_invalid_get_call("tuning_freq_MHz");
  }
  return m_tuning_freq_MHz;
}

config_value_t
DataStreamConfigLockRequest::get_bandwidth_3dB_MHz() const {
  if(not m_including_bandwidth_3dB_MHz) {
    throw_for_invalid_get_call("bandwidth_3dB_MHz");
  }
  return m_bandwidth_3dB_MHz;
}

config_value_t
DataStreamConfigLockRequest::get_sampling_rate_Msps() const {
  if(not m_including_sampling_rate_Msps) {
    throw_for_invalid_get_call("sampling_rate_Msps");
  }
  return m_sampling_rate_Msps;
}

bool
DataStreamConfigLockRequest::get_samples_are_complex() const {
  if(not m_including_samples_are_complex) {
    throw_for_invalid_get_call("samples_are_complex");
  }
  return m_samples_are_complex;
}

gain_mode_value_t
DataStreamConfigLockRequest::get_gain_mode() const {
  if(not m_including_gain_mode) {
    throw_for_invalid_get_call("gain_mode");
  }
  return m_gain_mode;
}

config_value_t
DataStreamConfigLockRequest::get_gain_dB() const {
  if(not m_including_gain_dB) {
    throw_for_invalid_get_call("gain_dB");
  }
  return m_gain_dB;
}

config_value_t
DataStreamConfigLockRequest::get_tolerance_tuning_freq_MHz() const {
  if(not m_including_tuning_freq_MHz) {
    throw_for_invalid_get_call("tuning_freq_MHz");
  }
  return m_tolerance_tuning_freq_MHz;
}

config_value_t
DataStreamConfigLockRequest::get_tolerance_bandwidth_3dB_MHz() const {
  if(not m_including_bandwidth_3dB_MHz) {
    throw_for_invalid_get_call("bandwidth_3dB_MHz");
  }
  return m_tolerance_bandwidth_3dB_MHz;
}

config_value_t
DataStreamConfigLockRequest::get_tolerance_sampling_rate_Msps() const {
  if(not m_including_sampling_rate_Msps) {
    throw_for_invalid_get_call("sampling_rate_Msps");
  }
  return m_tolerance_sampling_rate_Msps;
}

config_value_t
DataStreamConfigLockRequest::get_tolerance_gain_dB() const {
  if(not m_including_gain_dB) {
    throw_for_invalid_get_call("gain_dB");
  }
  return m_tolerance_gain_dB;
}

bool
DataStreamConfigLockRequest::get_including_data_stream_direction() const {
  return m_including_direction;
}

bool
DataStreamConfigLockRequest::get_including_data_stream_id() const {
  return m_including_data_stream_id;
}

bool
DataStreamConfigLockRequest::get_including_routing_id() const {
  return m_including_routing_id;
}

bool
DataStreamConfigLockRequest::get_including_tuning_freq_MHz() const {
  return m_including_tuning_freq_MHz;
}

bool
DataStreamConfigLockRequest::get_including_bandwidth_3dB_MHz() const {
  return m_including_bandwidth_3dB_MHz;
}

bool
DataStreamConfigLockRequest::get_including_sampling_rate_Msps() const {
  return m_including_sampling_rate_Msps;
}

bool
DataStreamConfigLockRequest::get_including_samples_are_complex() const {
  return m_including_samples_are_complex;
}

bool
DataStreamConfigLockRequest::get_including_gain_mode() const {
  return m_including_gain_mode;
}

bool
DataStreamConfigLockRequest::get_including_gain_dB() const {
  return m_including_gain_dB;
}

void
DataStreamConfigLockRequest::include_data_stream_direction(
    const data_stream_direction_t val) {
  m_direction = val;
  m_including_direction = true;
}

void
DataStreamConfigLockRequest::include_data_stream_id(
    const data_stream_id_t val) {
  m_data_stream_id = val;
  m_including_data_stream_id = true;
}

void
DataStreamConfigLockRequest::include_routing_id(const routing_id_t val) {
  m_routing_id = val;
  m_including_routing_id = true;
}

void
DataStreamConfigLockRequest::include_tuning_freq_MHz(const config_value_t val,
    const config_value_t tolerance) {
  m_tuning_freq_MHz           = val;
  m_tolerance_tuning_freq_MHz = tolerance;
  m_including_tuning_freq_MHz = true;
}

void
DataStreamConfigLockRequest::include_bandwidth_3dB_MHz(const config_value_t val,
    const config_value_t tolerance) {
  m_bandwidth_3dB_MHz           = val;
  m_tolerance_bandwidth_3dB_MHz = tolerance;
  m_including_bandwidth_3dB_MHz = true;
}

void
DataStreamConfigLockRequest::include_sampling_rate_Msps(
    const config_value_t val, const config_value_t tolerance) {
  m_sampling_rate_Msps           = val;
  m_tolerance_sampling_rate_Msps = tolerance;
  m_including_sampling_rate_Msps = true;
}
void
DataStreamConfigLockRequest::include_samples_are_complex(const bool val) {
  m_samples_are_complex = val;
  m_including_samples_are_complex = true;
}

void
DataStreamConfigLockRequest::include_gain_mode(const gain_mode_value_t val) {
  m_gain_mode = val;
  m_including_gain_mode = true;
}

void
DataStreamConfigLockRequest::include_gain_dB(const config_value_t val,
    const config_value_t tolerance) {
  m_gain_dB           = val;
  m_tolerance_gain_dB = tolerance;
  m_including_gain_dB = true;
}

void
DataStreamConfigLockRequest::throw_for_invalid_get_call(
    const char* config) const {
  std::ostringstream oss;
  oss << "attempted to read radio controller's config request data ";
  oss << "stream's ";
  oss << config;
  oss << ", which was never included as a part of the request";
  throw oss.str();
}

template<class L,class C>
ARC<L,C>::ARC(const char* descriptor) : m_descriptor(descriptor),
    m_cache_initialized(false) {
}

template<class L,class C> const std::string&
ARC<L,C>::get_descriptor() const {
  return m_descriptor;
}

template<class L,class C> const std::vector<ConfigLock>&
ARC<L,C>::get_config_locks() const {
  return m_config_locks;
}

template<class L,class C> void
ARC<L,C>::initialize_cache() {
  auto it = m_configurator.get_data_stream_ids().begin();
  for(; it!=m_configurator.get_data_stream_ids().end(); ++it) {
    m_cache_direction[        *it] = get_direction(        *it);
    m_cache_tuning_freq_MHz[  *it] = get_tuning_freq_MHz(  *it);
    m_cache_bandwidth_3dB_MHz[*it] = get_bandwidth_3dB_MHz(*it);
  }
}

template<class L,class C> bool
ARC<L,C>::request_config_lock(
    config_lock_id_t         config_lock_ID,
    const ConfigLockRequest& config_lock_request) {
  if(!m_cache_initialized) {
    initialize_cache();
    m_cache_initialized = true;
  }
#ifdef IS_LOCKING
  ConfigLock config_lock;
  config_lock.m_config_lock_ID = config_lock_ID;
  bool configurator_config_lock_request_was_successful = false;
  auto it = config_lock_request.m_data_streams.begin();
  for(; it != config_lock_request.m_data_streams.end(); it++) {
    throw_if_data_stream_lock_request_malformed(*it);
    std::vector<data_stream_id_t> data_streams;
    if(it->get_including_data_stream_direction()) {
      this->m_configurator.find_data_streams_which_support_direction(
          it->get_direction(), data_streams);
      if(data_streams.empty()) {
        // configurator did not have any data streams of the requested data
        // stream direction
        return false;
      }
    }
    else { // assuming including data stream ID
      data_streams.push_back(it->get_data_stream_id());
    }
    bool found_lock = false;
    auto it_found_streams = data_streams.begin();
    for(; it_found_streams != data_streams.end(); it_found_streams++) {
      found_lock |= do_min_data_stream_config_locks(*it_found_streams, *it);
      const char* ds = it_found_streams->c_str();
      if(found_lock) {
        DataStreamConfigLock lock;
        lock.m_data_stream_id    = ds;
        lock.m_direction         = it->get_direction();
        lock.m_tuning_freq_MHz   = it->get_tuning_freq_MHz();
        lock.m_bandwidth_3dB_MHz = it->get_bandwidth_3dB_MHz();
        config_lock.m_data_streams.push_back(lock);
        break;
      }
    }
    if(not found_lock) {
      configurator_config_lock_request_was_successful = false;
      break;
    }
    configurator_config_lock_request_was_successful = true;
  }
  if(configurator_config_lock_request_was_successful) {
    m_config_locks.push_back(config_lock);
    return true;
  }
  else { // unroll
    auto it = config_lock.m_data_streams.begin();
    for(; it != config_lock.m_data_streams.end(); ++it) {
      unlock_config(it->m_data_stream_id, config_key_direction);
      unlock_config(it->m_data_stream_id, config_key_tuning_freq_MHz);
      unlock_config(it->m_data_stream_id, config_key_bandwidth_3dB_MHz);
    }
  }
#endif
  return false;
}

template<class L,class C> void
ARC<L,C>::unlock_config_lock(const config_lock_id_t config_lock_ID) {
  bool found_config_lock = false;
  for(auto itcl = m_config_locks.begin(); itcl != m_config_locks.end(); itcl++){
    if(itcl->m_config_lock_ID.compare(config_lock_ID) == 0) {
      found_config_lock = true;
      auto itds = itcl->m_data_streams.begin();
      for(; itds != itcl->m_data_streams.end(); itds++) {
        unlock_config(itds->m_data_stream_id, config_key_direction);
        unlock_config(itds->m_data_stream_id, config_key_tuning_freq_MHz);
        unlock_config(itds->m_data_stream_id, config_key_bandwidth_3dB_MHz);
      }
      break;
    }
  }
  if(not found_config_lock) {
    std::ostringstream oss;
    oss << "for config unlock request, config lock ID " << config_lock_ID;
    oss << " not found";
    throw oss.str();
  }
}

template<class L,class C> void
ARC<L,C>::unlock_all() {
#ifdef IS_LOCKING
  this->m_configurator.unlock_all();
  m_config_locks.clear();
#endif
}

template<class L,class C> void
ARC<L,C>::throw_if_data_stream_lock_request_malformed(
    const DataStreamConfigLockRequest& data_stream_config_lock_request) const {
  const DataStreamConfigLockRequest& req = data_stream_config_lock_request;
  if(not req.get_including_data_stream_direction() and
     not req.get_including_data_stream_id()) {
    throw std::string("request malformed: type/id");
  }
  // note that including routing ID is not *universally* necessary, so
  // we don't check for it here (it's really only necessary for radio
  // controllers w/ multiple data streams of the same type)
  if(not req.get_including_tuning_freq_MHz()) {
    throw std::string("request malformed: did not include tuning_freq_MHz");
  }
  if(not req.get_including_bandwidth_3dB_MHz()) {
    throw std::string("request malformed: did not include bandwidth_3dB_MHz");
  }
}

template<class L,class C> bool
ARC<L,C>::lock_config(data_stream_id_t ds_id, config_value_t val,
    config_key_t cfg_key, bool do_tol, config_value_t tol) {
  // the configurator, which is a software emulation of hardware capabilties,
  // tells us whether a hardware attempt to set value will corrupt
  // any existing locks
  bool did_lock = do_tol ?
    this->m_configurator.lock_config(ds_id, cfg_key, val, tol) :
    this->m_configurator.lock_config(ds_id, cfg_key, val);
  //bool is = false; // is within tolerance
  if(did_lock) {
    config_value_t cfglval; // configurator locked value
    cfglval = this->m_configurator.get_config_locked_value(ds_id, cfg_key);
    if(cfg_key == config_key_direction) {
      if(m_cache_direction[ds_id] != (data_stream_direction_t)val) {
        //std::cout << "drc: cache invalid, upating direction\n";
        set_direction(ds_id, (data_stream_direction_t)cfglval);
        m_cache_direction[ds_id] = (data_stream_direction_t)val;
      }
    }
    else if(cfg_key == config_key_tuning_freq_MHz) {
      if(std::abs(m_cache_tuning_freq_MHz[ds_id]-val) > tol) {
        //std::cout << "drc: cache invalid, upating tuning_freq_MHz\n";
        set_tuning_freq_MHz(ds_id, cfglval);
        m_cache_tuning_freq_MHz[ds_id] = cfglval;
      }
    }
    else if(cfg_key == config_key_bandwidth_3dB_MHz) {
      if(std::abs(m_cache_bandwidth_3dB_MHz[ds_id]-val) > tol) {
        //std::cout << "drc: cache invalid, upating bandwidth_3dB_MHz\n";
        set_bandwidth_3dB_MHz(ds_id, cfglval);
        m_cache_bandwidth_3dB_MHz[ds_id] = cfglval;
      }
    }
  }
  return did_lock;
}

template<class L,class C> void
ARC<L,C>::unlock_config(const data_stream_id_t ds_id,
    const config_key_t cfg_key) {
  this->m_configurator.unlock_config(ds_id, cfg_key);
}

template<class L,class C> bool
ARC<L,C>::do_min_data_stream_config_locks(const data_stream_id_t id,
    const DataStreamConfigLockRequest& req) {
  bool ret = true;
  throw_if_data_stream_lock_request_malformed(req);
  if(ret) {
    auto val = req.get_direction();
    ret = lock_config(id, (int32_t) val, config_key_direction, false, 0);
  }
  if(ret) {
    const config_value_t& val = req.get_tuning_freq_MHz();
    const config_value_t& tol = req.get_tolerance_tuning_freq_MHz();
    if(not lock_config(id, val, config_key_tuning_freq_MHz, true, tol)) {
      // unroll
      unlock_config(id, config_key_direction);
      ret = false;
    }
  }
  if(ret) {
    const config_value_t& val = req.get_bandwidth_3dB_MHz();
    const config_value_t& tol = req.get_tolerance_bandwidth_3dB_MHz();
    if(not lock_config(id, val, config_key_bandwidth_3dB_MHz, true, tol)) {
      // unroll
      unlock_config(id, config_key_direction);
      unlock_config(id, config_key_tuning_freq_MHz);
      ret = false;
    }
  }
  return ret;
}

template<class L,class C> bool
ARC<L,C>::config_val_is_within_tolerance(config_value_t expected_val,
    config_value_t tolerance, config_value_t val) const {
  return std::abs(val - expected_val) <= tolerance;
}

template<class L,class C> void
ARC<L,C>::throw_if_data_stream_disabled_for_read(
    const data_stream_id_t& ds_id,
    const char* config_description) const {
  if(not get_enabled(ds_id)) {
    std::ostringstream oss;
    oss << "requested read of " << config_description << " for disabled ";
    oss << ds_id << " data stream";
    throw oss.str();
  }
}

template<class L,class C> void
ARC<L,C>::throw_if_data_stream_disabled_for_write(
    const data_stream_id_t& ds_id,
    const char* config_description) const {
  if(not get_enabled(ds_id)) {
    std::ostringstream oss;
    oss << "requested write of " << config_description << " for disabled ";
    oss << ds_id << " data stream";
    throw oss.str();
  }
}

template<class L,class C> void
ARC<L,C>::throw_invalid_data_stream_id(data_stream_id_t data_stream_id) const {
  throw std::string("invalid data stream id ") + data_stream_id;
}


template<class L,class C>
DRC<L,C>::DRC(const char* descriptor) : ARC<L,C>(descriptor) {
}

template<class L,class C> void
DRC<L,C>::initialize_cache() {
  ARC<L,C>::initialize_cache();
  auto it = this->m_configurator.get_data_stream_ids().begin();
  for(; it!=this->m_configurator.get_data_stream_ids().end(); ++it) {
    m_cache_sampling_rate_Msps[ *it] = get_sampling_rate_Msps( *it);
    m_cache_samples_are_complex[*it] = get_samples_are_complex(*it);
    m_cache_gain_mode[          *it] = get_gain_mode(          *it);
    m_cache_gain_dB[            *it] = get_gain_dB(            *it);
  }
#if 0
  std::cout << "drc:    **************** initializing cache\n";
  it = this->m_configurator.get_data_stream_ids().begin();
  for(; it!=this->m_configurator.get_data_stream_ids().end(); ++it) {
    std::string tmp = "rx";
    if(this->m_cache_direction[*it] == data_stream_direction_t::tx) {
      tmp = "tx";
    }
    std::cout << "cache.direction           [" << *it << "]=" << tmp                                    << "\n";
    std::cout << "cache.tuning_freq_MHz     [" << *it << "]=" << this->m_cache_tuning_freq_MHz[    *it] << "\n";
    std::cout << "cache.bandwidth_3dB_MHz   [" << *it << "]=" << this->m_cache_bandwidth_3dB_MHz[  *it] << "\n";
    std::cout << "cache.sampling_rate_Msps  [" << *it << "]=" << m_cache_sampling_rate_Msps[ *it] << "\n";
    std::cout << "cache.samples_are_complex [" << *it << "]=" << m_cache_samples_are_complex[*it] << "\n";
    std::cout << "cache.gain_mode           [" << *it << "]=" << m_cache_gain_mode[          *it] << "\n";
    std::cout << "cache.gain_dB             [" << *it << "]=" << m_cache_gain_dB[            *it] << "\n";
  }
#endif
}

template<class L,class C> bool
DRC<L,C>::request_config_lock(
    const config_lock_id_t   config_lock_ID,
    const ConfigLockRequest& config_lock_request) {
  if(!this->m_cache_initialized) {
    initialize_cache();
    this->m_cache_initialized = true;
  }
#ifdef IS_LOCKING
  ///@TODO probably want to add back the readback check for ensuring tolerance requirements are met (e.g. No-OS tx_attenuation)
  ConfigLock config_lock;
  config_lock.m_config_lock_ID = config_lock_ID;
  bool configurator_config_lock_request_was_successful = false;
  auto it = config_lock_request.m_data_streams.begin();
  for(; it != config_lock_request.m_data_streams.end(); it++) {
    throw_if_data_stream_lock_request_malformed(*it);
    std::vector<data_stream_id_t> data_streams;
    if(it->get_including_data_stream_direction()) {
      if(it->get_including_data_stream_id()) {
        data_streams.push_back(it->get_data_stream_id());
      }
      else {
        this->m_configurator.find_data_streams_which_support_direction(
            it->get_direction(), data_streams);
        if(data_streams.empty()) {
          // configurator did not have any data streams of the requested data
          // stream type
          return false;
        }
      }
    }
    else {
      data_streams.push_back(it->get_data_stream_id());
    }
    bool found_lock = false;
    auto it_found_streams = data_streams.begin();
    for(; it_found_streams != data_streams.end(); it_found_streams++) {
      if(not this->get_enabled(*it_found_streams)) {
        if(it->get_including_data_stream_id()) {
          std::ostringstream oss;
          oss << "requested config lock specifically for data stream ID ";
          oss << it_found_streams->c_str() << ", which is not currently ";
          oss << "enabled";
          throw oss.str();
        }
        continue;
      }
      found_lock |= do_min_data_stream_config_locks(*it_found_streams, *it);
      const char* ds = it_found_streams->c_str();
      if(found_lock) {
        //printf("data stream %s met data stream config lock request requirements\n", ds);
        DataStreamConfigLock lock;
        lock.m_data_stream_id      = ds;
        lock.m_direction           = it->get_direction();
        lock.m_tuning_freq_MHz     = it->get_tuning_freq_MHz();
        lock.m_bandwidth_3dB_MHz   = it->get_bandwidth_3dB_MHz();
        lock.m_sampling_rate_Msps  = it->get_sampling_rate_Msps();
        lock.m_samples_are_complex = it->get_samples_are_complex();
        if(it->get_including_gain_mode()) {
          lock.m_gain_mode         = it->get_gain_mode();
          lock.m_including_gain_mode = true;
        }
        else {
          lock.m_including_gain_mode = false;
        }
        if(it->get_including_gain_dB()) {
          lock.m_gain_dB           = it->get_gain_dB();
          lock.m_including_gain_dB = true;
        }
        else {
          lock.m_including_gain_dB = false;
        }
        config_lock.m_data_streams.push_back(lock);
        break;
      }
      //printf("data stream %s did not meet data stream config lock request requirements\n", ds);
    }
    if(not found_lock) {
      configurator_config_lock_request_was_successful = false;
      break;
    }
    configurator_config_lock_request_was_successful = true;
  }
  if(configurator_config_lock_request_was_successful) {
    //printf("request config lock %s succeeded\n", config_lock_ID.c_str());
    this->m_config_locks.push_back(config_lock);
    //std::cout << "drc: add    config_lock: id=" << config_lock_ID << "\n";
    return true;
  }
  else { // unroll
    auto it = config_lock.m_data_streams.begin();
    for(; it != config_lock.m_data_streams.end(); ++it) {
      this->unlock_config(it->m_data_stream_id, config_key_direction);
      this->unlock_config(it->m_data_stream_id, config_key_tuning_freq_MHz);
      this->unlock_config(it->m_data_stream_id, config_key_bandwidth_3dB_MHz);
      this->unlock_config(it->m_data_stream_id, config_key_sampling_rate_Msps);
      this->unlock_config(it->m_data_stream_id, config_key_samples_are_complex);
      if(it->m_including_gain_mode) {
        this->unlock_config(it->m_data_stream_id, config_key_gain_mode);
      }
      if(it->m_including_gain_dB) {
        this->unlock_config(it->m_data_stream_id, config_key_gain_dB);
      }
    }
  }
#endif
  return false;
}

template<class L,class C> void
DRC<L,C>::unlock_config_lock(const config_lock_id_t config_lock_ID) {
#ifdef IS_LOCKING
  //std::cout << "drc: unlock_config_lock: id=" << config_lock_ID << "\n";
  bool found_config_lock = false;
  auto itcl = this->m_config_locks.begin();
  for(; itcl != this->m_config_locks.end(); itcl++) {
    if(itcl->m_config_lock_ID.compare(config_lock_ID) == 0) {
      //std::cout << "drc: unlock_config_lock: found id=" << config_lock_ID << "\n";
      found_config_lock = true;
      auto itds = itcl->m_data_streams.begin();
      for(; itds != itcl->m_data_streams.end(); itds++) {
        this->unlock_config(  itds->m_data_stream_id, config_key_direction);
        this->unlock_config(  itds->m_data_stream_id, config_key_tuning_freq_MHz);
        this->unlock_config(  itds->m_data_stream_id, config_key_bandwidth_3dB_MHz);
        this->unlock_config(  itds->m_data_stream_id, config_key_sampling_rate_Msps);
        this->unlock_config(  itds->m_data_stream_id, config_key_samples_are_complex);
        if(itds->m_including_gain_mode) {
          this->unlock_config(itds->m_data_stream_id, config_key_gain_mode);
        }
        if(itds->m_including_gain_dB) {
          this->unlock_config(itds->m_data_stream_id, config_key_gain_dB);
        }
      }
      this->m_config_locks.erase(itcl);
      break;
    }
  }
  if(not found_config_lock) {
    std::ostringstream oss;
    oss << "for config unlock request, config lock ID " << config_lock_ID;
    oss << " not found";
    throw oss.str();
  }
#endif
}

template<class L,class C> bool
DRC<L,C>::lock_config(data_stream_id_t ds_id, config_value_t val,
    config_key_t cfg, bool do_tol, config_value_t tol) {
  bool did_lock = false;
#ifdef IS_LOCKING
  // the configurator, which is a software emulation of hardware capabilties,
  // tells us whether a hardware attempt to set value will corrupt
  // any existing locks
  did_lock = do_tol ?
    this->m_configurator.lock_config(ds_id, cfg, val, tol) :
    this->m_configurator.lock_config(ds_id, cfg, val);
  if(did_lock) {
#if 0
    std::ostringstream oss;
    oss << "configurator: lock succeeded for config " << cfg;
    oss << " for requested value of " << val << " with tolerance of +/- ";
    oss << tol << "\n";
    printf(oss.str().c_str());
#endif
    config_value_t cfglval;
    cfglval = this->m_configurator.get_config_locked_value(ds_id, cfg);
    if(cfg == config_key_sampling_rate_Msps) {
      if(std::abs(m_cache_sampling_rate_Msps[ds_id]-cfglval) > tol) {
        //std::cout << "drc: cache invalid, upating sampling_rate_Msps\n";
        set_sampling_rate_Msps(ds_id, cfglval);
        m_cache_sampling_rate_Msps[ds_id] = cfglval;
      }
    }
    else if(cfg == config_key_samples_are_complex) {
      bool tmp = (((int32_t)cfglval) == 1);
      if(m_cache_samples_are_complex[ds_id] != tmp) {
        //std::cout << "drc: cache invalid, upating samples_are_complex\n";
        set_samples_are_complex(ds_id, tmp);
        m_cache_samples_are_complex[ds_id] = tmp;
      }
    }
    else if(cfg == config_key_gain_mode) {
      //auto agc = gain_mode_value_t::agc;
      //auto man = gain_mode_value_t::manual;
      gain_mode_value_t tmp = (((int32_t)cfglval) == 0 ? "agc" : "manual");
      if(m_cache_gain_mode[ds_id] != tmp) {
        //std::cout << "drc: cache invalid, upating gain_mode\n";
        set_gain_mode(ds_id, tmp);
        m_cache_gain_mode[ds_id] = tmp;
      }
    }
    else if(cfg == config_key_gain_dB) {
      if(std::abs(m_cache_gain_dB[ds_id]-cfglval) > tol) {
        //std::cout << "drc: cache invalid, upating gain_dB\n";
        set_gain_dB(ds_id, cfglval);
        m_cache_gain_dB[ds_id] = cfglval;
      }
    }
  }
#if 0
  else {
    std::ostringstream oss;
    oss << "configurator: lock failed for config " << cfg;
    oss << " for attempted lock value of " << val;
    oss << " with tolerance of +/- " << tol << "\n";
    printf(oss.str().c_str());
  }
#endif
#endif // IS_LOCKING
  return did_lock;
}

template<class L,class C> bool
DRC<L,C>::do_min_data_stream_config_locks(const data_stream_id_t id,
    const DataStreamConfigLockRequest& req) {
#ifdef IS_LOCKING
  throw_if_data_stream_lock_request_malformed(req);
  // first perform all the analog-specific config locks
  bool ret = ARC<L,C>::do_min_data_stream_config_locks(id, req);
  // second perform all the digital-specific config locks
  if(ret) {
    config_value_t val = req.get_sampling_rate_Msps();
    config_value_t tol = req.get_tolerance_sampling_rate_Msps();
    if(not lock_config(id, val, config_key_sampling_rate_Msps, true, tol)) {
      // unroll
      this->unlock_config(id, config_key_direction);
      this->unlock_config(id, config_key_tuning_freq_MHz);
      this->unlock_config(id, config_key_bandwidth_3dB_MHz);
      ret = false;
    }
  }
  if(ret) {
    config_value_t val = (config_value_t)req.get_samples_are_complex();
    if(not lock_config(id, val, config_key_samples_are_complex, false, 0)) {
      // unroll
      this->unlock_config(id, config_key_direction);
      this->unlock_config(id, config_key_tuning_freq_MHz);
      this->unlock_config(id, config_key_bandwidth_3dB_MHz);
      this->unlock_config(id, config_key_sampling_rate_Msps);
      ret = false;
    }
  }
  if(ret && req.get_including_gain_mode()) {
    config_value_t val = req.get_gain_mode() == "agc" ? 0 : 1;
    if(not lock_config(id, val, config_key_gain_mode, false, 0)) {
      this->unlock_config(id, config_key_direction);
      this->unlock_config(id, config_key_tuning_freq_MHz);
      this->unlock_config(id, config_key_bandwidth_3dB_MHz);
      this->unlock_config(id, config_key_sampling_rate_Msps);
      this->unlock_config(id, config_key_samples_are_complex);
      ret = false;
    }
  }
  if(ret && req.get_including_gain_dB()) {
    config_value_t val = req.get_gain_dB();
    config_value_t tol = req.get_tolerance_gain_dB();
    if(not lock_config(id, val, config_key_gain_dB, true, tol)) {
      this->unlock_config(id, config_key_direction);
      this->unlock_config(id, config_key_tuning_freq_MHz);
      this->unlock_config(id, config_key_bandwidth_3dB_MHz);
      this->unlock_config(id, config_key_sampling_rate_Msps);
      this->unlock_config(id, config_key_samples_are_complex);
      this->unlock_config(id, config_key_gain_mode);
      ret = false;
    }
  }
  //std::cout << "[INFO] " << m_solver.get_feasible_region_limits() << "\n";
#endif
  return ret;
}

template<class L,class C> void
DRC<L,C>::throw_if_data_stream_lock_request_malformed(
    const DataStreamConfigLockRequest& req) const {
  // first check all the analog-specific config locks
  ARC<L,C>::throw_if_data_stream_lock_request_malformed(req);
  // second check all the digital-specific config locks
  if(not req.get_including_sampling_rate_Msps()) {
    throw std::string("DRC request malformed: missing sampling_rate_Msps");
  }
  if(not req.get_including_samples_are_complex()) {
    throw std::string("DRC request malformed: missing samples_are_complex");
  }
  if(req.get_including_gain_dB()) {
    if(not req.get_including_gain_mode()) {
      throw std::string("DRC request malformed: included gain_dB, not mode");
    }
    else if(req.get_gain_mode() == "agc") {//gain_mode_value_t::agc)
      throw std::string("DRC request malformed: included gain_dB, not manual");
    }
  }
}

template<class L,class C> bool
DRC<L,C>::prepare(unsigned config, const ConfigLockRequest& req) {
  //std::cout << "drc: prepare: config " << config << "\n";
  bool ret = request_config_lock(std::to_string(config), req);
  this->m_requests[config] = req;
  return ret;
}

template<class L,class C> bool
DRC<L,C>::start(unsigned config) {
  bool ret = true;
  //std::cout << "drc: start: config " << config << "\n";
  auto it = this->m_config_locks.begin();
  for(; it != this->m_config_locks.end(); ++it) {
    bool prepared = !(it->m_config_lock_ID.compare(std::to_string(config)));
    if(!prepared) {
      ret = this->prepare(config, this->m_requests[config]);
      break;
    }
  }
  //std::cout << "drc: start: config " << config << " ret = " << (ret ? "tt" : "ff") << "\n";
  return ret;
}

template<class L,class C> bool
DRC<L,C>::stop(unsigned /*config*/) {
  //std::cout << "drc: stop: config " << config << "\n";
  return true;
}

template<class L,class C> bool
DRC<L,C>::release(unsigned config) {
  //std::cout << "drc: release: config " << config << "\n";
  auto it = this->m_config_locks.begin();
  for(; it != this->m_config_locks.end(); ++it) {
    //std::cout << "drc: release: config_lock_ID = " << it->m_config_lock_ID << "\n";
    bool config_prepared = !(it->m_config_lock_ID.compare(std::to_string(config)));
    if(config_prepared) {
      this->unlock_config_lock(std::to_string(config));
      break;
    }
  }
  return stop(config);
}

} // namespace DRC
