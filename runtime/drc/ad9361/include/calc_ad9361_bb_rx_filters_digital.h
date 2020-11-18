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

#ifndef _CALC_AD9361_BB_RX_FILTERS_DIGITAL_H
#define _CALC_AD9361_BB_RX_FILTERS_DIGITAL_H

/*! @file
 *  @brief
 *
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
   |                            "effective" ADC                                |
   |        /-----------------------------------------+               RX       |
   |       /                 +---+    +---+    +---+  |       +---+  data      |
   |      /            +---->|HB3|--->|HB2|--->|HB1|->|------>|FIR|------->    |
   |     /    /-----+  |     |   |    |   |    |   |  |       |   |            |
   |    /    /  ADC |--+     |   |    |   |    |   |  |       |   |            |
   | ->+--->+       |     +--|> <|----|> <|----|> <|--|------>|> <|........    |
   |    \    \      |-+---+  +---+ R2 +---+ R1 +---+  | CLKRF +---+(RX_SAMPL   |
   |     \    \-----+ |ADC    x1   FREQ x1  FREQ x1   | FREQ   x1   FREQ)      |
   |      \           |FREQ   x2        x2       x2   |        x2              |
   |       \          |       x3                      |        x4              |
   |        \-----------------------------------------+                        |
   |                  /\                                                       |
   |                  | ADC_FREQ                                               |
   |                                                                           |
   +---------------------------------------------------------------------------+
 
   \endverbatim
 *
 ******************************************************************************/

#include <string>          // std::string
#include <cstdint>         // uint8_t type
#include <sstream>         // std::ostringstream
extern "C" {
#include "ad9361_platform.h" // BITMASK_D... macros
}
struct regs_general_rx_enable_filter_ctrl_t {
  uint8_t general_rx_enable_filter_ctrl;
};

typedef regs_general_rx_enable_filter_ctrl_t regs_calc_AD9361_RHB3_decimation_factor_t;

struct calc_AD9361_RHB3_decimation_factor_t {
  DEFINE_AD9361_SETTING(RHB3_decimation_factor, uint8_t)
};

void get_min_AD9361_RHB3_decimation_factor(calc_AD9361_RHB3_decimation_factor_t& calc_obj);
void get_max_AD9361_RHB3_decimation_factor(calc_AD9361_RHB3_decimation_factor_t& calc_obj);

const char* regs_calc_AD9361_RHB3_decimation_factor(calc_AD9361_RHB3_decimation_factor_t& calc_obj,
						    const regs_calc_AD9361_RHB3_decimation_factor_t& regs);

typedef regs_general_rx_enable_filter_ctrl_t regs_calc_AD9361_RHB2_decimation_factor_t;

struct calc_AD9361_RHB2_decimation_factor_t {
  DEFINE_AD9361_SETTING(RHB2_decimation_factor, uint8_t)
};

void get_min_AD9361_RHB2_decimation_factor(calc_AD9361_RHB2_decimation_factor_t& calc_obj);
void get_max_AD9361_RHB2_decimation_factor(calc_AD9361_RHB2_decimation_factor_t& calc_obj);
const char* regs_calc_AD9361_RHB2_decimation_factor(calc_AD9361_RHB2_decimation_factor_t& calc_obj,
						    const   regs_calc_AD9361_RHB2_decimation_factor_t& regs);

typedef regs_general_rx_enable_filter_ctrl_t regs_calc_AD9361_RHB1_decimation_factor_t;

struct calc_AD9361_RHB1_decimation_factor_t {
  DEFINE_AD9361_SETTING(RHB1_decimation_factor, uint8_t)
};

void get_min_AD9361_RHB1_decimation_factor(calc_AD9361_RHB1_decimation_factor_t& calc_obj);
void get_max_AD9361_RHB1_decimation_factor(calc_AD9361_RHB1_decimation_factor_t& calc_obj);

const char* regs_calc_AD9361_RHB1_decimation_factor(calc_AD9361_RHB1_decimation_factor_t& calc_obj,
						    const regs_calc_AD9361_RHB1_decimation_factor_t& regs);

typedef regs_general_rx_enable_filter_ctrl_t regs_calc_AD9361_Rx_FIR_decimation_factor_t;

enum class AD9361_Rx_FIR_decimation_factor_t {one=1, two=2, four=4};

struct calc_AD9361_Rx_FIR_decimation_factor_t {
  AD9361_Rx_FIR_decimation_factor_t Rx_FIR_decimation_factor;
};

void get_min_AD9361_Rx_FIR_decimation_factor(calc_AD9361_Rx_FIR_decimation_factor_t& calc_obj);
void get_max_AD9361_Rx_FIR_decimation_factor(calc_AD9361_Rx_FIR_decimation_factor_t& calc_obj);

const char* regs_calc_AD9361_Rx_FIR_decimation_factor(calc_AD9361_Rx_FIR_decimation_factor_t& calc_obj,
						      const regs_calc_AD9361_Rx_FIR_decimation_factor_t& regs);

#endif // _CALC_AD9361_BB_RX_FILTERS_DIGITAL_H
