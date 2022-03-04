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

#ifndef _AD9361_DRC_HH
#define _AD9361_DRC_HH

// define any of the following for debugging purposes
//#define DISABLE_AD9361 // remove hardware actuation, useful for testing

#include <iostream>
#include <unistd.h> // usleep()
#include <cinttypes> // PRI...
#include "DRC.hh"
#include "LogForwarder.hh"
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
class AD9361CSP : public CSPBase {
  protected:
  typedef CSPSolver::Constr::Cond Cond;
  typedef CSPSolver::Constr::Func Func;
  /* @brief for the AD9361,
   *        define variables (X) and their domains (D) for <X,D,C> which
   *        comprises its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void
  define_x_d_ad9361() {
    m_solver.add_var<double>("ad9361_rx_rfpll_lo_freq_meghz", dfp_tol);
    m_solver.add_var<double>("ad9361_tx_rfpll_lo_freq_meghz", dfp_tol);
    m_solver.add_var<double>("ad9361_rx_sampl_freq_meghz", dfp_tol);
    m_solver.add_var<double>("ad9361_tx_sampl_freq_meghz", dfp_tol);
    m_solver.add_var<double>("ad9361_rx_rf_bandwidth_meghz", dfp_tol);
    m_solver.add_var<double>("ad9361_tx_rf_bandwidth_meghz", dfp_tol);
    // @TODO  Does ad9361_dac_clk_divider need to be added to the ad9361_drc.rst?
    m_solver.add_var<int32_t>("ad9361_dac_clk_divider");
    m_solver.add_var<int32_t>("ad9361_dir_rx1");
    m_solver.add_var<int32_t>("ad9361_dir_rx2");
    m_solver.add_var<int32_t>("ad9361_dir_tx1");
    m_solver.add_var<int32_t>("ad9361_dir_tx2");
    m_solver.add_var<double>("ad9361_fc_meghz_rx1", dfp_tol);
    m_solver.add_var<double>("ad9361_fc_meghz_rx2", dfp_tol);
    m_solver.add_var<double>("ad9361_fc_meghz_tx1", dfp_tol);
    m_solver.add_var<double>("ad9361_fc_meghz_tx2", dfp_tol);
    m_solver.add_var<double>("ad9361_bw_meghz_rx1", dfp_tol);
    m_solver.add_var<double>("ad9361_bw_meghz_rx2", dfp_tol);
    m_solver.add_var<double>("ad9361_bw_meghz_tx1", dfp_tol);
    m_solver.add_var<double>("ad9361_bw_meghz_tx2", dfp_tol);
    m_solver.add_var<double>("ad9361_fs_megsps_rx1", dfp_tol);
    m_solver.add_var<double>("ad9361_fs_megsps_rx2", dfp_tol);
    m_solver.add_var<double>("ad9361_fs_megsps_tx1", dfp_tol);
    m_solver.add_var<double>("ad9361_fs_megsps_tx2", dfp_tol);
    m_solver.add_var<int32_t>("ad9361_samps_comp_rx1");
    m_solver.add_var<int32_t>("ad9361_samps_comp_rx2");
    m_solver.add_var<int32_t>("ad9361_samps_comp_tx1");
    m_solver.add_var<int32_t>("ad9361_samps_comp_tx2");
    m_solver.add_var<int32_t>("ad9361_gain_mode_rx1");
    m_solver.add_var<int32_t>("ad9361_gain_mode_rx2");
    m_solver.add_var<int32_t>("ad9361_gain_mode_tx1");
    m_solver.add_var<int32_t>("ad9361_gain_mode_tx2");
    m_solver.add_var<double>("ad9361_gain_db_rx1", dfp_tol);
    m_solver.add_var<double>("ad9361_gain_db_rx2", dfp_tol);
    m_solver.add_var<double>("ad9361_gain_db_tx1", dfp_tol);
    m_solver.add_var<double>("ad9361_gain_db_tx2", dfp_tol);
  }
  /* @brief for the AD9361,
   *        define constraints (C) for <X,D,C> which
   *        comprise its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void
  define_c_ad9361() {
    m_solver.add_constr("ad9361_rx_rfpll_lo_freq_meghz", ">=", 70.);
    m_solver.add_constr("ad9361_rx_rfpll_lo_freq_meghz", "<=", 6000.);
    m_solver.add_constr("ad9361_tx_rfpll_lo_freq_meghz", ">=", 70.);
    m_solver.add_constr("ad9361_tx_rfpll_lo_freq_meghz", "<=", 6000.);
    m_solver.add_constr("ad9361_rx_rf_bandwidth_meghz", ">=", 0.2);
    m_solver.add_constr("ad9361_rx_rf_bandwidth_meghz", "<=", 56.);
    m_solver.add_constr("ad9361_tx_rf_bandwidth_meghz", ">=", 1.25);
    m_solver.add_constr("ad9361_tx_rf_bandwidth_meghz", "<=", 40.);
    m_solver.add_constr("ad9361_rx_sampl_freq_meghz", ">=", 2.083334);
    m_solver.add_constr("ad9361_rx_sampl_freq_meghz", "<=", 61.44);
    m_solver.add_constr("ad9361_tx_sampl_freq_meghz", ">=", 2.083334);
    m_solver.add_constr("ad9361_tx_sampl_freq_meghz", "<=", 61.44);
    m_solver.add_constr("ad9361_dac_clk_divider", ">=", (int32_t)1);
    m_solver.add_constr("ad9361_dac_clk_divider", "<=", (int32_t)2);
    m_solver.add_constr("ad9361_dir_rx1", "=", (int32_t)data_stream_direction_t::rx);
    m_solver.add_constr("ad9361_dir_rx2", "=", (int32_t)data_stream_direction_t::rx);
    m_solver.add_constr("ad9361_dir_tx1", "=", (int32_t)data_stream_direction_t::tx);
    m_solver.add_constr("ad9361_dir_tx2", "=", (int32_t)data_stream_direction_t::tx);
    m_solver.add_constr("ad9361_fc_meghz_rx1", "=", "ad9361_rx_rfpll_lo_freq_meghz");
    m_solver.add_constr("ad9361_fc_meghz_rx2", "=", "ad9361_rx_rfpll_lo_freq_meghz");
    m_solver.add_constr("ad9361_fc_meghz_tx1", "=", "ad9361_tx_rfpll_lo_freq_meghz");
    m_solver.add_constr("ad9361_fc_meghz_tx2", "=", "ad9361_tx_rfpll_lo_freq_meghz");
    m_solver.add_constr("ad9361_bw_meghz_rx1", "=", "ad9361_rx_rf_bandwidth_meghz");
    m_solver.add_constr("ad9361_bw_meghz_rx2", "=", "ad9361_rx_rf_bandwidth_meghz");
    m_solver.add_constr("ad9361_bw_meghz_tx1", "=", "ad9361_tx_rf_bandwidth_meghz");
    m_solver.add_constr("ad9361_bw_meghz_tx2", "=", "ad9361_tx_rf_bandwidth_meghz");
    m_solver.add_constr("ad9361_fs_megsps_rx1", "=", "ad9361_rx_sampl_freq_meghz");
    m_solver.add_constr("ad9361_fs_megsps_rx2", "=", "ad9361_rx_sampl_freq_meghz");
    m_solver.add_constr("ad9361_fs_megsps_tx1", "=", "ad9361_tx_sampl_freq_meghz");
    m_solver.add_constr("ad9361_fs_megsps_tx2", "=", "ad9361_tx_sampl_freq_meghz");
    m_solver.add_constr("ad9361_samps_comp_rx1", "=", (int32_t)1);
    m_solver.add_constr("ad9361_samps_comp_rx2", "=", (int32_t)1);
    m_solver.add_constr("ad9361_samps_comp_tx1", "=", (int32_t)1);
    m_solver.add_constr("ad9361_samps_comp_tx2", "=", (int32_t)1);
    m_solver.add_constr("ad9361_gain_mode_rx1", ">=", (int32_t)0); // agc
    m_solver.add_constr("ad9361_gain_mode_rx1", "<=", (int32_t)1); // manual
    m_solver.add_constr("ad9361_gain_mode_rx2", ">=", (int32_t)0); // agc
    m_solver.add_constr("ad9361_gain_mode_rx2", "<=", (int32_t)1); // manual
    m_solver.add_constr("ad9361_gain_mode_tx1", "=", (int32_t)1); // manual
    m_solver.add_constr("ad9361_gain_mode_tx2", "=", (int32_t)1); // manual
    /// @TODO add gain conditional constraints
    m_solver.add_constr("ad9361_gain_db_rx1", ">=", -10.);//, &if_freq_gt_4000);
    m_solver.add_constr("ad9361_gain_db_rx1", "<=", 77.);//, &if_freq_le_1300);
    m_solver.add_constr("ad9361_gain_db_rx2", ">=", -10.);//, &if_freq_gt_4000);
    m_solver.add_constr("ad9361_gain_db_rx2", "<=", 77.);//, &if_freq_le_1300);
    m_solver.add_constr("ad9361_gain_db_tx1", ">=", -89.75);
    m_solver.add_constr("ad9361_gain_db_tx1", "<=", 0.);
    m_solver.add_constr("ad9361_gain_db_tx2", ">=", -89.75);
    m_solver.add_constr("ad9361_gain_db_tx2", "<=", 0.);
  }
  public:
  AD9361CSP() : CSPBase() {
    define();
    //std::cout << "[INFO] " << get_feasible_region_limits() << "\n";
  }
  /* @brief instance AD9361
   *        by defining its Constraint Satisfaction Problem (CSP) as <X,D,C>
   ****************************************************************************/
  void instance_ad9361() {
    define_x_d_ad9361();
    define_c_ad9361();
  }
  /// @brief define Constraint Satisfaction Problem (CSP)
  void define() {
    instance_ad9361();
  }
}; // class AD9361CSP
#endif

