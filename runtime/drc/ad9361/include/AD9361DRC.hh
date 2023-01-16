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

#include "DRC.hh"
#include "LogForwarder.hh"
#ifndef DISABLE_AD9361
#include "RCC_Worker.h" // OCPI::RCC::RCCUserSlave
#endif

#ifndef DISABLE_AD9361
extern "C" {
#include "ad9361_api.h"
#include "ad9361.h" // (from No-OS) struct ad9361_rf_phy
#include "ad9361_platform.h"
}
#endif

namespace DRC {

// -----------------------------------------------------------------------------
// STEP 1 - IF IS_LOCKING SUPPORTED,
//          DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

///@TODO / FIXME handle DDC constant(s) in separate DDC/DUC class
class DDCDUCConstants {
  public:
  DDCDUCConstants();
  const double m_divider;
};

#ifdef IS_LOCKING
///@TODO / FIXME handle DDC constant(s) in separate DDC/DUC class
class AD9361CSP : public CSPBase, public DDCDUCConstants {
  protected:
  typedef CSPSolver::Constr::Cond Cond;
  typedef CSPSolver::Constr::Func Func;
  /* @brief for the AD9361,
   *        define variables (X) and their domains (D) for <X,D,C> which
   *        comprises its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void define_x_d_ad9361();
  /* @brief for the AD9361,
   *        define constraints (C) for <X,D,C> which
   *        comprise its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void define_c_ad9361();
  public:
  AD9361CSP();
  /* @brief instance AD9361
   *        by defining its Constraint Satisfaction Problem (CSP) as <X,D,C>
   ****************************************************************************/
  void instance_ad9361();
  /// @brief defining Constraint Satisfaction Problem (CSP)
  void define();
}; // class AD9361CSP
#endif

// -----------------------------------------------------------------------------
// STEP 2 - IF IS_LOCKING SUPPORTED, DEFINE CONFIGURATOR THAT UTILIZES THE CSP
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class AD9361Configurator : public Configurator<AD9361CSP> {
  public:
  AD9361Configurator();
};
#endif

// -----------------------------------------------------------------------------
// STEP 3 - DEFINE DRC (get/set APIs)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
#define AD9361_CONFIGURATOR AD9361Configurator
#else
#define AD9361_CONFIGURATOR Configurator<CSPBase>
#endif

/*! @brief ad9361_config worker's props whose purpose is to read back
 *         the static configuration of the FPGA bitstream - reference the OWD.
 ******************************************************************************/
struct Ad9361ConfigConfig {
  bool qadc1_is_present;
  bool qdac1_is_present;
  bool rx_frame_toggle;
  bool data_bus_index_reverse;
  bool data_clk_is_inverted;
  bool rx_frame_is_inverted;
  bool LVDS;
  bool single_port;
  bool swap_ports;
  bool half_duplex;
  bool data_rate_ddr;
};

/*! @brief ad9361_data_sub worker's props whose purpose is to read back
 *         the static configuration of the FPGA bitstream - reference the OWD.
 ******************************************************************************/
struct Ad9361DataSubConfig {
  uint16_t DATA_CLK_Delay;
  uint16_t RX_Data_Delay;
  uint16_t FB_CLK_Delay;
  uint16_t TX_Data_Delay;
};

/*! @brief Purpose is to read back the static configuration of the FPGA
 *         bitstream.
 ******************************************************************************/
struct Ad9361InitConfig : Ad9361ConfigConfig, Ad9361DataSubConfig {
  bool xo_disable_use_ext_ref_clk;
  double ext_ref_clk_freq;  
};

// TODO: sort out the multi-device issues of device args vs. separate callback objects
struct AD9361DeviceCallBack {
  // First three here are from the low level ADI library
  virtual void get_byte(uint8_t /*id_no*/, uint16_t addr, uint8_t *buf) = 0;
  virtual void set_byte(uint8_t /*id_no*/, uint16_t addr, const uint8_t *buf) = 0;
  virtual void set_reset(uint8_t id_no, bool on) = 0;
  // These are touching the DSP slaves
  virtual bool isMixerPresent(bool rx, unsigned /*stream*/) = 0;
  virtual config_value_t getDecimation(unsigned /*stream*/) = 0; // return 1 if not present
  virtual config_value_t getInterpolation(unsigned stream) = 0;  // return 1 if not present
  virtual config_value_t getPhaseIncrement(bool rx, unsigned stream) = 0; // return 0 if not present
  virtual void setPhaseIncrement(bool rx, unsigned stream, int16_t inc) = 0; // ignore if not present
  // These are three hooks during initial configuration
  virtual void initialConfig(uint8_t id_no, Ad9361InitConfig &config) = 0; // before a config attempt
  virtual void postConfig(uint8_t id_no) = 0;  // after a config attempt, on success or failure
  virtual void finalConfig(uint8_t id_no, Ad9361InitConfig &config) = 0; // after a config attempt, on success
  // These are for both channels
  virtual unsigned getRfInput(unsigned device, config_value_t tuning_freq_MHz) = 0;
  virtual unsigned getRfOutput(unsigned device, config_value_t tuning_freq_MHz) = 0;
};

#ifndef DISABLE_AD9361
// A templated helper function that simply initializes our Ad9361InitialConfig from the two required slaves
// and performs any other worker actions required prior to the call to ad9361_init.
template<class Config, class DataSub> void
ad9361InitialConfig(Config &config, DataSub &dataSub, Ad9361InitConfig &cfg) {
  memset(&cfg, 0, sizeof(cfg)); // a known initial state
  // set this default to use ext ref clk, not dcxo
  cfg.xo_disable_use_ext_ref_clk = true;

  // set the default external reference clock frequency 
  cfg.ext_ref_clk_freq = 40e6;

  // don't care about qadc0_is_present
  cfg.qadc1_is_present         = config.get_qadc1_is_present();
  // don't care about qadc1_is_present
  cfg.qdac1_is_present         = config.get_qdac1_is_present();
  cfg.rx_frame_toggle          = config.get_rx_frame_usage() != 0;
  cfg.data_bus_index_reverse   = config.get_data_bus_index_direction() != 0;
  cfg.data_clk_is_inverted     = config.get_data_clk_is_inverted();
  cfg.rx_frame_is_inverted     = config.get_rx_frame_is_inverted();
  cfg.LVDS                     = config.get_LVDS();
  cfg.single_port              = config.get_single_port();
  cfg.swap_ports               = config.get_swap_ports();
  cfg.half_duplex              = config.get_half_duplex();
  cfg.data_rate_ddr            = config.get_data_rate_config() != 0;

  if (dataSub.isPresent()) {
    cfg.DATA_CLK_Delay = dataSub.get_DATA_CLK_Delay();
    cfg.RX_Data_Delay = dataSub.get_RX_Data_Delay();
    cfg.FB_CLK_Delay = dataSub.get_FB_CLK_Delay();
    cfg.TX_Data_Delay = dataSub.get_TX_Data_Delay();
  }
  // ADI forum post recommended setting ENABLE/TXNRX pins high *prior to
  // ad9361_init() call* when
  // frequency_division_duplex_independent_mode_enable is set to 1
  config.set_ENABLE_force_set(true);
  config.set_TXNRX_force_set(true);
  // here is where we enforce the ad9361_config OWD comment
  // "[the force_two_r_two_t_timing] property is expected to correspond to the
  // D2 bit of the Parallel Port Configuration 1 register at SPI address 0x010
  config.set_force_two_r_two_t_timing(false);
  // Tell the config whether we asked for FDD or not.  Curious since it knows it already...
  config.set_Half_Duplex_Mode(cfg.half_duplex);
}

// A templated helper function that simply initializes the Ad9361BitStreamConfig from the two required slaves
// and performs any other actions required prior to the call to ad9361_init.
template<class Config> void
ad9361PostConfig(Config &config) {
  config.set_ENABLE_force_set(false);
  config.set_TXNRX_force_set(false);
}

// A templated helper function that simply initializes the Ad9361BitStreamConfig from the two required slaves
// and performs any other actions required prior to the call to ad9361_init.
template<class Config> void
ad9361FinalConfig(Config &config, Ad9361InitConfig &/*cfg*/) {
  // enforce_ensm_config
  uint8_t
    ensm_config_1 = config.get_ensm_config_1(),
    ensm_config_2 = config.get_ensm_config_2(),
    // because channel config potentially changed
    general_rx_enable_filter_ctrl = config.get_general_rx_enable_filter_ctrl(),
    general_tx_enable_filter_ctrl = config.get_general_tx_enable_filter_ctrl();

  config.set_ENSM_Pin_Control((ensm_config_1 & 0x10) == 0x10);
  config.set_Level_Mode((ensm_config_1 & 0x08) == 0x08);
  config.set_FDD_External_Control_Enable((ensm_config_2 & 0x80) == 0x80);
  config.set_config_is_two_r(RX_CHANNEL_ENABLE(RX_1 | RX_2) == (general_rx_enable_filter_ctrl & 0xc0));
  config.set_config_is_two_t(TX_CHANNEL_ENABLE(TX_1 | TX_2) == (general_tx_enable_filter_ctrl & 0xc0));
}
#endif

///@TODO / FIXME handle DDC constant(s) in separate DDC/DUC class
template<class log_t,class cfgrtr_t = AD9361_CONFIGURATOR>
class AD9361DRC : public DRC<log_t,cfgrtr_t>, public DDCDUCConstants {
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
  AD9361DeviceCallBack   &m_callback;
  unsigned               m_device;
  template<typename T> T convert_milli_db_to_db(T val_milli_db) const;
  template<typename T> T convert_db_to_milli_db(T val_milli_db) const;
#ifndef DISABLE_AD9361
  void init_init_param();
  bool any_configurator_configs_locked_which_prevent_ad9361_init() const;
  void throw_if_ad9361_init_failed(const char* operation) const;
  void apply_config_to_init_param(const Ad9361InitConfig &config);
  void enforce_ensm_config();
  void set_ad9361_fpga_channel_config();
#endif
  void init_if_required();
  public:
  AD9361DRC<log_t, cfgrtr_t>(unsigned which,
      AD9361DeviceCallBack &dev, double fref_hz,
      const char* rx1 = "rx1",const char* rx2 = "rx2",
      const char* tx1 = "tx1",const char* tx2 = "tx2",
      const char* descriptor = "AD9361");
  bool get_rx_and_throw_if_invalid_ds(data_stream_id_t data_stream_id) const;
  void set_rx_rf_port_input(uint32_t mode);
  void set_tx_rf_port_output(uint32_t mode);
  void throw_if_no_os_api_call_returns_non_zero(int32_t res);
  bool                    get_data_stream_is_enabled(data_stream_id_t id);
  data_stream_direction_t get_data_stream_direction( data_stream_id_t id);
  config_value_t          get_tuning_freq_MHz(       data_stream_id_t id);
  config_value_t          get_bandwidth_3dB_MHz(     data_stream_id_t id);
  config_value_t          get_sampling_rate_Msps(    data_stream_id_t id);
  bool                    get_samples_are_complex(   data_stream_id_t id);
  gain_mode_value_t       get_gain_mode(             data_stream_id_t id);
  config_value_t          get_gain_dB(               data_stream_id_t id);
  void set_data_stream_direction(data_stream_id_t id,data_stream_direction_t v);
  void set_tuning_freq_MHz(      data_stream_id_t id,config_value_t    val);
  void set_bandwidth_3dB_MHz(    data_stream_id_t id,config_value_t    val);
  void set_sampling_rate_Msps(   data_stream_id_t id,config_value_t    val);
  void set_samples_are_complex(  data_stream_id_t id,bool              val);
  void set_gain_mode(            data_stream_id_t id,gain_mode_value_t val);
  void set_gain_dB(              data_stream_id_t id,config_value_t    val);
  bool request_config_lock(const config_lock_id_t id,
      const ConfigLockRequest& request);
  void init();
  bool shutdown();
  ~AD9361DRC();
}; // class AD9361DRC

} // namespace DRC

#include "AD9361DRC.cc"

#endif // _AD9361_DRC_HH
