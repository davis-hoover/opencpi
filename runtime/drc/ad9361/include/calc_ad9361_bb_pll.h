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

#ifndef _CALC_AD9361_BBPLL_H
#define _CALC_AD9361_BBPLL_H

/*! @file
 *  @brief
 *
 * \verbatim
                         AD9361 IC
   +---------------------------------------------------------------------------+
   |                                                                           |
   |                       BBPLL                                               |
   |         +-------------------------------+                                 |
   |         |   ref                         |                                 |
   |         |   scaler                      |                                 |
   |         |   +---+   +-----------------+ |             +----+              |
   |         |   |   |   | x (N_integer    | | BBPLL_FREQ  |    |              |
   | F_REF-->|-->|   |-->| + [N_fractional |-|------------>|    |--> ADC_FREQ  |
   |         |   +---+   | /BBPLL_MODULUS)]| |             |    |              |
   |         |    x1     +-----------------+ |             +----+              |
   |         |    /2                         |             /1,  /2             |
   |         |    /4                         |             /4,  /8             |
   |         |    *2                         |             /16, /32            |
   |         |                               |             /64, /128           |
   |         |                               |             (/[2^BBPLL_Divider])|
   |         +-------------------------------+                                 |
   +---------------------------------------------------------------------------+
  
   BBPLL_freq formula
   BBPLL_freq = F_REF*ref_scaler*(N_Integer + (N_Fractional/BBPLL_MODULUS))
  
   \endverbatim
 *
 ******************************************************************************/

#include <cstdint>         // uint8_t, uint32_t types
#include <sstream>         // std::ostringstream
extern "C" {
#include "ad9361.h"        // BBPLL_MODULUS macro
#include "ad9361_platform.h" // regs_clock_bbpll_t
}
struct regs_calc_AD9361_BBPLL_ref_scaler_t {
  uint8_t bbpll_ref_clock_scaler;
};

struct calc_AD9361_BBPLL_ref_scaler_t {
  typedef float BBPLL_ref_scaler_t;
  BBPLL_ref_scaler_t BBPLL_ref_scaler ;
};

void get_min_AD9361_BBPLL_ref_scaler(calc_AD9361_BBPLL_ref_scaler_t& calc_obj);
void get_max_AD9361_BBPLL_ref_scaler(calc_AD9361_BBPLL_ref_scaler_t& calc_obj);
const char* regs_calc_AD9361_BBPLL_ref_scaler(calc_AD9361_BBPLL_ref_scaler_t& calc_obj,
					      const regs_calc_AD9361_BBPLL_ref_scaler_t& regs);
struct regs_calc_AD9361_BBPLL_N_Integer_t {
  uint8_t bbpll_integer_bb_freq_word;
};

struct calc_AD9361_BBPLL_N_Integer_t {
  typedef uint8_t BBPLL_N_Integer_t;
  BBPLL_N_Integer_t BBPLL_N_Integer;
};

void get_min_AD9361_BBPLL_N_Integer(calc_AD9361_BBPLL_N_Integer_t& calc_obj);
void get_max_AD9361_BBPLL_N_Integer(calc_AD9361_BBPLL_N_Integer_t& calc_obj);
const char* regs_calc_AD9361_BBPLL_N_Integer(calc_AD9361_BBPLL_N_Integer_t& calc_obj,
					     const regs_calc_AD9361_BBPLL_N_Integer_t& regs);

struct regs_calc_AD9361_BBPLL_N_Fractional_t {
  uint8_t bbpll_fract_bb_freq_word_1;
  uint8_t bbpll_fract_bb_freq_word_2;
  uint8_t bbpll_fract_bb_freq_word_3;
};

struct calc_AD9361_BBPLL_N_Fractional_t {
  typedef uint32_t BBPLL_N_Fractional_t;
  BBPLL_N_Fractional_t BBPLL_N_Fractional;
};

void get_min_AD9361_BBPLL_N_Fractional(calc_AD9361_BBPLL_N_Fractional_t& calc_obj);
void get_max_AD9361_BBPLL_N_Fractional(calc_AD9361_BBPLL_N_Fractional_t& calc_obj);
const char* regs_calc_AD9361_BBPLL_N_Fractional(calc_AD9361_BBPLL_N_Fractional_t& calc_obj,
						const regs_calc_AD9361_BBPLL_N_Fractional_t& regs);

struct regs_calc_AD9361_BBPLL_FREQ_Hz_t :
       regs_calc_AD9361_BBPLL_ref_scaler_t,
       regs_calc_AD9361_BBPLL_N_Integer_t,
       regs_calc_AD9361_BBPLL_N_Fractional_t {
};

struct calc_AD9361_BBPLL_FREQ_Hz_t :
       calc_AD9361_BBPLL_ref_scaler_t ,
       calc_AD9361_BBPLL_N_Integer_t,
       calc_AD9361_BBPLL_N_Fractional_t {
  typedef double BBPLL_input_F_REF_t;
  BBPLL_input_F_REF_t BBPLL_input_F_REF;
  typedef double BBPLL_FREQ_Hz_t;
  BBPLL_FREQ_Hz_t BBPLL_FREQ_Hz;
};

void calc_AD9361_BBPLL_FREQ_Hz(calc_AD9361_BBPLL_FREQ_Hz_t& calc_obj);
void calc_min_AD9361_BBPLL_FREQ_Hz(//double AD9361_BBPLL_input_F_REF,
				   calc_AD9361_BBPLL_FREQ_Hz_t& calc_obj);
void calc_max_AD9361_BBPLL_FREQ_Hz(//double AD9361_BBPLL_input_F_REF,
				   calc_AD9361_BBPLL_FREQ_Hz_t& calc_obj);
const char* regs_calc_AD9361_BBPLL_FREQ_Hz(calc_AD9361_BBPLL_FREQ_Hz_t& calc_obj,
					   const regs_calc_AD9361_BBPLL_FREQ_Hz_t& regs);
typedef regs_clock_bbpll_t regs_calc_AD9361_BBPLL_Divider_t;

struct calc_AD9361_BBPLL_Divider_t {
  typedef uint8_t BBPLL_Divider_t;
  BBPLL_Divider_t BBPLL_Divider;
};

void get_min_AD9361_BBPLL_Divider(calc_AD9361_BBPLL_Divider_t& calc_obj);
void get_max_AD9361_BBPLL_Divider(calc_AD9361_BBPLL_Divider_t& calc_obj);
const char* regs_calc_AD9361_BBPLL_Divider(calc_AD9361_BBPLL_Divider_t& calc_obj,
					   const regs_calc_AD9361_BBPLL_Divider_t& regs);

#endif // _CALC_AD9361_BBPLL_H
