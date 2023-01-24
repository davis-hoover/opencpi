/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Tue Jan 10 17:47:24 2023 EST
 * BASED ON THE FILE: drc_fmcomms_2_3.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the drc_fmcomms_2_3 worker in C++
 */

#include "drc_fmcomms_2_3-worker.hh"

#define IS_LOCKING
#include "FMCOMMS2_3DRC.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Drc_fmcomms_2_3WorkerTypes;

namespace OD = OCPI::DRC_PHASE_2;
#include "OcpiDrcProxyApi.hh" // this must be after the "using namespace" of the types namespace

typedef OCPI::DRC::DrcProxyBase BASE_CLASS;

class Drc_fmcomms_2_3Worker : public BASE_CLASS {
  // ================================================================================================
  // trampoline between the DRC ad9361 helper classes in the framework library and the slave workers
  // accessible from this worker.  It lets the former call the latter
  struct DoSlave : OD::AD9361DeviceCallBack {
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
      ad9361InitialConfig(m_slaves.config, m_slaves.data_sub, config);
      config.xo_disable_use_ext_ref_clk=false;
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
  OD::FMCOMMS2_3DRC<OD::FMCOMMS2_3Configurator> m_ctrlr;
public:
  ///@TODO / FIXME - replace "3" with FMCOMMS_NUM parameter property
  Drc_fmcomms_2_3Worker()
    : m_doSlave(slaves),
      m_ctrlr(0,m_doSlave,40e6,3,"Rx0","Rx1","Tx0","Tx1") {
  }
  // ================================================================================================
  // These methods interface with the helper 9361 classes etc.
  // ================================================================================================
  RCCResult prepare_config(unsigned config) {
    auto &conf = m_properties.configurations.data[config];
    OD::ConfigLockRequest req;
    // convert the data structure dictated by the drc spec property to the one
    // defined by the older DRC helper class(es)
    auto nChannels = conf.channels.length;
    req.m_data_streams.resize(nChannels);
    unsigned nRx = 0, nTx = 0;
    for (unsigned n = 0; n < nChannels; ++n) {
      auto &channel = conf.channels.data[n];
      auto &stream = req.m_data_streams[n];
      stream = OD::DataStreamConfigLockRequest(); // zero out any previous requests
      stream.include_data_stream_direction(channel.rx ?
                                      OD::data_stream_direction_t::rx : OD::data_stream_direction_t::tx);
      if (!std::string(channel.rf_port_name).empty()) {
        stream.include_data_stream_id(channel.rf_port_name);
      }
      ///@TODO / FIXME - probably need to associate routing_id with app_port_NAME
      //stream.include_routing_id((channel.rx ? "RX" : "TX") +
      //                          std::to_string(channel.rx ? nRx : nTx));
      ++(channel.rx ? nRx : nTx);
      stream.include_tuning_freq_MHz(channel.tuning_freq_MHz, channel.tolerance_tuning_freq_MHz);
      stream.include_bandwidth_3dB_MHz(channel.bandwidth_3dB_MHz, channel.tolerance_bandwidth_3dB_MHz);
      stream.include_sampling_rate_Msps(channel.sampling_rate_Msps, channel.tolerance_sampling_rate_Msps);
      stream.include_samples_are_complex(channel.samples_are_complex);
      stream.include_gain_mode(channel.gain_mode);
      if (!stream.get_gain_mode().compare("manual")) {
        stream.include_gain_dB(channel.gain_dB, channel.tolerance_gain_dB);
      }
    }
    try {
      return m_ctrlr.prepare(config, req) ? RCC_OK :
        setError("config prepare request was unsuccessful, set OCPI_LOG_LEVEL to 8 "
                 "(or higher) for more info");
    } catch(const char* err) {
      return setError(err);
    }
    return RCC_OK;
  }
  RCCResult start_config(unsigned config) {
    try {
      return m_ctrlr.start(config) ? RCC_OK :
        setError("config start was unsuccessful, set OCPI_LOG_LEVEL to 8 "
                 "(or higher) for more info");
    } catch(const char* err) {
      return setError(err);
    }
    return RCC_OK;
  }
  RCCResult stop_config(unsigned config) { 
    log(8, "DRC: stop_config: %u", config);
    try {
      return m_ctrlr.stop(config) ? RCC_OK :
        setError("config stop was unsuccessful, set OCPI_LOG_LEVEL to 8 "
                 "(or higher) for more info");
    } catch(const char* err) {
      return setError(err);
    }
    return RCC_OK;

  }
  // notification that start property has been written
  RCCResult start_written() {
    log(8, "start config %u %u", m_properties.start, isOperating());
    unsigned config = m_properties.start;
    if (config >= OCPI_DRC_MAX_CONFIGURATIONS)
      return setError("Configuration %u started, but is out of range (0 to %u)",
          config, OCPI_DRC_MAX_CONFIGURATIONS - 1);
    init_status(config);
    //if (isOperating()) {
      log(8, "operating, so calling");
      RCCResult rc = OCPI::DRC::DrcProxyBase::start_config(config, false);
      if (rc == RCC_OK)
        m_properties.status.data[config].state = STATUS_STATE_OPERATING;
      return rc;
    //}
    //else {
    //  log(8, "not operating so not calling");
    //}
    // Deferred start
    m_started[m_properties.start] = true;
    return RCC_OK;
  }
  RCCResult release_config(unsigned config) {
    log(8, "DRC: release_config");
    return m_ctrlr.release(config) ? RCC_OK :
      setError("config release was unsuccessful, set OCPI_LOG_LEVEL to 8 "
               "(or higher) for more info");
  }
};

DRC_FMCOMMS_2_3_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case
DRC_FMCOMMS_2_3_END_INFO
