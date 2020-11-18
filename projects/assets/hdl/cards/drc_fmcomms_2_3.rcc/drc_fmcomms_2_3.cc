/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Mon Nov 16 20:26:11 2020 CST
 * BASED ON THE FILE: drc_fmcomms_2_3.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the drc_fmcomms_2_3 worker in C++
 */

#include "drc_fmcomms_2_3-worker.hh"

// These are the helper classes for the ad9361 helpers
#include "RadioCtrlrConfiguratorTuneResamp.hh"
#include "RadioCtrlrConfiguratorAD9361.hh"
#include "RadioCtrlrNoOSTuneResamp.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Drc_fmcomms_2_3WorkerTypes;

//This is for the generic drc helper class
#include "OcpiDrcProxyApi.hh" // this must be after the "using namespace" of the types namespace

namespace OD = OCPI::DRC;

class Drc_fmcomms_2_3Worker : public OD::DrcProxyBase { 

  // ========================================================================
  // To use the ad9361 DRC helper classes, we need a configurator class that combines the bas ad9361 
  // one with the tuneresamp soft tuning
  class Fmcomms_2_3_Configurator: public OD::ConfiguratorAD9361, public OD::ConfiguratorTuneResamp {
  public:
    Fmcomms_2_3_Configurator()
      : OD::ConfiguratorAD9361(DRC_FMCOMMS_2_3_RF_PORTS_RX.data[0], NULL,
		               DRC_FMCOMMS_2_3_RF_PORTS_TX.data[0], NULL), 
	OD::ConfiguratorTuneResamp(ad9361MaxRxSampleMhz(), ad9361MaxTxSampleMhz()) { 
    }
    // All concrete Configurator classes must have this clone method for virtual copying. 
    OD::Configurator *clone() const { return new Fmcomms_2_3_Configurator(*this); }
  protected:
    // The virtual callback to impose all constraints. 
    void impose_constraints_single_pass() {
      ConfiguratorAD9361::impose_constraints_single_pass();
      ConfiguratorTuneResamp::impose_constraints_single_pass();
      Configurator::impose_constraints_single_pass();
    }
  } m_configurator;

  // ================================================================================================
  // trampoline between the DRC ad9361 helper classes in the framework library and the slave workers
  // accessible from this worker.  It lets the former call the latter
  struct DoSlave : OD::DeviceCallBack {
    Slaves &m_slaves;
    DoSlave(Slaves &slaves) : m_slaves(slaves) {}
    void get_byte(uint8_t /*id_no*/, uint16_t addr, uint8_t *buf) {
      m_slaves.config.getRawPropertyBytes(addr, buf, 1);
    }
    void set_byte(uint8_t /*id_no*/, uint16_t addr, const uint8_t *buf) {
      m_slaves.config.setRawPropertyBytes(addr, buf, 1);
    }
    void set_reset(uint8_t /*id_no*/, bool on) {
      m_slaves.config.set_force_reset(on ? 1 : 0);
    }
    bool isMixerPresent(bool rx, unsigned stream) {
      return stream == 0 && rx ? m_slaves.rx_complex_mixer0.isPresent() : false;
    }
    OD::config_value_t getDecimation(unsigned /*stream*/) {
      return m_slaves.rx_cic_dec0.isPresent() ? m_slaves.rx_cic_dec0.get_R() : 1;
    }
    OD::config_value_t getInterpolation(unsigned /*stream*/) {
      return m_slaves.tx_cic_int0.isPresent() ? m_slaves.tx_cic_int0.get_R() : 1;
    }
    OD::config_value_t getPhaseIncrement(bool rx, unsigned /*stream*/) {
      return rx ? m_slaves.rx_complex_mixer0.get_phs_inc() : 0;
    }
    void setPhaseIncrement(bool rx, unsigned /*stream*/, int16_t inc) {
      if (rx)
        m_slaves.rx_complex_mixer0.set_phs_inc(inc);
    }
    void initialConfig(uint8_t /*id_no*/, OD::Ad9361InitConfig &config) {
      OD::ad9361InitialConfig(m_slaves.config, m_slaves.data_sub, config);
    }
    void postConfig(uint8_t /*id_no*/) {
      OD::ad9361PostConfig(m_slaves.config);
    }
    void finalConfig(uint8_t /*id_no*/, OD::Ad9361InitConfig &config) {
      OD::ad9361FinalConfig(m_slaves.config, config);
    }
    // both of these apply to both channels on the 9361
    unsigned getRfInput(unsigned /*device*/, OD::config_value_t /*tuning_freq_MHz*/) { return 0; }
    unsigned getRfOutput(unsigned /*device*/, OD::config_value_t /*tuning_freq_MHz*/) { return 0; }
  } m_doSlave;

  OD::RadioCtrlrNoOSTuneResamp m_ctrlr;
  OD::ConfigLockRequest m_requests[DRC_FMCOMMS_2_3_MAX_CONFIGURATIONS_P];

public:
  Drc_fmcomms_2_3Worker()
    : m_doSlave(slaves),
      m_ctrlr(0, "drc_fmcomms_2_3", m_configurator, m_doSlave) {
  }
  // ================================================================================================
  // These methods interface with the helper 9361 classes etc.
  // ================================================================================================
  RCCResult prepare_config(unsigned config) {
    auto &conf = m_properties.configurations.data[config];
    auto &req = m_requests[config];
    // So here we basically convert the data structure dictated by the drc spec property to the one
    // defined by the older DRC/ad9361 helper classes
    auto nChannels = conf.channels.length;
    req.m_data_streams.resize(nChannels);
    unsigned nRx = 0, nTx = 0;
    for (unsigned n = 0; n < nChannels; ++n) {
      auto &channel = conf.channels.data[n];
      auto &stream = req.m_data_streams[n];
      stream.include_data_stream_type(channel.rx ?
                                      OD::data_stream_type_t::RX : OD::data_stream_type_t::TX);
      stream.include_data_stream_ID(channel.rx ?
                                    DRC_FMCOMMS_2_3_RF_PORTS_RX.data[nRx] :
                                    DRC_FMCOMMS_2_3_RF_PORTS_TX.data[nTx]);
      stream.include_routing_ID((channel.rx ? "RX0" : "TX0") +
                                std::to_string(channel.rx ? nRx : nTx));
      ++(channel.rx ? nRx : nTx);
      stream.include_tuning_freq_MHz(channel.tuning_freq_MHz, channel.tolerance_tuning_freq_MHz);
      stream.include_bandwidth_3dB_MHz(channel.bandwidth_3dB_MHz, channel.tolerance_bandwidth_3dB_MHz);
      stream.include_sampling_rate_Msps(channel.sampling_rate_Msps, channel.tolerance_sampling_rate_Msps);
      stream.include_samples_are_complex(channel.samples_are_complex);
      stream.include_gain_mode(channel.gain_mode);
    }
    // Ideally we would validate them here, but not now.
    return RCC_OK;
  }
  RCCResult start_config(unsigned config) {
    try {
      return m_ctrlr.request_config_lock(std::to_string(config), m_requests[config]) ?
        RCC_OK :
        setError("config lock request was unsuccessful, set OCPI_LOG_LEVEL to 8 "
                 "(or higher) for more info");
    } catch(const char* err) {
      return setError(err);
    }
    return RCC_OK;
  }

};

DRC_FMCOMMS_2_3_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
DRC_FMCOMMS_2_3_END_INFO
