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

#ifndef _FMCOMMS2_3_DRC_HH
#define _FMCOMMS2_3_DRC_HH

#include "AD9361DRC.hh"

namespace DRC {

// -----------------------------------------------------------------------------
// STEP 1 - IF IS_LOCKING SUPPORTED,
//          DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class FMCOMMS2_3CSP : public AD9361CSP {
  protected:
  typedef CSPSolver::Constr::Cond Cond;
  typedef CSPSolver::Constr::Func Func;
  /* @brief for the FMCOMMS2_3,
   *        define variables (X) and their domains (D) for <X,D,C> which
   *        comprises its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void define_x_d_fmcomms2_3() {
    // N/A
    m_solver.add_var<int32_t>("fmcomms_num");
    m_solver.add_var<double>("fmcomms2_fc_baluns_meghz", dfp_tol);
    // direction
    m_solver.add_var<int32_t>("fmcomms2_3_dir_rx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_dir_rx2a");
    m_solver.add_var<int32_t>("fmcomms2_3_dir_tx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_dir_tx2a");
    // tuning_freq_MHz
    m_solver.add_var<double>("fmcomms2_3_fc_meghz_rx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fc_meghz_rx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fc_meghz_tx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fc_meghz_tx2a", dfp_tol);
    // bandwidth_3dB_MHz
    m_solver.add_var<double>("fmcomms2_3_bw_meghz_rx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_bw_meghz_rx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_bw_meghz_tx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_bw_meghz_tx2a", dfp_tol);
    // sampling_rate_Msps
    m_solver.add_var<double>("fmcomms2_3_fs_megsps_rx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fs_megsps_rx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fs_megsps_tx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fs_megsps_tx2a", dfp_tol);
    // samples_are_complex
    m_solver.add_var<int32_t>("fmcomms2_3_samps_comp_rx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_samps_comp_rx2a");
    m_solver.add_var<int32_t>("fmcomms2_3_samps_comp_tx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_samps_comp_tx2a");
    // gain_mode
    m_solver.add_var<int32_t>("fmcomms2_3_gain_mode_rx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_gain_mode_rx2a");
    m_solver.add_var<int32_t>("fmcomms2_3_gain_mode_tx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_gain_mode_tx2a");
    // gain_dB
    m_solver.add_var<double>("fmcomms2_3_gain_db_rx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_gain_db_rx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_gain_db_tx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_gain_db_tx2a", dfp_tol);
  }
  /* @brief for the AD9361,
   *        define constraints (C) for <X,D,C> which
   *        comprise its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void define_c_fmcomms2_3() {
    // N/A
    m_solver.add_constr("fmcomms_num", ">=", (int32_t)2);
    m_solver.add_constr("fmcomms_num", "<=", (int32_t)3);
    m_solver.add_constr("fmcomms2_fc_baluns_meghz", ">=", 2400.);
    m_solver.add_constr("fmcomms2_fc_baluns_meghz", "<=", 2500.);
    // direction
    m_solver.add_constr("fmcomms2_3_dir_rx1a", "=", "ad9361_dir_rx1");
    m_solver.add_constr("fmcomms2_3_dir_rx2a", "=", "ad9361_dir_rx2");
    m_solver.add_constr("fmcomms2_3_dir_tx1a", "=", "ad9361_dir_tx1");
    m_solver.add_constr("fmcomms2_3_dir_tx2a", "=", "ad9361_dir_tx2");
    // tuning_freq_MHz (fmcomms2)
    //  @TODO add 'intersected with' functionality
    m_solver.add_constr("fmcomms2_3_fc_meghz_rx1a", "=", "ad9361_fc_meghz_rx1");//, intersected with fmcomms2_fc_baluns_meghz
    m_solver.add_constr("fmcomms2_3_fc_meghz_rx2a", "=", "ad9361_fc_meghz_rx2");//, intersected with fmcomms2_fc_baluns_meghz
    m_solver.add_constr("fmcomms2_3_fc_meghz_tx1a", "=", "ad9361_fc_meghz_tx1");//, intersected with fmcomms2_fc_baluns_meghz
    m_solver.add_constr("fmcomms2_3_fc_meghz_tx2a", "=", "ad9361_fc_meghz_tx2");//, intersected with fmcomms2_fc_baluns_meghz
    // tuning_freq_MHz (fmcomms3)
    m_solver.add_constr("fmcomms2_3_fc_meghz_rx1a", "=", "ad9361_fc_meghz_rx1");
    m_solver.add_constr("fmcomms2_3_fc_meghz_rx2a", "=", "ad9361_fc_meghz_rx2");
    m_solver.add_constr("fmcomms2_3_fc_meghz_tx1a", "=", "ad9361_fc_meghz_tx1");
    m_solver.add_constr("fmcomms2_3_fc_meghz_tx2a", "=", "ad9361_fc_meghz_tx2");
    // bandwidth_3dB_MHz
    m_solver.add_constr("fmcomms2_3_bw_meghz_rx1a", "=", "ad9361_bw_meghz_rx1");
    m_solver.add_constr("fmcomms2_3_bw_meghz_rx2a", "=", "ad9361_bw_meghz_rx2");
    m_solver.add_constr("fmcomms2_3_bw_meghz_tx1a", "=", "ad9361_bw_meghz_tx1");
    m_solver.add_constr("fmcomms2_3_bw_meghz_tx2a", "=", "ad9361_bw_meghz_tx2");
    // sampling_rate_Msps
    m_solver.add_constr("fmcomms2_3_fs_megsps_rx1a", "=", "ad9361_fs_megsps_rx1");
    m_solver.add_constr("fmcomms2_3_fs_megsps_rx2a", "=", "ad9361_fs_megsps_rx2");
    m_solver.add_constr("fmcomms2_3_fs_megsps_tx1a", "=", "ad9361_fs_megsps_tx1");
    m_solver.add_constr("fmcomms2_3_fs_megsps_tx2a", "=", "ad9361_fs_megsps_tx2");
    // samples_are_complex
    m_solver.add_constr("fmcomms2_3_samps_comp_rx1a", "=", "ad9361_samps_comp_rx1");
    m_solver.add_constr("fmcomms2_3_samps_comp_rx2a", "=", "ad9361_samps_comp_rx2");
    m_solver.add_constr("fmcomms2_3_samps_comp_tx1a", "=", "ad9361_samps_comp_tx1");
    m_solver.add_constr("fmcomms2_3_samps_comp_tx2a", "=", "ad9361_samps_comp_tx2");
    // gain_mode
    m_solver.add_constr("fmcomms2_3_gain_mode_rx1a", "=", "ad9361_gain_mode_rx1");
    m_solver.add_constr("fmcomms2_3_gain_mode_rx2a", "=", "ad9361_gain_mode_rx2");
    m_solver.add_constr("fmcomms2_3_gain_mode_tx1a", "=", "ad9361_gain_mode_tx1");
    m_solver.add_constr("fmcomms2_3_gain_mode_tx2a", "=", "ad9361_gain_mode_rx2");
    // gain_dB
    m_solver.add_constr("fmcomms2_3_gain_db_rx1a", "=", "ad9361_gain_db_rx1");
    m_solver.add_constr("fmcomms2_3_gain_db_rx2a", "=", "ad9361_gain_db_rx2");
    m_solver.add_constr("fmcomms2_3_gain_db_tx1a", "=", "ad9361_gain_db_tx1");
    m_solver.add_constr("fmcomms2_3_gain_db_tx2a", "=", "ad9361_gain_db_tx2");
  }
  public:
  FMCOMMS2_3CSP() : AD9361CSP() {
    define();
    //std::cout << "[INFO] " << get_feasible_region_limits() << "\n";
  }
  void connect_fmcomms2_3_to_ad9361() {
    define_c_fmcomms2_3();
  }
  /* @brief instance FMCOMMS2/3
   *        by defining its Constraint Satisfaction Problem (CSP) as <X,D,C>
   ****************************************************************************/
  void instance_fmcomms2_3() {
    instance_ad9361();
    define_x_d_fmcomms2_3();
    connect_fmcomms2_3_to_ad9361();
  }
  /// @brief define Constraint Satisfaction Problem (CSP)
  void define() {
    instance_fmcomms2_3();
  }
}; // class FMCOMMS2_3CSP
#endif

