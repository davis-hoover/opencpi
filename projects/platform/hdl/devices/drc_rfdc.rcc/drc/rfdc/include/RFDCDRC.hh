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

#ifndef _RFDC_DRC_HH
#define _RFDC_DRC_HH

#include "DRC.hh"
extern "C" {
#undef __cplusplus
#include "xrfdc.h"
}

// -----------------------------------------------------------------------------
// STEP 1 - DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

class RFDCCSP : public CSPBase {
  protected:
  void define_x_d_rfdc();
  void define_c_rfdc();
  public:
  RFDCCSP();
  void instance_rfdc();
  void define();
};

// -----------------------------------------------------------------------------
// STEP 2 - DEFINE CONFIGURATOR THAT UTILIZES THE CSP
// -----------------------------------------------------------------------------

class RFDCConfigurator : public Configurator<RFDCCSP> {
  public:
  RFDCConfigurator();
  protected:
  void init_rf_port_rx1();
  void init_rf_port_rx2();
  void init_rf_port_tx1();
  void init_rf_port_tx2();
};

// -----------------------------------------------------------------------------
// STEP 3 - DEFINE DRC (get/set APIs)
// -----------------------------------------------------------------------------

template<class cfgrtr_t = RFDCConfigurator>
class RFDCDRC : public DRC<cfgrtr_t> {
  public:
  RFDCDRC();
  bool                get_enabled(            const std::string& rf_port_name);
  RFPort::direction_t get_direction(          const std::string& rf_port_name);
  double              get_tuning_freq_MHz(    const std::string& rf_port_name);
  double              get_bandwidth_3dB_MHz(  const std::string& rf_port_name);
  double              get_sampling_rate_Msps( const std::string& rf_port_name);
  bool                get_samples_are_complex(const std::string& rf_port_name);
  std::string         get_gain_mode(          const std::string& rf_port_name);
  double              get_gain_dB(            const std::string& rf_port_name);
  uint8_t             get_app_port_num(       const std::string& rf_port_name);
  void set_direction(const std::string& rf_port_name, RFPort::direction_t val);
  void set_tuning_freq_MHz(    const std::string& rf_port_name, double val);
  void set_bandwidth_3dB_MHz(  const std::string& rf_port_name, double val);
  void set_sampling_rate_Msps( const std::string& rf_port_name, double val);
  void set_samples_are_complex(const std::string& rf_port_name, bool val);
  void set_gain_mode(          const std::string& rf_port_name, const std::string& val);
  void set_gain_dB(            const std::string& rf_port_name, double val);
  void set_app_port_num(       const std::string& rf_port_name, uint8_t val);
  protected:
  XRFdc m_xrfdc;
  void init();
};

#endif // _RFDC_DRC_HH
