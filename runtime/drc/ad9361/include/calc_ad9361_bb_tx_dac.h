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

#ifndef _CALC_AD9361_TX_DAC_H
#define _CALC_AD9361_TX_DAC_H

/*! @file
 *  @brief
 * \verbatim
 
    TX_SAMPL_FREQ..corresponds to the overall effective DAC sampling
                   rate divided by the TX FIR interpolation rate in
                   complex samples per second. (I *think* this is
                   assumed to be the TX_FB_CLK pin's clock rate, the AD9361 
                   probably synchronizes at some point between
                   the TX_FB_CLK domain and the clocks derived from
                   the DAC_FREQ clock domain.)
    CLKTF_FREQ.....corresponds to the overall effective DAC sampling
                   rate in complex samples per second.

                                     AD9361 IC
   +---------------------------------------------------------------------------+
   |                            "effective" DAC                                |
   |    TX               +----------------------------------------\            |
   |   data  +---+       |  +---+    +---+    +---+                \           |
   | ------->|FIR|------>|->|HB1|--->|HB2|--->|HB3|----+            \          |
   |         |   |       |  |   |    |   |    |   |    |  +-----\    \         |
   |         |   |       |  |   |    |   |    |   |    +->| DAC  \    \        |
   | ........|> <|------>|--|> <|----|> <|----|> <|-+     |       +--->+->     |
   |(TX_SAMPL+---+ CLKTF |  +---+ T1 +---+ T2 +---+ +---+-|>     /    /        |
   | FREQ)    x1   FREQ  |   x1   FREQ x1  FREQ x1  DAC | +-----/    /         |
   |          x2         |   x2        x2       x2  FREQ|           /          |
   |          x4         |                      x3      |          /           |
   |                     +----------------------------------------/            |
   |                                                    /\                     |
   |                                                    | DAC_FREQ             |
   |                                                    |                      |
   |                                                  +---+ DAC                |
   |                                                  |   | divider            |
   |                                                  +---+ /1, /2             |
   |                                                    /\                     |
   |                                                    |                      |
   |                                               -----+ ADC_FREQ             |
   |                                                                           |
   +---------------------------------------------------------------------------+
 
   CLKTF_FREQ formula:
   DAC_FREQ = BBPLL_freq / DAC_divider
   CLKTF_FREQ = 1/HB1/HB2/HB3*DAC_FREQ

   \endverbatim
 *
 ******************************************************************************/

#include <cstdint> // uint8_t, uint32_t types
#include "calc_ad9361_bb_rx_adc.h"
#include "calc_ad9361_bb_tx_filters_digital.h"

typedef regs_clock_bbpll_t regs_calc_AD9361_DAC_Clk_div2_t;

struct calc_AD9361_DAC_Clk_div2_t {
  DEFINE_AD9361_SETTING(DAC_Clk_div2, bool)
};

const char* calc_AD9361_DAC_Clk_div2(calc_AD9361_DAC_Clk_div2_t& calc_obj,
				     const regs_calc_AD9361_DAC_Clk_div2_t& regs);

typedef regs_calc_AD9361_DAC_Clk_div2_t regs_calc_AD9361_DAC_divider_t;

struct calc_AD9361_DAC_divider_t : calc_AD9361_DAC_Clk_div2_t {
  DEFINE_AD9361_SETTING(DAC_divider, uint8_t)
};

void get_min_AD9361_DAC_divider(calc_AD9361_DAC_divider_t& calc_obj);
void get_max_AD9361_DAC_divider(calc_AD9361_DAC_divider_t& calc_obj);

const char*    calc_AD9361_DAC_divider(calc_AD9361_DAC_divider_t& calc_obj,
				       const regs_calc_AD9361_DAC_divider_t& regs);

struct regs_calc_AD9361_DAC_FREQ_Hz_t :
       regs_calc_AD9361_ADC_FREQ_Hz_t {
};

struct calc_AD9361_DAC_FREQ_Hz_t :
       calc_AD9361_ADC_FREQ_Hz_t,
       calc_AD9361_DAC_divider_t {
  DEFINE_AD9361_SETTING(DAC_FREQ_Hz, double)
};
void calc_AD9361_DAC_FREQ_Hz(calc_AD9361_DAC_FREQ_Hz_t& calc_obj);

void calc_min_AD9361_DAC_FREQ_Hz(calc_AD9361_DAC_FREQ_Hz_t& calc_obj);

void calc_max_AD9361_DAC_FREQ_Hz(calc_AD9361_DAC_FREQ_Hz_t& calc_obj);

const char* calc_AD9361_DAC_FREQ_Hz(calc_AD9361_DAC_FREQ_Hz_t& calc_obj,
				    const regs_calc_AD9361_DAC_FREQ_Hz_t& regs);

struct regs_calc_AD9361_T2_FREQ_Hz_t :
       regs_calc_AD9361_DAC_FREQ_Hz_t,
       regs_calc_AD9361_THB3_interpolation_factor_t {
};

struct calc_AD9361_T2_FREQ_Hz_t :
       calc_AD9361_DAC_FREQ_Hz_t,
       calc_AD9361_THB3_interpolation_factor_t {
  DEFINE_AD9361_SETTING(T2_FREQ_Hz, double)
};

