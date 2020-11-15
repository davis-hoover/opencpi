
// This file is expected to be included after the line in the proxy code that includes
// the proxy worker's type namespace, e.g.:
// using namespace Drc_plutosdrWorkerTypes;

// The helper class for DRC proxy workers
namespace OCPI {
namespace DRC {
class DrcProxyBase : public WorkerBase {
protected:
  std::vector<bool> m_started; // record what should be started when the proxy is started.

  DrcProxyBase() : m_started(DRC_PLUTOSDR_MAX_CONFIGURATIONS_P) {
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
      // fall into
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
    unsigned config = m_properties.start;
    if (config >= DRC_PLUTOSDR_MAX_CONFIGURATIONS_P)
      return setError("Configuration %u started, but is out of range (0 to %u)",
		      config, DRC_PLUTOSDR_MAX_CONFIGURATIONS_P - 1);
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
    if (config >= DRC_PLUTOSDR_MAX_CONFIGURATIONS_P)
      return setError("Configuration %u started, but is out of range (0 to %u)",
		      config, DRC_PLUTOSDR_MAX_CONFIGURATIONS_P - 1);
    init_status(config);
    if (isOperating())
      return start_config(config, false);
    // Deferred start
    m_started[m_properties.start] = true;
    return RCC_OK;
  }
  // notification that stop property has been written
  RCCResult stop_written() {
    log(8, "stop config %u", m_properties.stop);
    return RCC_OK;
  }
  // notification that release property has been written
  RCCResult release_written() {
    log(8, "release config %u", m_properties.release);
    return RCC_OK;
  }
  // notification that status property will be read
  RCCResult status_read() {
    size_t nConfigs = m_properties.configurations.size();
    m_properties.status.resize(nConfigs);
    for (size_t n = 0; n < nConfigs; ++n) {
      for (size_t nch = 0; nch < m_properties.configurations.data[n].channels.size(); ++nch) {
	printf("STATUS READ config %zu, channel %zu\n", n, nch);
      }
    }
    return RCC_OK;
  }
  // ==========================================================================================
  // Required methods supplied by the actual proxy code
  virtual RCCResult prepare_config(unsigned config) = 0;
  virtual RCCResult start_config(unsigned config) = 0;
};
} // DRC
} // OCPI
