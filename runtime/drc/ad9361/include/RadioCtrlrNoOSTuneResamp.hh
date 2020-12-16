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

#ifndef _OCPI_PROJECTS_RADIO_CTRLR_NO_OS_TUNE_RESAMP_HH
#define _OCPI_PROJECTS_RADIO_CTRLR_NO_OS_TUNE_RESAMP_HH

#include <cstring>
#include "RadioCtrlr.hh"   // DigRadioCtrlr
#include "RadioCtrlrConfiguratorAD9361.hh"

// needed to use ADI No-OS library (via the OpenCPI ad9361 prerequisite)
extern "C" {
#include "ad9361_api.h" // from No-OS
}
namespace OCPI {

namespace DRC {

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
};

/// @brief Callbacks to proxy worker (and its slaves) for register access, etc.
  
// TODO: sort out the multi-device issues of device args vs. separate callback objects
struct DeviceCallBack {
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
// A templated helper function that simply initializes our Ad9361InitialConfig from the two required slaves
// and performs any other worker actions required prior to the call to ad9361_init.
template<class Config, class DataSub> void
ad9361InitialConfig(Config &config, DataSub &dataSub, Ad9361InitConfig &cfg) {
  memset(&cfg, 0, sizeof(cfg)); // a known initial state
  // set this default to use ext ref clk, not dcxo
  cfg.xo_disable_use_ext_ref_clk = true;
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
/// @brief controls AD9361 via an OpenCPI device proxy's slaves
class RadioCtrlrNoOSTuneResamp : public DigRadioCtrlr {

  DeviceCallBack &m_callBack;

protected : ConfiguratorAD9361 &m_configurator;
protected : unsigned m_device;
/// @brief No-OS struct pointer which is only used if managing No-OS internally
protected : struct ad9361_rf_phy* _ad9361_rf_phy;

/// @brief No-OS struct pointer (used in all scenarios)
protected : struct ad9361_rf_phy*& m_ad9361_rf_phy;

protected : const double m_AD9361_FREF_Hz;

protected : int32_t m_ad9361_init_ret;

protected : bool m_ad9361_init_called;

/// @brief No-OS struct used to initialize AD9361
protected : AD9361_InitParam m_AD9361_InitParam;

protected : bool m_configurator_tune_resamp_locked;

protected : bool m_readback_gain_mode_as_standard_value;

/*! @brief Managing No-OS internally (this class instanced somewhere that
 *         doesn't need to use No-OS).
 ******************************************************************************/
public    : RadioCtrlrNoOSTuneResamp(unsigned which, const char *descriptor, ConfiguratorAD9361 &c,
				     DeviceCallBack &dev);

#if 0
/*! @brief Managing No-OS externally (this class instanced somewhere that
 *         doesn't need to use No-OS). ad9361_rf_phy must be freed
 *         (using ad9361_free) outside of this class!!
 ******************************************************************************/
public    : RadioCtrlrNoOSTuneResamp(const char *descriptor, Configurator &c, DSPCallback &dsp, slaves_t &slaves,
                struct ad9361_rf_phy *&ad9361_rf_phy);
#endif
private: const std::string &RX1_id() const { return m_configurator.RX1_id(); }
private: const std::string &RX2_id() const { return m_configurator.RX2_id(); }
private: const std::string &TX1_id() const { return m_configurator.TX1_id(); }
private: const std::string &TX2_id() const { return m_configurator.TX2_id(); }

public    : virtual bool request_config_lock(
                config_lock_ID_t         config_lock_ID,
                const ConfigLockRequest& config_lock_request);

/*! @brief     Requests configurator lock, and if that succeeds, attempt to set
 *             on-hardware value to desired value.
 *  @param[in] ds_ID Data stream ID for which to apply lock.
 *  @param[in] inst  Application instance name of complex_mixer worker which
 *                   is associated with the data stream ID (*THIS* is why
 *                   we have a routing ID).
 *  @param[in] val   Desired value to lock to.
 *  @param[in] tol   If the configurator lock succeeds and the read back
 *                   on-hardware value is within val +/- tol, the lock will be
 *                   considered successful.
 *  @return    Boolean indicator of success.
 ******************************************************************************/
protected : bool lock_tuning_freq_complex_mixer_MHz(data_stream_ID_t   ds_ID,
                                                    bool tx, unsigned which,
                                                    config_value_t     val,
                                                    config_value_t     tol);

/// @brief Unlocks configurator lock (no hardware action is performed).
protected : void unlock_tuning_freq_complex_mixer_MHz(data_stream_ID_t ds_ID);

public    : void throw_if_data_stream_lock_request_malformed(
                const DataStreamConfigLockRequest&
                data_stream_config_lock_request) const;

/*! @brief Performs the minimum config locks required per data stream
 *         for a AnaRadioCtrlr.
 ******************************************************************************/
protected : virtual bool do_min_data_stream_config_locks(
                data_stream_ID_t ds_ID, const DataStreamConfigLockRequest& req);

/*! @brief Measure value as it exists on hardware. Exception will be throw
 *         if hardware access fails or if invalid data stream ID is
 *         requested.
 ******************************************************************************/
public    : Meas<config_value_t> get_tuning_freq_MHz(
                data_stream_ID_t data_stream_ID) const;
/*! @brief Measure value as it exists on hardware. Exception will be throw
 *         if hardware access fails or if invalid data stream ID is
 *         requested.
 ******************************************************************************/
public    : Meas<config_value_t> get_bandwidth_3dB_MHz(
                data_stream_ID_t data_stream_ID) const;
/*! @brief Determine whether the AD9361 data stream is powered on, fully
 *         active, and data is flowing.
 ******************************************************************************/
public    : bool get_data_stream_is_enabled(
                data_stream_ID_t data_stream_ID) const;
/*! @brief Measure value as it exists on hardware. Exception will be throw
 *         if hardware access fails or if invalid data stream ID is
 *         requested.
 ******************************************************************************/
public    : Meas<config_value_t> get_sampling_rate_Msps(
                data_stream_ID_t data_stream_ID) const;
/*! @brief Measure value as it exists on hardware. Exception will be throw
 *         only if invalid data stream ID is requested.
 ******************************************************************************/
public    : bool get_samples_are_complex(
                data_stream_ID_t data_stream_ID) const;
/*! @brief Measure value as it exists on hardware. Exception will be throw
 *         if hardware access fails or if invalid data stream ID is
 *         requested.
 ******************************************************************************/
public    : Meas<gain_mode_value_t> get_gain_mode(
                data_stream_ID_t data_stream_ID) const;
/*! @brief Measure value as it exists on hardware. Exception will be throw
 *         if hardware access fails or if invalid data stream ID is
 *         requested.
 ******************************************************************************/
public    : Meas<config_value_t> get_gain_dB(
                data_stream_ID_t data_stream_ID) const;

public    : virtual void unlock_all();

public    : std::vector<gain_mode_value_t>
            get_ranges_possible_gain_mode(
                data_stream_ID_t data_stream_ID) const;

public    : ~RadioCtrlrNoOSTuneResamp();

/*! @brief  Attempt to set on-hardware value with no guarantee of success.
 *          Exception will be thrown if invalid data stream ID is requested.
 *          or if hardware access fails.
 *  @return Value measured after set attempt.
 ******************************************************************************/
protected : Meas<config_value_t> set_tuning_freq_MHz(
                data_stream_ID_t data_stream_ID,
                config_value_t   tuning_freq_MHz);
/*! @brief  Attempt to set on-hardware value with no guarantee of success.
 *          Exception will be thrown if invalid data stream ID is requested.
 *          or if hardware access fails.
 *  @return Value measured after set attempt.
 ******************************************************************************/
protected : Meas<config_value_t> set_bandwidth_3dB_MHz(
                data_stream_ID_t         data_stream_ID,
                config_value_t bandwidth_3dB_MHz);
/*! @brief  Attempt to set on-hardware value with no guarantee of success.
 *          Exception will be thrown if invalid data stream ID is requested.
 *          or if hardware access fails.
 *  @return Value measured after set attempt.
 ******************************************************************************/
protected : Meas<config_value_t> set_sampling_rate_Msps(
                data_stream_ID_t data_stream_ID,
                config_value_t   sampling_rate_Msps);
/*! @brief  Attempt to set on-hardware value with no guarantee of success.
 *          Exception will be thrown if invalid data stream ID is requested.
 *          or if hardware access fails.
 *  @return Value measured after set attempt.
 ******************************************************************************/
protected : bool set_samples_are_complex(
                data_stream_ID_t data_stream_ID,
                bool             samples_are_complex);
/*! @brief  Attempt to set on-hardware value with no guarantee of success.
 *          Exception will be thrown if invalid data stream ID is requested.
 *          or if hardware access fails.
 *  @return Value measured after set attempt.
 ******************************************************************************/
protected : Meas<gain_mode_value_t> set_gain_mode(
                data_stream_ID_t  data_stream_ID,
                gain_mode_value_t gain_mode);
/*! @brief  Attempt to set on-hardware value with no guarantee of success.
 *          Exception will be thrown if invalid data stream ID is requested.
 *          or if hardware access fails.
 *  @return Value measured after set attempt.
 ******************************************************************************/
protected : Meas<config_value_t> set_gain_dB(
                data_stream_ID_t data_stream_ID,
                config_value_t   gain_dB);
/*! @brief  Attempt to set on-hardware value with no guarantee of success.
 *          Exception will be thrown if invalid data stream ID is requested.
 *          or if hardware access fails.
 *  @return Value measured after set attempt.
 ******************************************************************************/
protected : Meas<config_value_t> set_tuning_freq_complex_mixer_MHz(
                const data_stream_ID_t data_stream_ID,
		bool tx, unsigned which,
                const config_value_t   tuning_freq_MHz);

/*! @brief Measure value as it exists on hardware.
 *  @param[in] data_stream_ID
 *  @param[in] inst  Application instance name of complex_mixer worker which
 *                   is associated with the data stream ID (*THIS* is why
 *                   we have a routing ID).
 ******************************************************************************/
protected : Meas<config_value_t> get_tuning_freq_complex_mixer_MHz(
              const data_stream_ID_t data_stream_ID,
              bool tx, unsigned which) const;

//protected :  bool lock_gain_mode(data_stream_ID_t  ds_ID,
//                                 gain_mode_value_t val);

/*! @brief Get configurator data stream ID which maps to the controller
 *         data stream ID.
 *  @param[in] ctrlr_ds_ID Controller data stream ID.
 *  @return                Configurator data stream ID.
 ******************************************************************************/
protected : data_stream_ID_t get_configurator_ds_ID(
                const data_stream_ID_t& ctrlr_ds_ID) const;

protected : void log_debug_ad9361_init(const AD9361_InitParam &init_param) const;

/*! @brief Initialize No-OS/the AD9361. Not needed to be called outside of this
 *         class for normal config lock use. Is necessary outside of this class,
 *         for example, when doing something like enabling BIST loopback on
 *         AD9361 (outside of this class) before this class performs a config
 *         lock.
 ******************************************************************************/
public    : void init();

protected : void init_AD9361_InitParam();
protected : void update_AD9361_InitParam(const Ad9361InitConfig &cfg);
#if 0
protected : void enforce_ensm_config();

protected : void configurator_lock_cic_dec(data_stream_ID_t ds_ID,
                unsigned which, configurator_t& configurator);

protected : void configurator_lock_cic_int(data_stream_ID_t ds_ID,
                unsigned which, configurator_t& configurator);

protected : void configurator_lock_complex_mixer(data_stream_ID_t ds_ID,
						 bool tx, unsigned which, configurator_t& configurator);

protected : void ensure_configurator_lock_tune_resamp();
#endif

/*! @brief 1. Checks if configurator will allow lock request (check only,
 *            don't actually lock configurator or hardware values yet)
 *         2. If configurator will allow lock, re-initialize AD9361 if it
 *            is necessary for the lock that is about to occur.
 *  @param[in]  config_lock_request
 *  @param[out] requires_reinit      This function sets this to inidicate that
 *                                   an AD9361 re-initialization must occur.
 *  @return Boolean indicator that lock is expected to succeed.
 ******************************************************************************/
protected : bool configurator_check_and_reinit(const ConfigLockRequest &config_lock_request);

/*! @param[in]  reql_RX2B            A lock of the SMA_RX2B data stream is
 *                                   required/pending.
 *  @param[in]  reql_RX2A            A lock of the SMA_RX2A data stream is
 *                                   required/pending.
 *  @param[in]  reql_TRXB            A lock of the SMA_TRXB data stream is
 *                                   required/pending.
 *  @param[in]  reql_TRXA            A lock of the SMA_TRXA data stream is
 *                                   required/pending.
 *  @param[in]  configurator_copy    Reference to COPY of m_configurator.
 *  @return Boolean indication of whether any initialization procedure failed
 *          (which may occur depending on current config locks)
 ******************************************************************************/
protected : bool reinit_AD9361_if_required(bool reql_RX2B, bool reql_RX2A,
                bool reql_TRXB, bool reql_TRXA,
                const Configurator& configurator_copy);

protected : bool any_configurator_configs_locked_which_prevent_ad9361_init()
                const;

protected:
template<typename T>
const char* get_No_OS_err_str(const char* API_function_cstr,
    T API_call_return_val) const {
  std::ostringstream oss;
  oss << "No-OS API call " << API_function_cstr << "()";
  oss << " returned error: \"" << strerror(-API_call_return_val) << "\"";
  return oss.str().c_str();
}

protected : unsigned get_complex_mixer(const DataStreamConfigLockRequest& req, bool &tx) const;
protected : unsigned get_cic_dec(
                const DataStreamConfigLockRequest& req) const;
protected : unsigned get_cic_int(
                const DataStreamConfigLockRequest& req) const;

protected : void throw_if_ad9361_init_failed(const char* operation = 0) const;

}; // class RadioCtrlrNoOSTuneResamp

} // namespace DRC

} // namespace OCPI

#endif // _OCPI_PROJECTS_RADIO_CTRLR_NO_OS_TUNE_RESAMP_HH
