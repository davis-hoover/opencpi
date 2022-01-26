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

/*! @file
 *  @brief Implements functions for reading values from an AD9361 IC.
 ******************************************************************************/

#include "calc_ad9361_bb_rx_adc.h"
#include "calc_ad9361_bb_tx_dac.h"
#include "calc_ad9361_rf_rx_pll.h"
#include "calc_ad9361_rf_tx_pll.h"
#include "read_ad9361.h"

/*! @brief Retrieve with double floating point precision
 *         the theoretical value of the
 *             AD9361 RX SAMPL FREQ in Hz
 *         from an AD9361 IC.
 *
 *  @param[in]  phy                 ad9361 library rf_phy handle
 *  @param[in]  AD9361_XTAL_freq_Hz Frequency of the device connected to the
 *                                  AD9361 XTAL pin(s).
 *  @param[out] val                 Retrieved value.
 *
 *  @return 0 if there are no errors, non-zero char array pointer if there
 *          are errors (char array content will describe the error).
 ******************************************************************************/
const char *
get_ad9361_rx_sampl_freq_hz(const struct ad9361_rf_phy *phy, double reference_clock_rate_Hz,
			    double &val) {
  regs_calc_AD9361_CLKRF_FREQ_Hz_t regs;

  regs.bbpll_ref_clock_scaler        = (uint8_t)ad9361_spi_read(phy->spi, REG_CLOCK_CTRL);
  regs.bbpll_fract_bb_freq_word_1    = (uint8_t)ad9361_spi_read(phy->spi, REG_FRACT_BB_FREQ_WORD_1);
  regs.bbpll_fract_bb_freq_word_2    = (uint8_t)ad9361_spi_read(phy->spi, REG_FRACT_BB_FREQ_WORD_2);
  regs.bbpll_fract_bb_freq_word_3    = (uint8_t)ad9361_spi_read(phy->spi, REG_FRACT_BB_FREQ_WORD_3);
  regs.bbpll_integer_bb_freq_word    = (uint8_t)ad9361_spi_read(phy->spi, REG_INTEGER_BB_FREQ_WORD);
  regs.clock_bbpll                   = (uint8_t)ad9361_spi_read(phy->spi, REG_BBPLL);
  regs.general_rx_enable_filter_ctrl = (uint8_t)ad9361_spi_read(phy->spi, REG_RX_ENABLE_FILTER_CTRL);

  calc_AD9361_RX_SAMPL_FREQ_Hz_t calc_obj;
  calc_obj.BBPLL_input_F_REF = reference_clock_rate_Hz;
  const char* ret = regs_calc_AD9361_RX_SAMPL_FREQ_Hz(calc_obj, regs);

  val = calc_obj.RX_SAMPL_FREQ_Hz;
  return ret;
}

/*! @brief Retrieve with double floating point precision
 *         the theoretical value of the
 *             AD9361 CLKTF frequency in Hz
 *         from an AD9361 IC.
 *
 *  @param[in]  phy                 ad9361 library rf_phy handle
 *  @param[in]  AD9361_XTAL_freq_Hz Frequency of the device connected to the
 *                                  AD9361 XTAL pin(s).
 *  @param[out] val                 Retrieved value.
 *
 *  @return 0 if there are no errors, non-zero char array pointer if there
 *          are errors (char array content will describe the error).
 ******************************************************************************/
const char *
get_ad9361_tx_sampl_freq_hz(const struct ad9361_rf_phy *phy,
			    double reference_clock_rate_Hz, double &val) {

  regs_calc_AD9361_CLKTF_FREQ_Hz_t regs;

  regs.bbpll_ref_clock_scaler        = (uint8_t)ad9361_spi_read(phy->spi, REG_CLOCK_CTRL);
  regs.bbpll_fract_bb_freq_word_1    = (uint8_t)ad9361_spi_read(phy->spi, REG_FRACT_BB_FREQ_WORD_1);
  regs.bbpll_fract_bb_freq_word_2    = (uint8_t)ad9361_spi_read(phy->spi, REG_FRACT_BB_FREQ_WORD_2);
  regs.bbpll_fract_bb_freq_word_3    = (uint8_t)ad9361_spi_read(phy->spi, REG_FRACT_BB_FREQ_WORD_3);
  regs.bbpll_integer_bb_freq_word    = (uint8_t)ad9361_spi_read(phy->spi, REG_INTEGER_BB_FREQ_WORD);
  regs.clock_bbpll                   = (uint8_t)ad9361_spi_read(phy->spi, REG_BBPLL);
  regs.general_tx_enable_filter_ctrl = (uint8_t)ad9361_spi_read(phy->spi, REG_TX_ENABLE_FILTER_CTRL);

  calc_AD9361_TX_SAMPL_FREQ_Hz_t calc_obj;
  calc_obj.BBPLL_input_F_REF = reference_clock_rate_Hz;
  const char* ret = regs_calc_AD9361_TX_SAMPL_FREQ_Hz(calc_obj, regs);

  val = calc_obj.TX_SAMPL_FREQ_Hz;
  return ret;
}
/*! @brief Retrieve with double floating point precision
 *         the theoretical value of the
 *             AD9361 RX RF LO frequency in Hz
 *         from an AD9361 IC.
 *
 *  @param[in]  phy                 ad9361 library rf_phy handle
 *  @param[in]  AD9361_reference_clock_rate_Hz Frequency of the device connected
 *                                             to the AD9361 XTAL pin(s).
 *  @param[out] val                 Retrieved value.
 *  @return 0 if there are no errors, non-zero char array pointer if there
 *          are errors (char array content will describe the error).
 ******************************************************************************/
