
// This file is expected to be included after the line in the proxy code that includes
// the proxy worker's type namespace, e.g.:
// using namespace Drc_plutosdrWorkerTypes;

// The helper class for DRC proxy workers
namespace OCPI {
namespace DRC {

#define OCPI_DRC_CAT_(a,b) a##b
#define OCPI_DRC_CAT(a,b) OCPI_DRC_CAT_(a,b)
#define OCPI_DRC_MAX_CONFIGURATIONS OCPI_DRC_CAT(OCPI_WORKER_NAME,_MAX_CONFIGURATIONS_P)
class DrcProxyBase : public WorkerBase {
protected:
  std::vector<bool> m_started; // record what should be started when the proxy is started.

  DrcProxyBase() : m_started(OCPI_DRC_MAX_CONFIGURATIONS) {
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
  RCCResult stop() {
    log(8, "STOPPING DRC PROXY");
    size_t nConfigs = m_properties.configurations.size();
    RCCResult rc;
    for (size_t n = 0; n < nConfigs; ++n) {
      if ((rc = stop_config(n,true)))
        return rc; 
    }
    return RCC_OK;
  }
  RCCResult release_config(unsigned config, bool /*atRelease*/) {
    log(8, "RELEASING DRC PROXY CONFIGURATION: %u", config);
    switch (m_properties.status.data[config].state) {
      case STATUS_STATE_INACTIVE:
        return RCC_OK;
      case STATUS_STATE_PREPARED:
      case STATUS_STATE_OPERATING:
	log(8, "RELEASING CONFIG");
	return release_config(config);
      case STATUS_STATE_ERROR: 
      default:
	return setError("Configuration %u is in an error state and cannot be started", config);
    }
  }
  RCCResult release() {
    log(8, "RELEASING DRC PROXY");
    size_t nConfigs = m_properties.configurations.size();
    RCCResult rc;
    for (size_t n = 0; n < nConfigs; ++n) {
      if ((rc = release_config(n, true)))
        return rc;
    }
    return RCC_OK;
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
  // notification that start property has been written, indicating which config to start.
  RCCResult start_written() {
    log(8, "start config %u %u", m_properties.start, isOperating());
    unsigned config = m_properties.start;
    if (config >= OCPI_DRC_MAX_CONFIGURATIONS)
      return setError("Configuration %u started, but is out of range (0 to %u)",
		      config, OCPI_DRC_MAX_CONFIGURATIONS - 1);
    init_status(config);
    if (isOperating()) {
      RCCResult rc = start_config(config, false);
      if (rc == RCC_OK)
	m_properties.status.data[config].state = STATUS_STATE_OPERATING;
      return rc;
    }
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
  // ==========================================================================================
  virtual RCCResult prepare_config(unsigned /*config*/) { return RCC_OK; }; // default if only start is used
  virtual RCCResult start_config(unsigned config) = 0;
  virtual RCCResult stop_config(unsigned config) = 0;
  virtual RCCResult release_config(unsigned /*config*/) = 0;
  virtual RCCResult status_config(unsigned /*config*/) { return RCC_OK; }
};
} // DRC
} // OCPI
