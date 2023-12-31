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

#include <sstream>         // std::ostringstream
#include <cstdint>         // uin32_t, etc
#include "UtilMisc.hh"
#include "ad9361_platform.h" // regs_general_rfpll_divider_t
#include "ad9361.h"        // RFPLL_MODULUS macro (this is a ADI No-OS header)
#include "calc_ad9361_rf_tx_pll.h"

namespace OU = OCPI::Util;

const char* calc_AD9361_Tx_RFPLL_ref_divider(
    float& val,
    const regs_calc_AD9361_Tx_RFPLL_ref_divider_t& regs) {
  // see AD9361_Register_Map_Reference_Manual_UG-671.pdf Rev. 0 pg. 68
  uint8_t Ref_Divide_Config_2 = regs.ref_divide_config_2;
  uint8_t Tx_Ref_Divider_1_0 = (uint8_t)((Ref_Divide_Config_2 & 0x0c) >> 2);
  switch(Tx_Ref_Divider_1_0) {
    case        0x00: val = 1.0F;  break;
    case        0x01: val = 0.5F;  break;
    case        0x02: val = 0.25F; break;
    default: // 0x03
                      val = 2.0F;  break;
  }
  return 0;
}

const char* calc_AD9361_Tx_RFPLL_N_Integer(
    uint16_t& val,
    const regs_calc_AD9361_Tx_RFPLL_N_Integer_t& regs) {
  uint16_t integer = (uint16_t)regs.tx_synth_integer_byte_0;
  integer |= ((uint16_t)((regs.tx_synth_integer_byte_1 & 0x07)) << 8);
  val = integer;

  return 0;
}

const char* calc_AD9361_Tx_RFPLL_N_Fractional(
    uint32_t& val,
    const regs_calc_AD9361_Tx_RFPLL_N_Fractional_t& regs) {
  uint32_t frac = (uint32_t)regs.tx_synth_fract_byte_0;
  frac |= ((uint32_t)regs.tx_synth_fract_byte_1) << 8;
  frac |= ((uint32_t)(regs.tx_synth_fract_byte_2 & 0x7f)) << 16;
  val = frac;

  return 0;
}

const char* calc_AD9361_Tx_RFPLL_external_div_2_enable(
    bool& val,
    const regs_calc_AD9361_Tx_RFPLL_external_div_2_enable_t& regs) {
  uint8_t divider = (regs.general_rfpll_dividers & 0xf0) >> 4;
  if(divider <= 7) {
    val = (divider == 7);
  }
  else
    return OU::esprintf("Invalid value read for general_rfpll_dividers register 0x%x", 
			regs.general_rfpll_dividers);
  return NULL;
}

const char* calc_AD9361_Tx_RFPLL_VCO_Divider(
    uint8_t& val,
    const regs_calc_AD9361_Tx_RFPLL_VCO_Divider_t& regs) {
  uint8_t divider = (regs.general_rfpll_dividers & 0xf0) >> 4;
  switch(divider)
  {
    case 0: val = 2; break;
    case 1: val = 4; break;
    case 2: val = 8; break;
    case 3: val = 16; break;
    case 4: val = 32; break;
    case 5: val = 64; break;
    case 6: val = 128; break;
    case 7:
      return "Value requested for AD9361_Tx_RFPLL_VCO_Divider before "
	"checking if register was set to divide-by-2";
    default:
      return OU::esprintf("Invalid value read for general_rfpll_dividers register 0x%x",
			  regs.general_rfpll_dividers);
  }
  return 0;
}

/*! @brief Calculate with double floating point precision
 *         the value of the
 *             AD9361 TX RF LO frequency in Hz
 *         based on register values passed in via arguments.
 *
 *  @param[out] val                 Calculated value.
 *  @param[in]  Tx_RFPLL_input_FREF Frequency in Hz of RFPLL input clock.
 *  @param[in]  regs                Struct containing register values for
 *                                  the registers which the Tx RFPLL LO
 *                                  freq depends upon.
 *  @return 0 if there are no errors, non-zero char array pointer if there
 *          are errors (char array content will describe the error).
 ******************************************************************************/