// -----------------------------------------------------------------------------
// STEP 2 - IF IS_LOCKING SUPPORTED, DEFINE CONFIGURATOR THAT UTILIZES THE CSP
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class AD9361Configurator : public Configurator<AD9361CSP> {
  public:
  AD9361Configurator() : Configurator<AD9361CSP>() {
    {
      DataStream::CSPVarMap map;
      map.insert(std::make_pair(config_key_tuning_freq_MHz.c_str(),
          "ad9361_fc_meghz_rx1"));
      map.insert(std::make_pair(config_key_bandwidth_3dB_MHz.c_str(),
          "ad9361_bw_meghz_rx1"));
      map.insert(std::make_pair(config_key_sampling_rate_Msps.c_str(),
          "ad9361_fs_megsps_rx1"));
      map.insert(std::make_pair(config_key_samples_are_complex.c_str(),
          "ad9361_samps_comp_rx1"));
      map.insert(std::make_pair(config_key_gain_mode.c_str(),
          "ad9361_gain_mode_rx1"));
      map.insert(std::make_pair(config_key_gain_dB.c_str(),
          "ad9361_gain_db_rx1"));
      add_data_stream(DataStream("rx1", true, false, map));
    }
    {
      DataStream::CSPVarMap map;
      map.insert(std::make_pair(config_key_tuning_freq_MHz.c_str(),
          "ad9361_fc_meghz_rx2"));
      map.insert(std::make_pair(config_key_bandwidth_3dB_MHz.c_str(),
          "ad9361_bw_meghz_rx2"));
      map.insert(std::make_pair(config_key_sampling_rate_Msps.c_str(),
          "ad9361_fs_megsps_rx2"));
      map.insert(std::make_pair(config_key_samples_are_complex.c_str(),
          "ad9361_samps_comp_rx2"));
      map.insert(std::make_pair(config_key_gain_mode.c_str(),
          "ad9361_gain_mode_rx2"));
      map.insert(std::make_pair(config_key_gain_dB.c_str(),
          "ad9361_gain_db_rx2"));
      add_data_stream(DataStream("rx2", true, false, map));
    }
    {
      DataStream::CSPVarMap map;
      map.insert(std::make_pair(config_key_tuning_freq_MHz.c_str(),
          "ad9361_fc_meghz_tx1"));
      map.insert(std::make_pair(config_key_bandwidth_3dB_MHz.c_str(),
          "ad9361_bw_meghz_tx1"));
      map.insert(std::make_pair(config_key_sampling_rate_Msps.c_str(),
          "ad9361_fs_megsps_tx1"));
      map.insert(std::make_pair(config_key_samples_are_complex.c_str(),
          "ad9361_samps_comp_tx1"));
      map.insert(std::make_pair(config_key_gain_mode.c_str(),
          "ad9361_gain_mode_tx1"));
      map.insert(std::make_pair(config_key_gain_dB.c_str(),
          "ad9361_gain_db_tx1"));
      add_data_stream(DataStream("tx1", false, true, map));
    }
    {
      DataStream::CSPVarMap map;
      map.insert(std::make_pair(config_key_tuning_freq_MHz.c_str(),
          "ad9361_fc_meghz_tx2"));
      map.insert(std::make_pair(config_key_bandwidth_3dB_MHz.c_str(),
          "ad9361_bw_meghz_tx2"));
      map.insert(std::make_pair(config_key_sampling_rate_Msps.c_str(),
          "ad9361_fs_megsps_tx2"));
      map.insert(std::make_pair(config_key_samples_are_complex.c_str(),
          "ad9361_samps_comp_tx2"));
      map.insert(std::make_pair(config_key_gain_mode.c_str(),
          "ad9361_gain_mode_tx2"));
      map.insert(std::make_pair(config_key_gain_dB.c_str(),
          "ad9361_gain_db_tx2"));
      add_data_stream(DataStream("tx2", false, true, map));
    }
  }
}; // class AD9361Configurator
#endif

// -----------------------------------------------------------------------------
// STEP 3 - DEFINE DRC (get/set APIs)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
#define AD9361_CONFIGURATOR AD9361Configurator
#else
#define AD9361_CONFIGURATOR Configurator<CSPBase>
#endif