// -----------------------------------------------------------------------------
// STEP 2 - IF IS_LOCKING SUPPORTED, DEFINE CONFIGURATOR THAT UTILIZES THE CSP
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class FMCOMMS2_3Configurator : public Configurator<FMCOMMS2_3CSP> {
  public:
  FMCOMMS2_3Configurator(int32_t fmcomms_num) : Configurator<FMCOMMS2_3CSP>() {
    ///@TODO / FIXME - add below line
    //m_solver.add_constr("fmcomms_num", "=", (int32_t)fmcomms_num);
    {
      DataStream::CSPVarMap map;
      map.insert(std::make_pair(config_key_tuning_freq_MHz.c_str(),
          "fmcomms2_3_fc_meghz_rx1a"));
      map.insert(std::make_pair(config_key_bandwidth_3dB_MHz.c_str(),
          "fmcomms2_3_bw_meghz_rx1a"));
      map.insert(std::make_pair(config_key_sampling_rate_Msps.c_str(),
          "fmcomms2_3_fs_megsps_rx1a"));
      map.insert(std::make_pair(config_key_samples_are_complex.c_str(),
          "fmcomms2_3_samps_comp_rx1a"));
      map.insert(std::make_pair(config_key_gain_mode.c_str(),
          "fmcomms2_3_gain_mode_rx1a"));
      map.insert(std::make_pair(config_key_gain_dB.c_str(),
          "fmcomms2_3_gain_db_rx1a"));
      add_data_stream(DataStream("rx1a", true, false, map));
    }
    {
      DataStream::CSPVarMap map;
      map.insert(std::make_pair(config_key_tuning_freq_MHz.c_str(),
          "fmcomms2_3_fc_meghz_rx2a"));
      map.insert(std::make_pair(config_key_bandwidth_3dB_MHz.c_str(),
          "fmcomms2_3_bw_meghz_rx2a"));
      map.insert(std::make_pair(config_key_sampling_rate_Msps.c_str(),
          "fmcomms2_3_fs_megsps_rx2a"));
      map.insert(std::make_pair(config_key_samples_are_complex.c_str(),
          "fmcomms2_3_samps_comp_rx2a"));
      map.insert(std::make_pair(config_key_gain_mode.c_str(),
          "fmcomms2_3_gain_mode_rx2a"));
      map.insert(std::make_pair(config_key_gain_dB.c_str(),
          "fmcomms2_3_gain_db_rx2a"));
      add_data_stream(DataStream("rx2a", true, false, map));
    }
    {
      DataStream::CSPVarMap map;
      map.insert(std::make_pair(config_key_tuning_freq_MHz.c_str(),
          "fmcomms2_3_fc_meghz_tx1a"));
      map.insert(std::make_pair(config_key_bandwidth_3dB_MHz.c_str(),
          "fmcomms2_3_bw_meghz_tx1a"));
      map.insert(std::make_pair(config_key_sampling_rate_Msps.c_str(),
          "fmcomms2_3_fs_megsps_tx1a"));
      map.insert(std::make_pair(config_key_samples_are_complex.c_str(),
          "fmcomms2_3_samps_comp_tx1a"));
      map.insert(std::make_pair(config_key_gain_mode.c_str(),
          "fmcomms2_3_gain_mode_tx1a"));
      map.insert(std::make_pair(config_key_gain_dB.c_str(),
          "fmcomms2_3_gain_db_tx1a"));
      add_data_stream(DataStream("tx1a", false, true, map));
    }
    {
      DataStream::CSPVarMap map;
      map.insert(std::make_pair(config_key_tuning_freq_MHz.c_str(),
          "fmcomms2_3_fc_meghz_tx2a"));
      map.insert(std::make_pair(config_key_bandwidth_3dB_MHz.c_str(),
          "fmcomms2_3_bw_meghz_tx2a"));
      map.insert(std::make_pair(config_key_sampling_rate_Msps.c_str(),
          "fmcomms2_3_fs_megsps_tx2a"));
      map.insert(std::make_pair(config_key_samples_are_complex.c_str(),
          "fmcomms2_3_samps_comp_tx2a"));
      map.insert(std::make_pair(config_key_gain_mode.c_str(),
          "fmcomms2_3_gain_mode_tx2a"));
      map.insert(std::make_pair(config_key_gain_dB.c_str(),
          "fmcomms2_3_gain_db_tx2a"));
      add_data_stream(DataStream("tx2a", false, true, map));
    }
  }
}; // class FMCOMMS2_3Configurator
#endif