const char* calc_AD9361_Tx_RFPLL_LO_freq_Hz(
    double& val,
    double Tx_RFPLL_input_F_REF,
    const regs_calc_AD9361_Tx_RFPLL_LO_freq_Hz_t& regs) {
  double d_Tx_RFPLL_input_F_REF;
  double d_Tx_RFPLL_ref_divider;
  double d_Tx_RFPLL_N_Integer;
  double d_Tx_RFPLL_N_Fractional;
  double d_Tx_RFPLL_VCO_Divider;

  { // restrict scope so we don't accidentally use non-double values
    // for later calculation

    bool Tx_RFPLL_external_div_2_enable = false;
    {
      bool& b = Tx_RFPLL_external_div_2_enable;
      const char* ret = calc_AD9361_Tx_RFPLL_external_div_2_enable(b, regs);
      if(ret != 0) {
        return ret;
      }
    }

    if(Tx_RFPLL_external_div_2_enable) {
      val = ((double)Tx_RFPLL_input_F_REF) / 2.;
      return 0;
    }

    float Tx_RFPLL_ref_divider;
    {
      float& f = Tx_RFPLL_ref_divider;
      const char* ret = calc_AD9361_Tx_RFPLL_ref_divider(f, regs);
      if(ret != 0) {
        return ret;
      }
    }

    uint16_t Tx_RFPLL_N_Integer;
    {
      uint16_t& u16 = Tx_RFPLL_N_Integer;
      const char* ret = calc_AD9361_Tx_RFPLL_N_Integer(u16, regs);
      if(ret != 0) {
        return ret;
      }
    }

    uint32_t Tx_RFPLL_N_Fractional;
    {
      uint32_t& u32 = Tx_RFPLL_N_Fractional;
      const char* ret = calc_AD9361_Tx_RFPLL_N_Fractional(u32, regs);
      if(ret != 0) {
        return ret;
      }
    }

    uint8_t Tx_RFPLL_VCO_Divider;
    {
      uint8_t& u8 = Tx_RFPLL_VCO_Divider;
      const char* ret = calc_AD9361_Tx_RFPLL_VCO_Divider(u8, regs);
      if(ret != 0) {
        return ret;
      }
    }

    d_Tx_RFPLL_input_F_REF  = (double) Tx_RFPLL_input_F_REF;
    d_Tx_RFPLL_ref_divider  = (double) Tx_RFPLL_ref_divider;
    d_Tx_RFPLL_N_Integer    = (double) Tx_RFPLL_N_Integer;
    d_Tx_RFPLL_N_Fractional = (double) Tx_RFPLL_N_Fractional;
    d_Tx_RFPLL_VCO_Divider  = (double) Tx_RFPLL_VCO_Divider;
  }

  //AD9361_Reference_Manual_UG-570.pdf Figure 4. PLL Synthesizer Block Diagram
  //(calculating the "FREF = 10MHz TO 80MHz" signal)
  double x = d_Tx_RFPLL_input_F_REF;
  // why multiply (*) not divide? (I suspect ADI's term "divider" is a misnomer)
  x *= d_Tx_RFPLL_ref_divider;

  //AD9361_Reference_Manual_UG-570.pdf Figure 4. PLL Synthesizer Block Diagram
  //(calculating the "TO VCO DIVIDER BLOCK" signal)
  // this calculation is similar to what's done in Analog Device's No-OS's
  // ad9361.c's ad9361_calc_rfpll_int_freq() function, except WE use floating
  // point and don't round
  x *= (d_Tx_RFPLL_N_Integer + (d_Tx_RFPLL_N_Fractional/RFPLL_MODULUS));
  //log_debug("d_Tx_RFPLL_N_Integer=%.15f", d_Tx_RFPLL_N_Integer);
  //log_debug("d_Tx_RFPLL_N_Fractional=%.15f", d_Tx_RFPLL_N_Fractional);

  //AD9361_Reference_Manual_UG-570.pdf Figure 4. VCO Divider
  //(calculating the "LO" signal which is the  output of the MUX)
  x /= d_Tx_RFPLL_VCO_Divider;
  //log_debug("d_Tx_RFPLL_VCO_Divider=%.15f", d_Tx_RFPLL_VCO_Divider);

  val = x;

  return 0;
}