template<class log_t, class slave_cfg_t, class slave_data_sub_t, class cfgrtr_t = AD9361_CONFIGURATOR>
class AD9361DRC : public DRC<log_t,cfgrtr_t> {
  protected:
#ifndef DISABLE_AD9361
  enum class rx_frame_usage_t {enable, toggle};
  enum class data_bus_index_direction_t {normal, reverse};
  enum class data_rate_config_t {sdr, ddr};
  double                 m_fref_hz;
  /// @brief No-OS struct used to initialize AD9361
  AD9361_InitParam       m_init_param;
  /// @brief No-OS struct pointer
  struct ad9361_rf_phy*  _ad9361_phy;
  struct ad9361_rf_phy*& m_ad9361_rf_phy;
  int32_t                m_ad9361_init_ret;
  bool                   m_ad9361_init_called;
#endif
  /// @brief name of the data stream that corresponds to AD9361 RX1 channel
  const char*            m_ds_rx1;
  const char*            m_ds_rx2;
  const char*            m_ds_tx1;
  const char*            m_ds_tx2;
  /// @brief ad9361_config.hdl slave
  slave_cfg_t&           m_cfg_slave;
  /// @brief ad9361_data_sub.hdl slave
  slave_data_sub_t&      m_data_sub_slave;
  template<typename T> T convert_milli_db_to_db(T val_milli_db) const {
    return val_milli_db/1000;
  }
  template<typename T> T convert_db_to_milli_db(T val_milli_db) const {
    return val_milli_db*1000;
  }
#ifndef DISABLE_AD9361
  void init_init_param() {
    AD9361_InitParam init_param = {
      /* Device selection */
      ID_AD9361,	// dev_sel
      /* Identification number */
      0,		//id_no
      /* Reference Clock */
      40000000UL,	//reference_clk_rate
      /* Base Configuration */
      1,		//two_rx_two_tx_mode_enable *** adi,2rx-2tx-mode-enable
      1,		//one_rx_one_tx_mode_use_rx_num *** adi,1rx-1tx-mode-use-rx-num
      1,		//one_rx_one_tx_mode_use_tx_num *** adi,1rx-1tx-mode-use-tx-num
      1,		//frequency_division_duplex_mode_enable *** adi,frequency-division-duplex-mode-enable

      // frequency_division_duplex_independent_mode_enable=1 required for
      // ad9361_dac.hdl event port to operate as intended
      1,		//frequency_division_duplex_independent_mode_enable *** adi,frequency-division-duplex-independent-mode-enable

      0,		//tdd_use_dual_synth_mode_enable *** adi,tdd-use-dual-synth-mode-enable
      0,		//tdd_skip_vco_cal_enable *** adi,tdd-skip-vco-cal-enable
      0,		//tx_fastlock_delay_ns *** adi,tx-fastlock-delay-ns
      0,		//rx_fastlock_delay_ns *** adi,rx-fastlock-delay-ns
      0,		//rx_fastlock_pincontrol_enable *** adi,rx-fastlock-pincontrol-enable
      0,		//tx_fastlock_pincontrol_enable *** adi,tx-fastlock-pincontrol-enable
      0,		//external_rx_lo_enable *** adi,external-rx-lo-enable
      0,		//external_tx_lo_enable *** adi,external-tx-lo-enable
      5,		//dc_offset_tracking_update_event_mask *** adi,dc-offset-tracking-update-event-mask
      6,		//dc_offset_attenuation_high_range *** adi,dc-offset-attenuation-high-range
      5,		//dc_offset_attenuation_low_range *** adi,dc-offset-attenuation-low-range
      0x28,	//dc_offset_count_high_range *** adi,dc-offset-count-high-range
      0x32,	//dc_offset_count_low_range *** adi,dc-offset-count-low-range
      0,		//split_gain_table_mode_enable *** adi,split-gain-table-mode-enable
      MAX_SYNTH_FREF,	//trx_synthesizer_target_fref_overwrite_hz *** adi,trx-synthesizer-target-fref-overwrite-hz
      0,		// qec_tracking_slow_mode_enable *** adi,qec-tracking-slow-mode-enable
      /* ENSM Control */
      0,		//ensm_enable_pin_pulse_mode_enable *** adi,ensm-enable-pin-pulse-mode-enable
      0,		//ensm_enable_txnrx_control_enable *** adi,ensm-enable-txnrx-control-enable
      /* LO Control */
      2400000000UL,	//rx_synthesizer_frequency_hz *** adi,rx-synthesizer-frequency-hz
      2400000000UL,	//tx_synthesizer_frequency_hz *** adi,tx-synthesizer-frequency-hz
      1,        //tx_lo_powerdown_managed_enable *** adi,tx-lo-powerdown-managed-enable
      /* Rate & BW Control */
      {983040000, 245760000, 122880000, 61440000, 30720000, 30720000},// rx_path_clock_frequencies[6] *** adi,rx-path-clock-frequencies
      {983040000, 122880000, 122880000, 61440000, 30720000, 30720000},// tx_path_clock_frequencies[6] *** adi,tx-path-clock-frequencies
      18000000,//rf_rx_bandwidth_hz *** adi,rf-rx-bandwidth-hz
      18000000,//rf_tx_bandwidth_hz *** adi,rf-tx-bandwidth-hz
      /* RF Port Control */
      0,		//rx_rf_port_input_select *** adi,rx-rf-port-input-select
      0,		//tx_rf_port_input_select *** adi,tx-rf-port-input-select
      /* TX Attenuation Control */
      10000,	//tx_attenuation_mdB *** adi,tx-attenuation-mdB
      0,		//update_tx_gain_in_alert_enable *** adi,update-tx-gain-in-alert-enable
      /* Reference Clock Control */
      0,		//xo_disable_use_ext_refclk_enable *** adi,xo-disable-use-ext-refclk-enable
      {8, 5920},	//dcxo_coarse_and_fine_tune[2] *** adi,dcxo-coarse-and-fine-tune
      CLKOUT_DISABLE,	//clk_output_mode_select *** adi,clk-output-mode-select
      /* Gain Control */
      2,		//gc_rx1_mode *** adi,gc-rx1-mode
      2,		//gc_rx2_mode *** adi,gc-rx2-mode
      58,		//gc_adc_large_overload_thresh *** adi,gc-adc-large-overload-thresh
      4,		//gc_adc_ovr_sample_size *** adi,gc-adc-ovr-sample-size
      47,		//gc_adc_small_overload_thresh *** adi,gc-adc-small-overload-thresh
      8192,	//gc_dec_pow_measurement_duration *** adi,gc-dec-pow-measurement-duration
      0,		//gc_dig_gain_enable *** adi,gc-dig-gain-enable
      800,	//gc_lmt_overload_high_thresh *** adi,gc-lmt-overload-high-thresh
      704,	//gc_lmt_overload_low_thresh *** adi,gc-lmt-overload-low-thresh
      24,		//gc_low_power_thresh *** adi,gc-low-power-thresh
      15,		//gc_max_dig_gain *** adi,gc-max-dig-gain
      /* Gain MGC Control */
      2,		//mgc_dec_gain_step *** adi,mgc-dec-gain-step
      2,		//mgc_inc_gain_step *** adi,mgc-inc-gain-step
      0,		//mgc_rx1_ctrl_inp_enable *** adi,mgc-rx1-ctrl-inp-enable
      0,		//mgc_rx2_ctrl_inp_enable *** adi,mgc-rx2-ctrl-inp-enable
      0,		//mgc_split_table_ctrl_inp_gain_mode *** adi,mgc-split-table-ctrl-inp-gain-mode
      /* Gain AGC Control */
      10,		//agc_adc_large_overload_exceed_counter *** adi,agc-adc-large-overload-exceed-counter
      2,		//agc_adc_large_overload_inc_steps *** adi,agc-adc-large-overload-inc-steps
      0,		//agc_adc_lmt_small_overload_prevent_gain_inc_enable *** adi,agc-adc-lmt-small-overload-prevent-gain-inc-enable
      10,		//agc_adc_small_overload_exceed_counter *** adi,agc-adc-small-overload-exceed-counter
      4,		//agc_dig_gain_step_size *** adi,agc-dig-gain-step-size
      3,		//agc_dig_saturation_exceed_counter *** adi,agc-dig-saturation-exceed-counter
      1000,	// agc_gain_update_interval_us *** adi,agc-gain-update-interval-us
      0,		//agc_immed_gain_change_if_large_adc_overload_enable *** adi,agc-immed-gain-change-if-large-adc-overload-enable
      0,		//agc_immed_gain_change_if_large_lmt_overload_enable *** adi,agc-immed-gain-change-if-large-lmt-overload-enable
      10,		//agc_inner_thresh_high *** adi,agc-inner-thresh-high
      1,		//agc_inner_thresh_high_dec_steps *** adi,agc-inner-thresh-high-dec-steps
      12,		//agc_inner_thresh_low *** adi,agc-inner-thresh-low
      1,		//agc_inner_thresh_low_inc_steps *** adi,agc-inner-thresh-low-inc-steps
      10,		//agc_lmt_overload_large_exceed_counter *** adi,agc-lmt-overload-large-exceed-counter
      2,		//agc_lmt_overload_large_inc_steps *** adi,agc-lmt-overload-large-inc-steps
      10,		//agc_lmt_overload_small_exceed_counter *** adi,agc-lmt-overload-small-exceed-counter
      5,		//agc_outer_thresh_high *** adi,agc-outer-thresh-high
      2,		//agc_outer_thresh_high_dec_steps *** adi,agc-outer-thresh-high-dec-steps
      18,		//agc_outer_thresh_low *** adi,agc-outer-thresh-low
      2,		//agc_outer_thresh_low_inc_steps *** adi,agc-outer-thresh-low-inc-steps
      1,		//agc_attack_delay_extra_margin_us; *** adi,agc-attack-delay-extra-margin-us
      0,		//agc_sync_for_gain_counter_enable *** adi,agc-sync-for-gain-counter-enable
      /* Fast AGC */
      64,		//fagc_dec_pow_measuremnt_duration ***  adi,fagc-dec-pow-measurement-duration
      260,	//fagc_state_wait_time_ns ***  adi,fagc-state-wait-time-ns
      /* Fast AGC - Low Power */
      0,		//fagc_allow_agc_gain_increase ***  adi,fagc-allow-agc-gain-increase-enable
      5,		//fagc_lp_thresh_increment_time ***  adi,fagc-lp-thresh-increment-time
      1,		//fagc_lp_thresh_increment_steps ***  adi,fagc-lp-thresh-increment-steps
      /* Fast AGC - Lock Level (Lock Level is set via slow AGC inner high threshold) */
      1,		//fagc_lock_level_lmt_gain_increase_en ***  adi,fagc-lock-level-lmt-gain-increase-enable
      5,		//fagc_lock_level_gain_increase_upper_limit ***  adi,fagc-lock-level-gain-increase-upper-limit
      /* Fast AGC - Peak Detectors and Final Settling */
      1,		//fagc_lpf_final_settling_steps ***  adi,fagc-lpf-final-settling-steps
      1,		//fagc_lmt_final_settling_steps ***  adi,fagc-lmt-final-settling-steps
      3,		//fagc_final_overrange_count ***  adi,fagc-final-overrange-count
      /* Fast AGC - Final Power Test */
      0,		//fagc_gain_increase_after_gain_lock_en ***  adi,fagc-gain-increase-after-gain-lock-enable
      /* Fast AGC - Unlocking the Gain */
      0,		//fagc_gain_index_type_after_exit_rx_mode ***  adi,fagc-gain-index-type-after-exit-rx-mode
      1,		//fagc_use_last_lock_level_for_set_gain_en ***  adi,fagc-use-last-lock-level-for-set-gain-enable
      1,		//fagc_rst_gla_stronger_sig_thresh_exceeded_en ***  adi,fagc-rst-gla-stronger-sig-thresh-exceeded-enable
      5,		//fagc_optimized_gain_offset ***  adi,fagc-optimized-gain-offset
      10,		//fagc_rst_gla_stronger_sig_thresh_above_ll ***  adi,fagc-rst-gla-stronger-sig-thresh-above-ll
      1,		//fagc_rst_gla_engergy_lost_sig_thresh_exceeded_en ***  adi,fagc-rst-gla-engergy-lost-sig-thresh-exceeded-enable
      1,		//fagc_rst_gla_engergy_lost_goto_optim_gain_en ***  adi,fagc-rst-gla-engergy-lost-goto-optim-gain-enable
      10,		//fagc_rst_gla_engergy_lost_sig_thresh_below_ll ***  adi,fagc-rst-gla-engergy-lost-sig-thresh-below-ll
      8,		//fagc_energy_lost_stronger_sig_gain_lock_exit_cnt ***  adi,fagc-energy-lost-stronger-sig-gain-lock-exit-cnt
      1,		//fagc_rst_gla_large_adc_overload_en ***  adi,fagc-rst-gla-large-adc-overload-enable
      1,		//fagc_rst_gla_large_lmt_overload_en ***  adi,fagc-rst-gla-large-lmt-overload-enable
      0,		//fagc_rst_gla_en_agc_pulled_high_en ***  adi,fagc-rst-gla-en-agc-pulled-high-enable
      0,		//fagc_rst_gla_if_en_agc_pulled_high_mode ***  adi,fagc-rst-gla-if-en-agc-pulled-high-mode
      64,		//fagc_power_measurement_duration_in_state5 ***  adi,fagc-power-measurement-duration-in-state5
      /* RSSI Control */
      1,		//rssi_delay *** adi,rssi-delay
      1000,	//rssi_duration *** adi,rssi-duration
      3,		//rssi_restart_mode *** adi,rssi-restart-mode
      0,		//rssi_unit_is_rx_samples_enable *** adi,rssi-unit-is-rx-samples-enable
      1,		//rssi_wait *** adi,rssi-wait
      /* Aux ADC Control */
      256,	//aux_adc_decimation *** adi,aux-adc-decimation
      40000000UL,	//aux_adc_rate *** adi,aux-adc-rate
      /* AuxDAC Control */
      1,		//aux_dac_manual_mode_enable ***  adi,aux-dac-manual-mode-enable
      0,		//aux_dac1_default_value_mV ***  adi,aux-dac1-default-value-mV
      0,		//aux_dac1_active_in_rx_enable ***  adi,aux-dac1-active-in-rx-enable
      0,		//aux_dac1_active_in_tx_enable ***  adi,aux-dac1-active-in-tx-enable
      0,		//aux_dac1_active_in_alert_enable ***  adi,aux-dac1-active-in-alert-enable
      0,		//aux_dac1_rx_delay_us ***  adi,aux-dac1-rx-delay-us
      0,		//aux_dac1_tx_delay_us ***  adi,aux-dac1-tx-delay-us
      0,		//aux_dac2_default_value_mV ***  adi,aux-dac2-default-value-mV
      0,		//aux_dac2_active_in_rx_enable ***  adi,aux-dac2-active-in-rx-enable
      0,		//aux_dac2_active_in_tx_enable ***  adi,aux-dac2-active-in-tx-enable
      0,		//aux_dac2_active_in_alert_enable ***  adi,aux-dac2-active-in-alert-enable
      0,		//aux_dac2_rx_delay_us ***  adi,aux-dac2-rx-delay-us
      0,		//aux_dac2_tx_delay_us ***  adi,aux-dac2-tx-delay-us
      /* Temperature Sensor Control */
      256,	//temp_sense_decimation *** adi,temp-sense-decimation
      1000,	//temp_sense_measurement_interval_ms *** adi,temp-sense-measurement-interval-ms
      (int8_t)0xCE,	//temp_sense_offset_signed *** adi,temp-sense-offset-signed //0xCE,	//temp_sense_offset_signed *** adi,temp-sense-offset-signed
      1,		//temp_sense_periodic_measurement_enable *** adi,temp-sense-periodic-measurement-enable
      /* Control Out Setup */
      0xFF,	//ctrl_outs_enable_mask *** adi,ctrl-outs-enable-mask
      0,		//ctrl_outs_index *** adi,ctrl-outs-index
      /* External LNA Control */
      0,		//elna_settling_delay_ns *** adi,elna-settling-delay-ns
      0,		//elna_gain_mdB *** adi,elna-gain-mdB
      0,		//elna_bypass_loss_mdB *** adi,elna-bypass-loss-mdB
      0,		//elna_rx1_gpo0_control_enable *** adi,elna-rx1-gpo0-control-enable
      0,		//elna_rx2_gpo1_control_enable *** adi,elna-rx2-gpo1-control-enable
      0,		//elna_gaintable_all_index_enable *** adi,elna-gaintable-all-index-enable
      /* Digital Interface Control */
      0,		//digital_interface_tune_skip_mode *** adi,digital-interface-tune-skip-mode
      0,		//digital_interface_tune_fir_disable *** adi,digital-interface-tune-fir-disable
      1,		//pp_tx_swap_enable *** adi,pp-tx-swap-enable
      1,		//pp_rx_swap_enable *** adi,pp-rx-swap-enable
      0,		//tx_channel_swap_enable *** adi,tx-channel-swap-enable
      0,		//rx_channel_swap_enable *** adi,rx-channel-swap-enable
      1,		//rx_frame_pulse_mode_enable *** adi,rx-frame-pulse-mode-enable
      0,		//two_t_two_r_timing_enable *** adi,2t2r-timing-enable
      0,		//invert_data_bus_enable *** adi,invert-data-bus-enable
      0,		//invert_data_clk_enable *** adi,invert-data-clk-enable
      0,		//fdd_alt_word_order_enable *** adi,fdd-alt-word-order-enable
      0,		//invert_rx_frame_enable *** adi,invert-rx-frame-enable
      0,		//fdd_rx_rate_2tx_enable *** adi,fdd-rx-rate-2tx-enable
      0,		//swap_ports_enable *** adi,swap-ports-enable
      0,		//single_data_rate_enable *** adi,single-data-rate-enable
      1,		//lvds_mode_enable *** adi,lvds-mode-enable
      0,		//half_duplex_mode_enable *** adi,half-duplex-mode-enable
      0,		//single_port_mode_enable *** adi,single-port-mode-enable
      0,		//full_port_enable *** adi,full-port-enable
      0,		//full_duplex_swap_bits_enable *** adi,full-duplex-swap-bits-enable
      0,		//delay_rx_data *** adi,delay-rx-data
      0,		//rx_data_clock_delay *** adi,rx-data-clock-delay
      4,		//rx_data_delay *** adi,rx-data-delay
      7,		//tx_fb_clock_delay *** adi,tx-fb-clock-delay
      0,		//tx_data_delay *** adi,tx-data-delay
    #ifdef ALTERA_PLATFORM
      300,	//lvds_bias_mV *** adi,lvds-bias-mV
    #else
      150,	//lvds_bias_mV *** adi,lvds-bias-mV
    #endif
      1,		//lvds_rx_onchip_termination_enable *** adi,lvds-rx-onchip-termination-enable
      0,		//rx1rx2_phase_inversion_en *** adi,rx1-rx2-phase-inversion-enable
      0xFF,	//lvds_invert1_control *** adi,lvds-invert1-control
      0x0F,	//lvds_invert2_control *** adi,lvds-invert2-control
      /* GPO Control */
      0,		//gpo0_inactive_state_high_enable *** adi,gpo0-inactive-state-high-enable
      0,		//gpo1_inactive_state_high_enable *** adi,gpo1-inactive-state-high-enable
      0,		//gpo2_inactive_state_high_enable *** adi,gpo2-inactive-state-high-enable
      0,		//gpo3_inactive_state_high_enable *** adi,gpo3-inactive-state-high-enable
      0,		//gpo0_slave_rx_enable *** adi,gpo0-slave-rx-enable
      0,		//gpo0_slave_tx_enable *** adi,gpo0-slave-tx-enable
      0,		//gpo1_slave_rx_enable *** adi,gpo1-slave-rx-enable
      0,		//gpo1_slave_tx_enable *** adi,gpo1-slave-tx-enable
      0,		//gpo2_slave_rx_enable *** adi,gpo2-slave-rx-enable
      0,		//gpo2_slave_tx_enable *** adi,gpo2-slave-tx-enable
      0,		//gpo3_slave_rx_enable *** adi,gpo3-slave-rx-enable
      0,		//gpo3_slave_tx_enable *** adi,gpo3-slave-tx-enable
      0,		//gpo0_rx_delay_us *** adi,gpo0-rx-delay-us
      0,		//gpo0_tx_delay_us *** adi,gpo0-tx-delay-us
      0,		//gpo1_rx_delay_us *** adi,gpo1-rx-delay-us
      0,		//gpo1_tx_delay_us *** adi,gpo1-tx-delay-us
      0,		//gpo2_rx_delay_us *** adi,gpo2-rx-delay-us
      0,		//gpo2_tx_delay_us *** adi,gpo2-tx-delay-us
      0,		//gpo3_rx_delay_us *** adi,gpo3-rx-delay-us
      0,		//gpo3_tx_delay_us *** adi,gpo3-tx-delay-us
      /* Tx Monitor Control */
      37000,	//low_high_gain_threshold_mdB *** adi,txmon-low-high-thresh
      0,		//low_gain_dB *** adi,txmon-low-gain
      24,		//high_gain_dB *** adi,txmon-high-gain
      0,		//tx_mon_track_en *** adi,txmon-dc-tracking-enable
      0,		//one_shot_mode_en *** adi,txmon-one-shot-mode-enable
      511,	//tx_mon_delay *** adi,txmon-delay
      8192,	//tx_mon_duration *** adi,txmon-duration
      2,		//tx1_mon_front_end_gain *** adi,txmon-1-front-end-gain
      2,		//tx2_mon_front_end_gain *** adi,txmon-2-front-end-gain
      48,		//tx1_mon_lo_cm *** adi,txmon-1-lo-cm
      48,		//tx2_mon_lo_cm *** adi,txmon-2-lo-cm
      /* GPIO definitions */
      -1,		//gpio_resetb *** reset-gpios
      /* MCS Sync */
      -1,		//gpio_sync *** sync-gpios
      -1,		//gpio_cal_sw1 *** cal-sw1-gpios
      -1,		//gpio_cal_sw2 *** cal-sw2-gpios
      /* External LO clocks */
      NULL,	//(*ad9361_rfpll_ext_recalc_rate)()
      NULL,	//(*ad9361_rfpll_ext_round_rate)()
      NULL	//(*ad9361_rfpll_ext_set_rate)()
    };
    m_init_param = init_param;
  }
  void init() {
    // only initialize if there are no existing locks which conflict
    if(any_configurator_configs_locked_which_prevent_ad9361_init()) {
      throw std::string("reinit required but configs locked which prevent");
    }
    if(not m_ad9361_init_called) { // spi_init() only needs to happen once
      // nasty cast below included since compiler wouldn't let us cast from
      // ...WorkerTypes::...WorkerBase::Slave to
      // OCPI::RCC_RCCUserSlave since the former inherits privately from the
      // latter inside the RCC worker's generated header
      spi_init(static_cast<OCPI::RCC::RCCUserSlave*>(static_cast<void *>(&m_cfg_slave)));
    }
    // initialize No-OS using the No-OS platform_opencpi layer and
    // ad9361_config.hdl
    apply_config_to_init_param();
    // assign m_AD9361_InitParam.gpio_resetb to the arbitrarily defined GPIO_RESET_PIN so
    // that the No-OS opencpi platform driver knows to drive the force_reset
    // property of the sub-device
    m_init_param.gpio_resetb = GPIO_RESET_PIN;
    m_init_param.reference_clk_rate = (uint32_t) round(m_fref_hz);
    // here is where we enforce the ad9361_config OWD comment
    // "[the force_two_r_two_t_timing] property is expected to correspond to the
    // D2 bit of the Parallel Port Configuration 1 register at SPI address 0x010
    m_cfg_slave.set_force_two_r_two_t_timing(m_init_param.two_t_two_r_timing_enable);
    // ADI forum post recommended setting ENABLE/TXNRX pins high *prior to
    // ad9361_init() call* when
    // frequency_division_duplex_independent_mode_enable is set to 1
    m_cfg_slave.set_ENABLE_force_set(true);
    m_cfg_slave.set_TXNRX_force_set(true);
    // sleep duration chosen to be relatively small in relation to AD9361
    // initialization duration (which, through observation, appears to be
    // roughly 200 ms), but a long enough pulse that AD9361 is likely
    // recognizing it many, many times over
    usleep(1000);
    // the below method call allocates memory for ad9361, the address of which is
    // pointed to by m_ad9361_rf_phy once the method returns
    this->log_info("noos ad9361_init");
    this->log_info("noos 1");
    struct ad9361_rf_phy** ad9361_phy = &m_ad9361_rf_phy;
    this->log_info("noos 2");
    AD9361_InitParam* init_param = &m_init_param;
    this->log_info("noos 3");
    m_ad9361_init_ret = ad9361_init(ad9361_phy, init_param);
    this->log_info("noos exit ad9361_init");
    m_ad9361_init_called = true;
    m_cfg_slave.set_ENABLE_force_set(false);
    m_cfg_slave.set_TXNRX_force_set(false);
    if(m_ad9361_init_ret == -ENODEV) {
      throw std::string("AD9361 init failed: SPI could not be established");
    }
    else if(m_ad9361_init_ret != 0) {
      throw std::string("AD9361 init failed");
    }
    if(m_ad9361_rf_phy == 0) {
      throw std::string("AD9361 init failed");
    }
    this->log_info("enforce_ensm_configinit()");
    enforce_ensm_config();
    //because channel config potentially changed
    this->log_info("set_ad9361_fpga_channel_config()");
    set_ad9361_fpga_channel_config();
    this->log_info("exiting init()");
  }
  bool any_configurator_configs_locked_which_prevent_ad9361_init() const {
    std::vector<const char*> data_streams;
    data_streams.push_back((m_ds_rx1));
    data_streams.push_back((m_ds_rx2));
    data_streams.push_back((m_ds_tx1));
    data_streams.push_back((m_ds_tx2));
    // unfortunately necessary to make this function const
    auto configurator_copy = this->m_configurator;
    auto it = data_streams.begin();
    for(; it != data_streams.end(); it++) {
      if(configurator_copy.get_config_is_locked(configurator_copy.get_config(*it, config_key_tuning_freq_MHz))) {
        return true;
      }
      if(configurator_copy.get_config_is_locked(configurator_copy.get_config(*it, config_key_bandwidth_3dB_MHz))) {
        return true;
      }
      if(configurator_copy.get_config_is_locked(configurator_copy.get_config(*it, config_key_sampling_rate_Msps))) {
        return true;
      }
      if(configurator_copy.get_config_is_locked(configurator_copy.get_config(*it, config_key_gain_mode))) {
        return true;
      }
      if(configurator_copy.get_config_is_locked(configurator_copy.get_config(*it, config_key_gain_dB))) {
        return true;
      }
    }
    return false;
  }
  void throw_if_ad9361_init_failed(const char* operation) const {
    if(m_ad9361_init_ret != 0) {
      std::ostringstream oss;
      oss << "cannot perform ";
      oss << (operation ? operation : "operation");
      oss << " because ad9361_init() failed";
      throw oss.str();
    }
  }
  void apply_config_to_init_param() {
    bool is_2r1t_or_1r2t_or_2r2t =
        m_cfg_slave.get_qadc1_is_present() or
        m_cfg_slave.get_qdac1_is_present();
    bool mode_is_sdr = m_cfg_slave.get_data_rate_config() == 
        Platform_ad9361_configWorkerTypes::DATA_RATE_CONFIG_SDR;
    m_init_param.rx_frame_pulse_mode_enable =
        (int)m_cfg_slave.get_rx_frame_usage() ? 1 : 0;
    m_init_param.invert_data_bus_enable =
        (int)m_cfg_slave.get_data_bus_index_direction() ? 1 : 0;
    m_init_param.invert_data_clk_enable =
        m_cfg_slave.get_data_clk_is_inverted() ? 1 : 0;
    m_init_param.invert_rx_frame_enable =
        m_cfg_slave.get_rx_frame_is_inverted() ? 1 : 0;
    if(m_cfg_slave.get_LVDS())
    {
      m_init_param.lvds_rx_onchip_termination_enable = 1;
      m_init_param.lvds_mode_enable                  = 1;
      // AD9361_Reference_Manual_UG-570.pdf (Rev. A):
      // "The following bits are not supported in LVDS mode:
      // * Swap Ports-In LVDS mode, P0 is Tx and P1 is Rx. This configuration cannot be changed.
      // * Single Port Mode-Both ports are enabled in LVDS mode.
      // * FDD Full Port-Not supported in LVDS.
      // * FDD Alt Word Order-Not supported in LVDS.
      // * FDD Swap Bits-Not supported in LVDS."
      m_init_param.swap_ports_enable            = 0;
      m_init_param.single_port_mode_enable      = 0;
      m_init_param.full_port_enable             = 0;
      m_init_param.fdd_alt_word_order_enable    = 0; ///@TODO/FIXME read this value from FPGA?
      m_init_param.half_duplex_mode_enable      = 0;
      m_init_param.single_data_rate_enable      = 0;
      m_init_param.full_duplex_swap_bits_enable = 0; ///@TODO / FIXME read this value from FPGA?
    }
    else { // mode is CMOS
      m_init_param.lvds_rx_onchip_termination_enable = 0;
      m_init_param.lvds_mode_enable                  = 0;
      m_init_param.swap_ports_enable         =
          m_cfg_slave.get_swap_ports() ? 1 : 0;
      bool single_port = m_cfg_slave.get_single_port();
      m_init_param.single_port_mode_enable   =
          m_cfg_slave.get_single_port() ? 1 : 0;
      m_init_param.fdd_alt_word_order_enable = 0; ///@TODO/FIXME read this value from FPGA?
      bool half_duplex = m_cfg_slave.get_half_duplex();
      m_init_param.full_port_enable          = (!half_duplex) and (!m_cfg_slave.get_single_port());
      m_init_param.half_duplex_mode_enable   = half_duplex ? 1 : 0;
      m_init_param.single_data_rate_enable   =
          m_cfg_slave.get_data_rate_config() == mode_is_sdr ? 1 : 0;
      m_init_param.full_duplex_swap_bits_enable = 0; ///@TODO / FIXME read this value from FPGA?
    }
    m_init_param.two_rx_two_tx_mode_enable = is_2r1t_or_1r2t_or_2r2t ? 1 : 0;
    m_init_param.rx_data_clock_delay = m_data_sub_slave.get_DATA_CLK_Delay();
    m_init_param.rx_data_delay       = m_data_sub_slave.get_RX_Data_Delay();
    m_init_param.tx_fb_clock_delay   = m_data_sub_slave.get_FB_CLK_Delay();
    m_init_param.tx_data_delay       = m_data_sub_slave.get_TX_Data_Delay();
  }
  void enforce_ensm_config() {
    m_cfg_slave.set_Half_Duplex_Mode(not m_ad9361_rf_phy->pdata->fdd);
    uint8_t ensm_config_1 = m_cfg_slave.get_ensm_config_1();
    m_cfg_slave.set_ENSM_Pin_Control((ensm_config_1 & 0x10) == 0x10);
    m_cfg_slave.set_Level_Mode((ensm_config_1 & 0x08) == 0x08);
    uint8_t ensm_config_2 = m_cfg_slave.get_ensm_config_2();
    m_cfg_slave.set_FDD_External_Control_Enable((ensm_config_2 & 0x80) == 0x80);
  }
  /* @brief The AD9361 register set determines which channel mode is used (1R1T,
   * 1R2T, 2R1T, or 1R2T). This mode eventually determines which timing diagram
   * the AD9361 is expecting for the TX data path pins. This function
   * tells the FPGA bitstream which channel mode should be assumed when
   * generating the TX data path signals.
   ***************************************************************************/
  void set_ad9361_fpga_channel_config() {
    uint8_t tx_ctrl = m_cfg_slave.get_general_tx_enable_filter_ctrl();
    bool two_t = TX_CHANNEL_ENABLE(TX_1 | TX_2) == (tx_ctrl & 0xc0);
    uint8_t rx_ctrl = m_cfg_slave.get_general_rx_enable_filter_ctrl();
    bool two_r = RX_CHANNEL_ENABLE(RX_1 | RX_2) == (rx_ctrl & 0xc0);
    m_cfg_slave.set_config_is_two_r(two_r);
    m_cfg_slave.set_config_is_two_t(two_t);
  }
#endif
  void init_if_required() {
#ifndef DISABLE_AD9361
    if(not m_ad9361_init_called) {
      init();
    }
#endif
  }
  public:
  AD9361DRC<log_t, slave_cfg_t, slave_data_sub_t, cfgrtr_t>(slave_cfg_t& slave_cfg,
      slave_data_sub_t& slave_data_sub, double fref_hz, const char* rx1 = "rx1",
      const char* rx2 = "rx2",
      const char* tx1 = "tx1", const char* tx2 = "tx2",
      const char* descriptor = "AD9361") : DRC<log_t,cfgrtr_t>(descriptor),
#ifndef DISABLE_AD9361
      m_fref_hz(fref_hz),
      m_ad9361_rf_phy(_ad9361_phy),
      m_ad9361_init_ret(-1),
      m_ad9361_init_called(false),
#endif
      m_ds_rx1(rx1), m_ds_rx2(rx2), m_ds_tx1(tx1), m_ds_tx2(tx2),
      m_cfg_slave(slave_cfg),
      m_data_sub_slave(slave_data_sub) {
    std::ostringstream oss;
    oss << "constructor ";
    oss << this->m_configurator.get_feasible_region_limits() << "\n";
    std::cout << oss.str() << "\n";
    this->log_info(oss.str().c_str());
#ifndef DISABLE_AD9361
    init_init_param();
#endif
  }
  bool get_rx_and_throw_if_invalid_ds(data_stream_id_t data_stream_id) const {
    bool do_rx = false;
    if(data_stream_id == m_ds_rx1) {
      do_rx = true;
    }
    else if(data_stream_id == m_ds_rx2) {
      do_rx = true;
    }
    else if(data_stream_id == m_ds_tx1) {
      do_rx = false;
    }
    else if(data_stream_id == m_ds_tx2) {
      do_rx = false;
    }
    else {
      this->throw_invalid_data_stream_id(data_stream_id);
    }
    return do_rx;
  }
  void set_rx_rf_port_input(uint32_t mode) {
    init_if_required();
    this->log_info("noos ad9361_set_rx_rf_port_input %" PRIu32, mode);
#ifndef DISABLE_AD9361
    this->log_info("noos ad9361_set_rx_rf_port_input m_ad9361_rf_phy %i %" PRIu32, m_ad9361_rf_phy, mode);
    int32_t res = ad9361_set_rx_rf_port_input(m_ad9361_rf_phy, mode);
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
  }
  void set_tx_rf_port_output(uint32_t mode) {
    init_if_required();
    this->log_info("noos ad9361_set_tx_rf_port_output %" PRIu32, mode);
#ifndef DISABLE_AD9361
    int32_t res = ad9361_set_tx_rf_port_output(m_ad9361_rf_phy, mode);
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
  }
  void throw_if_no_os_api_call_returns_non_zero(int32_t res) {
    init_if_required();
    if(res != 0) {
      throw std::string("No-OS API call returned non-zero value");
    }
  }
/// @todo / FIXME - check for existence of qadc/qdac?
  bool get_data_stream_is_enabled(data_stream_id_t data_stream_id) {
    bool ret = true;
    get_rx_and_throw_if_invalid_ds(data_stream_id);
#ifndef DISABLE_AD9361
    if(not m_ad9361_init_called) {
      ret = false;
    }
    if(ret) {
      if(data_stream_id == m_ds_rx1) {
        if(m_init_param.two_rx_two_tx_mode_enable) {
          ret = true;
        }
        else if(m_init_param.one_rx_one_tx_mode_use_rx_num == 1) {
          ret = true;
        }
      }
      else if(data_stream_id == m_ds_rx2) {
        if(m_init_param.two_rx_two_tx_mode_enable) {
          ret = true;
        }
        else if(m_init_param.one_rx_one_tx_mode_use_rx_num == 2) {
          ret = true;
        }
      }
      else if(data_stream_id == m_ds_tx1) {
        if(m_init_param.two_rx_two_tx_mode_enable) {
          ret = true;
        }
        else if(m_init_param.one_rx_one_tx_mode_use_tx_num == 1) {
          ret = true;
        }
      }
      else if(data_stream_id == m_ds_tx2) {
        if(m_init_param.two_rx_two_tx_mode_enable) {
          ret = true;
        }
        else if(m_init_param.one_rx_one_tx_mode_use_tx_num == 2) {
          ret = true;
        }
      }
    }
#endif
    return ret;
  }
  data_stream_direction_t get_data_stream_direction(data_stream_id_t id) {
    bool do_rx = get_rx_and_throw_if_invalid_ds(id);
    return do_rx ? data_stream_direction_t::rx : data_stream_direction_t::tx;
  }
  config_value_t get_tuning_freq_MHz(data_stream_id_t data_stream_id) {
    init_if_required();
    uint64_t val = 0;
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    do_rx ?
        this->log_info("noos ad9361_get_rx_lo_freq") :
        this->log_info("noos ad9361_get_tx_lo_freq");
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS get tuning freq");
    int32_t res = do_rx ?
        ad9361_get_rx_lo_freq(m_ad9361_rf_phy, &val) :
        ad9361_get_tx_lo_freq(m_ad9361_rf_phy, &val);
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
    return (config_value_t)val;
  }
  config_value_t get_bandwidth_3dB_MHz(data_stream_id_t data_stream_id) {
    init_if_required();
    uint32_t val = 0;
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    do_rx ?
        this->log_info("noos ad9361_get_rx_rf_bandwidth") :
        this->log_info("noos ad9361_get_tx_rf_bandwidth");
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS get bandwidth");
    int32_t res = do_rx ?
        ad9361_get_rx_rf_bandwidth(m_ad9361_rf_phy, &val) :
        ad9361_get_tx_rf_bandwidth(m_ad9361_rf_phy, &val);
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
    return (config_value_t)val;
  }
  config_value_t get_sampling_rate_Msps(data_stream_id_t data_stream_id) {
    init_if_required();
    uint32_t val = 0;
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    do_rx ?
        this->log_info("noos ad9361_get_rx_sampling_freq") :
        this->log_info("noos ad9361_get_tx_sampling_freq");
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS get sampling rate");
    int32_t res = do_rx ?
        ad9361_get_rx_sampling_freq(m_ad9361_rf_phy, &val) :
        ad9361_get_tx_sampling_freq(m_ad9361_rf_phy, &val);
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
    return (config_value_t)val;
  }
  bool get_samples_are_complex(data_stream_id_t data_stream_id) {
    get_rx_and_throw_if_invalid_ds(data_stream_id);
    return true;
  }
  gain_mode_value_t get_gain_mode(data_stream_id_t data_stream_id) {
    init_if_required();
    gain_mode_value_t ret = "manual";//gain_mode_value_t::manual;
    uint8_t val = 0;
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    if(do_rx) {
      this->log_info("noos ad9361_get_rx_gain_control_mode");
    }
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS get gain mode");
    // assign No-OS-specific "channel" macro (RX1/RX2/TX1/TX2 in ad9361_api.h)
    uint8_t ch;
    if(data_stream_id == m_ds_rx1) {
      if(m_ad9361_rf_phy->pdata->rx2tx2) {
        ch = RX1;
      }
      else {
        ch = (m_init_param.one_rx_one_tx_mode_use_rx_num == 1) ? RX1 : RX2;
      }
    }
    else if(data_stream_id == m_ds_rx2) {
      if(m_ad9361_rf_phy->pdata->rx2tx2) {
        ch = RX2;
      }
      else {
        ch = (m_init_param.one_rx_one_tx_mode_use_rx_num == 2) ? RX1 : RX2;
      }
    }
    if(do_rx) {
      int32_t res = ad9361_get_rx_gain_control_mode(m_ad9361_rf_phy, ch, &val);
      throw_if_no_os_api_call_returns_non_zero(res);
      if(val == RF_GAIN_MGC) {
        ret = "manual";
      }
      else if(val == RF_GAIN_FASTATTACK_AGC) {
        ret = "agc";
      }
      else if(val == RF_GAIN_SLOWATTACK_AGC) {
        ret = "agc";
      }
      else if(val == RF_GAIN_HYBRID_AGC) {
        ret = "agc";
      }
      else {
        throw std::string("invalid read ad9361_get_rx_gain_control_mode");
      }
    }
    else { // tx
      ret = "manual";//gain_mode_value_t::manual;
    }
#endif
    return ret;
  }
  config_value_t get_gain_dB(data_stream_id_t data_stream_id) {
    init_if_required();
    int32_t val_rx = 0;
    uint32_t val_tx = 0;
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    do_rx ?
        this->log_info("noos ad9361_get_rx_rf_gain") :
        this->log_info("noos ad9361_get_tx_attenuation");
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS get gain");
    auto& id = data_stream_id;
    // assign No-OS-specific "channel" macro (RX1/RX2/TX1/TX2 in ad9361_api.h)
    uint8_t ch = 
        (id == m_ds_rx1) ? RX1 :
        (id == m_ds_rx2) ? (m_ad9361_rf_phy->pdata->rx2tx2 ? RX2 : RX1) :
        (id == m_ds_tx1) ? TX1 :
        (id == m_ds_tx2) ? (m_ad9361_rf_phy->pdata->rx2tx2 ? TX2 : TX1) : RX1;
    int32_t res = do_rx ?
        ad9361_get_rx_rf_gain(    m_ad9361_rf_phy, ch, &val_rx) :
        ad9361_get_tx_attenuation(m_ad9361_rf_phy, ch, &val_tx);
    if(not do_rx) {
      val_tx = convert_milli_db_to_db(val_tx);
    }
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
    if(do_rx) {
      return (config_value_t)val_rx;
    }
    else {
      return (config_value_t)val_tx;
    }
  }
  void set_data_stream_direction(data_stream_id_t data_stream_id,
      data_stream_direction_t val) {
    get_rx_and_throw_if_invalid_ds(data_stream_id);
  }
  void set_tuning_freq_MHz(data_stream_id_t data_stream_id,
      config_value_t val) {
    init_if_required();
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    do_rx ?
        this->log_info("noos ad9361_set_rx_lo_freq %" PRIu64, (uint64_t)std::round(val*1000000.)) :
        this->log_info("noos ad9361_set_tx_lo_freq %" PRIu64, (uint64_t)std::round(val*1000000.));
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS set tuning freq");
    int32_t res = do_rx ?
        ad9361_set_rx_lo_freq(m_ad9361_rf_phy, (uint64_t)std::round(val*1000000.)) :
        ad9361_set_tx_lo_freq(m_ad9361_rf_phy, (uint64_t)std::round(val*1000000.));
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
  }
  void set_bandwidth_3dB_MHz(data_stream_id_t data_stream_id,
      config_value_t val) {
    init_if_required();
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    do_rx ?
        this->log_info("noos ad9361_set_rx_rf_bandwidth %" PRIu32, (uint32_t)std::round(val*1000000.)) :
        this->log_info("noos ad9361_set_tx_rf_bandwidth %" PRIu32, (uint32_t)std::round(val*1000000.));
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS set bandwidth");
    int32_t res = do_rx ?
        ad9361_set_rx_rf_bandwidth(m_ad9361_rf_phy, (uint32_t)std::round(val*1000000.)) :
        ad9361_set_tx_rf_bandwidth(m_ad9361_rf_phy, (uint32_t)std::round(val*1000000.));
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
  }
  void set_sampling_rate_Msps(
      data_stream_id_t data_stream_id, config_value_t val) {
    init_if_required();
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    do_rx ?
        this->log_info("noos ad9361_set_rx_sampling_freq %" PRIu32, (uint32_t)std::round(val*1000000.)) :
        this->log_info("noos ad9361_set_tx_sampling_freq %" PRIu32, (uint32_t)std::round(val*1000000.));
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS set sampling freq");
    int32_t res = do_rx ?
        ad9361_set_rx_sampling_freq(m_ad9361_rf_phy, (uint32_t)std::round(val*1000000.)) :
        ad9361_set_tx_sampling_freq(m_ad9361_rf_phy, (uint32_t)std::round(val*1000000.));
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
  }
  void set_samples_are_complex(data_stream_id_t data_stream_id,
      bool val) {
    // nothing to do on hardware, just validate settings
    if(val == false) {
      throw std::string("samples_are_complex must be set to true");
    }
    get_rx_and_throw_if_invalid_ds(data_stream_id);
  }
  void set_gain_mode(data_stream_id_t data_stream_id,
      gain_mode_value_t val) {
    init_if_required();
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    if((not do_rx) and val == "agc") {
      throw std::string("AGC is not a valid setting for TX");
    }
    if(do_rx) {
      this->log_info("noos ad9361_set_rx_gain_control_mode ??");
    }
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS set gain mode");
    // assign No-OS-specific "channel" macro (RX1/RX2/TX1/TX2 in ad9361_api.h)
    uint8_t ch =
        (data_stream_id == m_ds_rx1) ? RX1 :
        (data_stream_id == m_ds_rx2) ? (m_ad9361_rf_phy->pdata->rx2tx2 ? RX2 : RX1) : 0;
    uint8_t gc_mode = (val == "manual") ? RF_GAIN_MGC :
                      (val == "RF_GAIN_MGC") ? RF_GAIN_MGC :
                      (val == "auto") ? RF_GAIN_SLOWATTACK_AGC :
                      (val == "RF_GAIN_SLOWATTACK_AGC") ? RF_GAIN_SLOWATTACK_AGC :
                      (val == "RF_GAIN_FASTATTACK_AGC") ? RF_GAIN_FASTATTACK_AGC :
                      (val == "RF_GAIN_HYBRID_AGC ") ? RF_GAIN_HYBRID_AGC :
                      RF_GAIN_MGC;

    if(do_rx) {
      //this->log_info("noos ad9361_set_rx_gain_control_mode %" PRIu32 (uint32_t)gc_mode);
      int32_t res = do_rx ?
          ad9361_set_rx_gain_control_mode(m_ad9361_rf_phy, ch, gc_mode) : 0;
      throw_if_no_os_api_call_returns_non_zero(res);
    }
#endif
  }
  void set_gain_dB(data_stream_id_t data_stream_id,
      config_value_t val) {
    init_if_required();
    bool do_rx = get_rx_and_throw_if_invalid_ds(data_stream_id);
    do_rx ?
        this->log_info("noos ad9361_set_rx_rf_gain %" PRId32, (int32_t)std::round(val*1000000.)) :
        this->log_info("noos ad9361_set_tx_attenuation %" PRId32, (int32_t)std::round(val*1000000.));
#ifndef DISABLE_AD9361
    this->throw_if_ad9361_init_failed("No-OS set get");
    // assign No-OS-specific "channel" macro (RX1/RX2/TX1/TX2 in ad9361_api.h)
    uint8_t ch = (data_stream_id == m_ds_rx1) ? RX1 :
        (data_stream_id == m_ds_rx2) ?
        (m_ad9361_rf_phy->pdata->rx2tx2 ? RX2 : RX1) : 0;
    int32_t res = do_rx ?
        ad9361_set_rx_rf_gain(m_ad9361_rf_phy, ch, (int32_t)std::round(val)) :
        ad9361_set_tx_attenuation(m_ad9361_rf_phy, ch,
        (uint32_t)std::round(convert_db_to_milli_db(val)));
    throw_if_no_os_api_call_returns_non_zero(res);
#endif
  }
  ~AD9361DRC() {
#ifndef DISABLE_AD9361
    // only free internally managed No-OS memory
    ad9361_free(m_ad9361_rf_phy); // this function added in ad9361.patch
#endif
  }
}; // class AD9361DRC

} // namespace DRC

#endif // _AD9361_DRC_HH
