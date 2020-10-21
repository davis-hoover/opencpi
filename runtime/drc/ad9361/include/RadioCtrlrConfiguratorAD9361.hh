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

#ifndef _OCPI_PROJECTS_RADIO_CTRLR_CONFIGURATOR_AD9361_HH
#define _OCPI_PROJECTS_RADIO_CTRLR_CONFIGURATOR_AD9361_HH

#include <string> //std::string
#include <cassert>
#include "RadioCtrlr.hh"
#include "RadioCtrlrConfigurator.hh" // Configurator

namespace OCPI {

namespace DRC {

/*! @brief Configurator for an AD9361.
 *         data stream 0 -maps-to-> AD9361 RX1 physical pin port,
 *         data stream 1 -maps-to-> AD9361 RX2 physical pin port,
 *         data stream 2 -maps-to-> AD9361 TX2 physical pin port,
 *         data stream 3 -maps-to-> AD9361 TX2 physical pin port.
 *         A configurator is a software-only representation of hardware
 *         capabilities.
 *         This class is intended to be used as a member of a
 *         DigRadioCtrlr class.
 ******************************************************************************/
class ConfiguratorAD9361 :
    public Configurator {
// this class assumed fixed AD9361 REFCLK FREQ
#define REFCLK40MHz 40e6
// this class assumed fixed AD9361 Rx FIR decimation factor
#define RX_FIR_DEC_FACTOR AD9361_Rx_FIR_decimation_factor_t::one
// this class assumed fixed AD9361 Tx FIR decimation factor
#define TX_FIR_INT_FACTOR AD9361_Tx_FIR_interpolation_factor_t::one

// we model and AD9361 data stream as a standard data stream that has gain
typedef DigRadioConfiguratorDataStreamWithGain DataStreamAD9361;

protected : std::string m_data_stream_RX1;
protected : std::string m_data_stream_RX2;
protected : std::string m_data_stream_TX1;
protected : std::string m_data_stream_TX2;
public: const std::string &RX1_id() const { return m_data_stream_RX1; }
public: const std::string &RX2_id() const { return m_data_stream_RX2; }
public: const std::string &TX1_id() const { return m_data_stream_TX1; }
public: const std::string &TX2_id() const { return m_data_stream_TX2; }

// the chip has three inputs per rx and two outputs per tx.
// both channels must have the same configuration at the RF input and output
// in fact, there are 9 RX configurations (12 if you are doing tx monitoring)
// allowing either side of one of three input pairs to be// selected as an unbalanced input
// for 6 different unbalanced inputs or 3 different balanced inputs.
// 

// The derived class or instantiator must assign the stream names.
// This leaves the default constructor alone, to be used for copying
public    : ConfiguratorAD9361(const char* data_stream_RX1,
			       const char* data_stream_RX2,
			       const char* data_stream_TX1,
			       const char* data_stream_TX2);

protected : void constrain_config_by_Rx_RFPLL_LO_freq(
                data_stream_ID_t data_stream);
protected : void constrain_config_by_neg_89p75_to_0(LockRConstrConfig& cfg);

protected : void constrain_gain_mode_data_stream_0_equals_0_or_1();
protected : void constrain_gain_mode_data_stream_1_equals_0_or_1();
protected : void constrain_gain_mode_data_stream_2_equals_1();
protected : void constrain_gain_mode_data_stream_3_equals_1();
protected : void constrain_tuning_freq_MHz_data_stream_0_equals_Rx_RFPLL_LO_freq();
protected : void constrain_tuning_freq_MHz_data_stream_1_equals_Rx_RFPLL_LO_freq();
protected : void constrain_tuning_freq_MHz_data_stream_2_equals_Tx_RFPLL_LO_freq();
protected : void constrain_tuning_freq_MHz_data_stream_3_equals_Tx_RFPLL_LO_freq();
protected : void constrain_gain_dB_data_stream_0_equals_func_of_Rx_RFPLL_LO_freq();
protected : void constrain_gain_dB_data_stream_1_equals_func_of_Rx_RFPLL_LO_freq();
protected : void constrain_gain_dB_data_stream_2_is_in_range_neg_89p75_to_0();
protected : void constrain_gain_dB_data_stream_3_is_in_range_neg_89p75_to_0();
protected : void constrain_bandwidth_3dB_MHz_data_stream_0_equals_rx_rf_bandwidth();
protected : void constrain_bandwidth_3dB_MHz_data_stream_1_equals_rx_rf_bandwidth();
protected : void constrain_bandwidth_3dB_MHz_data_stream_2_equals_tx_rf_bandwidth();
protected : void constrain_bandwidth_3dB_MHz_data_stream_3_equals_tx_rf_bandwidth();
protected : void constrain_RX_SAMPL_FREQ_MHz_equals_TX_SAMPL_FREQ_MHz_times_DAC_Clk_divider();
protected : void constrain_sampling_rate_Msps_data_stream_0_equals_RX_SAMPL_FREQ();
protected : void constrain_sampling_rate_Msps_data_stream_1_equals_RX_SAMPL_FREQ();
protected : void constrain_sampling_rate_Msps_data_stream_2_equals_TX_SAMPL_FREQ();
protected : void constrain_sampling_rate_Msps_data_stream_3_equals_TX_SAMPL_FREQ();
protected : void constrain_samples_are_complex_data_stream_0_equals_1();
protected : void constrain_samples_are_complex_data_stream_1_equals_1();
protected : void constrain_samples_are_complex_data_stream_2_equals_1();
protected : void constrain_samples_are_complex_data_stream_3_equals_1();

protected : void constrain_rx_rf_bandwidth_less_than_or_equal_to_RX_SAMPL_FREQ_MHz();
protected : void constrain_tx_rf_bandwidth_less_than_or_equal_to_TX_SAMPL_FREQ_MHz();

/*! @brief Here is where we apply a single pass of all of the constraints
 *         specific to this class. 'Single pass' simply means that
 *         there may be a domino effect that occurs across multiple configs,
 *         and that this function is not intended to handle the multi-config
 *         effect but rather implement single config-to-config constraints.
 ******************************************************************************/
protected : void impose_constraints_single_pass();
public : Configurator *clone() const { assert("UNEXPECTED CLONE"==0); return NULL;}; // a link

}; // class ConfiguratorAD9361

} // namespace RadioCtrlr

} // namespace OCPIProjects

#endif // _OCPI_PROJECTS_RADIO_CTRLR_CONFIGURATOR_AD9361_HH