// -----------------------------------------------------------------------------
// STEP 3 - DEFINE DRC (get/set APIs)
// -----------------------------------------------------------------------------

//#ifdef IS_LOCKING
#define FMCOMMS2_3_CONFIGURATOR FMCOMMS2_3Configurator
//#else
//#define FMCOMMS2_3_CONFIGURATOR Configurator<CSPBase>
//#endif

template<class log_t, class s_cfg_t, class s_ds_t, class cfgrtr_t = FMCOMMS2_3_CONFIGURATOR>
class FMCOMMS2_3DRC : public AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t> {
  protected:
  /// @brief name of the data stream that corresponds to FMCOMMS2/3 RX1A channel
  const char* m_ds_rx1a;
  const char* m_ds_rx2a;
  const char* m_ds_tx1a;
  const char* m_ds_tx2a;
  public:
  FMCOMMS2_3DRC<log_t, s_cfg_t, s_ds_t, cfgrtr_t>(s_cfg_t& slave_cfg,
      s_ds_t& slave_data_sub, double fref_hz, int32_t fmcomms_num, const char* rx1a = "rx1a",
      const char* rx2a = "rx2a",
      const char* tx1a = "tx1a", const char* tx2a = "tx2a",
      const char* descriptor = "FMCOMMS2_3") :
      AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>(slave_cfg,slave_data_sub,descriptor),
      m_ds_rx1a(rx1a), m_ds_rx2a(rx2a), m_ds_tx1a(tx1a), m_ds_tx2a(tx2a),
      AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::m_configurator(fmcomms_num) {
  }
  /* @brief this is what maps, for the DRC, the AD9361 channels to
   *         the FMCOMMS2/3 channels
   ****************************************************************************/
  const char* get_ad9361_ds_id(data_stream_id_t id) const {
    return id==m_ds_rx1a ? "rx1" :  id==m_ds_rx1a ? "rx2" : id==m_ds_rx1a ? "tx1" : id==m_ds_rx1a ? "tx2" : "rx1"; 
  }
  data_stream_direction_t get_data_stream_direction(data_stream_id_t id) {
    data_stream_direction_t ret = data_stream_direction_t::tx;
    if((id==m_ds_rx1a) or (id==m_ds_rx2a)) {
      ret = data_stream_direction_t::rx;
    }
    return ret;
  }
  config_value_t get_tuning_freq_MHz(data_stream_id_t data_stream_id) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::get_tuning_freq_MHz(get_ad9361_ds_id(data_stream_id));
  }
  config_value_t get_bandwidth_3dB_MHz(data_stream_id_t data_stream_id) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::get_bandwidth_3dB_MHz(get_ad9361_ds_id(data_stream_id));
  }
  config_value_t get_sampling_rate_Msps(data_stream_id_t data_stream_id) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::get_sampling_rate_Msps(get_ad9361_ds_id(data_stream_id));
  }
  bool get_samples_are_complex(data_stream_id_t data_stream_id) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::get_samples_are_complex(get_ad9361_ds_id(data_stream_id));
  }
  gain_mode_value_t get_gain_mode(data_stream_id_t data_stream_id) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::get_gain_mode(get_ad9361_ds_id(data_stream_id));
  }
  config_value_t get_gain_dB(data_stream_id_t data_stream_id) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::get_gain_dB(get_ad9361_ds_id(data_stream_id));
  }
  void set_data_stream_direction(data_stream_id_t data_stream_id,
      data_stream_direction_t val) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::set_data_stream_direction(get_ad9361_ds_id(data_stream_id),val);
  }
  void set_tuning_freq_MHz(data_stream_id_t data_stream_id,
      config_value_t val) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::set_tuning_freq_MHz(get_ad9361_ds_id(data_stream_id),val);
  }
  void set_bandwidth_3dB_MHz(data_stream_id_t data_stream_id,
      config_value_t val) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::set_bandwidth_3dB_MHz(get_ad9361_ds_id(data_stream_id),val);
  }
  void set_sampling_rate_Msps(
      data_stream_id_t data_stream_id, config_value_t val) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::set_sampling_rate_Msps(get_ad9361_ds_id(data_stream_id),val);
  }
  void set_samples_are_complex(data_stream_id_t data_stream_id,
      bool val) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::set_samples_are_complex(get_ad9361_ds_id(data_stream_id),val);
  }
  void set_gain_mode(data_stream_id_t data_stream_id,
      gain_mode_value_t val) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::set_gain_mode(get_ad9361_ds_id(data_stream_id),val);
  }
  void set_gain_dB(data_stream_id_t data_stream_id,
      config_value_t val) {
    return AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::set_gain_dB(get_ad9361_ds_id(data_stream_id),val);
  }
}; // class FMCOMMS2_3DRC

} // namespace DRC

#endif // _FMCOMMS2_3_DRC_HH
