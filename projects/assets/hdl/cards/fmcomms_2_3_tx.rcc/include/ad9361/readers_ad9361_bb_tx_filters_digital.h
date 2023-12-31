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

#ifndef _READERS_AD9361_TX_FILTERS_DIGITAL_H
#define _READERS_AD9361_TX_FILTERS_DIGITAL_H

/*! @file
 *  @brief Provides functions for reading in-situ TX digital filter/interpolator
 *         values from an operating AD9361 IC using an OpenCPI application.
 *
 * \verbatim
 
    TX_SAMPL_FREQ..corresponds to the overall effective DAC sampling
                   rate (CLKTF_FREQ) divided by the TX FIR interpolation factor.
                   The unit is in complex samples per second.
    CLKTF_FREQ.....corresponds to the overall effective DAC sampling
                   rate in complex samples per second. (I *think* this is
                   assumed to be the TX_FB_CLK pin's clock rate, the AD9361
                   probably synchronizes at some point between the TX_FB_CLK
                   domain and the clocks derived from the DAC_FREQ clock
                   domain.)

    x1,x2,x3,x4 below refers to the multiplication of the clock rate

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
   |                                                                           |
   +---------------------------------------------------------------------------+
 
   \endverbatim
 *
 ******************************************************************************/

#include <string>     // std::string
#include <cstdint>    // uint8_t type
#include "OcpiApi.hh" // OA namespace

namespace OA = OCPI::API;

/*! @brief Get the in-situ value with exact precision of the
 *         Transmit Half-Band filter 3's interpolation factor
 *         from an operating AD9361 IC controlled by the specified OpenCPI
 *         application instance of the ad9361_config_proxy.rcc worker.
 *
 *  @param[in]  app                 OpenCPI application reference
 *  @param[in]  app_inst_name_proxy OpenCPI application instance name of the
 *                                  OpenCPI ad9361_config_proxy.rcc worker
 *  @param[out] val                 Retrieved value.
 ******************************************************************************/
void get_AD9361_THB3_interpolation_factor(
    OA::Application& app, const char* app_inst_name_proxy,
    uint8_t& val)
{
  std::string enum_str;
  app.getProperty(app_inst_name_proxy, "THB3_Enable_and_Interp", enum_str);

  if(enum_str == "Interpolate_by_1_no_filtering")
  {
    val = 1;
  }
  else if(enum_str == "Interpolate_by_2_half_band_filter")
  {
    val = 2;
  }
  else if(enum_str == "Interpolate_by_3_and_filter")
  {
    val = 3;
  }
  else
  {
    std::string err;
    err = "Invalid value read for ad9361_config_proxy.rcc ";
    err += "THB3_Enable_and_Interp property: " + enum_str;
    throw err;
  }
}

/*! @brief Get the in-situ value with exact precision of the
 *         Transmit Half-Band filter 2's interpolation factor
 *         from an operating AD9361 IC controlled by the specified OpenCPI
 *         application instance of the ad9361_config_proxy.rcc worker.
 *
 *  @param[in]  app                 OpenCPI application reference
 *  @param[in]  app_inst_name_proxy OpenCPI application instance name of the
 *                                  OpenCPI ad9361_config_proxy.rcc worker
 *  @param[out] val                 Retrieved value.
 ******************************************************************************/
void get_AD9361_THB2_interpolation_factor(
    OA::Application& app, const char* app_inst_name_proxy,
    uint8_t& val)
{
  OA::Property p(app, app_inst_name_proxy, "THB2_Enable");
  val = p.getBoolValue() ? 2 : 1;
}

/*! @brief Get the in-situ value with exact precision of the
 *         Transmit Half-Band filter 1's interpolation factor
 *         from an operating AD9361 IC controlled by the specified OpenCPI
 *         application instance of the ad9361_config_proxy.rcc worker.
 *
 *  @param[in]  app                 OpenCPI application reference
 *  @param[in]  app_inst_name_proxy OpenCPI application instance name of the
 *                                  OpenCPI ad9361_config_proxy.rcc worker
 *  @param[out] val                 Retrieved value.
 ******************************************************************************/
void get_AD9361_THB1_interpolation_factor(
    OA::Application& app, const char* app_inst_name_proxy,
    uint8_t& val)
{
  OA::Property p(app, app_inst_name_proxy, "THB1_Enable");
  val = p.getBoolValue() ? 2 : 1;
}

#endif // _READERS_AD9361_TX_FILTERS_DIGITAL_H
