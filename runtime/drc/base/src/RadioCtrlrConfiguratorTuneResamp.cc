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

#include <limits> // std::numeric_limits
#include "RadioCtrlrConfiguratorTuneResamp.hh"

namespace OCPI {

namespace DRC {

ConfiguratorTuneResamp::
ConfiguratorTuneResamp(double maxRxSampleFreqMhz, double maxTxSampleFreqMhz,
		       const ConfigValueRanges *CIC_dec_abs_ranges,
		       const ConfigValueRanges *CIC_int_abs_ranges) {

  ConfigValueRanges abs_ranges;
  config_value_t max = std::numeric_limits<config_value_t>::max();
  abs_ranges.add_valid_range(-max, max);
  if (!CIC_dec_abs_ranges)
    CIC_dec_abs_ranges = &abs_ranges;
  if (!CIC_int_abs_ranges)
    CIC_int_abs_ranges = &abs_ranges;

  bool rx;
  data_stream_ID_t *id;
  for (unsigned ii = 0; getNextStream(ii, false, rx, id); ++ii)
    if (rx) {
      add_stream_config_RX_tuning_freq_complex_mixer(*id, maxRxSampleFreqMhz);
      add_stream_config_CIC_dec_decimation_factor(   *id, *CIC_dec_abs_ranges);
    } else {
      add_stream_config_TX_tuning_freq_complex_mixer(*id, maxTxSampleFreqMhz);
      add_stream_config_CIC_int_interpolation_factor(*id, *CIC_int_abs_ranges);
    }
}

void ConfiguratorTuneResamp::
add_stream_config_RX_tuning_freq_complex_mixer(const data_stream_ID_t &data_stream,
					       double maxRxSampFreqMhz) {

  ConfigValueRanges abs_ranges;
  {
    config_value_t min_tuning_freq_complex_mixer_MHz;
    config_value_t max_tuning_freq_complex_mixer_MHz;
    {
      typedef int16_t complex_mixer_phs_inc_t;
      double min_complex_mixer_NCO_freq_MHz;
      {
        double& x = min_complex_mixer_NCO_freq_MHz;
        complex_mixer_phs_inc_t phs_inc_min;
        phs_inc_min = std::numeric_limits<complex_mixer_phs_inc_t>::min();
        // see Complex_mixer.pdf formula (4)
        x = maxRxSampFreqMhz*phs_inc_min/65536.;
      }
      double max_complex_mixer_NCO_freq_MHz;
      {
        double& x = max_complex_mixer_NCO_freq_MHz;
        complex_mixer_phs_inc_t phs_inc_max;
        phs_inc_max = std::numeric_limits<complex_mixer_phs_inc_t>::max();
        // see Complex_mixer.pdf formula (4)
        x = maxRxSampFreqMhz*phs_inc_max/65536.;
      }
      // e.g. if tuning freq is 10 MHz, you always mix by the *negative* of
      // 10 MHz to achieve the mix *down* behavior, for complex mixer
      // you mix by the NCO freq
      min_tuning_freq_complex_mixer_MHz = -max_complex_mixer_NCO_freq_MHz;
      max_tuning_freq_complex_mixer_MHz = -min_complex_mixer_NCO_freq_MHz;
    }
    const config_value_t& min = min_tuning_freq_complex_mixer_MHz;
    const config_value_t& max = max_tuning_freq_complex_mixer_MHz;
    abs_ranges.add_valid_range(min, max);
  }
  LockRConstrConfig cfg(abs_ranges);
  typedef std::map<config_key_t, LockRConstrConfig> stream_cfgs_t;
  stream_cfgs_t& cfgs = m_data_streams.at(data_stream).m_configs;
  cfgs.insert(std::make_pair("tuning_freq_complex_mixer_MHz", cfg));
}

void ConfiguratorTuneResamp::
add_stream_config_TX_tuning_freq_complex_mixer(const data_stream_ID_t &data_stream,
					       double maxTxSampFreqMhz) {

  ConfigValueRanges abs_ranges;
  {
    config_value_t min_tuning_freq_complex_mixer_MHz;
    config_value_t max_tuning_freq_complex_mixer_MHz;
    {
      typedef int16_t complex_mixer_phs_inc_t;
      double min_complex_mixer_NCO_freq_MHz;
      {
        double& x = min_complex_mixer_NCO_freq_MHz;
        complex_mixer_phs_inc_t phs_inc_min;
        phs_inc_min = std::numeric_limits<complex_mixer_phs_inc_t>::min();
        // see Complex_mixer.pdf formula (4)
        x = maxTxSampFreqMhz*phs_inc_min/65536.;
      }
      double max_complex_mixer_NCO_freq_MHz;
      {
        double& x = max_complex_mixer_NCO_freq_MHz;
        complex_mixer_phs_inc_t phs_inc_max;
        phs_inc_max = std::numeric_limits<complex_mixer_phs_inc_t>::max();
        // see Complex_mixer.pdf formula (4)
        x = maxTxSampFreqMhz*phs_inc_max/65536.;
      }
      // e.g. if tuning freq is 10 MHz, you always mix by the *negative* of
      // 10 MHz to achieve the mix *down* behavior, for complex mixer
      // you mix by the NCO freq
      min_tuning_freq_complex_mixer_MHz = -max_complex_mixer_NCO_freq_MHz;
      max_tuning_freq_complex_mixer_MHz = -min_complex_mixer_NCO_freq_MHz;
    }
    const config_value_t& min = min_tuning_freq_complex_mixer_MHz;
    const config_value_t& max = max_tuning_freq_complex_mixer_MHz;
    abs_ranges.add_valid_range(min, max);
  }
  LockRConstrConfig cfg(abs_ranges);
  typedef std::map<config_key_t, LockRConstrConfig> stream_cfgs_t;
  stream_cfgs_t& cfgs = m_data_streams.at(data_stream).m_configs;
  cfgs.insert(std::make_pair("tuning_freq_complex_mixer_MHz", cfg));
}

void ConfiguratorTuneResamp::add_stream_config_CIC_dec_decimation_factor(
    const data_stream_ID_t &data_stream, const ConfigValueRanges CIC_dec_abs_ranges) {

  LockRConstrConfig cfg(CIC_dec_abs_ranges);

  typedef std::map<config_key_t, LockRConstrConfig> stream_cfgs_t;
  stream_cfgs_t& cfgs = m_data_streams.at(data_stream).m_configs;
  cfgs.insert(std::make_pair("CIC_dec_decimation_factor", cfg));
}

void ConfiguratorTuneResamp::add_stream_config_CIC_int_interpolation_factor(
    const data_stream_ID_t &data_stream, const ConfigValueRanges CIC_int_abs_ranges) {

  LockRConstrConfig cfg(CIC_int_abs_ranges);

  typedef std::map<config_key_t, LockRConstrConfig> stream_cfgs_t;
  stream_cfgs_t& cfgs = m_data_streams.at(data_stream).m_configs;
  cfgs.insert(std::make_pair("CIC_int_interpolation_factor", cfg));
}

void ConfiguratorTuneResamp::constrain_FE_samp_rate_equals_func_of_DS_complex_mixer_freq(
    const data_stream_ID_t &data_stream, const config_key_t samp_rate) {

  constrain_FE_samp_rate_to_func_of_DS_complex_mixer_freq(data_stream,samp_rate); // (1/2)
  constrain_DS_complex_mixer_freq_to_func_of_FE_samp_rate(data_stream,samp_rate); // (2/2)
}

void ConfiguratorTuneResamp::constrain_FE_samp_rate_to_func_of_DS_complex_mixer_freq(
    const data_stream_ID_t &data_stream, const config_key_t samp_rate) {

  LockRConstrConfig& cfg_X = get_config(samp_rate);

  const LockRConstrConfig& cfg_Y = get_config(data_stream, "tuning_freq_complex_mixer_MHz");

  // newly constrained ValidRanges that will be applied to X
  ConfigValueRanges new_constrained_ranges_X;

  ConfigValueRanges possible_ranges_Y = cfg_Y.get_ranges_possible();

  auto it_Y = possible_ranges_Y.m_ranges.begin();
  for(; it_Y != possible_ranges_Y.m_ranges.end(); it_Y++) {

    typedef int16_t phs_inc_t;
    double min_samp_rate;

    // tuning freq is negative of complex mixer NCO freq,
    // e.g. if tuning freq is 10 MHz, you always mix by the *negative* of
    // 10 MHz to achieve the mix *down* behavior, for complex mixer
    // you mix by the NCO freq
    double min_complex_mixer_NCO_freq_MHz = -it_Y->get_max();
    double max_complex_mixer_NCO_freq_MHz = -it_Y->get_min();

    if(min_complex_mixer_NCO_freq_MHz >= 0.) {
      double min_NCO_freq_magnitude = min_complex_mixer_NCO_freq_MHz;
      phs_inc_t phs_inc_upper_limit = std::numeric_limits<phs_inc_t>::max();
      // nco_output_freq = sample_freq*phs_inc/(2^phs_acc_width)
      min_samp_rate = min_NCO_freq_magnitude/(phs_inc_upper_limit/65536.);
    }
    else { // (min_complex_mixer_NCO_freq_MHz < 0.)
      double min_NCO_freq_magnitude;
      if(max_complex_mixer_NCO_freq_MHz >= 0.) {
        min_NCO_freq_magnitude = 0.;
      }
      else {
        min_NCO_freq_magnitude = -max_complex_mixer_NCO_freq_MHz;
      }
      phs_inc_t phs_inc_lower_limit = std::numeric_limits<phs_inc_t>::min();
      // nco_output_freq = sample_freq*phs_inc/(2^phs_acc_width)
      min_samp_rate = min_NCO_freq_magnitude/(-phs_inc_lower_limit/65536.);
    }
    config_value_t min = min_samp_rate;
    config_value_t max = std::numeric_limits<config_value_t>::max();

    new_constrained_ranges_X.add_valid_range(min, max);
  }

  if(not cfg_X.is_locked()) {
    cfg_X.overlap_constrained(new_constrained_ranges_X);
  }
}

void ConfiguratorTuneResamp::constrain_DS_complex_mixer_freq_to_func_of_FE_samp_rate(
    const data_stream_ID_t &data_stream, const config_key_t samp_rate) {

  LockRConstrConfig& cfg_X = get_config(data_stream, "tuning_freq_complex_mixer_MHz");

  const LockRConstrConfig& cfg_Y = get_config(samp_rate);

  // newly constrained ValidRanges that will be applied to X
  ConfigValueRanges new_constrained_ranges_X;

  ConfigValueRanges possible_ranges_Y = cfg_Y.get_ranges_possible();

  auto it_Y = possible_ranges_Y.m_ranges.begin();
  for(; it_Y != possible_ranges_Y.m_ranges.end(); it_Y++) {

    double min_tuning_freq_complex_mixer_MHz;
    double max_tuning_freq_complex_mixer_MHz;
    {
      // assuming Y (sampling rate) is positive
      double min_complex_mixer_NCO_freq_MHz = it_Y->get_max()*-32768./65536.;
      double max_complex_mixer_NCO_freq_MHz = it_Y->get_max()*32767./65536.;
      // tuning freq is negative of complex mixer NCO freq,
      // e.g. if tuning freq is 10 MHz, you always mix by the *negative* of
      // 10 MHz to achieve the mix *down* behavior, for complex mixer
      // you mix by the NCO freq
      min_tuning_freq_complex_mixer_MHz = -max_complex_mixer_NCO_freq_MHz;
      max_tuning_freq_complex_mixer_MHz = -min_complex_mixer_NCO_freq_MHz;
    }
    const config_value_t& min = min_tuning_freq_complex_mixer_MHz;
    const config_value_t& max = max_tuning_freq_complex_mixer_MHz;

    new_constrained_ranges_X.add_valid_range(min, max);
  }

  if(not cfg_X.is_locked()) {
    cfg_X.overlap_constrained(new_constrained_ranges_X);
  }
}


void ConfiguratorTuneResamp::constrain_DS_bandwidth_equals_FE_bandwidth_divided_by_CIC_dec(
    const data_stream_ID_t &data_stream,
    const config_key_t    frontend_bandwidth) {

  LockRConstrConfig& cfg_X = get_config(data_stream, config_key_bandwidth_3dB_MHz);
  LockRConstrConfig& cfg_A = get_config(frontend_bandwidth);
  LockRConstrConfig& cfg_B = get_config(data_stream, "CIC_dec_decimation_factor");

  constrain_all_XAB_such_that_X_equals_A_divided_by_B(cfg_X, cfg_A, cfg_B);
}

void ConfiguratorTuneResamp::constrain_DS_bandwidth_equals_FE_bandwidth_divided_by_CIC_int(
    const data_stream_ID_t &data_stream,
    const config_key_t    frontend_bandwidth) {

  LockRConstrConfig& cfg_X = get_config(data_stream, config_key_bandwidth_3dB_MHz);
  LockRConstrConfig& cfg_A = get_config(frontend_bandwidth);
  LockRConstrConfig& cfg_B = get_config(data_stream, "CIC_int_interpolation_factor");

  constrain_all_XAB_such_that_X_equals_A_divided_by_B(cfg_X, cfg_A, cfg_B);
}

void ConfiguratorTuneResamp::constrain_sampling_rate_equals_FE_samp_rate_divided_by_CIC_dec(
    const data_stream_ID_t &data_stream,
    const config_key_t    frontend_samp_rate) {

  LockRConstrConfig& cfg_X = get_config(data_stream, config_key_sampling_rate_Msps);
  LockRConstrConfig& cfg_A = get_config(frontend_samp_rate);
  LockRConstrConfig& cfg_B = get_config(data_stream, "CIC_dec_decimation_factor");

  constrain_all_XAB_such_that_X_equals_A_divided_by_B(cfg_X, cfg_A, cfg_B);
}

void ConfiguratorTuneResamp::constrain_sampling_rate_equals_FE_samp_rate_divided_by_CIC_int(
    const data_stream_ID_t &data_stream,
    const config_key_t    frontend_samp_rate) {

  LockRConstrConfig& cfg_X = get_config(data_stream, config_key_sampling_rate_Msps);
  LockRConstrConfig& cfg_A = get_config(frontend_samp_rate);
  LockRConstrConfig& cfg_B = get_config(data_stream, "CIC_int_interpolation_factor");

  constrain_all_XAB_such_that_X_equals_A_divided_by_B(cfg_X, cfg_A, cfg_B);
}

void ConfiguratorTuneResamp::impose_constraints_single_pass() {

  bool rx;
  data_stream_ID_t *id;
  for (unsigned ii = 0; getNextStream(ii, true, rx, id); ++ii)
    if (rx) {
      constrain_DS_bandwidth_equals_FE_bandwidth_divided_by_CIC_dec(*id, "rx_rf_bandwidth");
      constrain_sampling_rate_equals_FE_samp_rate_divided_by_CIC_dec(*id, "RX_SAMPL_FREQ_MHz");
      constrain_FE_samp_rate_equals_func_of_DS_complex_mixer_freq(*id, "RX_SAMPL_FREQ_MHz");
    } else {
      constrain_DS_bandwidth_equals_FE_bandwidth_divided_by_CIC_int(*id, "tx_rf_bandwidth");
      constrain_sampling_rate_equals_FE_samp_rate_divided_by_CIC_int(*id, "TX_SAMPL_FREQ_MHz");
      constrain_FE_samp_rate_equals_func_of_DS_complex_mixer_freq(*id, "TX_SAMPL_FREQ_MHz");
    }
}

} // namespace DRC

} // namespace OCPI
