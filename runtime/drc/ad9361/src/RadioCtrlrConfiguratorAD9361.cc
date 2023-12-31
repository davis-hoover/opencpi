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

#include "RadioCtrlrConfigurator.hh"
#include "UtilValidRanges.hh"
#include "calc_ad9361_bb_rx_filters_digital.h" // AD9361_Rx_FIR_decimation_factor_t
#include "calc_ad9361_bb_tx_filters_digital.h" // AD9361_Tx_FIR_decimation_factor_t
#include "calc_ad9361_bb_rx_adc.h" // calc_min_AD9361_RX_SAMPL_FREQ_Hz(),
                                   // calc_max_AD9361_RX_SAMPL_FREQ_Hz()
#include "calc_ad9361_bb_tx_dac.h" // calc_min_AD9361_TX_SAMPL_FREQ_Hz(),
                                   // calc_max_AD9361_TX_SAMPL_FREQ_Hz()
#include "RadioCtrlrConfiguratorAD9361.hh"

namespace OCPI {

namespace DRC {

ConfiguratorAD9361::ConfiguratorAD9361(
    const char* data_stream_RX1,
    const char* data_stream_RX2,
    const char* data_stream_TX1,
    const char* data_stream_TX2) :
//-----------------------------------------------------------------------
// data stream 0                 -maps-to-> AD9361 RX1 physical pin port
//-----------------------------------------------------------------------
// data stream 0/1 tuning freq   -maps-to-> AD9361 Rx RFPLL LO freq
// data stream 0/1 bandwidth 3dB -maps-to-> AD9361 no-OS rx_rf_bandwidth
// data stream 0/1 sampling rate -maps-to-> AD9361 RX_SAMPL_FREQ
// data stream 0/1 gain mode     -maps-to-> (auto: AD9361 fastattack
//                                           slowattack/hybrid AGC,
//                                           manual: AD9361 MGC)
// data stream 0/1 gain          -maps-to-> AD9361 no-OS rx_rf_gain
// data stream 2/3 tuning freq   -maps-to-> AD9361 Tx RFPLL LO freq
// data stream 2/3 bandwidth 3dB -maps-to-> AD9361 no-OS rx_rf_bandwidth
// data stream 2/3 sampling rate -maps-to-> AD9361 TX_SAMPL_FREQ
// data stream 2/3 gain mode     is always manual (AD9361 TX has no AGC)
// data stream 2/3 gain          -maps-to-> negative of AD9361 no-OS
//                                          tx_attenuation
/// @todo / FIXME - move the constraint imposition functionality herein to impose_constrains() for clarity
  m_data_stream_RX1(data_stream_RX1),
  m_data_stream_RX2(data_stream_RX2 ? data_stream_RX2 : ""),
  m_data_stream_TX1(data_stream_TX1 ? data_stream_TX1 : ""),
  m_data_stream_TX2(data_stream_TX2 ? data_stream_TX2 : "") {
  if (data_stream_RX1)
    m_data_streams.insert(std::make_pair(data_stream_RX1, DataStreamAD9361(data_stream_type_t::RX)));
  if (data_stream_RX2)
    m_data_streams.insert(std::make_pair(data_stream_RX2, DataStreamAD9361(data_stream_type_t::RX)));
  if (data_stream_TX1)
    m_data_streams.insert(std::make_pair(data_stream_TX1, DataStreamAD9361(data_stream_type_t::TX)));
  if (data_stream_TX2)
    m_data_streams.insert(std::make_pair(data_stream_TX2, DataStreamAD9361(data_stream_type_t::TX)));

  {
    ConfigValueRanges abs_ranges;
    abs_ranges.add_valid_range(1., 1.);
    abs_ranges.add_valid_range(2., 2.);
    LockRConstrConfig cfg(abs_ranges);
    m_configs.insert(std::make_pair("DAC_Clk_divider", cfg));
  }
  {
    ConfigValueRanges abs_ranges;
    config_value_t min, max;
    /// @todo / FIXME - support REFCLK rates other than 40 MHz
    /// @todo / FIXME - support all Rx FIR decimation factors
    //min =calc_min_AD9361_RX_SAMPL_FREQ_Hz(REFCLK40MHz, RX_FIR_DEC_FACTOR)/1e6;
    max =calc_max_AD9361_RX_SAMPL_FREQ_Hz(REFCLK40MHz, RX_FIR_DEC_FACTOR)/1e6;

    // While calc_min_AD9361_RX_SAMPL_FREQ_Hz() returns the correct theoretical
    // value (which is 2.0833333.... for REFCLK40MHz), the No-OS software
    // implementation, which is known to suffer from sub-optimal rounding, will
    // fail with the error "ad9361_calculate_rf_clock_chain: Failed to find
    // suitable dividers: ADC clock below limit" when calling e.g.
    // ad9361_set_sampling_rx_sampling_freq(phy, 2083333) (note that the No-OS
    // API necessitates rounding to nearest integer, so 2083333.3333... rounds
    // to 2083333). The min value is set here to 2.083334 to get No-OS to operate
    // succesfully. Note that all the aforemention values assume the on-AD9361
    // FIR filter is disabled.
    min = 2.083334;

    abs_ranges.add_valid_range(min, max);
    LockRConstrConfig cfg(abs_ranges);
    m_configs.insert(std::make_pair("RX_SAMPL_FREQ_MHz", cfg));
  }
  {
    ConfigValueRanges abs_ranges;
    config_value_t min, max;
    /// @todo / FIXME - support REFCLK rates other than 40 MHz
    /// @todo / FIXME - support all Tx FIR decimation factors
    min =calc_min_AD9361_TX_SAMPL_FREQ_Hz(REFCLK40MHz, TX_FIR_INT_FACTOR)/1e6;
    max =calc_max_AD9361_TX_SAMPL_FREQ_Hz(REFCLK40MHz, TX_FIR_INT_FACTOR)/1e6;
    abs_ranges.add_valid_range(min, max);
    LockRConstrConfig cfg(abs_ranges);
    m_configs.insert(std::make_pair("TX_SAMPL_FREQ_MHz", cfg));
  }
  {
    ConfigValueRanges abs_ranges;
    abs_ranges.add_valid_range(0.40, 56.);
    LockRConstrConfig cfg(abs_ranges);
    m_configs.insert(std::make_pair("rx_rf_bandwidth", cfg));
  }
  {
    ConfigValueRanges abs_ranges;
    abs_ranges.add_valid_range(1.25, 40.);
    LockRConstrConfig cfg(abs_ranges);
    m_configs.insert(std::make_pair("tx_rf_bandwidth", cfg));
  }
  {
    ConfigValueRanges abs_ranges;
    abs_ranges.add_valid_range(70., 6000.);
    LockRConstrConfig cfg(abs_ranges);
    m_configs.insert(std::make_pair("Rx_RFPLL_LO_freq", cfg));
    m_configs.insert(std::make_pair("Tx_RFPLL_LO_freq", cfg));
  }
}

void ConfiguratorAD9361::constrain_config_by_Rx_RFPLL_LO_freq(
    data_stream_ID_t data_stream) {

  typedef ConfigValueRanges VR;
  VR VR_Y = get_config("Rx_RFPLL_LO_freq").get_ranges_possible();

  VR VR_gain_new;

  // see No-OS ad9361.c ad9361_gt_table_index()
  bool some_range_within_70_to_1300_is_possible;
  {
    ConfigValueRange range_under_test(70., 1300.);

    VR test_range = VR_Y;
    test_range.overlap(range_under_test);
    some_range_within_70_to_1300_is_possible = (test_range.m_ranges.size()>0);
  }
  if(some_range_within_70_to_1300_is_possible) {
    // see No-OS ad9361.c full_gain_table_abs_gain
    VR_gain_new.add_valid_range(1., 73.);
  }
  // see No-OS ad9361.c ad9361_gt_table_index()
  bool some_range_within_1300_4000_is_possible;
  {
    //                                   M   k  _  m  u
    ConfigValueRange range_under_test(1300.000000000001, 4000.);

    VR test_range = VR_Y;
    test_range.overlap(range_under_test);
    some_range_within_1300_4000_is_possible= (test_range.m_ranges.size()>0);
  }
  if(some_range_within_1300_4000_is_possible) {
    // see No-OS ad9361.c full_gain_table_abs_gain
    VR_gain_new.add_valid_range(-3., 71.);
  }
  // see No-OS ad9361.c ad9361_gt_table_index()
  bool some_range_within_4000_6000_is_possible;
  {
    //                                   M   k  _  m  u
    ConfigValueRange range_under_test(4000.000000000001, 6000.);

    VR test_range = VR_Y;
    test_range.overlap(range_under_test);
    some_range_within_4000_6000_is_possible = (test_range.m_ranges.size()>0);
  }
  if(some_range_within_4000_6000_is_possible) {
    // see No-OS ad9361.c full_gain_table_abs_gain
    VR_gain_new.add_valid_range(-10., 62);
  }

  LockRConstrConfig& cfg = get_config(data_stream, config_key_gain_dB);

  if(not cfg.is_locked()) {
    cfg.overlap_constrained(VR_gain_new);
  }
}

void ConfiguratorAD9361::constrain_config_by_neg_89p75_to_0(
    LockRConstrConfig& cfg) {

  if(not cfg.is_locked()) {

    ConfigValueRanges abs_ranges;
    abs_ranges.add_valid_range(-89.75, 0.);

    cfg.overlap_constrained(abs_ranges);
  }
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & gain\_mode_{data\_stream\_0} \in \{0, 1\}
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::constrain_gain_mode_data_stream_0_equals_0_or_1() {

  LockRConstrConfig& cfg = get_config(m_data_stream_RX1, config_key_gain_mode);

  if(not cfg.is_locked()) {

    ConfigValueRanges abs_ranges;
    abs_ranges.add_valid_range(0, 0);
    abs_ranges.add_valid_range(1, 1);

    cfg.overlap_constrained(abs_ranges);
  }

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & gain\_mode_{data\_stream\_1} \in \{0, 1\}
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::constrain_gain_mode_data_stream_1_equals_0_or_1() {

  LockRConstrConfig& cfg = get_config(m_data_stream_RX2, config_key_gain_mode);

  if(not cfg.is_locked()) {

    ConfigValueRanges abs_ranges;
    abs_ranges.add_valid_range(0, 0);
    abs_ranges.add_valid_range(1, 1);

    cfg.overlap_constrained(abs_ranges);
  }

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & gain\_mode_{data\_stream\_2} = 1
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::constrain_gain_mode_data_stream_2_equals_1() {

  LockRConstrConfig& cfg_Y = get_config(m_data_stream_TX1, config_key_gain_mode);

  constrain_Y_equals_constant(cfg_Y, 1);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & gain\_mode_{data\_stream\_3} = 1
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::constrain_gain_mode_data_stream_3_equals_1() {

  LockRConstrConfig& cfg_Y = get_config(m_data_stream_TX2, config_key_gain_mode);

  constrain_Y_equals_constant(cfg_Y, 1);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & tuning\_freq\_MHz_{data\_stream\_0} = Rx\_RFPLL\_LO\_freq
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_tuning_freq_MHz_data_stream_0_equals_Rx_RFPLL_LO_freq() {

  LockRConstrConfig& cfg_X = get_config("Rx_RFPLL_LO_freq");
  LockRConstrConfig& cfg_Y = get_config(m_data_stream_RX1, config_key_tuning_freq_MHz);

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & tuning\_freq\_MHz_{data\_stream\_1} = Rx\_RFPLL\_LO\_freq
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_tuning_freq_MHz_data_stream_1_equals_Rx_RFPLL_LO_freq() {

  LockRConstrConfig& cfg_X = get_config("Rx_RFPLL_LO_freq");
  LockRConstrConfig& cfg_Y = get_config(m_data_stream_RX2, config_key_tuning_freq_MHz);

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & tuning\_freq\_MHz_{data\_stream\_2} = Tx\_RFPLL\_LO\_freq
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_tuning_freq_MHz_data_stream_2_equals_Tx_RFPLL_LO_freq() {

  LockRConstrConfig& cfg_X = get_config("Tx_RFPLL_LO_freq");
  LockRConstrConfig& cfg_Y = get_config(m_data_stream_TX1, config_key_tuning_freq_MHz);

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & tuning\_freq\_MHz_{data\_stream\_3} = Tx\_RFPLL\_LO\_freq
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_tuning_freq_MHz_data_stream_3_equals_Tx_RFPLL_LO_freq() {

  LockRConstrConfig& cfg_X = get_config("Tx_RFPLL_LO_freq");
  LockRConstrConfig& cfg_Y = get_config(m_data_stream_TX2, config_key_tuning_freq_MHz);

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & gain\_dB_{data\_stream\_0} \in \begin{cases} [1,77] if Rx\_RFPLL\_LO\_freq <= 1300, \\
 *                                                      [-3,71] if Rx\_RFPLL\_LO\_freq <= 4000, \\
 *                                                      [-10,62] otherwise 
 *                                                    \end{cases}
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_gain_dB_data_stream_0_equals_func_of_Rx_RFPLL_LO_freq() {

  constrain_config_by_Rx_RFPLL_LO_freq(m_data_stream_RX1);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & gain\_dB_{data\_stream\_1} \in \begin{cases} [1,77] if Rx\_RFPLL\_LO\_freq <= 1300, \\
 *                                                      [-3,71] if Rx\_RFPLL\_LO\_freq <= 4000, \\
 *                                                      [-10,62] otherwise 
 *                                                    \end{cases}
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_gain_dB_data_stream_1_equals_func_of_Rx_RFPLL_LO_freq() {

  constrain_config_by_Rx_RFPLL_LO_freq(m_data_stream_RX2);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & gain\_dB_{data\_stream\_2} \in [-89.75,0]
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_gain_dB_data_stream_2_is_in_range_neg_89p75_to_0() {

  LockRConstrConfig& cfg = get_config(m_data_stream_TX1, config_key_gain_dB);

  constrain_config_by_neg_89p75_to_0(cfg);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & gain\_dB_{data\_stream\_3} \in [-89.75,0]
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_gain_dB_data_stream_3_is_in_range_neg_89p75_to_0() {

  LockRConstrConfig& cfg = get_config(m_data_stream_TX2, config_key_gain_dB);

  constrain_config_by_neg_89p75_to_0(cfg);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & bandwidth\_3dB\_MHz_{data\_stream\_0} = rx\_rf\_bandwidth
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_bandwidth_3dB_MHz_data_stream_0_equals_rx_rf_bandwidth() {

  LockRConstrConfig& cfg_X = get_config(m_data_stream_RX1, config_key_bandwidth_3dB_MHz);
  LockRConstrConfig& cfg_Y = get_config("rx_rf_bandwidth");

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & bandwidth\_3dB\_MHz_{data\_stream\_1} = rx\_rf\_bandwidth
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_bandwidth_3dB_MHz_data_stream_1_equals_rx_rf_bandwidth() {

  LockRConstrConfig& cfg_X = get_config(m_data_stream_RX2, config_key_bandwidth_3dB_MHz);
  LockRConstrConfig& cfg_Y = get_config("rx_rf_bandwidth");

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & bandwidth\_3dB\_MHz_{data\_stream\_2} = tx\_rf\_bandwidth
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_bandwidth_3dB_MHz_data_stream_2_equals_tx_rf_bandwidth() {

  LockRConstrConfig& cfg0 = get_config("tx_rf_bandwidth");
  LockRConstrConfig& cfg1 = get_config(m_data_stream_TX1, config_key_bandwidth_3dB_MHz);

  constrain_all_XY_such_that_X_equals_Y(cfg0, cfg1);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & bandwidth\_3dB\_MHz_{data\_stream\_3} = tx\_rf\_bandwidth
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_bandwidth_3dB_MHz_data_stream_3_equals_tx_rf_bandwidth() {

  LockRConstrConfig& cfg0 = get_config("tx_rf_bandwidth");
  LockRConstrConfig& cfg1 = get_config(m_data_stream_TX2, config_key_bandwidth_3dB_MHz);

  constrain_all_XY_such_that_X_equals_Y(cfg0, cfg1);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & RX\_SAMPL\_FREQ\_MHz=TX\_SAMPL\_FREQ\_MHz \times DAC\_Clk\_divider
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_RX_SAMPL_FREQ_MHz_equals_TX_SAMPL_FREQ_MHz_times_DAC_Clk_divider() {

  LockRConstrConfig& cfg_X = get_config("RX_SAMPL_FREQ_MHz");
  LockRConstrConfig& cfg_A = get_config("TX_SAMPL_FREQ_MHz");
  LockRConstrConfig& cfg_B = get_config("DAC_Clk_divider");

  this->constrain_all_XAB_such_that_X_equals_A_multiplied_by_B(cfg_X, cfg_A, cfg_B);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & sampling\_rate\_Msps_{data\_stream\_0} = RX\_SAMPL\_FREQ\_MHz
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_sampling_rate_Msps_data_stream_0_equals_RX_SAMPL_FREQ() {

  LockRConstrConfig& cfg_X = get_config("RX_SAMPL_FREQ_MHz");
  LockRConstrConfig& cfg_Y = get_config(m_data_stream_RX1, config_key_sampling_rate_Msps);

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & sampling\_rate\_Msps_{data\_stream\_1} = RX\_SAMPL\_FREQ\_MHz
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_sampling_rate_Msps_data_stream_1_equals_RX_SAMPL_FREQ() {

  LockRConstrConfig& cfg_X = get_config("RX_SAMPL_FREQ_MHz");
  LockRConstrConfig& cfg_Y = get_config(m_data_stream_RX2, config_key_sampling_rate_Msps);

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & sampling\_rate\_Msps_{data\_stream\_2} = TX\_SAMPL\_FREQ\_MHz 
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_sampling_rate_Msps_data_stream_2_equals_TX_SAMPL_FREQ() {

  LockRConstrConfig& cfg_X = get_config("TX_SAMPL_FREQ_MHz");
  LockRConstrConfig& cfg_Y = get_config(m_data_stream_TX1, config_key_sampling_rate_Msps);

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & sampling\_rate\_Msps_{data\_stream\_3} = TX\_SAMPL\_FREQ\_MHz 
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_sampling_rate_Msps_data_stream_3_equals_TX_SAMPL_FREQ() {

  LockRConstrConfig& cfg_X = get_config("TX_SAMPL_FREQ_MHz");
  LockRConstrConfig& cfg_Y = get_config(m_data_stream_TX2, config_key_sampling_rate_Msps);

  constrain_all_XY_such_that_X_equals_Y(cfg_X, cfg_Y);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}


/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & samples\_are\_complex_{data\_stream\_0} = 1
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_samples_are_complex_data_stream_0_equals_1() {

  LockRConstrConfig& cfg_Y = get_config(m_data_stream_RX1, config_key_samples_are_complex);
  constrain_Y_equals_constant(cfg_Y, 1);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & samples\_are\_complex_{data\_stream\_1} = 1
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_samples_are_complex_data_stream_1_equals_1() {

  LockRConstrConfig& cfg_Y = get_config(m_data_stream_RX2, config_key_samples_are_complex);
  constrain_Y_equals_constant(cfg_Y, 1);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & samples\_are\_complex_{data\_stream\_2} = 1
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_samples_are_complex_data_stream_2_equals_1() {

  LockRConstrConfig& cfg_Y = get_config(m_data_stream_TX1, config_key_samples_are_complex);
  constrain_Y_equals_constant(cfg_Y, 1);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

/*! @brief This enforces the constraint:
 * @f{eqnarray*}{
 *  s.t. & samples\_are\_complex_{data\_stream\_3} = 1
 * @f}
 ******************************************************************************/
void ConfiguratorAD9361::
constrain_samples_are_complex_data_stream_3_equals_1() {

  LockRConstrConfig& cfg_Y = get_config(m_data_stream_TX2, config_key_samples_are_complex);
  constrain_Y_equals_constant(cfg_Y, 1);

  this->throw_if_any_possible_ranges_are_empty(__func__);
}

void ConfiguratorAD9361::
constrain_tuning_freq_equals_Rx_RFPLL_LO_freq_plus_complex_mixer_NCO_freq(
    const data_stream_ID_t &data_stream) {

  LockRConstrConfig& cfg_X = get_config(data_stream, config_key_tuning_freq_MHz);
  LockRConstrConfig& cfg_A = get_config("Rx_RFPLL_LO_freq");
  LockRConstrConfig& cfg_B = get_config(data_stream, "tuning_freq_complex_mixer_MHz");

  constrain_all_XAB_such_that_X_equals_A_plus_B(cfg_X, cfg_A, cfg_B);
}

void ConfiguratorAD9361::
constrain_tuning_freq_equals_Tx_RFPLL_LO_freq_plus_complex_mixer_NCO_freq(
    const data_stream_ID_t &data_stream) {

  LockRConstrConfig& cfg_X = get_config(data_stream, config_key_tuning_freq_MHz);
  LockRConstrConfig& cfg_A = get_config("Tx_RFPLL_LO_freq");
  LockRConstrConfig& cfg_B = get_config(data_stream, "tuning_freq_complex_mixer_MHz");

  constrain_all_XAB_such_that_X_equals_A_plus_B(cfg_X, cfg_A, cfg_B);
}

/*! @brief The AD9361 configuration space is modelled as a constrained
 *         \f$N\f$-dimensional space \f$S \in R^N\f$ where each
 *         dimension corresponds to a variable which maps to a possible value
 *         for an AD9361 configuration setting, e.g. a sampling rate value. This
 *         is similar to a constrained optimization/linear programming problem.
 *         The AD9361 configuration space is represented as follows.
 *
 * @f{eqnarray*}{
 *  S:=\{
 *  DAC\_Clk\_divider,
 *  RX\_SAMPL\_FREQ\_MHz,
 *  TX\_SAMPL\_FREQ\_MHz, \\
 *  rx\_rf\_bandwidth,
 *  tx\_rf\_bandwidth, \\
 *  Rx\_RFPLL\_LO\_freq,
 *  Tx\_RFPLL\_LO\_freq, \\
 *  tuning\_freq\_MHz_{data\_stream\_0},
 *  tuning\_freq\_MHz_{data\_stream\_1}, \\
 *  tuning\_freq\_MHz_{data\_stream\_2},
 *  tuning\_freq\_MHz_{data\_stream\_3}, \\
 *  bandwidth\_3dB\_MHz_{data\_stream\_0},
 *  bandwidth\_3dB\_MHz_{data\_stream\_1}, \\
 *  bandwidth\_3dB\_MHz_{data\_stream\_2},
 *  bandwidth\_3dB\_MHz_{data\_stream\_3}, \\
 *  sampling\_rate\_Msps_{data\_stream\_0},
 *  sampling\_rate\_Msps_{data\_stream\_1}, \\
 *  sampling\_rate\_Msps_{data\_stream\_2},
 *  sampling\_rate\_Msps_{data\_stream\_3}, \\
 *  samples\_are\_complex_{data\_stream\_0},
 *  samples\_are\_complex_{data\_stream\_1}, \\
 *  samples\_are\_complex_{data\_stream\_2},
 *  samples\_are\_complex_{data\_stream\_3}, \\
 *  gain\_mode_{data\_stream\_0},
 *  gain\_mode_{data\_stream\_1}, \\
 *  gain\_mode_{data\_stream\_2},
 *  gain\_mode_{data\_stream\_3}, \\
 *  gain\_dB_{data\_stream\_0},
 *  gain\_dB_{data\_stream\_1}, \\
 *  gain\_dB_{data\_stream\_2},
 *  gain\_dB_{data\_stream\_3}
 *  \}
 * @f}
 * @f{eqnarray*}{
 *  s.t. & gain\_mode_{data\_stream\_0} \in \{0, 1\}, \\
 *       & gain\_mode_{data\_stream\_1} \in \{0, 1\}, \\
 *       & gain\_mode_{data\_stream\_2} = 1, \\
 *       & gain\_mode_{data\_stream\_3} = 1, \\
 *       & tuning\_freq\_MHz_{data\_stream\_0} = Rx\_RFPLL\_LO\_freq, \\
 *       & tuning\_freq\_MHz_{data\_stream\_1} = Rx\_RFPLL\_LO\_freq, \\
 *       & tuning\_freq\_MHz_{data\_stream\_2} = Tx\_RFPLL\_LO\_freq, \\
 *       & tuning\_freq\_MHz_{data\_stream\_3} = Tx\_RFPLL\_LO\_freq, \\
 *       & gain\_dB_{data\_stream\_0} \in \begin{cases} [1,77] if Rx\_RFPLL\_LO\_freq <= 1300, \\
 *                                                      [-3,71] if Rx\_RFPLL\_LO\_freq <= 4000, \\
 *                                                      [-10,62] otherwise 
 *                                                    \end{cases},\\
 *       & gain\_dB_{data\_stream\_1} \in \begin{cases} [1,77] if Rx\_RFPLL\_LO\_freq <= 1300, \\
 *                                                      [-3,71] if Rx\_RFPLL\_LO\_freq <= 4000, \\
 *                                                      [-10,62] otherwise 
 *                                                    \end{cases},\\
 *       & gain\_dB_{data\_stream\_2} \in [-89.75,0], \\
 *       & gain\_dB_{data\_stream\_3} \in [-89.75,0], \\
 *       & bandwidth\_3dB\_MHz_{data\_stream\_0} = rx\_rf\_bandwidth, \\
 *       & bandwidth\_3dB\_MHz_{data\_stream\_1} = rx\_rf\_bandwidth, \\
 *       & bandwidth\_3dB\_MHz_{data\_stream\_2} = tx\_rf\_bandwidth, \\
 *       & bandwidth\_3dB\_MHz_{data\_stream\_3} = tx\_rf\_bandwidth, \\
 *       & RX\_SAMPL\_FREQ\_MHz=TX\_SAMPL\_FREQ\_MHz \times DAC\_Clk\_divider, \\
 *       & sampling\_rate\_Msps_{data\_stream\_0} = RX\_SAMPL\_FREQ\_MHz, \\
 *       & sampling\_rate\_Msps_{data\_stream\_1} = RX\_SAMPL\_FREQ\_MHz, \\
 *       & sampling\_rate\_Msps_{data\_stream\_2} = TX\_SAMPL\_FREQ\_MHz, \\
 *       & sampling\_rate\_Msps_{data\_stream\_3} = TX\_SAMPL\_FREQ\_MHz, \\
 *       & samples\_are\_complex_{data\_stream\_0} = 1, \\
 *       & samples\_are\_complex_{data\_stream\_1} = 1, \\
 *       & samples\_are\_complex_{data\_stream\_2} = 1, \\
 *       & samples\_are\_complex_{data\_stream\_3} = 1
 * @f}
 * In addition to the AD9361-specific constraints, Nyquist criterion
 * constraints are applied:
 * @f{eqnarray*}{
 *  s.t. & rx\_rf\_bandwidth <= RX\_SAMPL\_FREQ\_MHz, \\
 *       & tx\_rf\_bandwidth <= TX\_SAMPL\_FREQ\_MHz
 * @f}
 * For simplicity @f$gain\_mode@f$ is modelled via@f$gain\_mode \in R@f$ and
 * @f$samples\_are\_complex@f$ is modelled via 
 * @f$samples\_are\_complex \in R@f$. 0/1 represents auto/manual for
 * @f$gain\_mode@f$. 0/1 represents false/true for @f$samples\_are\_complex@f$.
 ******************************************************************************/
void ConfiguratorAD9361::impose_constraints_single_pass() {

  // unfortunately, order in which these are called matters...

  Configurator::data_stream_t
    *s0 = find_data_stream(m_data_stream_RX1),
    *s1 = find_data_stream(m_data_stream_RX2),
    *s2 = find_data_stream(m_data_stream_TX1),
    *s3 = find_data_stream(m_data_stream_TX2);

  if (s0) constrain_gain_mode_data_stream_0_equals_0_or_1();
  if (s1) constrain_gain_mode_data_stream_1_equals_0_or_1();
  if (s2) constrain_gain_mode_data_stream_2_equals_1();
  if (s3) constrain_gain_mode_data_stream_3_equals_1();
  if (s2) constrain_gain_dB_data_stream_2_is_in_range_neg_89p75_to_0();
  if (s3) constrain_gain_dB_data_stream_3_is_in_range_neg_89p75_to_0();

  // When we are being used in a TuneResamp context, but the constraints are ad9361-specific
  if (s0 && s0->m_configs.find("tuning_freq_complex_mixer_MHz") != s0->m_configs.end())
    constrain_tuning_freq_equals_Rx_RFPLL_LO_freq_plus_complex_mixer_NCO_freq(m_data_stream_RX1); // (all/3)
  if (s1 && s1->m_configs.find("tuning_freq_complex_mixer_MHz") != s1->m_configs.end())
    constrain_tuning_freq_equals_Rx_RFPLL_LO_freq_plus_complex_mixer_NCO_freq(m_data_stream_RX2); // (all/3)
  if (s2 && s2->m_configs.find("tuning_freq_complex_mixer_MHz") != s2->m_configs.end())
    constrain_tuning_freq_equals_Tx_RFPLL_LO_freq_plus_complex_mixer_NCO_freq(m_data_stream_TX1); // (all/3)
  if (s3 && s3->m_configs.find("tuning_freq_complex_mixer_MHz") != s3->m_configs.end())
    constrain_tuning_freq_equals_Tx_RFPLL_LO_freq_plus_complex_mixer_NCO_freq(m_data_stream_TX2); // (all/3)

  if (s0) constrain_gain_dB_data_stream_0_equals_func_of_Rx_RFPLL_LO_freq();
  if (s1) constrain_gain_dB_data_stream_1_equals_func_of_Rx_RFPLL_LO_freq();

  constrain_RX_SAMPL_FREQ_MHz_equals_TX_SAMPL_FREQ_MHz_times_DAC_Clk_divider();

  if (s0) constrain_samples_are_complex_data_stream_0_equals_1();
  if (s1) constrain_samples_are_complex_data_stream_1_equals_1();
  if (s2) constrain_samples_are_complex_data_stream_2_equals_1();
  if (s3) constrain_samples_are_complex_data_stream_3_equals_1();

#if 0
  if (s0) constrain_tuning_freq_MHz_data_stream_0_equals_Rx_RFPLL_LO_freq();
  if (s1) constrain_tuning_freq_MHz_data_stream_1_equals_Rx_RFPLL_LO_freq();
  if (s2) constrain_tuning_freq_MHz_data_stream_2_equals_Tx_RFPLL_LO_freq();
  if (s3) constrain_tuning_freq_MHz_data_stream_3_equals_Tx_RFPLL_LO_freq();
  if (s0) constrain_bandwidth_3dB_MHz_data_stream_0_equals_rx_rf_bandwidth();
  if (s1) constrain_bandwidth_3dB_MHz_data_stream_1_equals_rx_rf_bandwidth();
  if (s2) constrain_bandwidth_3dB_MHz_data_stream_2_equals_tx_rf_bandwidth();
  if (s3) constrain_bandwidth_3dB_MHz_data_stream_3_equals_tx_rf_bandwidth();
  if (s0) constrain_sampling_rate_Msps_data_stream_0_equals_RX_SAMPL_FREQ();
  if (s1) constrain_sampling_rate_Msps_data_stream_1_equals_RX_SAMPL_FREQ();
  if (s2) constrain_sampling_rate_Msps_data_stream_2_equals_TX_SAMPL_FREQ();
  if (s3) constrain_sampling_rate_Msps_data_stream_3_equals_TX_SAMPL_FREQ();
#endif
}
double ConfiguratorAD9361::
ad9361MaxRxSampleMhz() {
  return calc_max_AD9361_RX_SAMPL_FREQ_Hz(REFCLK40MHz, RX_FIR_DEC_FACTOR)/1e6;
}
double ConfiguratorAD9361::
ad9361MaxTxSampleMhz() {
  return calc_max_AD9361_TX_SAMPL_FREQ_Hz(REFCLK40MHz, TX_FIR_INT_FACTOR)/1e6;
}

} // namespace DRC

} // namespace OCPI
