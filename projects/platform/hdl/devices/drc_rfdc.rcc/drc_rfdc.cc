/*
 * THIS FILE WAS ORIGINALLY GENERATED ON Wed Mar 15 22:57:04 2023 EDT
 * BASED ON THE FILE: drc_rfdc.xml
 * YOU *ARE* EXPECTED TO EDIT IT
 *
 * This file contains the implementation skeleton for the drc_rfdc worker in C++
 */

#include "drc_rfdc-worker.hh"

#include <stdexcept>
#include "metal/io.h" // libmetal opencpi system RFDC_*OFFSET definitions
#include "RFDCDRC.hh"

using namespace OCPI::RCC; // for easy access to RCC data types and constants
using namespace Drc_rfdcWorkerTypes;

#include "OcpiDrcProxyApi.hh" // this must be after the "using namespace" of the types namespace

namespace OD = OCPI::DRC;

class Drc_rfdcWorker : public OD::DrcProxyBase {
  struct DoSlave : DeviceCallBack {
    Slaves &m_slaves;
    DoSlave(Slaves &slaves) : m_slaves(slaves) {}
    void access_prop(uint16_t addr, unsigned long pof, uint8_t* buf, size_t sz,
        bool read) {
      if (pof == RFDC_OFFSET) {
        if (read) {
          m_slaves.rfdc.getRawPropertyBytes(addr, buf, sz);
        }
        else {
          m_slaves.rfdc.setRawPropertyBytes(addr, buf, sz);
        }
      }
      else if (pof == RFDC_DAC_CONFIG_0_OFFSET) {
        if (read) {
          m_slaves.rfdc_dac_config_0.getRawPropertyBytes(addr, buf, sz);
        }
        else {
          m_slaves.rfdc_dac_config_0.setRawPropertyBytes(addr, buf, sz);
        }
      }
      else if (pof == RFDC_DAC_CONFIG_1_OFFSET) {
        if (read) {
          m_slaves.rfdc_dac_config_1.getRawPropertyBytes(addr, buf, sz);
        }
        else {
          m_slaves.rfdc_dac_config_1.setRawPropertyBytes(addr, buf, sz);
        }
      }
      else if (pof == RFDC_DAC_CONFIG_2_OFFSET) {
        if (read) {
          m_slaves.rfdc_dac_config_2.getRawPropertyBytes(addr, buf, sz);
        }
        else {
          m_slaves.rfdc_dac_config_2.setRawPropertyBytes(addr, buf, sz);
        }
      }
      else if (pof == RFDC_DAC_CONFIG_3_OFFSET) {
        if (read) {
          m_slaves.rfdc_dac_config_3.getRawPropertyBytes(addr, buf, sz);
        }
        else {
          m_slaves.rfdc_dac_config_3.setRawPropertyBytes(addr, buf, sz);
        }
      }
      else if (pof == RFDC_ADC_CONFIG_0_OFFSET) {
        if (read) {
          m_slaves.rfdc_adc_config_0.getRawPropertyBytes(addr, buf, sz);
        }
        else {
          m_slaves.rfdc_adc_config_0.setRawPropertyBytes(addr, buf, sz);
        }
      }
      else if (pof == RFDC_ADC_CONFIG_1_OFFSET) {
        if (read) {
          m_slaves.rfdc_adc_config_1.getRawPropertyBytes(addr, buf, sz);
        }
        else {
          m_slaves.rfdc_adc_config_1.setRawPropertyBytes(addr, buf, sz);
        }
      }
      else if (pof == RFDC_ADC_CONFIG_2_OFFSET) {
        if (read) {
          m_slaves.rfdc_adc_config_2.getRawPropertyBytes(addr, buf, sz);
        }
        else {
          m_slaves.rfdc_adc_config_2.setRawPropertyBytes(addr, buf, sz);
        }
      }
      else if (pof == RFDC_ADC_CONFIG_3_OFFSET) {
        if (read) {
          m_slaves.rfdc_adc_config_3.getRawPropertyBytes(addr, buf, sz);
        }
        else {
          m_slaves.rfdc_adc_config_3.setRawPropertyBytes(addr, buf, sz);
        }
      }
    }
    // of  - address byte "of"fset relative to the slave worker property space
    // pof - address byte "p"roperty "off"set, or the offset of the worker's
    //       first property within the Xilinx RFDC IP address space (this is
    //       simply used to indicate which worker is to be accessed, based on
    //       the already defined segments from io.h)
    uint8_t get_uchar_prop(unsigned long of, unsigned long pof) {
      uint8_t ret;
      access_prop((uint16_t)of, pof, (uint8_t*)(&ret), sizeof(uint8_t), true);
      return ret;
    }
    uint16_t get_ushort_prop(unsigned long of, unsigned long pof) {
      uint16_t ret;
      access_prop((uint16_t)of, pof, (uint8_t*)(&ret), sizeof(uint16_t), true);
      return ret;
    }
    uint32_t get_ulong_prop(unsigned long of, unsigned long pof) {
      uint32_t ret;
      access_prop((uint16_t)of, pof, (uint8_t*)(&ret), sizeof(uint32_t), true);
      return ret;
    }
    uint64_t get_ulonglong_prop(unsigned long of, unsigned long pof) {
      uint64_t ret;
      access_prop((uint16_t)of, pof, (uint8_t*)(&ret), sizeof(uint64_t), true);
      return ret;
    }
    void set_uchar_prop(unsigned long of, unsigned long pof, uint8_t val) {
      access_prop((uint16_t)of, pof, (uint8_t*)(&val), sizeof(uint8_t), false);
    }
    void set_ushort_prop(unsigned long of, unsigned long pof, uint16_t val) {
      access_prop((uint16_t)of, pof, (uint8_t*)(&val), sizeof(uint16_t), false);
    }
    void set_ulong_prop(unsigned long of, unsigned long pof, uint32_t val) {
      access_prop((uint16_t)of, pof, (uint8_t*)(&val), sizeof(uint32_t), false);
    }
    void set_ulonglong_prop(unsigned long of, unsigned long pof, uint64_t val) {
      access_prop((uint16_t)of, pof, (uint8_t*)(&val), sizeof(uint64_t), false);
    }
  } m_doSlave;
  RFDCDRC<RFDCConfigurator> m_ctrlr;
public:
  Drc_rfdcWorker() : m_doSlave(slaves), m_ctrlr(m_doSlave) {
  }
  RCCResult prepare_config(unsigned config) {
    typedef RFPort::direction_t direction_t;
    auto &conf = m_properties.configurations.data[config];
    ConfigLockRequest req;
    auto nChannels = conf.channels.length;
    for (unsigned n = 0; n < nChannels; ++n) {
      auto &channel = conf.channels.data[n];
      direction_t direction = channel.rx ? direction_t::rx : direction_t::tx;
      RFPortConfigLockRequest rf_port(
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
        count = std::min(count, (size_t)DRC_RFDC_MAX_STRING_LENGTH_P);
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
  /// @todo / FIXME consolidate into OcpiDrcProxyApi.hh
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
  // notification that status property will be read
  RCCResult status_read() {
    size_t nConfigs = m_properties.configurations.size();
    m_properties.status.resize(nConfigs);
    for (size_t n = 0; n < nConfigs; ++n) {
      auto &conf = m_properties.configurations.data[n];
      auto &stat = m_properties.status.data[n];
      /// @todo / FIXME add below line in OcpiDrcProxyApi.hh
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

DRC_RFDC_START_INFO
// Insert any static info assignments here (memSize, memSizes, portInfo)
// e.g.: info.memSize = sizeof(MyMemoryStruct);
// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case
DRC_RFDC_END_INFO