void calc_AD9361_T2_FREQ_Hz(calc_AD9361_T2_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_T2_FREQ_Hz(calc_AD9361_T2_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_T2_FREQ_Hz(calc_AD9361_T2_FREQ_Hz_t& calc_obj);

const char* calc_AD9361_T2_FREQ_Hz(calc_AD9361_T2_FREQ_Hz_t& calc_obj,
				   const regs_calc_AD9361_T2_FREQ_Hz_t& regs);

typedef regs_calc_AD9361_T2_FREQ_Hz_t regs_calc_AD9361_T1_FREQ_Hz_t;

struct calc_AD9361_T1_FREQ_Hz_t :
       calc_AD9361_T2_FREQ_Hz_t,
       calc_AD9361_THB2_interpolation_factor_t {
  DEFINE_AD9361_SETTING(T1_FREQ_Hz, double)
};

void calc_AD9361_T1_FREQ_Hz(calc_AD9361_T1_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_T1_FREQ_Hz(calc_AD9361_T1_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_T1_FREQ_Hz(calc_AD9361_T1_FREQ_Hz_t& calc_obj);

const char* calc_AD9361_T1_FREQ_Hz(calc_AD9361_T1_FREQ_Hz_t& calc_obj,
				   const regs_calc_AD9361_T1_FREQ_Hz_t& regs);

typedef regs_calc_AD9361_T1_FREQ_Hz_t regs_calc_AD9361_CLKTF_FREQ_Hz_t;

struct calc_AD9361_CLKTF_FREQ_Hz_t :
       calc_AD9361_T1_FREQ_Hz_t,
       calc_AD9361_THB1_interpolation_factor_t {
  DEFINE_AD9361_SETTING(CLKTF_FREQ_Hz, double)
};

void calc_AD9361_CLKTF_FREQ_Hz(calc_AD9361_CLKTF_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_CLKTF_FREQ_Hz(calc_AD9361_CLKTF_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_CLKTF_FREQ_Hz(calc_AD9361_CLKTF_FREQ_Hz_t& calc_obj);

const char* calc_AD9361_CLKTF_FREQ_Hz(calc_AD9361_CLKTF_FREQ_Hz_t& calc_obj,
				      const regs_calc_AD9361_CLKTF_FREQ_Hz_t& regs);

typedef regs_calc_AD9361_CLKTF_FREQ_Hz_t regs_calc_AD9361_TX_SAMPL_FREQ_Hz_t;

struct calc_AD9361_TX_SAMPL_FREQ_Hz_t :
       calc_AD9361_CLKTF_FREQ_Hz_t,
       calc_AD9361_Tx_FIR_interpolation_factor_t {
  DEFINE_AD9361_SETTING(TX_SAMPL_FREQ_Hz, double)
};

void calc_AD9361_TX_SAMPL_FREQ_Hz(calc_AD9361_TX_SAMPL_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_TX_SAMPL_FREQ_Hz(calc_AD9361_TX_SAMPL_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_TX_SAMPL_FREQ_Hz(calc_AD9361_TX_SAMPL_FREQ_Hz_t& calc_obj);

calc_AD9361_TX_SAMPL_FREQ_Hz_t::TX_SAMPL_FREQ_Hz_t 
calc_min_AD9361_TX_SAMPL_FREQ_Hz(calc_AD9361_TX_SAMPL_FREQ_Hz_t::BBPLL_FREQ_Hz_t BBPLL_input_F_REF);

calc_AD9361_TX_SAMPL_FREQ_Hz_t::TX_SAMPL_FREQ_Hz_t 
calc_max_AD9361_TX_SAMPL_FREQ_Hz(calc_AD9361_TX_SAMPL_FREQ_Hz_t::BBPLL_FREQ_Hz_t BBPLL_input_F_REF);

calc_AD9361_TX_SAMPL_FREQ_Hz_t::TX_SAMPL_FREQ_Hz_t 
calc_min_AD9361_TX_SAMPL_FREQ_Hz(calc_AD9361_TX_SAMPL_FREQ_Hz_t::BBPLL_FREQ_Hz_t BBPLL_input_F_REF,
				 AD9361_Tx_FIR_interpolation_factor_t Tx_FIR_interpolation_factor);

calc_AD9361_TX_SAMPL_FREQ_Hz_t::TX_SAMPL_FREQ_Hz_t 
calc_max_AD9361_TX_SAMPL_FREQ_Hz(calc_AD9361_TX_SAMPL_FREQ_Hz_t::BBPLL_FREQ_Hz_t BBPLL_input_F_REF,
				 AD9361_Tx_FIR_interpolation_factor_t Tx_FIR_interpolation_factor);

const char* regs_calc_AD9361_TX_SAMPL_FREQ_Hz(calc_AD9361_TX_SAMPL_FREQ_Hz_t& calc_obj,
					      const regs_calc_AD9361_TX_SAMPL_FREQ_Hz_t& regs);
#endif // _CALC_AD9361_TX_DAC_H
