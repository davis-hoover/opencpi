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

#ifndef _OCPI_PROJECTS_DIG_RADIO_CONFIGURATOR_TUNE_RESAMP_HH
#define _OCPI_PROJECTS_DIG_RADIO_CONFIGURATOR_TUNE_RESAMP_HH

#include <cassert>
#include "RadioCtrlrConfigurator.hh"

namespace OCPI {

namespace DRC {

/*! @brief Configurator class for tuning/resampling using DSP workers.
 *         A configurator is a software-only representation of hardware
 *         capabilities.
 *
 * @verbatim
                 OpenCPI Assembly
           -------------------------------------------------------+
                                cic_dec.hdl     complex_mixer.hdl |   E31x
                               (downsampler)    (DDC)             |  +--------+
                                  +----+         +----+           |  |        |
           data stream 0 <--------|    |<--------|    |<----------|<-|----RX2B|<
                                  +----+         +----+           |  |    SMA |
                                                                  |  |        |
                                cic_dec.hdl     complex_mixer.hdl |  |        |
                               (downsampler)    (DDC)             |  |        |
                                  +----+         +----+           |  |        |
           data stream 1 <--------|    |<--------|    |<----------|<-|----RX2A|<
                                  +----+         +----+           |  |    SMA |
                                                                  |  |        |
                                cic_int.hdl     complex_mixer.hdl |  |        |
                               (upsampler)      (DUC)             |  |        |
                                  +----+         +----+           |  |        |
           data stream 2 -------->|    |-------->|    |---------->|->|----TRXB|>
                                  +----+         +----+           |  |    SMA |
                                                                  |  |        |
                                cic_int.hdl     complex_mixer.hdl |  |        |
                               (upsampler)      (DUC)             |  |        |
                                  +----+         +----+           |  |        |
           data stream 3 -------->|    |-------->|    |---------->|->|----TRXA|>
                                  +----+         +----+           |  |    SMA |
                                                                  |  +--------+
           -------------------------------------------------------+
   @endverbatim
 ******************************************************************************/
class ConfiguratorTuneResamp : virtual public Configurator {

public : Configurator *clone() const { assert("UNEXPECTED CLONE"==0); return NULL;};

// @brief Used for normal explicit construction, ranges not supplied allow any values
protected :
  void 
    add_stream_config_RX_tuning_freq_complex_mixer(const data_stream_ID_t &data_stream,
						   double maxRxSampFreqMhz),
    add_stream_config_TX_tuning_freq_complex_mixer(const data_stream_ID_t &data_stream,
						   double maxTxSampFreqMhz),
    add_stream_config_CIC_dec_decimation_factor(const data_stream_ID_t &data_stream,
						ConfigValueRanges CIC_dec_abs_ranges),
    add_stream_config_CIC_int_interpolation_factor(const data_stream_ID_t &data_stream,
						   ConfigValueRanges CIC_int_abs_ranges),
    constrain_FE_samp_rate_equals_func_of_DS_complex_mixer_freq(const data_stream_ID_t &data_stream,
								config_key_t samp_rate),
    constrain_FE_samp_rate_to_func_of_DS_complex_mixer_freq(const data_stream_ID_t &data_stream,
							    config_key_t samp_rate),
    constrain_DS_complex_mixer_freq_to_func_of_FE_samp_rate(const data_stream_ID_t &data_stream,
							    config_key_t samp_rate),
    constrain_DS_bandwidth_equals_FE_bandwidth_divided_by_CIC_dec(const data_stream_ID_t &data_stream,
								  config_key_t frontend_bandwidth),
    constrain_DS_bandwidth_equals_FE_bandwidth_divided_by_CIC_int(const data_stream_ID_t &data_stream,
								  config_key_t frontend_bandwidth),
    constrain_sampling_rate_equals_FE_samp_rate_divided_by_CIC_dec(const data_stream_ID_t &data_stream,
								   config_key_t frontend_samp_rate),
    constrain_sampling_rate_equals_FE_samp_rate_divided_by_CIC_int(const data_stream_ID_t &data_stream,
								   config_key_t frontend_samp_rate);

public : virtual void impose_constraints_single_pass();

}; // class RadioCtrlrConfiguratorTuneResamp

} // namespace DRC

} // namespace OCPI

#endif // _OCPI_DRC_CONFIGURATOR_TUNE_RESAMP_HH
