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

#ifndef _FMCOMMS2_3_DRC_HH
#define _FMCOMMS2_3_DRC_HH

#include "AD9361DRC.hh"

namespace DRC {

// -----------------------------------------------------------------------------
// STEP 1 - IF IS_LOCKING SUPPORTED,
//          DEFINE Constraint Satisfaction Problem (CSP)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class FMCOMMS2_3CSP : public AD9361CSP {
  protected:
  typedef CSPSolver::Constr::Cond Cond;
  typedef CSPSolver::Constr::Func Func;
  /* @brief for the FMCOMMS2_3,
   *        define variables (X) and their domains (D) for <X,D,C> which
   *        comprises its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void define_x_d_fmcomms2_3();
  /* @brief for the AD9361,
   *        define constraints (C) for <X,D,C> which
   *        comprise its Constraint Satisfaction Problem (CSP)
   ****************************************************************************/
  void define_c_fmcomms2_3();
  public:
  /* @brief instance FMCOMMS2/3
   *        by defining its Constraint Satisfaction Problem (CSP) as <X,D,C>
   ****************************************************************************/
  FMCOMMS2_3CSP();
  void connect_fmcomms2_3_to_ad9361();
  /* @brief instance FMCOMMS2/3
   *        by defining its Constraint Satisfaction Problem (CSP) as <X,D,C>
   ****************************************************************************/
  void instance_fmcomms2_3();
  /// @brief define Constraint Satisfaction Problem (CSP)
  void define();
}; // class FMCOMMS2_3CSP
#endif

// -----------------------------------------------------------------------------
// STEP 2 - IF IS_LOCKING SUPPORTED, DEFINE CONFIGURATOR THAT UTILIZES THE CSP
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
class FMCOMMS2_3Configurator : public Configurator<FMCOMMS2_3CSP> {
  public:
  ///@TODO / FIXME - remove default value of fmcomms_num 3
  FMCOMMS2_3Configurator(int32_t fmcomms_num = 3);
};
#endif

// -----------------------------------------------------------------------------
// STEP 3 - DEFINE DRC (get/set APIs)
// -----------------------------------------------------------------------------

#ifdef IS_LOCKING
#define FMCOMMS2_3_CONFIGURATOR FMCOMMS2_3Configurator
#else
#define FMCOMMS2_3_CONFIGURATOR Configurator<CSPBase>
#endif

template<class log_t,class s_cfg_t,class s_ds_t,
    class cfgrtr_t = FMCOMMS2_3_CONFIGURATOR>
class FMCOMMS2_3DRC : public AD9361DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t> {
  protected:
  /// @brief name of the data stream that corresponds to FMCOMMS2/3 RX1A channel
  const char* m_ds_rx1a;
  const char* m_ds_rx2a;
  const char* m_ds_tx1a;
  const char* m_ds_tx2a;
  public:
  FMCOMMS2_3DRC<log_t,s_cfg_t,s_ds_t,cfgrtr_t>(s_cfg_t& slave_cfg,
      s_ds_t& slave_data_sub,double fref_hz,int32_t fmcomms_num,
      const char* rx1a = "rx1a",const char* rx2a = "rx2a",
      const char* tx1a = "tx1a",const char* tx2a = "tx2a",
      const char* descriptor = "FMCOMMS2_3");
  /* @brief this is what maps, for the DRC, the AD9361 channels to
   *        the FMCOMMS2/3 channels
   ****************************************************************************/
  const char*             get_ad9361_ds_id(          data_stream_id_t id) const;
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
}; // class FMCOMMS2_3DRC

} // namespace DRC

#include "FMCOMMS2_3DRC.cc"

#endif // _FMCOMMS2_3_DRC_HH
