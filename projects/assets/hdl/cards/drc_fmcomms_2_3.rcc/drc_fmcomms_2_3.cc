/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Tue Jan 10 17:47:24 2023 EST
 * BASED ON THE FILE: drc_fmcomms_2_3.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the drc_fmcomms_2_3 worker in C++
 */

#include "drc_fmcomms_2_3-worker.hh"

/// @todo / FIXME remove IS_LOCKING
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
    double getDecimation(unsigned /*stream*/) {
      return m_slaves.rx_cic_dec0.isPresent() ? m_slaves.rx_cic_dec0.get_R() : 1;
    }
    double getInterpolation(unsigned /*stream*/) {
      return m_slaves.tx_cic_int0.isPresent() ? m_slaves.tx_cic_int0.get_R() : 1;
    }
    double getPhaseIncrement(bool rx, unsigned /*stream*/) {
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
    unsigned getRfInput(unsigned /*device*/, double /*tuning_freq_MHz*/) { return 0; }
    unsigned getRfOutput(unsigned /*device*/, double /*tuning_freq_MHz*/) { return 0; }
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
    ///@TODO / FIXME address app_port_num
    typedef OD::RFPort::direction_t direction_t;
    auto &conf = m_properties.configurations.data[config];
    OD::ConfigLockRequest req;
    // convert the data structure dictated by the drc spec property to the one
    // defined by the older DRC helper class(es)
    auto nChannels = conf.channels.length;
    for (unsigned n = 0; n < nChannels; ++n) {
      auto &channel = conf.channels.data[n];
      direction_t direction = channel.rx ? direction_t::rx : direction_t::tx;
      OD::RFPortConfigLockRequest rf_port(
          direction,
          channel.tuning_freq_MHz,
          channel.bandwidth_3dB_MHz,
          channel.sampling_rate_Msps,
          channel.samples_are_complex,
          channel.gain_mode,
          channel.gain_dB,
          channel.tolerance_tuning_freq_MHz,
          channel.tolerance_bandwidth_3dB_MHz,
          channel.tolerance_sampling_rate_Msps,
          channel.tolerance_gain_dB,
          channel.rf_port_name,
          channel.rf_port_num,
          channel.app_port_num);
      req.push_back(rf_port);
    }
    RCCResult rc = RCC_OK;
    try {
      m_ctrlr.set_configuration((uint16_t)config, req);
      if (!m_ctrlr.prepare((uint16_t)config))
        throw std::runtime_error("failed");
    } catch(std::exception& err) {
      //std::cout << "err=" << err << "\n";
      if(conf.recoverable) {
        std::string ctrlerr = m_ctrlr.get_error().c_str();
        size_t count = ctrlerr.size();
        count = std::min(count, (size_t)DRC_FMCOMMS_2_3_MAX_STRING_LENGTH_P);
        memcpy(&m_properties.status.data[config].error, ctrlerr.c_str(), count);
        rc = RCC_OK;
      }
      else {
        rc = setError("config prepare request was unsuccessful, set OCPI_LOG_LEVEL to 8 "
                 "(or higher) for more info");
      }
    }
    return rc;
  }
  RCCResult start_config(unsigned config) {
    try {
      return m_ctrlr.start((uint16_t)config) ? RCC_OK :
        setError("config start was unsuccessful, set OCPI_LOG_LEVEL to 8 "
                 "(or higher) for more info");
    } catch(std::exception& err) {
      return setError(err.what());
    }
    return RCC_OK;
  }
  RCCResult stop_config(unsigned config) { 
    log(8, "DRC: stop_config: %u", config);
    try {
      return m_ctrlr.stop((uint16_t)config) ? RCC_OK :
        setError("config stop was unsuccessful, set OCPI_LOG_LEVEL to 8 "
                 "(or higher) for more info");
    } catch(std::exception& err) {
      return setError(err.what());
    }
    return RCC_OK;
  }
  // notification that start property has been written
  RCCResult start_written() {
    log(8, "start config %u %u", m_properties.start, isOperating());
    uint16_t config = m_properties.start;
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
  // notification that status property will be read
  RCCResult status_read() {
    size_t nConfigs = m_properties.configurations.size();
    m_properties.status.resize(nConfigs);
    for (size_t n = 0; n < nConfigs; ++n) {
      auto &conf = m_properties.configurations.data[n];
      auto &stat = m_properties.status.data[n];
      stat.channels.resize(conf.channels.size());
      // stat.state member is already maintained
      // stat.error
      for (size_t nch = 0; nch < conf.channels.size(); ++nch) {
	auto &confchan = conf.channels.data[nch];
	auto &statchan = stat.channels.data[nch];
	statchan.tuning_freq_MHz = confchan.tuning_freq_MHz;
	statchan.bandwidth_3dB_MHz = confchan.bandwidth_3dB_MHz;
	statchan.sampling_rate_Msps = confchan.sampling_rate_Msps;
	statchan.gain_dB = confchan.gain_dB;
      }
      status_config(n);
    }
    return RCC_OK;
  }
  RCCResult release_config(unsigned config) {
    log(8, "DRC: release_config");
    return m_ctrlr.release((uint16_t)config) ? RCC_OK :
      setError("config release was unsuccessful, set OCPI_LOG_LEVEL to 8 "
               "(or higher) for more info");
  }
};

DRC_FMCOMMS_2_3_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case
DRC_FMCOMMS_2_3_END_INFO
