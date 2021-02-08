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

#include <cstdint>  // int32_t, uint8_t, etc
#include <cassert>
#include <memory>   // std::unique_ptr
#include <sstream>  // std::ostringstream
#include <cmath>    // round()
#include <unistd.h> // usleep()
#include <cinttypes> // PRIu32
#include "UtilValidRanges.hh" // Util::Range, Util::ValidRanges
#include "RadioCtrlrNoOSTuneResamp.hh"
#include "read_ad9361.h"
#include "OcpiOsDebugApi.hh"

extern "C" {
#include "ad9361.h" // (from No-OS) struct ad9361_rf_phy
#include "ad9361_platform.h"
}

namespace OCPI {

namespace DRC {

namespace OU = OCPI::Util;

static std::vector<DeviceCallBack*> g_devices;

RadioCtrlrNoOSTuneResamp::
RadioCtrlrNoOSTuneResamp(unsigned which, const char* descriptor, ConfiguratorAD9361 &c,
			 DeviceCallBack &dev) :
    DigRadioCtrlr(descriptor, c),
    m_callBack(dev),
    m_configurator(c),
    m_device(which),
    _ad9361_rf_phy(0),
    m_ad9361_rf_phy(_ad9361_rf_phy),
    m_AD9361_FREF_Hz(40e6), // just to match up w/ configurator for now...
    m_ad9361_init_ret(-1),
    m_ad9361_init_called(false),
    m_configurator_tune_resamp_locked(false),
    m_readback_gain_mode_as_standard_value(false) {

  init_AD9361_InitParam();
}

bool RadioCtrlrNoOSTuneResamp::request_config_lock(
    const config_lock_ID_t   config_lock_ID,
    const ConfigLockRequest& config_lock_request) {

  if(not configurator_check_and_reinit(config_lock_request)) {
    return false;
  }

  auto ID = config_lock_ID;
  auto request = config_lock_request;
  return DigRadioCtrlr::request_config_lock(ID,request);
}

bool RadioCtrlrNoOSTuneResamp::
lock_tuning_freq_complex_mixer_MHz(const data_stream_ID_t ds_ID, bool tx, unsigned which,
				   const config_value_t val, const config_value_t tol) {
  // the configurator, which is a software emulation of hardware capabilties,
  // tells us whether a hardware attempt to set value will corrupt
  // any existing locks
  const config_key_t cfg_key = "tuning_freq_complex_mixer_MHz";
  bool did_lock = this->m_configurator.lock_config(ds_ID, cfg_key, val, tol);

  bool is = false; // is within tolerance
  if(did_lock) {
    Meas<config_value_t> meas = set_tuning_freq_complex_mixer_MHz(ds_ID, tx, which, val);

    is = this->config_val_is_within_tolerance(val, tol, meas);

    this->log_info_config_lock_tol(did_lock, is, ds_ID, val, tol, cfg_key, "MHz", &meas);
  }
  else {
    this->log_info_config_lock_tol(did_lock, is, ds_ID, val, tol, cfg_key, "MHz");
  }

  return did_lock and is;
}

void RadioCtrlrNoOSTuneResamp::unlock_tuning_freq_complex_mixer_MHz(
    const data_stream_ID_t ds_ID) {
  
  this->unlock_config(ds_ID, "tuning_freq_complex_mixer_MHz");
}

bool RadioCtrlrNoOSTuneResamp::do_min_data_stream_config_locks(
    const data_stream_ID_t             ds_ID,
    const DataStreamConfigLockRequest& req) {

  throw_if_data_stream_lock_request_malformed(req);

  config_key_t key;
  config_value_t val, tol;
  std::string value;
  unsigned which;
  if (ds_ID == TX1_id() || ds_ID == TX2_id()) {
    key = "CIC_int_interpolation_factor";
    which = get_cic_int(req);
    val = m_callBack.getInterpolation(which);
  } else if (ds_ID == RX1_id() || ds_ID == RX2_id()) {
    key = "CIC_dec_decimation_factor";
    which = get_cic_dec(req);
    val = m_callBack.getDecimation(which);
  } else
    assert(!"ds_ID unexpected");
  tol = 0;
  if (!m_configurator.lock_config(ds_ID, key, val, tol)) {
    this->log_debug("unexpected config lock failure");
    goto unrollandfail;
  }

  // there is currently no use case to lock complex_mixer tune freq to any
  // value other than 0
  val = 0.;
  tol = 0.;

  bool tx;
  which = get_complex_mixer(req, tx);
  
  if (!m_callBack.isMixerPresent(!tx, which)) {
    key = "tuning_freq_complex_mixer_MHz";
    // intentionally ignoring return value
    m_configurator.lock_config(ds_ID, key, val, tol);
  } else {
    this->log_debug("data stream %s, which is associated w/ routing ID %s, has complex mixer",
		    ds_ID.c_str(), req.get_routing_ID().c_str());
    if (not lock_tuning_freq_complex_mixer_MHz(ds_ID, tx, which, val, tol)) {
      goto unrollandfail;
    }
  }

  if(not DigRadioCtrlr::do_min_data_stream_config_locks(ds_ID, req)) {
    return false; // unroll done inside do_min...(), so not necessary again
  }

  return true;

  unrollandfail:
  if((ds_ID == TX2_id()) or (ds_ID == TX1_id())) {
    m_configurator.unlock_config(ds_ID, "CIC_int_interpolation_factor");
  }
  else if((ds_ID == RX2_id()) or (ds_ID == RX1_id())) {
    m_configurator.unlock_config(ds_ID, "CIC_dec_decimation_factor");
  }
  unlock_tuning_freq_complex_mixer_MHz(ds_ID);
  return false;
}

void RadioCtrlrNoOSTuneResamp::throw_if_data_stream_lock_request_malformed(
    const DataStreamConfigLockRequest& req) const {

  DigRadioCtrlr::throw_if_data_stream_lock_request_malformed(req);

  // this class's implementation data stream config lock requests to include
  // routing ID (because there is more than one data stream of the same type)
  if(not req.get_including_routing_ID()) {
    throw std::string("radio controller's data stream config lock request malformed: did not include routing ID");
  }

  if((req.get_routing_ID() != "RX0") and
     (req.get_routing_ID() == "RX1") and
     (req.get_routing_ID() == "TX0") and
     (req.get_routing_ID() == "TX1")) {
    std::ostringstream oss;
    oss << "radio controller's data stream config lock request malformed: ";
    oss << "routing ID of " << req.get_routing_ID() << " was not one of the ";
    oss << "supported value: RX0, RX1, TX0, TX1";
    throw oss.str();
  }
}

Meas<config_value_t> RadioCtrlrNoOSTuneResamp::get_tuning_freq_MHz(
    const data_stream_ID_t data_stream_ID) const {

  this->throw_if_data_stream_disabled_for_read(data_stream_ID, "tuning freq");

  if(not m_ad9361_init_called) {
    throw std::string("attempted to read one of the AD961 data stream's tuning_freq_MHz values before AD9361 was initialized");
  }

  // this function essentially maps the generic representation which a
  // digital radio controller provides to methods which calculate
  // the thereotical value (direct AD9361 register reads) with high precision

  std::unique_ptr<Configurator> copy(m_configurator.clone());
  Configurator &configurator_copy = *copy;
  if((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id())) {

    const ConfigValueRanges& x = configurator_copy.get_ranges_possible(data_stream_ID,"tuning_freq_complex_mixer_MHz");

    /// @todo / FIXME - get locked value instead of assuming smallest min is equivalent to locked value
    config_value_t tuning_freq_complex_mixer_MHz = x.get_smallest_min();

    Meas<config_value_t> meas(meas_type_t::THEORETICAL);
    meas.m_unit.assign("MHz"); // we usually stick with MHz as the standard

    double val;
    const double& fref = m_AD9361_FREF_Hz;
    this->throw_if_ad9361_init_failed("calculation of Rx RFPLL LO freq Hz based on AD9361 register contents");

    const char* err = get_ad9361_rx_rfpll_lo_freq_hz(m_ad9361_rf_phy, fref, val);
    if(err != 0) {
      throw err;
    }
    meas.m_value = (val/1e6) - tuning_freq_complex_mixer_MHz;
    std::ostringstream oss;
    oss << meas;
    this->log_debug("data stream: %s, read from hardware tuning freq value of: %s", data_stream_ID.c_str(), oss.str().c_str());

    return meas;
  }
  else if((data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {

    const ConfigValueRanges& x = configurator_copy.get_ranges_possible(data_stream_ID,"tuning_freq_complex_mixer_MHz");

    /// @todo / FIXME - get locked value instead of assuming smallest min is equivalent to locked value
    config_value_t tuning_freq_complex_mixer_MHz = x.get_smallest_min();

    // get_AD9361_Tx_RFPLL_LO_freq_Hz() is a (highly precise) theoretical
    // calculation based upon AD9361 register values
    Meas<config_value_t> meas(meas_type_t::THEORETICAL);
    meas.m_unit.assign("MHz"); // we usually stick with MHz as the standard

    double val;
    const double& fref = m_AD9361_FREF_Hz;
    this->throw_if_ad9361_init_failed("calculation of Tx RFPLL LO freq Hz based on AD9361 register contents");
    const char* err = get_ad9361_tx_rfpll_lo_freq_hz(m_ad9361_rf_phy, fref, val);
    if(err != 0) {
      throw err;
    }
    meas.m_value = (val/1e6) - tuning_freq_complex_mixer_MHz;
    std::ostringstream oss;
    oss << meas;
    this->log_debug("data stream: %s, read from hardware tuning freq value of: %s", data_stream_ID.c_str(), oss.str().c_str());

    return meas;
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
}

Meas<config_value_t> RadioCtrlrNoOSTuneResamp::get_bandwidth_3dB_MHz(
    const data_stream_ID_t data_stream_ID) const {

  this->throw_if_data_stream_disabled_for_read(data_stream_ID, "bandwidth");

  if(not m_ad9361_init_called) {
    throw std::string("attempted to read one of the AD961 data stream's bandwidth_3dB_MHz values before AD9361 was initialized");
  }

  if((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id())) {

    // No-OS ad9361_get_rx_rf_bandwidth() call has nominal precision only
    Meas<config_value_t> meas(meas_type_t::NOMINAL);
    meas.m_unit.assign("MHz"); // we usually stick with MHz as the standard

    uint32_t bandwidth_hz;
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_get_rx_rf_bandwidth()");
    int32_t ret = ad9361_get_rx_rf_bandwidth(m_ad9361_rf_phy, &bandwidth_hz);
    if(ret != 0) {
      throw this->get_No_OS_err_str("ad9361_get_rx_rf_bandwidth", ret);
    }
    this->log_debug("No-OS call: ad9361_get_rx_rf_bandwidth, read value: %" PRIu32, bandwidth_hz);
    meas.m_value = ((double) bandwidth_hz) / 1e6;
    std::ostringstream oss;
    oss << meas;
    this->log_debug("data stream: %s, read from hardware AD9361 rx_rf_bandwidth value of: %s", data_stream_ID.c_str(), oss.str().c_str());
  
    return meas;
  }
  else if((data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {

    // No-OS ad9361_get_tx_rf_bandwidth() call has nominal precision
    Meas<config_value_t> meas(meas_type_t::NOMINAL);
    meas.m_unit.assign("MHz"); // we usually stick with MHz as the standard

    //NO_OS_CALL(ret, ad9361_get_tx_rf_bandwidth, phy, meas.m_value)
    uint32_t bandwidth_hz;
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_get_tx_rf_bandwidth()");
    int32_t ret = ad9361_get_tx_rf_bandwidth(m_ad9361_rf_phy, &bandwidth_hz);
    if(ret != 0) {
      throw this->get_No_OS_err_str("ad9361_get_tx_rf_bandwidth", ret);
    }
    this->log_debug("No-OS call: ad9361_get_tx_rf_bandwidth, read value: %" PRIu32, bandwidth_hz);
    meas.m_value = ((double) bandwidth_hz) / 1e6;
    std::ostringstream oss;
    oss << meas;
    this->log_debug("read from hardware AD9361 tx_rf_bandwidth value of: %s", oss.str().c_str());

    return meas;
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
}

Meas<config_value_t> RadioCtrlrNoOSTuneResamp::
get_tuning_freq_complex_mixer_MHz(const data_stream_ID_t data_stream_ID, bool  tx, unsigned which) const {

  std::string value;

  this->throw_if_data_stream_disabled_for_read(data_stream_ID, "complex_mixer tuning freq");

  if((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id()) or
     (data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {

    // measurement is based on samp rate, which is theoretical
    Meas<config_value_t> meas(meas_type_t::THEORETICAL);

    meas.m_unit.assign("MHz");

    const Meas<config_value_t> sr= get_sampling_rate_Msps(data_stream_ID);
    const config_value_t sample_freq = sr.m_value;

    int16_t phs_inc = m_callBack.getPhaseIncrement(!tx, which); // will return 0 if no mixer

    // see Complex_Mixer.pdf eq. (4)
    double nco_output_freq = ((double)sample_freq) * ((double)phs_inc) / 65536.;
    
    // It is desired that setting a + IF freq results in mixing *down*. Because
    // complex_mixer's NCO mixes *up* for + freqs (see complex mixer datasheet),
    // IF frequency is accurately reported as the negative of the NCO freq.
    meas.m_value = -nco_output_freq;

    //log_info("meas.m_value=%0.15f",meas.m_value);
    //log_info("phs_inc=%li",phs_inc);
    //log_info("sample_freq=%0.15f",sample_freq);
    std::ostringstream oss;
    oss << meas;
    this->log_debug("data stream: %s, read from hardware tuning freq complex mixer value of: %s", data_stream_ID.c_str(), oss.str().c_str());

    return meas;
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
}

/*template<class S>
bool RadioCtrlrNoOSTuneResamp::get_worker_exists_in_app(
    const char* inst) const {
  std::string val;
  app.getProperty(inst, "ocpi_debug", val);
  return (val.compare("true") == 0);
}*/

/// @todo / FIXME - check for existence of qadc/qdac?
bool RadioCtrlrNoOSTuneResamp::
get_data_stream_is_enabled(const data_stream_ID_t data_stream_ID) const {
  if (not m_ad9361_init_called)
    //throw std::string("ad9361_init was never called");
    return false;
  return m_configurator.find_data_stream(data_stream_ID)->isEnabled();
}

Meas<config_value_t> RadioCtrlrNoOSTuneResamp::get_sampling_rate_Msps(
    const data_stream_ID_t data_stream_ID) const {

  this->throw_if_data_stream_disabled_for_read(data_stream_ID, "sampling rate");

  // this function essentially maps the generic representation which a
  // digital radio controller provides to methods which calculate
  // the thereotical value (direct AD9361 register reads) with high precision

  std::unique_ptr<Configurator> copy(m_configurator.clone());
  Configurator &configurator_copy = *copy; // const necessitates this...
  if((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id())) {

    /// @todo / FIXME - the best thing to do is probably throw an exception if CIC_dec_decimation_factor is not locked (how can we read the hardware sampling rate if we don't know the decimation factor?)
    const ConfigValueRanges& x = configurator_copy.get_ranges_possible(data_stream_ID,"CIC_dec_decimation_factor");
    config_value_t CIC_dec_decimation_factor = x.get_smallest_min();

    // get_AD9361_RX_SAMPL_FREQ_Hz() is a (highly precise) theoretical
    // calculation based upon AD9361 register values
    Meas<config_value_t> meas(meas_type_t::THEORETICAL);
    meas.m_unit.assign("MHz"); // we usually stick with MHz as the standard

    double val;
    const double& fref = m_AD9361_FREF_Hz;
    this->throw_if_ad9361_init_failed("No-OS API call get_AD9361_RX_SAMPL_FREQ_Hz()");
    const char* err = get_ad9361_rx_sampl_freq_hz(m_ad9361_rf_phy, fref, val);
    if(err != 0) {
      throw err;
    }
    meas.m_value = val/CIC_dec_decimation_factor/1e6;
    std::ostringstream oss;
    oss << meas;


    this->log_debug("data stream: %s, read from hardware sampling rate value of: %s", data_stream_ID.c_str(), oss.str().c_str());
    {
      Meas<config_value_t> m2 = meas;
      m2.m_value = val/1e6;
      oss.str("");
      oss.clear();
      oss << m2;
      this->log_debug("data stream: %s, read from hardware AD9361 RX_SAMPL_FREQ value of: %s", data_stream_ID.c_str(), oss.str().c_str());
    }

    return meas;
  }
  else if((data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {

    /// @todo / FIXME - the best thing to do is probably throw an exception if CIC_int_interpolation_factor is not locked (how can we read the hardware sampling rate if we don't know the interpolation factor?)
    const ConfigValueRanges& x = configurator_copy.get_ranges_possible(data_stream_ID,"CIC_int_interpolation_factor");
    config_value_t CIC_int_interpolation_factor = x.get_smallest_min();

    // get_AD9361_RX_SAMPL_FREQ_Hz() is a (highly precise) theoretical
    // calculation based upon AD9361 register values
    Meas<config_value_t> meas(meas_type_t::THEORETICAL);
    meas.m_unit.assign("MHz"); // we usually stick with MHz as the standard

    double val;
    const double& fref = m_AD9361_FREF_Hz;
    this->throw_if_ad9361_init_failed("No-OS API call get_AD9361_TX_SAMPL_FREQ_Hz()");
    const char* err = get_ad9361_tx_sampl_freq_hz(m_ad9361_rf_phy, fref, val);
    if(err != 0) {
      throw err;
    }
    meas.m_value = val/CIC_int_interpolation_factor/1e6;
    std::ostringstream oss;
    oss << meas;
    this->log_debug("data stream: %s, read from hardware sampling rate value of: %s", data_stream_ID.c_str(), oss.str().c_str());
    {
      Meas<config_value_t> m2 = meas;
      m2.m_value = val/1e6;
      oss.str("");
      oss.clear();
      oss << m2;
      this->log_debug("data stream: %s, read from hardware AD9361 TX_SAMPL_FREQ value of: %s", data_stream_ID.c_str(), oss.str().c_str());
    }

    return meas;
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
}

bool RadioCtrlrNoOSTuneResamp::get_samples_are_complex(
    const data_stream_ID_t data_stream_ID) const {

  this->throw_if_data_stream_disabled_for_read(data_stream_ID, "samples are complex");

  if((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id()) or
     (data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {

    // AD9361 samples are always complex
    this->log_debug("data stream: %s, read from hardware samples_are_complex value of: true", data_stream_ID.c_str());
    return true;
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
}

Meas<gain_mode_value_t> RadioCtrlrNoOSTuneResamp::get_gain_mode(
    const data_stream_ID_t data_stream_ID) const {

  this->throw_if_data_stream_disabled_for_read(data_stream_ID, "gain mode");

  Meas<gain_mode_value_t> meas(meas_type_t::EXACT);

  // assign to No-OS-specific "channel" macro (RX1/RX2/TX1/TX2 in ad9361_api.h)
  uint8_t ch;
  bool do_rx = false;
  if(data_stream_ID == RX2_id()) {
    ch = RX1;
    do_rx = true;
  }
  else if(data_stream_ID == RX1_id()) {
    ch = m_ad9361_rf_phy->pdata->rx2tx2 ? RX2 : RX1;
    do_rx = true;
  } 
  
  if(do_rx) {

    uint8_t gc_mode;
    int32_t ret;
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_get_rx_gain_control_mode()");
    ret = ad9361_get_rx_gain_control_mode(m_ad9361_rf_phy, ch, &gc_mode);
    if(ret != 0) {
      throw this->get_No_OS_err_str("ad9361_get_rx_gain_control_mode", ret);
    }
    this->log_debug("No-OS call: ad9361_get_rx_gain_control_mode, read value: %" PRIu8 ", channel: %" PRIu8, gc_mode, ch);

    switch(gc_mode) {
      case RF_GAIN_MGC:
        this->log_debug("data stream: %s, read from hardware gain mode value of: RF_GAIN_MGC (manual)", data_stream_ID.c_str());
        if(m_readback_gain_mode_as_standard_value) {
          meas.m_value.assign("manual");
        }
        else {
          meas.m_value.assign("RF_GAIN_SLOWATTACK_AGC");
        }
        break;
      case RF_GAIN_FASTATTACK_AGC:
        this->log_debug("data stream: %s, read from hardware gain mode value of: RF_GAIN_FASTATTACK_AGC", data_stream_ID.c_str());
        meas.m_value.assign("RF_GAIN_FASTATTACK_AGC");
        break;
      case RF_GAIN_SLOWATTACK_AGC:
        this->log_debug("data stream: %s, read from hardware gain mode value of: RF_GAIN_SLOWATTACK_AGC (auto)", data_stream_ID.c_str());
        if(m_readback_gain_mode_as_standard_value) {
          meas.m_value.assign("auto");
        }
        else {
          meas.m_value.assign("RF_GAIN_SLOWATTACK_AGC");
        }
        break;
      case RF_GAIN_HYBRID_AGC:
        this->log_debug("data stream: %s, read from hardware gain mode value of: RF_GAIN_HYBRID_AGC", data_stream_ID.c_str());
        meas.m_value.assign("RF_GAIN_HYBRID_AGC");
        break;
      default:
        std::ostringstream oss;
        oss << "invalid value read from ad9361_get_rx_gain_control_mode(): ";
        oss << (unsigned) gc_mode;
        oss << ", expected one of the values: ";
        oss << RF_GAIN_MGC << ", ";
        oss << RF_GAIN_FASTATTACK_AGC << ", ";
        oss << RF_GAIN_SLOWATTACK_AGC << ", ";
        oss << RF_GAIN_HYBRID_AGC;
        throw oss.str().c_str();
    }
    return meas;
  }
  else if((data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {

    meas.m_value.assign("manual");

    return meas;
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
}

Meas<config_value_t> RadioCtrlrNoOSTuneResamp::get_gain_dB(
    const data_stream_ID_t data_stream_ID) const {

  this->throw_if_data_stream_disabled_for_read(data_stream_ID, "gain");

  Meas<config_value_t> meas(meas_type_t::THEORETICAL);
  meas.m_unit.assign("dB"); // we usually stick with dB as the standard

  // assign to No-OS-specific "channel" macro (RX1/RX2/TX1/TX2 in ad9361_api.h)
  uint8_t ch;

  bool do_rx = false;
  if(data_stream_ID == RX2_id()) {
    ch = RX1;
    do_rx = true;
  }
  else if(data_stream_ID == RX1_id()) {
    ch = m_ad9361_rf_phy->pdata->rx2tx2 ? RX2 : RX1;
    do_rx = true;
  }
  bool do_tx = false;
  if(do_rx) {

    int32_t gain_db;
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_get_rx_rf_gain()");
    int32_t ret = ad9361_get_rx_rf_gain(m_ad9361_rf_phy, ch, &gain_db);
    if(ret != 0) {
      throw this->get_No_OS_err_str("ad9361_get_rx_rf_gain", ret);
    }
    this->log_debug("No-OS call: ad9361_get_rx_rf_gain, read value: %" PRIi32 ", channel: %" PRIu8, gain_db, ch);

    meas.m_value = (double) gain_db;
    std::ostringstream oss;
    oss << meas;
    this->log_debug("data stream: %s, read from hardware AD9361 rx_rf_gain value of: %s", data_stream_ID.c_str(), oss.str().c_str());

    return meas;
  }
  else if(data_stream_ID == TX2_id()) {
    ch = TX1;
    do_tx = true;
  }
  else if(data_stream_ID == TX1_id()) {
    ch = m_ad9361_rf_phy->pdata->rx2tx2 ? TX2 : TX1;
    do_tx = true;
  }
  if(do_tx) {

    // note that gain mode is never auto for either TX data stream

    uint32_t attenuation_mdb;
    int32_t ret;
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_get_tx_attenuation()");
    ret = ad9361_get_tx_attenuation(m_ad9361_rf_phy, ch, &attenuation_mdb);
    if(ret != 0) {
      throw this->get_No_OS_err_str("ad9361_get_tx_attenuation", ret);
    }
    this->log_debug("No-OS call: ad9361_get_tx_attenuation, read value: %" PRIu32 ", channel: %" PRIu8, attenuation_mdb, ch);
    meas.m_value = -((double) attenuation_mdb)/1000.;
    std::ostringstream oss;
    oss << attenuation_mdb;
    this->log_debug("data stream: %s, read from hardware AD9361 tx_attenuation value of: %s", data_stream_ID.c_str(), oss.str().c_str());
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
  return meas;
}

RadioCtrlrNoOSTuneResamp::~RadioCtrlrNoOSTuneResamp() {
  // only free internally managed No-OS memory
  ad9361_free(_ad9361_rf_phy); // this function added in ad9361.patch
}

void RadioCtrlrNoOSTuneResamp::unlock_all() {
  log_debug("configurator: unlock_all1");
  this->m_configurator.unlock_all();
  this->m_config_locks.clear();

  // required for all ...TuneResamp classes
  m_configurator_tune_resamp_locked = false;
  //ensure_configurator_lock_tune_resamp();
}

Meas<config_value_t> RadioCtrlrNoOSTuneResamp::set_tuning_freq_MHz(
    const data_stream_ID_t data_stream_ID,
    const config_value_t   tuning_freq_MHz) {

  this->throw_if_data_stream_disabled_for_write(data_stream_ID, "tuning freq");

  // this function essentially maps the generic representation which a
  // digital radio controller provides to the underlying No-OS API calls
  // ---------------------------------------------------------------------
  // digital radio controller data stream   | No-OS API call
  // ---------------------------------------------------------------------
  // RX1                                    | ad9361_set_rx_lo_freq ()
  // RX2                                    | ad9361_set_rx_lo_freq ()
  // TX1                                    | ad9361_set_tx_lo_freq ()
  // TX2                                    | ad9361_set_tx_lo_freq ()

  if((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id())) {
    uint64_t lo_freq_hz = round(tuning_freq_MHz*1e6);
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_set_rx_lo_freq()");

    // set filter proxy rx frequency 
    /*    
    const char* filter_proxy_inst = m_app_inst_name_e31x_mimo_xcvr_filter_proxy.c_str();
    OCPI::API::Property filter_freq(m_app, filter_proxy_inst, "rx_frequency_MHz");
    filter_freq.setDoubleValue(tuning_freq_MHz);
    */

    // configure input rf port based on frequency 
    ad9361_set_rx_rf_port_input(m_ad9361_rf_phy, m_callBack.getRfInput(m_device, tuning_freq_MHz));

    this->log_debug("data stream: %s, configuring hardware w/ tuning freq value of: %" PRIu64 " Hz", data_stream_ID.c_str(), lo_freq_hz);
    this->log_debug("No-OS call: ad9361_set_rx_lo_freq w/ value: %" PRIu64, lo_freq_hz);
    // intentionally ignoring return value because this function provides no
    // guarantee of success
    ad9361_set_rx_lo_freq(m_ad9361_rf_phy, lo_freq_hz);
  }
  else if((data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {
    uint64_t lo_freq_hz = round(tuning_freq_MHz*1e6);
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_set_tx_lo_freq()");
  
    // set filter proxy tx frequency  
    /*
    const char* filter_proxy_inst = m_app_inst_name_e31x_mimo_xcvr_filter_proxy.c_str();
    OCPI::API::Property filter_freq(m_app, filter_proxy_inst, "tx_frequency_MHz");
    filter_freq.setDoubleValue(tuning_freq_MHz);
    */
    
    // configure output rf port based on frequency 
    ad9361_set_tx_rf_port_output(m_ad9361_rf_phy, m_callBack.getRfOutput(m_device, tuning_freq_MHz));

    this->log_debug("data stream: %s, configuration hardware w/ tuning freq value of: %" PRIu64 " Hz", data_stream_ID.c_str(), lo_freq_hz);
    this->log_debug("No-OS call: ad9361_set_tx_lo_freq w/ value: %" PRIu64, lo_freq_hz);
    // intentionally ignoring return value because this function provides no
    // guarantee of success
    ad9361_set_tx_lo_freq(m_ad9361_rf_phy, lo_freq_hz);
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
  return get_tuning_freq_MHz(data_stream_ID);
}

Meas<config_value_t>
RadioCtrlrNoOSTuneResamp::set_bandwidth_3dB_MHz(
    const data_stream_ID_t data_stream_ID,
    const config_value_t   bandwidth_3dB_MHz) {

  this->throw_if_data_stream_disabled_for_write(data_stream_ID, "bandwidth");

  if((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id())) {
    uint32_t bandwidth_hz = round(bandwidth_3dB_MHz*1e6);
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_set_rx_rf_bandwidth()");

    this->log_debug("data stream: %s, configuring hardware w/ 3dB bandwidth value of: %" PRIu32 " Hz", data_stream_ID.c_str(), bandwidth_hz);
    this->log_debug("No-OS call: ad9361_set_rx_rf_bandwidth w/ value: %" PRIu32, bandwidth_hz);
    // intentionally ignoring return value because this function provides no
    // guarantee of success
    ad9361_set_rx_rf_bandwidth(m_ad9361_rf_phy, bandwidth_hz);
  }
  else if((data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {
    uint32_t bandwidth_hz = round(bandwidth_3dB_MHz*1e6);
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_set_tx_rf_bandwidth()");

    this->log_debug("data stream: %s, configuring hardware w/ 3dB bandwidth value of: %" PRIu32 " Hz", data_stream_ID.c_str(), bandwidth_hz);
    this->log_debug("No-OS call: ad9361_set_tx_rf_bandwidth w/ value: %" PRIu32, bandwidth_hz);
    // intentionally ignoring return value because this function provides no
    // guarantee of success
    ad9361_set_tx_rf_bandwidth(m_ad9361_rf_phy, bandwidth_hz);
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
  return get_bandwidth_3dB_MHz(data_stream_ID);
}

Meas<config_value_t> RadioCtrlrNoOSTuneResamp::set_sampling_rate_Msps(
    const data_stream_ID_t data_stream_ID,
    const config_value_t   sampling_rate_Msps) {

  this->throw_if_data_stream_disabled_for_write(data_stream_ID, "sampling rate");

  if((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id())) {
    const ConfigValueRanges& x = m_configurator.get_ranges_possible(data_stream_ID,"CIC_dec_decimation_factor");

    /// @todo / FIXME - get locked value instead of assuming smallest min is equivalent to locked value
    config_value_t tmp = x.get_smallest_min();

    uint32_t sampling_freq_hz = round(sampling_rate_Msps*tmp*1e6);
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_set_rx_sampling_freq()");

    this->log_debug("data stream: %s, configuring hardware w/ sampling rate value of: %f sps", data_stream_ID.c_str(), ((double)sampling_freq_hz)/tmp);
    this->log_debug("No-OS call: ad9361_set_rx_sampling_freq w/ value: %" PRIu32, sampling_freq_hz);
    // intentionally ignoring return value because this function provides no
    // guarantee of success
    ad9361_set_rx_sampling_freq(m_ad9361_rf_phy, sampling_freq_hz);
  }
  else if((data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {
    const ConfigValueRanges& x = m_configurator.get_ranges_possible(data_stream_ID,"CIC_int_interpolation_factor");

    /// @todo / FIXME - get locked value instead of assuming smallest min is equivalent to locked value
    config_value_t tmp = x.get_smallest_min();

    uint32_t sampling_freq_hz = round(sampling_rate_Msps*tmp*1e6);
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_set_tx_sampling_freq()");

    this->log_debug("data stream: %s, configuring hardware w/ sampling rate value of: %f sps", data_stream_ID.c_str(), sampling_freq_hz/tmp);
    this->log_debug("No-OS call: ad9361_set_tx_sampling_freq w/ value: %" PRIu32, sampling_freq_hz);
    // intentionally ignoring return value because this function provides no
    // guarantee of success
    ad9361_set_tx_sampling_freq(m_ad9361_rf_phy, sampling_freq_hz);
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
  return get_sampling_rate_Msps(data_stream_ID);
}

bool RadioCtrlrNoOSTuneResamp::set_samples_are_complex(
    const data_stream_ID_t data_stream_ID,
    const bool             samples_are_complex) {

  this->throw_if_data_stream_disabled_for_write(data_stream_ID, "samples are complex");

  // samples are always complex for AD9361, so there is nothing to do

  if(samples_are_complex) { // purposefully ignore compiler warning
  }

  if(not ((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id()) or
          (data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id()))) {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str().c_str();
  }
  this->log_debug("data stream: %s, configuring hardware w/ samples are complex value of true", data_stream_ID.c_str());
  return get_samples_are_complex(data_stream_ID);
}

Meas<gain_mode_value_t> RadioCtrlrNoOSTuneResamp::set_gain_mode(
    const data_stream_ID_t  data_stream_ID,
    const gain_mode_value_t gain_mode) {

  this->throw_if_data_stream_disabled_for_write(data_stream_ID, "gain mode");

  // assign to No-OS-specific "channel" macro (RX1/RX2/TX1/TX2 in ad9361_api.h)
  uint8_t ch;

  bool do_rx = false;
  if(data_stream_ID == RX2_id()) {
    ch = RX1;
    do_rx = true;
  }
  else if(data_stream_ID == RX1_id()) {
    ch = m_ad9361_rf_phy->pdata->rx2tx2 ? RX2 : RX1;
    do_rx = true;
  }

  if(do_rx) {

    this->log_debug("data stream: %s, configuring hardware w/ gain mode setting of %s", data_stream_ID.c_str(), gain_mode.c_str());
    uint8_t gc_mode;
    if(gain_mode.compare("manual") == 0) {
      gc_mode = RF_GAIN_MGC;
      m_readback_gain_mode_as_standard_value = true;
    }
    else if(gain_mode.compare("RF_GAIN_MGC") == 0) {
      gc_mode = RF_GAIN_MGC;
      m_readback_gain_mode_as_standard_value = false;
    }
    else if(gain_mode.compare("auto") == 0) {
      gc_mode = RF_GAIN_SLOWATTACK_AGC;
      m_readback_gain_mode_as_standard_value = true;
    }
    else if(gain_mode.compare("RF_GAIN_SLOWATTACK_AGC") == 0) {
      gc_mode = RF_GAIN_SLOWATTACK_AGC;
      m_readback_gain_mode_as_standard_value = false;
    }
    else if(gain_mode.compare("RF_GAIN_FASTATTACK_AGC") == 0) {
      gc_mode = RF_GAIN_FASTATTACK_AGC;
    }
    else if(gain_mode.compare("RF_GAIN_HYBRID_AGC") == 0) {
      gc_mode = RF_GAIN_HYBRID_AGC;
    }
    else {
      std::string str("gain mode of ");
      str += gain_mode;
      str += " is invalid";
      throw str;
    }

    this->throw_if_ad9361_init_failed("No-OS API call ad9361_set_rx_gain_control_mode()");

    this->log_debug("No-OS call: ad9361_set_rx_gain_control_mode w/ value: %" PRIu32 ", channel: %" PRIu8, gc_mode, ch);
    // intentionally ignoring return value because this function provides no
    // guarantee of success
    ad9361_set_rx_gain_control_mode(m_ad9361_rf_phy, ch, gc_mode);
  }
  else if((data_stream_ID == TX2_id()) or (data_stream_ID == TX1_id())) {
    if(gain_mode.compare("manual") != 0) { 
      std::string str("gain mode of ");
      str += gain_mode;
      str += " is invalid for data stream";
      str += data_stream_ID.c_str();
      throw str;
    }
    // AD9361 does not support a changable TX gain mode, so there's nothing to
    // do
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str();
  }
  return get_gain_mode(data_stream_ID);
}

Meas<config_value_t> RadioCtrlrNoOSTuneResamp::set_gain_dB(
    const data_stream_ID_t data_stream_ID,
    const config_value_t   gain_dB) {

  this->throw_if_data_stream_disabled_for_write(data_stream_ID, "gain");

  // assign to No-OS-specific "channel" macro (RX1/RX2/TX1/TX2 in ad9361_api.h)
  uint8_t ch;

  bool do_rx = false;
  if(data_stream_ID == RX2_id()) {
    ch = RX1;
    do_rx = true;
  }
  else if(data_stream_ID == RX1_id()) {
    ch = m_ad9361_rf_phy->pdata->rx2tx2 ? RX2 : RX1;
    do_rx = true;
  }
  bool do_tx = false;
  if(do_rx) {

    Meas<gain_mode_value_t> mode = get_gain_mode(data_stream_ID);

    int32_t gain_db = round(gain_dB);
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_set_rx_rf_gain()");

    this->log_debug("data stream: %s, configuring hardware w/ gain value of %" PRIi32 " dB", data_stream_ID.c_str(), gain_db);
    this->log_debug("No-OS call: ad9361_set_rx_rf_gain w/ value: %" PRIi32 ", channel: %" PRIu8, gain_db, ch);
    // intentionally ignoring return value because this function provides no
    // guarantee of success
    ad9361_set_rx_rf_gain(m_ad9361_rf_phy, ch, gain_db);
  }
  else if(data_stream_ID == TX2_id()) {
    ch = TX1;
    do_tx = true;
  }
  else if(data_stream_ID == TX1_id()) {
    ch = m_ad9361_rf_phy->pdata->rx2tx2 ? TX2 : TX1;
    do_tx = true;
  }
  else {
    std::ostringstream oss;
    oss << "invalid data stream ID requested: " << data_stream_ID;
    throw oss.str();
  }
  if(do_tx) {
    // this check should be done before calling
    // ad9361_get_rx_rf_gain(_,RX2,_);
    if((m_ad9361_rf_phy->pdata->rx2tx2 == 0) and (ch == RX2)) {
      /// @todo / FIXME - query for controller data stream disablement here?
      throw std::string("requested read of gain for disabled AD9361 RX2 data stream");
    }

    // note that gain mode is never auto for either TX data stream

    uint32_t attenuation_mdb = round(-gain_dB*1000.);
    this->throw_if_ad9361_init_failed("No-OS API call ad9361_set_tx_attenuation()");

    this->log_debug("data stream: %s, configuring hardware w/ gain value of %f dB", data_stream_ID.c_str(), (double)-attenuation_mdb*1000);
    this->log_debug("No-OS call: ad9361_set_tx_attenuation w/ value: %" PRIu32 ", channel: %" PRIu8, attenuation_mdb, ch);
    // intentionally ignoring return value because this function provides no
    // guarantee of success
    ad9361_set_tx_attenuation(m_ad9361_rf_phy, ch, attenuation_mdb);
  }
  return get_gain_dB(data_stream_ID);
}

Meas<config_value_t> RadioCtrlrNoOSTuneResamp::
set_tuning_freq_complex_mixer_MHz(const data_stream_ID_t data_stream_ID, bool tx, unsigned which,
				  const config_value_t tuning_freq_MHz) {

  const Meas<config_value_t> meas = get_sampling_rate_Msps(data_stream_ID);
  const config_value_t sample_freq = meas.m_value;

  // It is desired that setting a + IF freq results in mixing *down*.
  // Because complex_mixer's NCO mixes *up* for + freqs (see complex mixer
  // datasheet), IF tune freq must be negated in order to achieve the
  // desired effect.
  config_value_t nco_output_freq = -tuning_freq_MHz;

  // todo this math might be better off in a small proxy that sits on top of complex_mixer
  // from complex mixer datasheet, nco_output_freq =
  // sample_freq * phs_inc / 2^phs_acc_width, phs_acc_width is fixed at 16
  int16_t phs_inc = round(nco_output_freq / sample_freq * 65536.);

  m_callBack.setPhaseIncrement(!tx, which, phs_inc);

  return get_tuning_freq_complex_mixer_MHz(data_stream_ID, tx, which);
}

/*template<class LC, class C>
bool DigRadioCtrlr<LC, C>::lock_gain_mode(
    const data_stream_ID_t  ds_ID,
    const gain_mode_value_t val) {

  // the configurator, which is a software emulation of hardware capabilties,
  // tells us whether a hardware attempt to set value will corrupt
  // any existing locks
  const config_key_t cfg_key = config_key_gain_mode;
  config_value_t v = val.compare("manual") == 0 ? 1 : 0; // auto=0, manual=1
  bool did_lock = this->m_configurator.lock_config(ds_ID, cfg_key, v);

  if(did_lock) {
    Meas<gain_mode_value_t> meas = set_gain_mode(ds_ID, val);

    if(meas.m_value != val) { // exact for gain mode
      did_lock = false;
    }
    log_info_config_lock(did_lock, ds_ID, val, cfg_key, &meas);
  }
  else {
    log_info_config_lock(did_lock, ds_ID, val, cfg_key); 
  }

  return did_lock;
}*/

#define INIT_PARAM_FIELDS\
  IPF(dev_sel, u32) \
  IPF(id_no, u8) \
  IPF(reference_clk_rate, u32) \
  IPF(two_rx_two_tx_mode_enable, u8) \
  IPF(one_rx_one_tx_mode_use_rx_num, u8) \
  IPF(one_rx_one_tx_mode_use_tx_num, u8) \
  IPF(frequency_division_duplex_mode_enable, u8) \
  IPF(frequency_division_duplex_independent_mode_enable, u8) \
  IPF(tdd_use_dual_synth_mode_enable, u8) \
  IPF(tdd_skip_vco_cal_enable, u8) \
  IPF(tx_fastlock_delay_ns, u32) \
  IPF(rx_fastlock_delay_ns, u32) \
  IPF(rx_fastlock_pincontrol_enable, u8) \
  IPF(tx_fastlock_pincontrol_enable, u8) \
  IPF(external_rx_lo_enable, u8) \
  IPF(external_tx_lo_enable, u8) \
  IPF(dc_offset_tracking_update_event_mask, u8) \
  IPF(dc_offset_attenuation_high_range, u8) \
  IPF(dc_offset_attenuation_low_range, u8) \
  IPF(dc_offset_count_high_range, u8) \
  IPF(dc_offset_count_low_range, u8) \
  IPF(split_gain_table_mode_enable, u8) \
  IPF(trx_synthesizer_target_fref_overwrite_hz, u32) \
  IPF(qec_tracking_slow_mode_enable, u8) \
  IPF(ensm_enable_pin_pulse_mode_enable, u8) \
  IPF(ensm_enable_txnrx_control_enable, u8) \
  IPF(rx_synthesizer_frequency_hz, u64) \
  IPF(tx_synthesizer_frequency_hz, u64) \
  IPF(tx_lo_powerdown_managed_enable, u8) \
  IPF(rx_path_clock_frequencies[6], u32) \
  IPF(tx_path_clock_frequencies[6], u32) \
  IPF(rf_rx_bandwidth_hz, u32) \
  IPF(rf_tx_bandwidth_hz, u32) \
  IPF(rx_rf_port_input_select, u32) \
  IPF(tx_rf_port_input_select, u32) \
  IPF(tx_attenuation_mdB, u32) \
  IPF(update_tx_gain_in_alert_enable, u8) \
  IPF(xo_disable_use_ext_refclk_enable, u8) \
  IPF(dcxo_coarse_and_fine_tune[2], u32) \
  IPF(clk_output_mode_select, u32) \
  IPF(gc_rx1_mode, u8) \
  IPF(gc_rx2_mode, u8) \
  IPF(gc_adc_large_overload_thresh, u8) \
  IPF(gc_adc_ovr_sample_size, u8) \
  IPF(gc_adc_small_overload_thresh, u8) \
  IPF(gc_dec_pow_measurement_duration, u16) \
  IPF(gc_dig_gain_enable, u8) \
  IPF(gc_lmt_overload_high_thresh, u16) \
  IPF(gc_lmt_overload_low_thresh, u16) \
  IPF(gc_low_power_thresh, u8) \
  IPF(gc_max_dig_gain, u8) \
  IPF(mgc_dec_gain_step, u8) \
  IPF(mgc_inc_gain_step, u8) \
  IPF(mgc_rx1_ctrl_inp_enable, u8) \
  IPF(mgc_rx2_ctrl_inp_enable, u8) \
  IPF(mgc_split_table_ctrl_inp_gain_mode, u8) \
  IPF(agc_adc_large_overload_exceed_counter, u8) \
  IPF(agc_adc_large_overload_inc_steps, u8) \
  IPF(agc_adc_lmt_small_overload_prevent_gain_inc_enable, u8) \
  IPF(agc_adc_small_overload_exceed_counter, u8) \
  IPF(agc_dig_gain_step_size, u8) \
  IPF(agc_dig_saturation_exceed_counter, u8) \
  IPF(agc_gain_update_interval_us, u32) \
  IPF(agc_immed_gain_change_if_large_adc_overload_enable, u8) \
  IPF(agc_immed_gain_change_if_large_lmt_overload_enable, u8) \
  IPF(agc_inner_thresh_high, u8) \
  IPF(agc_inner_thresh_high_dec_steps, u8) \
  IPF(agc_inner_thresh_low, u8) \
  IPF(agc_inner_thresh_low_inc_steps, u8) \
  IPF(agc_lmt_overload_large_exceed_counter, u8) \
  IPF(agc_lmt_overload_large_inc_steps, u8) \
  IPF(agc_lmt_overload_small_exceed_counter, u8) \
  IPF(agc_outer_thresh_high, u8) \
  IPF(agc_outer_thresh_high_dec_steps, u8) \
  IPF(agc_outer_thresh_low, u8) \
  IPF(agc_outer_thresh_low_inc_steps, u8) \
  IPF(agc_attack_delay_extra_margin_us, u32) \
  IPF(agc_sync_for_gain_counter_enable, u8) \
  IPF(fagc_dec_pow_measuremnt_duration, u32) \
  IPF(fagc_state_wait_time_ns, u32) \
  IPF(fagc_allow_agc_gain_increase, u8) \
  IPF(fagc_lp_thresh_increment_time, u32) \
  IPF(fagc_lp_thresh_increment_steps, u32) \
  IPF(fagc_lock_level_lmt_gain_increase_en, u8) \
  IPF(fagc_lock_level_gain_increase_upper_limit, u32) \
  IPF(fagc_lpf_final_settling_steps, u32) \
  IPF(fagc_lmt_final_settling_steps, u32) \
  IPF(fagc_final_overrange_count, u32) \
  IPF(fagc_gain_increase_after_gain_lock_en, u8) \
  IPF(fagc_gain_index_type_after_exit_rx_mode, u32) \
  IPF(fagc_use_last_lock_level_for_set_gain_en, u8) \
  IPF(fagc_rst_gla_stronger_sig_thresh_exceeded_en, u8) \
  IPF(fagc_optimized_gain_offset, u32) \
  IPF(fagc_rst_gla_stronger_sig_thresh_above_ll, u32) \
  IPF(fagc_rst_gla_engergy_lost_sig_thresh_exceeded_en, u8) \
  IPF(fagc_rst_gla_engergy_lost_goto_optim_gain_en, u8) \
  IPF(fagc_rst_gla_engergy_lost_sig_thresh_below_ll, u32) \
  IPF(fagc_energy_lost_stronger_sig_gain_lock_exit_cnt, u32) \
  IPF(fagc_rst_gla_large_adc_overload_en, u8) \
  IPF(fagc_rst_gla_large_lmt_overload_en, u8) \
  IPF(fagc_rst_gla_en_agc_pulled_high_en, u8) \
  IPF(fagc_rst_gla_if_en_agc_pulled_high_mode, u32) \
  IPF(fagc_power_measurement_duration_in_state5, u32) \
  IPF(rssi_delay, u32) \
  IPF(rssi_duration, u32) \
  IPF(rssi_restart_mode, u8) \
  IPF(rssi_unit_is_rx_samples_enable, u8) \
  IPF(rssi_wait, u32) \
  IPF(aux_adc_decimation, u32) \
  IPF(aux_adc_rate, u32) \
  IPF(aux_dac_manual_mode_enable, u8) \
  IPF(aux_dac1_default_value_mV, u32) \
  IPF(aux_dac1_active_in_rx_enable, u8) \
  IPF(aux_dac1_active_in_tx_enable, u8) \
  IPF(aux_dac1_active_in_alert_enable, u8) \
  IPF(aux_dac1_rx_delay_us, u32) \
  IPF(aux_dac1_tx_delay_us, u32) \
  IPF(aux_dac2_default_value_mV, u32) \
  IPF(aux_dac2_active_in_rx_enable, u8) \
  IPF(aux_dac2_active_in_tx_enable, u8) \
  IPF(aux_dac2_active_in_alert_enable, u8) \
  IPF(aux_dac2_rx_delay_us, u32) \
  IPF(aux_dac2_tx_delay_us, u32) \
  IPF(temp_sense_decimation, u32) \
  IPF(temp_sense_measurement_interval_ms, u16) \
  IPF(temp_sense_offset_signed, u8) \
  IPF(temp_sense_periodic_measurement_enable, u8) \
  IPF(ctrl_outs_enable_mask, u8) \
  IPF(ctrl_outs_index, u8) \
  IPF(elna_settling_delay_ns, u32) \
  IPF(elna_gain_mdB, u32) \
  IPF(elna_bypass_loss_mdB, u32) \
  IPF(elna_rx1_gpo0_control_enable, u8) \
  IPF(elna_rx2_gpo1_control_enable, u8) \
  IPF(elna_gaintable_all_index_enable, u8) \
  IPF(digital_interface_tune_skip_mode, u8) \
  IPF(digital_interface_tune_fir_disable, u8) \
  IPF(pp_tx_swap_enable, u8) \
  IPF(pp_rx_swap_enable, u8) \
  IPF(tx_channel_swap_enable, u8) \
  IPF(rx_channel_swap_enable, u8) \
  IPF(rx_frame_pulse_mode_enable, u8) \
  IPF(two_t_two_r_timing_enable, u8) \
  IPF(invert_data_bus_enable, u8) \
  IPF(invert_data_clk_enable, u8) \
  IPF(fdd_alt_word_order_enable, u8) \
  IPF(invert_rx_frame_enable, u8) \
  IPF(fdd_rx_rate_2tx_enable, u8) \
  IPF(swap_ports_enable, u8) \
  IPF(single_data_rate_enable, u8) \
  IPF(lvds_mode_enable, u8) \
  IPF(half_duplex_mode_enable, u8) \
  IPF(single_port_mode_enable, u8) \
  IPF(full_port_enable, u8) \
  IPF(full_duplex_swap_bits_enable, u8) \
  IPF(delay_rx_data, u32) \
  IPF(rx_data_clock_delay, u32) \
  IPF(rx_data_delay, u32) \
  IPF(tx_fb_clock_delay, u32) \
  IPF(tx_data_delay, u32) \
  IPF(lvds_bias_mV, u32) \
  IPF(lvds_rx_onchip_termination_enable, u8) \
  IPF(rx1rx2_phase_inversion_en, u8) \
  IPF(lvds_invert1_control, u8) \
  IPF(lvds_invert2_control, u8) \
  IPF(gpo0_inactive_state_high_enable, u8) \
  IPF(gpo1_inactive_state_high_enable, u8) \
  IPF(gpo2_inactive_state_high_enable, u8) \
  IPF(gpo3_inactive_state_high_enable, u8) \
  IPF(gpo0_slave_rx_enable, u8) \
  IPF(gpo0_slave_tx_enable, u8) \
  IPF(gpo1_slave_rx_enable, u8) \
  IPF(gpo1_slave_tx_enable, u8) \
  IPF(gpo2_slave_rx_enable, u8) \
  IPF(gpo2_slave_tx_enable, u8) \
  IPF(gpo3_slave_rx_enable, u8) \
  IPF(gpo3_slave_tx_enable, u8) \
  IPF(gpo0_rx_delay_us, u8) \
  IPF(gpo0_tx_delay_us, u8) \
  IPF(gpo1_rx_delay_us, u8) \
  IPF(gpo1_tx_delay_us, u8) \
  IPF(gpo2_rx_delay_us, u8) \
  IPF(gpo2_tx_delay_us, u8) \
  IPF(gpo3_rx_delay_us, u8) \
  IPF(gpo3_tx_delay_us, u8) \
  IPF(low_high_gain_threshold_mdB, u32) \
  IPF(low_gain_dB, u32) \
  IPF(high_gain_dB, u32) \
  IPF(tx_mon_track_en, u8) \
  IPF(one_shot_mode_en, u8) \
  IPF(tx_mon_delay, u32) \
  IPF(tx_mon_duration, u32) \
  IPF(tx1_mon_front_end_gain, u32) \
  IPF(tx2_mon_front_end_gain, u32) \
  IPF(tx1_mon_lo_cm, u32) \
  IPF(tx2_mon_lo_cm, u32) \
  IPF(gpio_resetb, u32) \
  IPF(gpio_sync, u32) \
  IPF(gpio_cal_sw1, u32) \
  IPF(gpio_cal_sw2, u32) \

void RadioCtrlrNoOSTuneResamp::log_debug_ad9361_init(const AD9361_InitParam &init_param) const {
  this->log_debug("No-OS call: ad9361_init w/ values: "
#define IPF(n,f) "\n  "#n": %" PRI##f
      INIT_PARAM_FIELDS "\n"
#undef IPF
#define IPF(n,f) ,init_param.n
      INIT_PARAM_FIELDS
		  );
#if 0


            "rx_data_clock_delay=%" PRIu32
            ",rx_data_delay=%" PRIu32
            ",tx_fb_clock_delay=%" PRIu32
            ",tx_data_delay=%" PRIu32,
            init_param.rx_data_clock_delay,
            init_param.rx_data_delay,
            init_param.tx_fb_clock_delay,
            init_param.tx_data_delay);
#endif
}


// C interface for NoOs Library callbacks to touch the actual device (config slave)
static void get_byte(uint8_t id_no, uint16_t addr, uint8_t *buf) {
  g_devices[id_no]->get_byte(id_no, addr, buf);
}
static void set_byte(uint8_t id_no, uint16_t addr, const uint8_t *buf) {
  g_devices[id_no]->set_byte(id_no, addr, buf);
}
static void set_reset(uint8_t id_no, bool on) {
  g_devices[id_no]->set_reset(id_no, on);
}

void RadioCtrlrNoOSTuneResamp::init() {

  // only initialize if there are no existing locks which conflict
  if(any_configurator_configs_locked_which_prevent_ad9361_init()) {
    throw std::string("reinit required but configurator configs locked which prevent reinit");
  }

  if(not m_ad9361_init_called) { // spi_init() only needs to happen once
    // Enable the lower level ADI NoOS C library to work by initializing
    // the callback structure for it to call our control plane
    ad9361_opencpi.get_byte = get_byte;
    ad9361_opencpi.set_byte = set_byte;
    ad9361_opencpi.set_reset = set_reset;
    ad9361_opencpi.worker = m_descriptor;
  }

  /*
    three phases of callback:
    1. Before init
    2. After init success or failure
    3. After init success
  */

  // This is our config structure which is then translated into the no-OS library's own init structure
  Ad9361InitConfig cfg;
  // Call back to the proxy to fill in or modify this structure further, before acting on it.
  m_callBack.initialConfig(m_device, cfg);
  // Translate from our config structure to the no-OS library's config structure
  update_AD9361_InitParam(cfg);

  // sleep duration chosen to be relatively small in relation to AD9361
  // initialization duration (which, through observation, appears to be
  // roughly 200 ms), but a long enough pulse that AD9361 is likely
  // recognizing it many, many times over
  usleep(1000);
  m_ad9361_init_called = true;
  this->log_debug_ad9361_init(m_AD9361_InitParam);
  m_ad9361_init_ret = ad9361_init(&m_ad9361_rf_phy, &m_AD9361_InitParam);

  ad9361_set_tx_fir_en_dis(m_ad9361_rf_phy, 0); // disable tx_fir with the ad9361_api library in all cases

  m_callBack.postConfig(m_device);

  if(m_ad9361_init_ret == -ENODEV) {
    throw "AD9361 initialization failed: SPI communication could not be established";
  }
  else if(m_ad9361_init_ret != 0) {
    throw "AD9361 initialization failed";
  }
  if(m_ad9361_rf_phy == 0) {
    std::string str;
    str += "AD9361 initialization failed:";
    str += "unknown failure resulted in null pointer";
    throw str.c_str();
  }

  // Successful Initialization, tell workers about what happened.
  m_callBack.finalConfig(m_device, cfg);

  // Update the status of the data streams as to whether they are now enabled or not.
  bool rx;
  data_stream_ID_t *id;
  for (unsigned ii = 0; m_configurator.getNextStream(ii, false, rx, id); ++ii)
    if (*id == RX1_id())
      m_configurator.find_data_stream(*id)->setEnable(m_AD9361_InitParam.two_rx_two_tx_mode_enable ||
						     m_AD9361_InitParam.one_rx_one_tx_mode_use_rx_num == 1);
    else if (*id == RX2_id())
      m_configurator.find_data_stream(*id)->setEnable(m_AD9361_InitParam.two_rx_two_tx_mode_enable ||
						     m_AD9361_InitParam.one_rx_one_tx_mode_use_rx_num == 2);
    else if (*id == TX1_id())
      m_configurator.find_data_stream(*id)->setEnable(m_AD9361_InitParam.two_rx_two_tx_mode_enable ||
						     m_AD9361_InitParam.one_rx_one_tx_mode_use_tx_num == 1);
    else if (*id == TX2_id())
      m_configurator.find_data_stream(*id)->setEnable(m_AD9361_InitParam.two_rx_two_tx_mode_enable ||
						     m_AD9361_InitParam.one_rx_one_tx_mode_use_tx_num == 2);
}

void RadioCtrlrNoOSTuneResamp::init_AD9361_InitParam() {

  static AD9361_InitParam init_param = {
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
    1,		//rx_rf_port_input_select *** adi,rx-rf-port-input-select
    1,		//tx_rf_port_input_select *** adi,tx-rf-port-input-select
    /* TX Attenuation Control */
    10000,	//tx_attenuation_mdB *** adi,tx-attenuation-mdB
    0,		//update_tx_gain_in_alert_enable *** adi,update-tx-gain-in-alert-enable
    /* Reference Clock Control */
    1,		//xo_disable_use_ext_refclk_enable *** adi,xo-disable-use-ext-refclk-enable
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
    // This setting *forces* into 2t/2r timing regardless of channel config.  We do not do this.
    // this disabled setting is assumed in the helper function.
    0,		//two_t_two_r_timing_enable *** adi,2t2r-timing-enable
    0,		//invert_data_bus_enable *** adi,invert-data-bus-enable
    0,		//invert_data_clk_enable *** adi,invert-data-clk-enable
    0,		//fdd_alt_word_order_enable *** adi,fdd-alt-word-order-enable
    0,		//invert_rx_frame_enable *** adi,invert-rx-frame-enable
    0,		//fdd_rx_rate_2tx_enable *** adi,fdd-rx-rate-2tx-enable
    0,		//swap_ports_enable *** adi,swap-ports-enable
    0,		//single_data_rate_enable *** adi,single-data-rate-enable
    0,		//lvds_mode_enable *** adi,lvds-mode-enable
    0,		//half_duplex_mode_enable *** adi,half-duplex-mode-enable
    1,		//single_port_mode_enable *** adi,single-port-mode-enable
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
    0,		//lvds_rx_onchip_termination_enable *** adi,lvds-rx-onchip-termination-enable
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
  m_AD9361_InitParam = init_param;
  m_AD9361_InitParam.id_no = m_device;
  // assign m_AD9361_InitParam.gpio_resetb to the arbitrarily defined GPIO_RESET_PIN so
  // that the No-OS opencpi platform driver knows to drive the force_reset
  // property of the sub-device
  m_AD9361_InitParam.gpio_resetb = (m_device << 8) | GPIO_RESET_PIN;
  g_devices.resize(m_device+1);
  g_devices[m_device] = &m_callBack;
}

void RadioCtrlrNoOSTuneResamp::update_AD9361_InitParam(const Ad9361InitConfig &config) {
  AD9361_InitParam& init = m_AD9361_InitParam;
  init.xo_disable_use_ext_refclk_enable = config.xo_disable_use_ext_ref_clk;
  init.reference_clk_rate = (uint32_t) round(m_AD9361_FREF_Hz);
  // printf("No-OS required rounding AD9361 reference clock rate from %0.15f to %" PRIu32, refclk, m_AD9361_InitParam.reference_clk_rate);
  bool is_2R1T_or_1R2T_or_2R2T = config.qadc1_is_present or config.qdac1_is_present;

  init.rx_frame_pulse_mode_enable = config.rx_frame_toggle ? 1 : 0;
  init.invert_data_bus_enable = config.data_bus_index_reverse ? 1:0;
  init.invert_data_clk_enable = config.data_clk_is_inverted ? 1 : 0;
  init.invert_rx_frame_enable = config.rx_frame_is_inverted ? 1 : 0;
  if(config.LVDS)
  {
    init.lvds_rx_onchip_termination_enable = 1;
    init.lvds_mode_enable                  = 1;

    // AD9361_Reference_Manual_UG-570.pdf (Rev. A):
    // "The following bits are not supported in LVDS mode:
    // * Swap Ports-In LVDS mode, P0 is Tx and P1 is Rx. This configuration cannot be changed.
    // * Single Port Mode-Both ports are enabled in LVDS mode.
    // * FDD Full Port-Not supported in LVDS.
    // * FDD Alt Word Order-Not supported in LVDS.
    // * FDD Swap Bits-Not supported in LVDS."
    init.swap_ports_enable            = 0;
    init.single_port_mode_enable      = 0;
    init.full_port_enable             = 0;
    init.fdd_alt_word_order_enable    = 0; ///@TODO/FIXME read this value from FPGA?
    init.half_duplex_mode_enable      = 0;
    init.single_data_rate_enable      = 0;
    init.full_duplex_swap_bits_enable = 0; ///@TODO / FIXME read this value from FPGA?
  }
  else { // mode is CMOS
    init.lvds_rx_onchip_termination_enable = 0;
    init.lvds_mode_enable                  = 0;

    init.swap_ports_enable         = config.swap_ports ? 1 : 0;
    init.single_port_mode_enable   = config.single_port ? 1 : 0;
    init.fdd_alt_word_order_enable = 0; ///@TODO/FIXME read this value from FPGA?
    init.full_port_enable          = (!config.half_duplex) and (!config.single_port);
    init.half_duplex_mode_enable   = config.half_duplex ? 1 : 0;
    init.single_data_rate_enable   = config.data_rate_ddr ? 0 : 1;
    init.full_duplex_swap_bits_enable = 0; ///@TODO / FIXME read this value from FPGA?
  }
  init.two_rx_two_tx_mode_enable = is_2R1T_or_1R2T_or_2R2T ? 1 : 0;

  init.rx_data_clock_delay = config.DATA_CLK_Delay;
  init.rx_data_delay       = config.RX_Data_Delay;
  init.tx_fb_clock_delay   = config.FB_CLK_Delay;
  init.tx_data_delay       = config.TX_Data_Delay;
}

bool RadioCtrlrNoOSTuneResamp::
configurator_check_and_reinit(const ConfigLockRequest& config_lock_request) {


  /*if(m_configurator_tune_resamp_locked) {
    this->log_debug("skipping locking tune resamp");
  }
  else {
    this->log_debug("not skipping locking tune resamp");
    m_configurator_tune_resamp_locked = true;
  }*/

  //configurator_copy.log_all_possible_config_values();
/* TODO REMOVE 
  // reset all 
  const char* filter_proxy_inst = m_app_inst_name_e31x_mimo_xcvr_filter_proxy.c_str(); 
  m_app.setProperty(filter_proxy_inst, "trxa_mode", "off");
  m_app.setProperty(filter_proxy_inst, "trxb_mode", "off");
  m_app.setProperty(filter_proxy_inst, "rx2a_mode", "off");
  m_app.setProperty(filter_proxy_inst, "rx2b_mode", "off");
*/
  auto it = config_lock_request.m_data_streams.begin(); 

  if(it == config_lock_request.m_data_streams.end()) {
    this->log_debug("config lock request was erroneously empty");
    return false;
  }

  bool reql_RX2 = false; // config_lock_request requires locking SMA RX2B
  bool reql_RX1 = false; // config_lock_request requires locking SMA RX2A
  bool reql_TX2 = false; // config_lock_request requires locking SMA TRXB
  bool reql_TX1 = false; // config_lock_request requires locking SMA TRXA

  // Create a copy of the most-derived object.
  std::unique_ptr<Configurator> clone(m_configurator.clone());
  Configurator &configurator_copy = *clone;
  for(; it != config_lock_request.m_data_streams.end(); it++) {

    throw_if_data_stream_lock_request_malformed(*it);

    if(not it->get_including_routing_ID()) {
      throw std::string("radio controller's data stream config lock request malformed: did not include routing_ID");
    }

    std::vector<data_stream_ID_t> data_streams;

    if(it->get_including_data_stream_ID()) {
      data_streams.push_back(it->get_data_stream_ID());
    }
    else { // assuming request by type only
      configurator_copy.find_data_streams_of_type(it->get_data_stream_type(), data_streams);

      if(data_streams.empty()) {
        // configurator_copy did not have any data streams of the requested data
        // stream type
        return false;
      }
    }
   
  /* TODO REMOVE data_stream_type_t dst_rx = data_stream_type_t::RX;
    data_stream_type_t dst_tx = data_stream_type_t::TX;
    data_stream_type_t it_dst = dst_rx; 
  */ 
    bool found_lock = false;
    // IDs of data streams what have the potential to meet the
    // requirements of the current data stream config lock request
    auto potential_ds_IDs = data_streams.begin();

    for(; potential_ds_IDs != data_streams.end(); potential_ds_IDs++) {

      config_key_t key;
      config_value_t val, tol;
      bool v;

/* TODO REMOVE
      bool is_tx; 
      this->log_debug("----TEST");    
      is_tx = (bool) it->get_data_stream_type();
      
      this->log_debug("Type: %d, %d ", is_tx, it->get_including_routing_ID());
  */    

      key = "tuning_freq_complex_mixer_MHz";
      val = 0;
      tol = 0;
      found_lock |= configurator_copy.lock_config(*potential_ds_IDs, key, val, tol);
      if(not found_lock) {
        this->log_info_config_lock_tol(false, false, *potential_ds_IDs,val,tol,key,"MHz");
        goto unrollandcontinue;
      }

      unsigned which;
      if((*potential_ds_IDs == TX2_id()) or (*potential_ds_IDs == TX1_id())) {
        key = "CIC_int_interpolation_factor";
	which = get_cic_int(*it);
	val = m_callBack.getInterpolation(which);
      }
      else if((*potential_ds_IDs == RX2_id()) or (*potential_ds_IDs == RX1_id())) {
        key = "CIC_dec_decimation_factor";
	which = get_cic_dec(*it);
	val = m_callBack.getDecimation(which);
      }
      tol = 0;
      found_lock |= configurator_copy.lock_config(*potential_ds_IDs, key, val, tol);
      if(not found_lock) {
        this->log_info_config_lock_tol(false, false, *potential_ds_IDs,val,tol,key,"");
        goto unrollandcontinue;
      }

      key = config_key_tuning_freq_MHz;
      val = it->get_tuning_freq_MHz();
      tol = it->get_tolerance_tuning_freq_MHz();
      found_lock |= configurator_copy.lock_config(*potential_ds_IDs, key, val, tol);
      if(not found_lock) {
        this->log_info_config_lock_tol(false, false, *potential_ds_IDs,val,tol,key,"MHz");
        goto unrollandcontinue;
      }

      key = config_key_bandwidth_3dB_MHz;
      val = it->get_bandwidth_3dB_MHz();
      tol = it->get_tolerance_bandwidth_3dB_MHz();
      found_lock |= configurator_copy.lock_config(*potential_ds_IDs, key, val, tol);
      if(not found_lock) {
        this->log_info_config_lock_tol(false, false, *potential_ds_IDs,val,tol,key,"MHz");
        goto unrollandcontinue;
      }

      key = config_key_sampling_rate_Msps;
      val = it->get_sampling_rate_Msps();
      tol = it->get_tolerance_sampling_rate_Msps();
      found_lock |= configurator_copy.lock_config(*potential_ds_IDs, key, val, tol);
      if(not found_lock) {
        this->log_info_config_lock_tol(false, false, *potential_ds_IDs,val,tol,key,"Msps");
        goto unrollandcontinue;
      }

      key = config_key_samples_are_complex;
      v = it->get_samples_are_complex();
      found_lock |= configurator_copy.lock_config(*potential_ds_IDs, key, v);
      if(not found_lock) {
        this->log_info_config_lock(false, *potential_ds_IDs,val,key,&v);
        goto unrollandcontinue;
      }

      if(it->get_including_gain_mode()) {
        key = config_key_gain_mode;

        config_value_t _auto = 0;
        config_value_t manual= 1;
        if((it->get_gain_mode().compare("manual") == 0) or
           (it->get_gain_mode().compare("RF_GAIN_MGC") == 0)) {
          found_lock |= configurator_copy.lock_config(*potential_ds_IDs, key, manual);
        }
        else if((it->get_gain_mode().compare("auto") == 0) or
                (it->get_gain_mode().compare("RF_GAIN_SLOWATTACK_AGC") == 0) or
                (it->get_gain_mode().compare("RF_GAIN_FASTATTACK_AGC") == 0) or
                (it->get_gain_mode().compare("RF_GAIN_HYBRID_AGC") == 0)) {
          found_lock |= configurator_copy.lock_config(*potential_ds_IDs, key, _auto);
        }

        if(not found_lock) {
          this->log_info_config_lock(false, *potential_ds_IDs,it->get_gain_mode(),key);
          goto unrollandcontinue;
        }
      }

      if(it->get_including_gain_dB()) {
        key = config_key_gain_dB;
        val = it->get_gain_dB();
        tol = it->get_tolerance_gain_dB();
        found_lock |= configurator_copy.lock_config(*potential_ds_IDs, key, val, tol);
        if(not found_lock) {
          this->log_info_config_lock_tol(false, false, *potential_ds_IDs,val,tol,key,"dB");
          goto unrollandcontinue;
        }
      }

      if(*potential_ds_IDs == RX2_id()) {
        reql_RX2 = true;
      }
      else if(*potential_ds_IDs == RX1_id()) {
        reql_RX1 = true;
      }
      else if(*potential_ds_IDs == TX2_id()) {
        reql_TX2 = true;
      }
      else if(*potential_ds_IDs == TX1_id()) {
        reql_TX1 = true;
      }

      break;
      unrollandcontinue:
      configurator_copy.unlock_config(*potential_ds_IDs, "tuning_freq_complex_mixer_MHz");
      if((*potential_ds_IDs == TX2_id()) or (*potential_ds_IDs == TX1_id())) {
        configurator_copy.unlock_config(*potential_ds_IDs, "CIC_int_interpolation_factor");
      }
      else if((*potential_ds_IDs == RX2_id()) or (*potential_ds_IDs == RX1_id())) {
        configurator_copy.unlock_config(*potential_ds_IDs, "CIC_dec_decimation_factor");
      }
      configurator_copy.unlock_config(*potential_ds_IDs, config_key_tuning_freq_MHz);
      configurator_copy.unlock_config(*potential_ds_IDs, config_key_bandwidth_3dB_MHz);
      configurator_copy.unlock_config(*potential_ds_IDs, config_key_sampling_rate_Msps);
      configurator_copy.unlock_config(*potential_ds_IDs, config_key_samples_are_complex);
      configurator_copy.unlock_config(*potential_ds_IDs, config_key_gain_mode);
      configurator_copy.unlock_config(*potential_ds_IDs, config_key_gain_dB);
    }

    if(not found_lock) {
      this->log_debug("configurator will not allow lock request\n");
      return false;
    }
  }

  bool s; // Boolean indication of whether any initialization procedure failed
          //(which may occur depending on current config locks)
  s = reinit_AD9361_if_required(reql_RX2,reql_RX1,reql_TX2,reql_TX1,configurator_copy);
  if(s) {
    this->log_debug("configurator will allow lock request\n");
  }
  return s;
}

bool RadioCtrlrNoOSTuneResamp::reinit_AD9361_if_required(
  const bool reql_RX2, const bool reql_RX1,
  const bool reql_TX2, const bool reql_TX1,
  const Configurator& configurator_copy) {
  this->log_debug("reql_RX2=%s,reql_RX1=%s,reql_TX2=%s,reql_TX1=%s",
 (reql_RX2 ? "t" : "f"),
 (reql_RX1 ? "t" : "f"),
 (reql_TX2 ? "t" : "f"),
 (reql_TX1 ? "t" : "f"));

  if((!reql_RX2) and (!reql_RX1) and (!reql_TX2) and (!reql_TX1)) {
    // this function should never be called if we end up here, but we handle it
    // to be robust
    return true;
  }
  else {
    // indicator that previous ad9361_init() was called w/ values that are
    // incompatible with the pending config lock request, thus requiring a
    // "re"-initialization
    bool requires_reinit = false;

    // values required by pending config lock request
    bool two_rx_two_tx;
    uint8_t use_rx_num;
    uint8_t use_tx_num;
    uint8_t fdd_rx_rate_2tx_enable;

    if((reql_RX2 and reql_RX1) or (reql_TX2 and reql_TX1)) {
      two_rx_two_tx = true;
      use_rx_num = 1; // don't care, just set to 1
      use_tx_num = 1; // don't care, just set to 1
    }
    else {
      two_rx_two_tx = false;
      use_rx_num = reql_RX2 ? 2 : 1;
      use_tx_num = reql_TX2 ? 2 : 1;
    }

    if(m_ad9361_init_called) {
      if(two_rx_two_tx != m_AD9361_InitParam.two_rx_two_tx_mode_enable) {
        this->log_debug("requires_reinit two_rx_two_tx");
        requires_reinit = true;
      }
      if(not two_rx_two_tx) {
        if(reql_RX2 or reql_RX1) {
          if(use_rx_num != m_AD9361_InitParam.one_rx_one_tx_mode_use_rx_num) {
            this->log_debug("requires_reinit use_rx_num");
            requires_reinit = true;
          }
        }
        if(reql_TX2 or reql_TX1) {
          if(use_tx_num != m_AD9361_InitParam.one_rx_one_tx_mode_use_tx_num) {
            this->log_debug("requires_reinit use_tx_num");
            requires_reinit = true;
          }
        }
      }
    }

    std::unique_ptr<Configurator> copy(configurator_copy.clone());
    Configurator &copycopy = *copy;
    const ConfigValueRanges& x = copycopy.get_ranges_possible("DAC_Clk_divider");
    fdd_rx_rate_2tx_enable = (x.get_smallest_min() < 1.5) ? 0 : 1;

    if(m_ad9361_init_called) {
      config_value_t DAC_Clk_divider;
      DAC_Clk_divider = (m_AD9361_InitParam.fdd_rx_rate_2tx_enable == 1) ? 2 :1;
      if(!x.is_valid(DAC_Clk_divider)) {
        this->log_debug("requires_reinit fdd_rx_rate_2tx_enable");
        requires_reinit = true;
      }
    }

    if((not m_ad9361_init_called) or requires_reinit) {
      if(requires_reinit) {
        if(any_configurator_configs_locked_which_prevent_ad9361_init()) {
          this->log_debug("reinit required but configurator configs locked which prevent reinit");
          return false;
        }
        this->log_info("re-initializing AD9361");
      }
      // prepare m_AD9361_InitParam and perform AD9361 initialization
      m_AD9361_InitParam.two_rx_two_tx_mode_enable = two_rx_two_tx;
      m_AD9361_InitParam.one_rx_one_tx_mode_use_rx_num = use_rx_num;
      m_AD9361_InitParam.one_rx_one_tx_mode_use_tx_num = use_tx_num;
      m_AD9361_InitParam.fdd_rx_rate_2tx_enable = fdd_rx_rate_2tx_enable;
      init();
    }
  }

  return true;
}

bool RadioCtrlrNoOSTuneResamp::any_configurator_configs_locked_which_prevent_ad9361_init() const {

  std::vector<data_stream_ID_t> data_streams;
  if (!RX1_id().empty())
    data_streams.push_back(std::string(RX1_id()));
  if (!RX2_id().empty())
    data_streams.push_back(std::string(RX2_id()));
  if (!TX1_id().empty())
    data_streams.push_back(std::string(TX1_id()));
  if (!TX2_id().empty())
    data_streams.push_back(std::string(TX2_id()));

  // unfortunately necessary to make this function const
  std::unique_ptr<Configurator> copy(m_configurator.clone());
  Configurator &configurator_copy = *copy;

  auto it = data_streams.begin();
  for(; it != data_streams.end(); it++) {
    if(configurator_copy.get_config_is_locked(*it, config_key_tuning_freq_MHz)) {
      return true;
    }
    if(configurator_copy.get_config_is_locked(*it, config_key_bandwidth_3dB_MHz)) {
      return true;
    }
    if(configurator_copy.get_config_is_locked(*it, config_key_sampling_rate_Msps)) {
      return true;
    }
    if(configurator_copy.get_config_is_locked(*it, config_key_gain_mode)) {
      return true;
    }
    if(configurator_copy.get_config_is_locked(*it, config_key_gain_dB)) {
      return true;
    }
  }
  return false;
}

void RadioCtrlrNoOSTuneResamp::throw_if_ad9361_init_failed(
    const char* operation) const {

  if(m_ad9361_init_ret != 0) {
    std::ostringstream oss;
    oss << "cannot perform ";
    oss << (operation ? operation : "operation");
    oss << " because ad9361_init() failed";
    throw oss.str();
  }
}

std::vector<gain_mode_value_t>
RadioCtrlrNoOSTuneResamp::get_ranges_possible_gain_mode(
    const data_stream_ID_t data_stream_ID) const {

  std::vector<gain_mode_value_t> ret;
  auto key = config_key_gain_mode;
  std::unique_ptr<Configurator> copy(m_configurator.clone());
  Configurator &configurator_copy = *copy;
  auto vr = configurator_copy.get_ranges_possible(data_stream_ID, key);

  if(vr.is_valid(0)) {
    // auto is generic value (which corresponds to AD9361-specific
    // RF_GAIN_SLOWATTACK_AGC)
    ret.push_back("auto");
  }
  if(vr.is_valid(1)) {
    // auto is generic value (which corresponds to AD9361-specific
    // RF_GAIN_MGC)
    ret.push_back("manual");
  }
  bool is_locked = vr.is_valid(0) xor vr.is_valid(1); // this is an assumption

  if(not is_locked) {
    if((data_stream_ID == RX2_id()) or (data_stream_ID == RX1_id())) {
      // AD9361/No-OS-specific values
      ret.push_back("RF_GAIN_FASTATTACK_AGC");
      ret.push_back("RF_GAIN_SLOWATTACK_AGC");
      ret.push_back("RF_GAIN_HYBRID_AGC");
    }
  }

  return ret;
}

unsigned RadioCtrlrNoOSTuneResamp::
get_complex_mixer(const DataStreamConfigLockRequest& req, bool &tx) const {

  throw_if_data_stream_lock_request_malformed(req);

  std::string inst;
  tx = false;
  if (req.get_routing_ID() == "RX0")
    return 0;
  if (req.get_routing_ID() == "RX1")
    return 1;
  tx = true;
  if(req.get_routing_ID() == "TX0")
    return 0;
  return 1;
}

unsigned RadioCtrlrNoOSTuneResamp::get_cic_int(
    const DataStreamConfigLockRequest& req) const {

  throw_if_data_stream_lock_request_malformed(req);

  if (req.get_routing_ID() == "TX0")
    return 0;
  if (req.get_routing_ID() == "TX1")
    return 1;
  std::ostringstream oss;
  oss << "attempted to access cic_int app inst name for bad routing ID of ";
  oss << req.get_routing_ID();
  throw oss.str();
}

unsigned RadioCtrlrNoOSTuneResamp::get_cic_dec(
    const DataStreamConfigLockRequest& req) const {

  throw_if_data_stream_lock_request_malformed(req);

  if (req.get_routing_ID() == "RX0")
    return 0;
  if (req.get_routing_ID() == "RX1")
    return 1;
  std::ostringstream oss;
  oss << "attempted to access cic_int app inst name for bad routing ID of ";
  oss << req.get_routing_ID();
  throw oss.str();
}


} // namespace RadioCtrlr

} // namespace OCPIProjects
