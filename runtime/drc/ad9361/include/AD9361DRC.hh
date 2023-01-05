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

#ifndef _AD9361_DRC_HH
#define _AD9361_DRC_HH

// define any of the following for debugging purposes
//#define DISABLE_AD9361 // remove hardware actuation, useful for testing

#include "DRC.hh"
#include "LogForwarder.hh"
#ifndef DISABLE_AD9361
#include "RCC_Worker.h" // OCPI::RCC::RCCUserSlave
#endif

#ifndef DISABLE_AD9361
extern "C" {
#include "config.h"
#include "ad9361_api.h"
#include "ad9361.h"
#include "parameters.h"
int32_t spi_init(OCPI::RCC::RCCUserSlave* _slave);
}
#endif

namespace DRC {

// -----------------------------------------------------------------------------
// STEP 1 - IF IS_LOCKING SUPPORTED,
//          DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class AD9361CSP : public CSPBase {
  protected:
  typedef CSPSolver::Constr::Cond Cond;
  typedef CSPSolver::Constr::Func Func;
  /* @brief for the AD9361,
   *        define variables (X) and their domains (D) for <X,D,C> which
   *        comprises its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void define_x_d_ad9361();
  /* @brief for the AD9361,
   *        define constraints (C) for <X,D,C> which
   *        comprise its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void define_c_ad9361();
  public:
  AD9361CSP();
  /* @brief instance AD9361
   *        by defining its Constraint Satisfaction Problem (CSP) as <X,D,C>
   ****************************************************************************/
  void instance_ad9361();
  /// @brief define Constraint Satisfaction Problem (CSP)
  void define();
}; // class AD9361CSP
#endif

// -----------------------------------------------------------------------------
// STEP 2 - IF IS_LOCKING SUPPORTED, DEFINE CONFIGURATOR THAT UTILIZES THE CSP
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class AD9361Configurator : public Configurator<AD9361CSP> {
  public:
  AD9361Configurator();
};
#endif

// -----------------------------------------------------------------------------
// STEP 3 - DEFINE DRC (get/set APIs)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
#define AD9361_CONFIGURATOR AD9361Configurator
#else
#define AD9361_CONFIGURATOR Configurator<CSPBase>
#endif

template<class log_t,class slave_cfg_t,class slave_data_sub_t,
    class cfgrtr_t = AD9361_CONFIGURATOR>
class AD9361DRC : public DRC<log_t,cfgrtr_t> {
  protected:
#ifndef DISABLE_AD9361
  enum class rx_frame_usage_t {enable, toggle};
  enum class data_bus_index_direction_t {normal, reverse};
  enum class data_rate_config_t {sdr, ddr};
  double                 m_fref_hz;
  /// @brief No-OS struct used to initialize AD9361
  AD9361_InitParam       m_init_param;
  /// @brief No-OS struct pointer
  struct ad9361_rf_phy*  _ad9361_phy;
  struct ad9361_rf_phy*& m_ad9361_rf_phy;
  int32_t                m_ad9361_init_ret;
  bool                   m_ad9361_init_called;
#endif
  /// @brief name of the data stream that corresponds to AD9361 RX1 channel
  const char*            m_ds_rx1;
  const char*            m_ds_rx2;
  const char*            m_ds_tx1;
  const char*            m_ds_tx2;
  /// @brief ad9361_config.hdl slave accessor
  slave_cfg_t&           m_cfg_slave;
  /// @brief ad9361_data_sub.hdl slave accessor
  slave_data_sub_t&      m_data_sub_slave;
  template<typename T> T convert_milli_db_to_db(T val_milli_db) const;
  template<typename T> T convert_db_to_milli_db(T val_milli_db) const;
#ifndef DISABLE_AD9361
  void init_init_param();
  void init();
  bool any_configurator_configs_locked_which_prevent_ad9361_init() const;
  void throw_if_ad9361_init_failed(const char* operation) const;
  void apply_config_to_init_param();
  void enforce_ensm_config();
  void set_ad9361_fpga_channel_config();
#endif
  void init_if_required();
  public:
  AD9361DRC<log_t,slave_cfg_t,slave_data_sub_t,cfgrtr_t>(
      slave_cfg_t& slave_cfg,slave_data_sub_t& slave_data_sub,double fref_hz,
      const char* rx1 = "rx1",const char* rx2 = "rx2",
      const char* tx1 = "tx1",const char* tx2 = "tx2",
      const char* descriptor = "AD9361");
  bool get_rx_and_throw_if_invalid_ds(data_stream_id_t data_stream_id) const;
  void set_rx_rf_port_input(uint32_t mode);
  void set_tx_rf_port_output(uint32_t mode);
  void throw_if_no_os_api_call_returns_non_zero(int32_t res);
  bool                    get_data_stream_is_enabled(data_stream_id_t id);
  data_stream_direction_t get_data_stream_direction( data_stream_id_t id);
  config_value_t          get_tuning_freq_MHz(       data_stream_id_t id);
  config_value_t          get_bandwidth_3dB_MHz(     data_stream_id_t id);
  config_value_t          get_sampling_rate_Msps(    data_stream_id_t id);
  bool                    get_samples_are_complex(   data_stream_id_t id);
  gain_mode_value_t       get_gain_mode(             data_stream_id_t id);
  config_value_t          get_gain_dB(               data_stream_id_t id);
  void set_data_stream_direction(data_stream_id_t id,data_stream_direction_t v);
  void set_tuning_freq_MHz(      data_stream_id_t id,config_value_t    val);
  void set_bandwidth_3dB_MHz(    data_stream_id_t id,config_value_t    val);
  void set_sampling_rate_Msps(   data_stream_id_t id,config_value_t    val);
  void set_samples_are_complex(  data_stream_id_t id,bool              val);
  void set_gain_mode(            data_stream_id_t id,gain_mode_value_t val);
  void set_gain_dB(              data_stream_id_t id,config_value_t    val);
  bool shutdown();
  ~AD9361DRC();
}; // class AD9361DRC

} // namespace DRC

#include "AD9361DRC.cc"

#endif // _AD9361_DRC_HH