const char *
get_ad9361_rx_rfpll_lo_freq_hz(const struct ad9361_rf_phy *phy,
			       double reference_clock_rate_Hz, double &val) {
  regs_calc_AD9361_Rx_RFPLL_LO_freq_Hz_t regs;

  regs.general_rfpll_dividers  = (uint8_t)ad9361_spi_read(phy->spi, REG_RFPLL_DIVIDERS);
  regs.ref_divide_config_1     = (uint8_t)ad9361_spi_read(phy->spi, REG_REF_DIVIDE_CONFIG_1);
  regs.ref_divide_config_2     = (uint8_t)ad9361_spi_read(phy->spi, REG_REF_DIVIDE_CONFIG_2);
  regs.rx_synth_integer_byte_0 = (uint8_t)ad9361_spi_read(phy->spi, REG_RX_INTEGER_BYTE_0);
  regs.rx_synth_integer_byte_1 = (uint8_t)ad9361_spi_read(phy->spi, REG_RX_INTEGER_BYTE_1);
  regs.rx_synth_fract_byte_0   = (uint8_t)ad9361_spi_read(phy->spi, REG_RX_FRACT_BYTE_0);
  regs.rx_synth_fract_byte_1   = (uint8_t)ad9361_spi_read(phy->spi, REG_RX_FRACT_BYTE_1);
  regs.rx_synth_fract_byte_2   = (uint8_t)ad9361_spi_read(phy->spi, REG_RX_FRACT_BYTE_2);

  return calc_AD9361_Rx_RFPLL_LO_freq_Hz(val, reference_clock_rate_Hz, regs);
}

/*! @brief Retrieve with double floating point precision
 *         the theoretical value of the
 *             AD9361 TX RF LO frequency in Hz
 *         from an AD9361 IC.
 *
 *  @param[in]  phy                 ad9361 library rf_phy handle
 *  @param[in]  AD9361_reference_clock_rate_Hz Frequency of the device connected
 *                                             to the AD9361 XTAL pin(s).
 *  @param[out] val                 Retrieved value.
 *  @return 0 if there are no errors, non-zero char array pointer if there
 *          are errors (char array content will describe the error).
 ******************************************************************************/
const char *
get_ad9361_tx_rfpll_lo_freq_hz(const struct ad9361_rf_phy *phy,
			       double reference_clock_rate_hz, double &val) {
  regs_calc_AD9361_Tx_RFPLL_LO_freq_Hz_t regs;

  regs.general_rfpll_dividers  = (uint8_t)ad9361_spi_read(phy->spi, REG_RFPLL_DIVIDERS);
  regs.ref_divide_config_2     = (uint8_t)ad9361_spi_read(phy->spi, REG_REF_DIVIDE_CONFIG_2);
  regs.tx_synth_integer_byte_0 = (uint8_t)ad9361_spi_read(phy->spi, REG_TX_INTEGER_BYTE_0);
  regs.tx_synth_integer_byte_1 = (uint8_t)ad9361_spi_read(phy->spi, REG_TX_INTEGER_BYTE_1);
  regs.tx_synth_fract_byte_0   = (uint8_t)ad9361_spi_read(phy->spi, REG_TX_FRACT_BYTE_0);
  regs.tx_synth_fract_byte_1   = (uint8_t)ad9361_spi_read(phy->spi, REG_TX_FRACT_BYTE_1);
  regs.tx_synth_fract_byte_2   = (uint8_t)ad9361_spi_read(phy->spi, REG_TX_FRACT_BYTE_2);

  return calc_AD9361_Tx_RFPLL_LO_freq_Hz(val, reference_clock_rate_hz, regs);
}
