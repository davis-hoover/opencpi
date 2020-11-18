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

#ifndef _CALC_AD9361_TX_RFPLL_H
#define _CALC_AD9361_TX_RFPLL_H

struct regs_calc_AD9361_Tx_RFPLL_ref_divider_t {
  uint8_t ref_divide_config_2;
};

const char* calc_AD9361_Tx_RFPLL_ref_divider(
    float& val,
    const regs_calc_AD9361_Tx_RFPLL_ref_divider_t& regs);

struct regs_calc_AD9361_Tx_RFPLL_N_Integer_t {
  uint8_t tx_synth_integer_byte_0;
  uint8_t tx_synth_integer_byte_1;
};

const char* calc_AD9361_Tx_RFPLL_N_Integer(
    uint16_t& val,
    const regs_calc_AD9361_Tx_RFPLL_N_Integer_t& regs);

struct regs_calc_AD9361_Tx_RFPLL_N_Fractional_t {
  uint8_t tx_synth_fract_byte_0;
  uint8_t tx_synth_fract_byte_1;
  uint8_t tx_synth_fract_byte_2;
};

const char* calc_AD9361_Tx_RFPLL_N_Fractional(
    uint32_t& val,
    const regs_calc_AD9361_Tx_RFPLL_N_Fractional_t& regs);

typedef regs_general_rfpll_divider_t regs_calc_AD9361_Tx_RFPLL_external_div_2_enable_t;

const char* calc_AD9361_Tx_RFPLL_external_div_2_enable(
    bool& val,
    const regs_calc_AD9361_Tx_RFPLL_external_div_2_enable_t& regs);

typedef regs_general_rfpll_divider_t regs_calc_AD9361_Tx_RFPLL_VCO_Divider_t;

const char* calc_AD9361_Tx_RFPLL_VCO_Divider(
    uint8_t& val,
    const regs_calc_AD9361_Tx_RFPLL_VCO_Divider_t& regs);

struct regs_calc_AD9361_Tx_RFPLL_LO_freq_Hz_t :
       regs_general_rfpll_divider_t,
       regs_calc_AD9361_Tx_RFPLL_ref_divider_t,
       regs_calc_AD9361_Tx_RFPLL_N_Integer_t,
       regs_calc_AD9361_Tx_RFPLL_N_Fractional_t {
};

const char* calc_AD9361_Tx_RFPLL_LO_freq_Hz(
    double& val,
    double Tx_RFPLL_input_F_REF,
    const regs_calc_AD9361_Tx_RFPLL_LO_freq_Hz_t& regs);

#endif // _CALC_AD9361_TX_RFPLL_H
