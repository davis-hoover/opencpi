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

#define OCPI_DRC_CAT_(a,b) a##b
#define OCPI_DRC_CAT(a,b) OCPI_DRC_CAT_(a,b)
#define OCPI_DRC_MAX_CONFIGURATIONS OCPI_DRC_CAT(OCPI_WORKER_NAME,_MAX_CONFIGURATIONS_P)
class Drc_fmcomms_2_3Worker : public Drc_fmcomms_2_3WorkerBase {
  std::vector<bool> m_started; // record what should be started when the proxy is started.
  // ================================================================================================
  // trampoline between the DRC ad9361 helper classes in the framework library and the slave workers
  // accessible from this worker.  It lets the former call the latter
  struct DoSlave : DRC::AD9361DeviceCallBack {
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
    DRC::config_value_t getDecimation(unsigned /*stream*/) {
      return m_slaves.rx_cic_dec0.isPresent() ? m_slaves.rx_cic_dec0.get_R() : 1;
    }
    DRC::config_value_t getInterpolation(unsigned /*stream*/) {
      return m_slaves.tx_cic_int0.isPresent() ? m_slaves.tx_cic_int0.get_R() : 1;
    }
    DRC::config_value_t getPhaseIncrement(bool rx, unsigned /*stream*/) {
      return rx ? m_slaves.rx_complex_mixer0.get_phs_inc() : 0;
    }
    void setPhaseIncrement(bool rx, unsigned /*stream*/, int16_t inc) {
      if (rx)
        m_slaves.rx_complex_mixer0.set_phs_inc(inc);
    }
    void initialConfig(uint8_t /*id_no*/, DRC::Ad9361InitConfig &config) {
      ad9361InitialConfig(m_slaves.config, m_slaves.data_sub, config);
      config.xo_disable_use_ext_ref_clk=false;
    }
    void postConfig(uint8_t /*id_no*/) {
      DRC::ad9361PostConfig(m_slaves.config);
    }
    void finalConfig(uint8_t /*id_no*/, DRC::Ad9361InitConfig &config) {
      DRC::ad9361FinalConfig(m_slaves.config, config);
    }
    // both of these apply to both channels on the 9361
    unsigned getRfInput(unsigned /*device*/, DRC::config_value_t /*tuning_freq_MHz*/) { return 0; }
    unsigned getRfOutput(unsigned /*device*/, DRC::config_value_t /*tuning_freq_MHz*/) { return 0; }
  } m_doSlave;
  DRC::FMCOMMS2_3DRC<DRC::OCPI_log_func_args_t,DRC::FMCOMMS2_3Configurator> m_ctrlr;
public:
  ///@TODO / FIXME - replace "3" with FMCOMMS_NUM parameter property
  Drc_fmcomms_2_3Worker()
    : m_started(OCPI_DRC_MAX_CONFIGURATIONS),
      m_doSlave(slaves),
      m_ctrlr(0,m_doSlave,40e6,3,"Rx0","Rx1","Tx0","Tx1") {
    //m_ctrlr.set_forwarding_callback_log_info(OCPI::OS::logPrintV);
  }
  // Initialize status for config if not already present.
  // This config is already error checked
  void init_status(unsigned config) {
    if (config >= m_properties.status.length) {
      m_properties.status.resize(config + 1);
      m_properties.status.data[config].state = STATUS_STATE_INACTIVE;
      m_properties.status.data[config].channels.length = 0;
    }
  }
  // ================================================================================================
  // These methods interface with the helper 9361 classes etc.
  // ================================================================================================
  RCCResult prepare_config(unsigned config) {
    auto &conf = m_properties.configurations.data[config];
    DRC::ConfigLockRequest req;
    // convert the data structure dictated by the drc spec property to the one
    // defined by the older DRC helper class(es)
    auto nChannels = conf.channels.length;
    req.m_data_streams.resize(nChannels);
    unsigned nRx = 0, nTx = 0;
    for (unsigned n = 0; n < nChannels; ++n) {
      auto &channel = conf.channels.data[n];
      auto &stream = req.m_data_streams[n];
      stream = DRC::DataStreamConfigLockRequest(); // zero out any previous requests
      stream.include_data_stream_direction(channel.rx ?
                                      DRC::data_stream_direction_t::rx : DRC::data_stream_direction_t::tx);
      if (!std::string(channel.rf_port_name).empty()) {
        stream.include_data_stream_id(channel.rf_port_name);
        //std::cout << "include data_stream_id=" << stream.get_data_stream_id() << "\n";
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
      //std::cout << "channel.gain_mode=" << channel.gain_mode << "\n";
      //std::cout << "stream.get_gain_mode()=" << stream.get_gain_mode() << "\n";
      //std::cout << "channel.gain_mode compare=" << (!stream.get_gain_mode().compare("manual")) << "\n";
      if (!stream.get_gain_mode().compare("manual")) {
        stream.include_gain_dB(channel.gain_dB, channel.tolerance_gain_dB);
        //std::cout << "including gain_db\n";
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
  // The control operation, where we will do any deferred starts indicated in XML
  // Note we only to this for one config.
  RCCResult
  start_config(unsigned config, bool /*atStart*/) {
    log(8, "STARTING DRC PROXY CONFIGURATION: %u", config);
    RCCResult rc;
    switch (m_properties.status.data[config].state) {
    case STATUS_STATE_INACTIVE:
      if ((rc = prepare_config(config)) != RCC_OK)
        return rc;
      m_properties.status.data[config].state = STATUS_STATE_PREPARED;
      // fall through
    case STATUS_STATE_PREPARED:
      if ((rc = start_config(config)) != RCC_OK)
        return rc;
      m_properties.status.data[config].state = STATUS_STATE_OPERATING;
      return RCC_OK;
    case STATUS_STATE_OPERATING:
      log(8, "Warning: DRC proxy started a configuration that was already started.  Ignored.");
      return RCC_OK;
    case STATUS_STATE_ERROR:
    default:
      return setError("Configuration %u is in an error state and cannot be started", config);
    }
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
  RCCResult start() {
    log(8, "STARTING DRC PROXY");
    size_t nConfigs = m_properties.configurations.size();
    RCCResult rc;
    for (size_t n = 0; n < nConfigs; ++n)
      if (m_started[n]) {
        m_started[n] = false;
        if ((rc = start_config(n, true)))
        return rc;
      }
    return RCC_OK;
  }
  RCCResult stop_config(unsigned config, bool /*atStop*/) {
    log(8, "STOPPING DRC PROXY CONFIGURATION: %u", config);
    switch (m_properties.status.data[config].state) {
      case STATUS_STATE_INACTIVE:
        return RCC_OK;
      case STATUS_STATE_PREPARED:
        return RCC_OK;
      case STATUS_STATE_OPERATING:
        log(8, "STOPPING CONFIG");
        return stop_config(config);
      case STATUS_STATE_ERROR: 
      default:
        return setError("Configuration %u is in an error state and cannot be started", config);
    }
  }
  RCCResult release_config(unsigned config) {
    log(8, "DRC: release_config");
    return m_ctrlr.release(config) ? RCC_OK :
      setError("config release was unsuccessful, set OCPI_LOG_LEVEL to 8 "
               "(or higher) for more info");
  }
  virtual RCCResult status_config(unsigned /*config*/) { return RCC_OK; }

  // notification that prepare property has been written
  RCCResult prepare_written() {
    log(8, "prepare config %u", m_properties.prepare);
    unsigned config = m_properties.prepare;
    if (config >= OCPI_DRC_MAX_CONFIGURATIONS)
      return setError("Configuration %u started, but is out of range (0 to %u)",
          config, OCPI_DRC_MAX_CONFIGURATIONS - 1);
    init_status(config);
    RCCResult rc = prepare_config(config);
    if (rc == RCC_OK)
      m_properties.status.data[config].state = STATUS_STATE_PREPARED;
    return rc;
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
      RCCResult rc = start_config(config, false);
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
  // notification that stop property has been written
  RCCResult stop_written() {
    log(8, "stop config %u", m_properties.stop);
    RCCResult rc = stop_config(m_properties.stop, false);
    m_properties.status.data[m_properties.stop].state =
      rc == RCC_OK ? STATUS_STATE_PREPARED : STATUS_STATE_ERROR;
    return rc;
  }
  // notification that release property has been written
  RCCResult release_written() {
    log(8, "release config %u", m_properties.release);
    RCCResult rc = release_config(m_properties.release);
    m_properties.status.data[m_properties.release].state =
      rc == RCC_OK ? STATUS_STATE_INACTIVE : STATUS_STATE_ERROR;
    return rc;
  }
  // notification that status property will be read
  RCCResult status_read() {
    size_t nConfigs = m_properties.configurations.size();
    m_properties.status.resize(nConfigs);
    for (size_t n = 0; n < nConfigs; ++n) {
      auto &conf = m_properties.configurations.data[n];
      auto &stat = m_properties.status.data[n];
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
  RCCResult run(bool /*timedout*/) {
    return RCC_DONE; // change this as needed for this worker to do something useful
    // return RCC_ADVANCE; when all inputs/outputs should be advanced each time "run" is called.
    // return RCC_ADVANCE_DONE; when all inputs/outputs should be advanced, and there is nothing more to do.
    // return RCC_DONE; when there is nothing more to do, and inputs/outputs do not need to be advanced.
  }
};

DRC_FMCOMMS_2_3_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case
DRC_FMCOMMS_2_3_END_INFO
