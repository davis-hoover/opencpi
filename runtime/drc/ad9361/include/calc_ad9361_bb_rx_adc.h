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

#ifndef _CALC_AD9361_RX_ADC_H
#define _CALC_AD9361_RX_ADC_H

/*! @file
 *  @brief
 * \verbatim
 
    RX_SAMPL_FREQ..corresponds to the overall effective ADC sampling
                   rate (CLKRF_FREQ) divided by the RX FIR decimation factor.
                   The unit is in complex samples per second.
    CLKRF_FREQ.....corresponds to the overall effective ADC sampling
                   rate in complex samples per second. This rate is
                   equivalent to the rate of the clock signal which drives the
                   AD9361 DATA_CLK_P pin.

    x1,x2,x3,x4 below refers to the multiplication of the clock rate

                                     AD9361 IC
   +---------------------------------------------------------------------------+
   |                              "effective" ADC                              |
   |          /-----------------------------------------+               RX     |
   |         /                 +---+    +---+    +---+  |       +---+  data    |
   |        /            +---->|HB3|--->|HB2|--->|HB1|->|------>|FIR|------->  |
   |       /    /-----+  |     |   |    |   |    |   |  |       |   |          |
   |      /    /  ADC |--+     |   |    |   |    |   |  |       |   |          |
   |  -->+--->+       |     +--|> <|----|> <|----|> <|--|-------|> <|........  |
   |      \    \      |-+---+  +---+ R2 +---+ R1 +---+  | CLKRF +---+(RX_SAMPL |
   |       \    \-----+ |ADC    x1   FREQ x1  FREQ x1   | FREQ   x1   FREQ)    |
   |        \           |FREQ   x2        x2       x2   |        x2            |
   |         \          |       x3                      |        x4            |
   |          \-----------------------------------------+                      |
   |                    /\                                                     |
   |             +----+ | ADC_FREQ                                             |
   | BBPLL_FREQ  |    | |                                                      |
   | ----------->|    |-+                                                      |
   |             |    |                                                        |
   |             +----+                                                        |
   |             /1,  /2                                                       |
   |             /4,  /8                                                       |
   |             /16, /32                                                      |
   |             /64, /128                                                     |
   |             (/[2^BBPLL_Divider])                                          |
   |                                                                           |
   +---------------------------------------------------------------------------+
 
   \endverbatim
 *
 ******************************************************************************/

#include <cmath>   // pow()
#include "calc_ad9361_bb_pll.h"
#include "calc_ad9361_bb_rx_filters_digital.h"

struct regs_calc_AD9361_ADC_FREQ_Hz_t :
       regs_calc_AD9361_BBPLL_FREQ_Hz_t,
       regs_calc_AD9361_BBPLL_Divider_t {
};

struct calc_AD9361_ADC_FREQ_Hz_t :
       calc_AD9361_BBPLL_FREQ_Hz_t,
       calc_AD9361_BBPLL_Divider_t {
  DEFINE_AD9361_SETTING(ADC_FREQ_Hz, double)
};

