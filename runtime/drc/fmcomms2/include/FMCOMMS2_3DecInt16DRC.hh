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

#ifndef _FMCOMMS2_3_DEC_INT16_HH
#define _FMCOMMS2_3_DEC_INT16_HH

// define any of the following for debugging purposes
//#define DISABLE_AD9361 // remove hardware actuation, useful for testing

#include <iostream>
#include <unistd.h> // usleep()
#include <cinttypes> // PRI...
#include <cmath> // std::round
#include "DRC.hh"
#include "LogForwarder.hh"
#include "FMCOMMS2_3DRC.hh"
#ifndef DISABLE_AD9361
#include "RCC_Worker.h" // OCPI::RCC::RCCUserSlave
#endif

#ifndef DISABLE_AD9361
extern "C" {
#include "config.h"
#include "ad9361_api.h"
#include "ad9361.h"
#include "parameters.h"
int32_t spi_init(OCPI::RCC::RCCUserSlave* _slave);
}
#endif

namespace DRC {

// -----------------------------------------------------------------------------
// STEP 1 - IF IS_LOCKING SUPPORTED,
//          DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class FMCOMMS2_3DecInt16CSP : public CSPBase {
  protected:
  typedef CSPSolver::Constr::Cond Cond;
  typedef CSPSolver::Constr::Func Func;
  /* @brief define variables (X) and their domains (D) for <X,D,C> which
   *        comprises its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void
  define_x_d() {
    m_solver.add_var<int32_t>("fmcomms_num");
    m_solver.add_var<double>("fmcomms2_3_rx_rfpll_lo_freq_meghz", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_tx_rfpll_lo_freq_meghz", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_rx_sampl_freq_meghz", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_tx_sampl_freq_meghz", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_rx_rf_bandwidth_meghz", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_tx_rf_bandwidth_meghz", dfp_tol);
    //m_solver.add_var<int32_t>("fmcomms2_3_dac_clk_divider");
    m_solver.add_var<int32_t>("fmcomms2_3_dir_rx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_dir_rx2a");
    m_solver.add_var<int32_t>("fmcomms2_3_dir_tx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_dir_tx2a");
    m_solver.add_var<double>("fmcomms2_3_fc_meghz_rx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fc_meghz_rx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fc_meghz_tx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fc_meghz_tx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_bw_meghz_rx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_bw_meghz_rx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_bw_meghz_tx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_bw_meghz_tx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fs_megsps_rx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fs_megsps_rx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fs_megsps_tx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_fs_megsps_tx2a", dfp_tol);
    m_solver.add_var<int32_t>("fmcomms2_3_samps_comp_rx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_samps_comp_rx2a");
    m_solver.add_var<int32_t>("fmcomms2_3_samps_comp_tx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_samps_comp_tx2a");
    m_solver.add_var<int32_t>("fmcomms2_3_gain_mode_rx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_gain_mode_rx2a");
    m_solver.add_var<int32_t>("fmcomms2_3_gain_mode_tx1a");
    m_solver.add_var<int32_t>("fmcomms2_3_gain_mode_tx2a");
    m_solver.add_var<double>("fmcomms2_3_gain_db_rx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_gain_db_rx2a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_gain_db_tx1a", dfp_tol);
    m_solver.add_var<double>("fmcomms2_3_gain_db_tx2a", dfp_tol);
  }
  /* @brief define constraints (C) for <X,D,C> which
   *        comprise its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void
  define_c() {
    double rr = 16.; // cic_dec and cic_int interpolation factor (R)
    double fmin = 2.083334/rr;
    ///@TODO / FIXME account for CMOS mode which is limited to 30.72 Msps
    double fmax = 61.44/rr;
    ///@TODO / FIXME extend range in below 4 constraints
    m_solver.add_constr("fmcomms2_3_rx_rfpll_lo_freq_meghz", ">=", 70.);//-fmin);
    m_solver.add_constr("fmcomms2_3_rx_rfpll_lo_freq_meghz", "<=", 6000.);//+fmin);
    m_solver.add_constr("fmcomms2_3_tx_rfpll_lo_freq_meghz", ">=", 70.);//-fmin);
    m_solver.add_constr("fmcomms2_3_tx_rfpll_lo_freq_meghz", "<=", 6000.);//+fmin);
    m_solver.add_constr("fmcomms2_3_rx_rf_bandwidth_meghz", ">=", 0.4/rr);
    m_solver.add_constr("fmcomms2_3_rx_rf_bandwidth_meghz", "<=", 56./rr);
    m_solver.add_constr("fmcomms2_3_tx_rf_bandwidth_meghz", ">=", 1.25/rr);
    m_solver.add_constr("fmcomms2_3_tx_rf_bandwidth_meghz", "<=", 40./rr);
    m_solver.add_constr("fmcomms2_3_rx_sampl_freq_meghz", ">=", fmin);
    m_solver.add_constr("fmcomms2_3_rx_sampl_freq_meghz", "<=", fmax);
    m_solver.add_constr("fmcomms2_3_tx_sampl_freq_meghz", ">=", fmin);
    m_solver.add_constr("fmcomms2_3_tx_sampl_freq_meghz", "<=", fmax);
    //m_solver.add_constr("fmcomms2_3_dac_clk_divider", ">=", (int32_t)1);
    //m_solver.add_constr("fmcomms2_3_dac_clk_divider", "<=", (int32_t)2);
    m_solver.add_constr("fmcomms2_3_dir_rx1a", "=", (int32_t)data_stream_direction_t::rx);
    m_solver.add_constr("fmcomms2_3_dir_rx2a", "=", (int32_t)data_stream_direction_t::rx);
    m_solver.add_constr("fmcomms2_3_dir_tx1a", "=", (int32_t)data_stream_direction_t::tx);
    m_solver.add_constr("fmcomms2_3_dir_tx2a", "=", (int32_t)data_stream_direction_t::tx);
    m_solver.add_constr("fmcomms2_3_fc_meghz_rx1a", "=", "fmcomms2_3_rx_rfpll_lo_freq_meghz");
    m_solver.add_constr("fmcomms2_3_fc_meghz_rx2a", "=", "fmcomms2_3_rx_rfpll_lo_freq_meghz");
    m_solver.add_constr("fmcomms2_3_fc_meghz_tx1a", "=", "fmcomms2_3_tx_rfpll_lo_freq_meghz");
    m_solver.add_constr("fmcomms2_3_fc_meghz_tx2a", "=", "fmcomms2_3_tx_rfpll_lo_freq_meghz");
    m_solver.add_constr("fmcomms2_3_bw_meghz_rx1a", "=", "fmcomms2_3_rx_rf_bandwidth_meghz");
    m_solver.add_constr("fmcomms2_3_bw_meghz_rx2a", "=", "fmcomms2_3_rx_rf_bandwidth_meghz");
    m_solver.add_constr("fmcomms2_3_bw_meghz_tx1a", "=", "fmcomms2_3_tx_rf_bandwidth_meghz");
    m_solver.add_constr("fmcomms2_3_bw_meghz_tx2a", "=", "fmcomms2_3_tx_rf_bandwidth_meghz");
    m_solver.add_constr("fmcomms2_3_fs_megsps_rx1a", "=", "fmcomms2_3_rx_sampl_freq_meghz");
    m_solver.add_constr("fmcomms2_3_fs_megsps_rx2a", "=", "fmcomms2_3_rx_sampl_freq_meghz");
    m_solver.add_constr("fmcomms2_3_fs_megsps_tx1a", "=", "fmcomms2_3_tx_sampl_freq_meghz");
    m_solver.add_constr("fmcomms2_3_fs_megsps_tx2a", "=", "fmcomms2_3_tx_sampl_freq_meghz");
    m_solver.add_constr("fmcomms2_3_samps_comp_rx1a", "=", (int32_t)1);
    m_solver.add_constr("fmcomms2_3_samps_comp_rx2a", "=", (int32_t)1);
    m_solver.add_constr("fmcomms2_3_samps_comp_tx1a", "=", (int32_t)1);
    m_solver.add_constr("fmcomms2_3_samps_comp_tx2a", "=", (int32_t)1);
    m_solver.add_constr("fmcomms2_3_gain_mode_rx1a", ">=", (int32_t)0); // agc
    m_solver.add_constr("fmcomms2_3_gain_mode_rx1a", "<=", (int32_t)1); // manual
    m_solver.add_constr("fmcomms2_3_gain_mode_rx2a", ">=", (int32_t)0); // agc
    m_solver.add_constr("fmcomms2_3_gain_mode_rx2a", "<=", (int32_t)1); // manual
    m_solver.add_constr("fmcomms2_3_gain_mode_tx1a", "=", (int32_t)1); // manual
    m_solver.add_constr("fmcomms2_3_gain_mode_tx2a", "=", (int32_t)1); // manual
    /// @TODO / FIXME add gain conditional constraints
    m_solver.add_constr("fmcomms2_3_gain_db_rx1a", ">=", -1.);
    m_solver.add_constr("fmcomms2_3_gain_db_rx1a", "<=", 62.);
    m_solver.add_constr("fmcomms2_3_gain_db_rx2a", ">=", -1.);
    m_solver.add_constr("fmcomms2_3_gain_db_rx2a", "<=", 62.);
    m_solver.add_constr("fmcomms2_3_gain_db_tx1a", ">=", -89.75);
    m_solver.add_constr("fmcomms2_3_gain_db_tx1a", "<=", 0.);
    m_solver.add_constr("fmcomms2_3_gain_db_tx2a", ">=", -89.75);
    m_solver.add_constr("fmcomms2_3_gain_db_tx2a", "<=", 0.);
  }
  public:
  FMCOMMS2_3DecInt16CSP() : CSPBase() {
    define();
    //std::cout << "[INFO] " << get_feasible_region_limits() << "\n";
  }
  void instance() {
    define_x_d();
    define_c();
  }
  /// @brief define Constraint Satisfaction Problem (CSP)
  void define() {
    instance();
  }
}; // class FMCOMMS2_3DecInt16CSP
#endif

// -----------------------------------------------------------------------------
// STEP 2 - IF IS_LOCKING SUPPORTED, DEFINE CONFIGURATOR THAT UTILIZES THE CSP
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class FMCOMMS2_3DecInt16Configurator :
    public Configurator<FMCOMMS2_3DecInt16CSP> {
  public:
  FMCOMMS2_3DecInt16Configurator(int32_t fmcomms_num) :
      Configurator<FMCOMMS2_3DecInt16CSP>() {
    ///@TODO / FIXME - add below line
    //m_solver.add_constr("fmcomms_num", "=", (int32_t)fmcomms_num);
    {
      DataStream::CSPVarMap map;
      map.insert(std::make_pair(config_key_direction.c_str(),
          "fmcomms2_3_dir_rx1a"));
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
      map.insert(std::make_pair(config_key_direction.c_str(),
          "fmcomms2_3_dir_rx2a"));
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
      map.insert(std::make_pair(config_key_direction.c_str(),
          "fmcomms2_3_dir_tx1a"));
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
      map.insert(std::make_pair(config_key_direction.c_str(),
          "fmcomms2_3_dir_tx2a"));
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
}; // class FMCOMMS2_3DecInt16Configurator
#endif

// -----------------------------------------------------------------------------
// STEP 3 - DEFINE DRC (get/set APIs)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
#define FMCOMMS2_3_DEC_INT_16_CONFIGURATOR FMCOMMS2_3DecInt16Configurator
#else
#define FMCOMMS2_3_DEC_INT_16_CONFIGURATOR Configurator<CSPBase>
#endif

template<class log_t, class s_cfg_t, class s_ds_t, class cfgrtr_t = FMCOMMS2_3_DEC_INT_16_CONFIGURATOR>
class FMCOMMS2_3DecInt16DRC : public FMCOMMS2_3DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t> {
  FMCOMMS2_3DecInt16DRC<log_t, s_cfg_t, s_ds_t, cfgrtr_t>(s_cfg_t& slave_cfg,
      s_ds_t& slave_data_sub, double fref_hz, int32_t fmcomms_num, const char* rx1a = "rx1a",
      const char* rx2a = "rx2a",
      const char* tx1a = "tx1a", const char* tx2a = "tx2a",
      const char* descriptor = "FMCOMMS2_3") :
      FMCOMMS2_3DecInt16DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>(slave_cfg,slave_data_sub,fref_hz,fmcomms_num,rx1a,rx2a,tx1a,tx2a,descriptor) {
  }
  ///@TODO / FIXME expand region and remove hackish implementation
  /*void set_tuning_freq_MHz(data_stream_id_t data_stream_id,
      config_value_t val) {
    //int16_t phs_inc = 0;
    //app.setProperty("phs_inc",phs_inc);
    FMCOMMS2_3DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>::set_tuning_freq_MHz(id,val);
  }*/
}; // class FMCOMMS2_3DecInt16DRC

} // namespace DRC

#endif // _FMCOMMS2_3_DEC_INT16_HH