void calc_AD9361_ADC_FREQ_Hz(calc_AD9361_ADC_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_ADC_FREQ_Hz(calc_AD9361_ADC_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_ADC_FREQ_Hz(calc_AD9361_ADC_FREQ_Hz_t& calc_obj);

const char* calc_AD9361_ADC_FREQ_Hz(calc_AD9361_ADC_FREQ_Hz_t& calc_obj,
				    const regs_calc_AD9361_ADC_FREQ_Hz_t& regs);

struct regs_calc_AD9361_R2_FREQ_Hz_t :
       regs_calc_AD9361_ADC_FREQ_Hz_t,
       regs_calc_AD9361_RHB3_decimation_factor_t {
};

struct calc_AD9361_R2_FREQ_Hz_t :
       calc_AD9361_ADC_FREQ_Hz_t,
       calc_AD9361_RHB3_decimation_factor_t {
  DEFINE_AD9361_SETTING(R2_FREQ_Hz, double)
};

void calc_AD9361_R2_FREQ_Hz(calc_AD9361_R2_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_R2_FREQ_Hz(calc_AD9361_R2_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_R2_FREQ_Hz(calc_AD9361_R2_FREQ_Hz_t& calc_obj);

const char* regs_calc_AD9361_R2_FREQ_Hz(calc_AD9361_R2_FREQ_Hz_t& calc_obj,
					const regs_calc_AD9361_R2_FREQ_Hz_t& regs);

typedef regs_calc_AD9361_R2_FREQ_Hz_t regs_calc_AD9361_R1_FREQ_Hz_t;

struct calc_AD9361_R1_FREQ_Hz_t :
       calc_AD9361_R2_FREQ_Hz_t,
       calc_AD9361_RHB2_decimation_factor_t {
  DEFINE_AD9361_SETTING(R1_FREQ_Hz, double)
};

void calc_AD9361_R1_FREQ_Hz(calc_AD9361_R1_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_R1_FREQ_Hz(calc_AD9361_R1_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_R1_FREQ_Hz(calc_AD9361_R1_FREQ_Hz_t& calc_obj);
const char* regs_calc_AD9361_R1_FREQ_Hz(calc_AD9361_R1_FREQ_Hz_t& calc_obj,
					const regs_calc_AD9361_R1_FREQ_Hz_t& regs);

typedef regs_calc_AD9361_R1_FREQ_Hz_t regs_calc_AD9361_CLKRF_FREQ_Hz_t;

struct calc_AD9361_CLKRF_FREQ_Hz_t :
       calc_AD9361_R1_FREQ_Hz_t,
       calc_AD9361_RHB1_decimation_factor_t {
  DEFINE_AD9361_SETTING(CLKRF_FREQ_Hz, double)
};

void calc_AD9361_CLKRF_FREQ_Hz(calc_AD9361_CLKRF_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_CLKRF_FREQ_Hz(calc_AD9361_CLKRF_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_CLKRF_FREQ_Hz(calc_AD9361_CLKRF_FREQ_Hz_t& calc_obj);

const char* regs_calc_AD9361_CLKRF_FREQ_Hz(calc_AD9361_CLKRF_FREQ_Hz_t& calc_obj,
					   const regs_calc_AD9361_CLKRF_FREQ_Hz_t& regs);

typedef regs_calc_AD9361_R1_FREQ_Hz_t regs_calc_AD9361_RX_SAMPL_FREQ_Hz_t;

struct calc_AD9361_RX_SAMPL_FREQ_Hz_t :
       calc_AD9361_CLKRF_FREQ_Hz_t,
       calc_AD9361_Rx_FIR_decimation_factor_t {
  DEFINE_AD9361_SETTING(RX_SAMPL_FREQ_Hz, double)
};

void calc_AD9361_RX_SAMPL_FREQ_Hz(calc_AD9361_RX_SAMPL_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_RX_SAMPL_FREQ_Hz(calc_AD9361_RX_SAMPL_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_RX_SAMPL_FREQ_Hz(calc_AD9361_RX_SAMPL_FREQ_Hz_t& calc_obj);

calc_AD9361_RX_SAMPL_FREQ_Hz_t::RX_SAMPL_FREQ_Hz_t 
calc_min_AD9361_RX_SAMPL_FREQ_Hz(calc_AD9361_RX_SAMPL_FREQ_Hz_t::BBPLL_FREQ_Hz_t BBPLL_input_F_REF);

calc_AD9361_RX_SAMPL_FREQ_Hz_t::RX_SAMPL_FREQ_Hz_t 
calc_max_AD9361_RX_SAMPL_FREQ_Hz(calc_AD9361_RX_SAMPL_FREQ_Hz_t::BBPLL_FREQ_Hz_t BBPLL_input_F_REF);

calc_AD9361_RX_SAMPL_FREQ_Hz_t::RX_SAMPL_FREQ_Hz_t 
calc_min_AD9361_RX_SAMPL_FREQ_Hz(calc_AD9361_RX_SAMPL_FREQ_Hz_t::BBPLL_FREQ_Hz_t BBPLL_input_F_REF,
				 AD9361_Rx_FIR_decimation_factor_t Rx_FIR_decimation_factor);

calc_AD9361_RX_SAMPL_FREQ_Hz_t::RX_SAMPL_FREQ_Hz_t 
calc_max_AD9361_RX_SAMPL_FREQ_Hz(calc_AD9361_RX_SAMPL_FREQ_Hz_t::BBPLL_FREQ_Hz_t BBPLL_input_F_REF,
				 AD9361_Rx_FIR_decimation_factor_t Rx_FIR_decimation_factor);

const char* regs_calc_AD9361_RX_SAMPL_FREQ_Hz(calc_AD9361_RX_SAMPL_FREQ_Hz_t& calc_obj,
					      const regs_calc_AD9361_RX_SAMPL_FREQ_Hz_t& regs);

#endif // _CALC_AD9361_RX_ADC_H
