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

#ifndef _READERS_AD9361_BBPLL_H
#define _READERS_AD9361_BBPLL_H

/*! @file readers_ad9361_bbpll.h
 *  @brief Provides functions for reading in-situ BaseBand Phase-Locked
 *         Loop (BBPLL) values from an operating AD9361 IC using an OpenCPI
 *         application.
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

#include <cstdint>    // uint8_t, uint32_t types
#include <string>     // std::string
#include "OcpiApi.hh" // OCPI::API namespace
#include "ad9361.h"   // BBPLL_MODULUS macro
#include "worker_prop_parsers_ad9361_config_proxy.h" // parse()

namespace OA = OCPI::API;

/*! @brief Get the nominal in-situ value with No-OS precision
 *         of the
 *         AD9361 BaseBand input F_REF clock frequency in Hz
 *         from an operating AD9361 IC controlled by the specified OpenCPI
 *         application instance of the ad9361_config_proxy.rcc worker.
 *
 *  @param[in]  app                 OpenCPI application reference
 *  @param[in]  app_inst_name_proxy OpenCPI application instance name of the
 *                                  OpenCPI ad9361_config_proxy.rcc worker
 *  @param[out] val                 Retrieved value.
 ******************************************************************************/
void get_AD9361_BBPLL_input_F_REF(
    OCPI::API::Application& app, const char* app_inst_name_proxy,
    OA::ULong& val)
{
  std::string vstr;
  app.getProperty(app_inst_name_proxy, "ad9361_rf_phy", vstr);

  struct ad9361_config_proxy_ad9361_rf_phy ad9361_rf_phy;

  parse(vstr.c_str(), ad9361_rf_phy);

  val = ad9361_rf_phy.clk_refin.rate;
}

void get_AD9361_BBPLL_ref_scaler(
    OCPI::API::Application& app, const char* app_inst_name_proxy,
    OA::Float& val)
{
  OCPI::API::Property p(app, app_inst_name_proxy, "BBPLL_Ref_Clock_Scaler");
  val = p.getFloatValue();
}

void get_AD9361_BBPLL_N_Integer(
    OCPI::API::Application& app, const char* app_inst_name_proxy,
    OA::UShort& val)
{
  OCPI::API::Property p(app, app_inst_name_proxy, "Integer_BB_Frequency_Word");
  val = p.getUShortValue();
}

void get_AD9361_BBPLL_N_Integer_step(
    double& val)
{
  val = 1.;
}

void get_AD9361_BBPLL_N_Fractional(
    OCPI::API::Application& app, const char* app_inst_name_proxy,
    OA::ULong& val)
{
  const char* inst = app_inst_name_proxy;
  OCPI::API::Property p(app, inst, "Fractional_BB_Frequency_Word");
  val = p.getULongValue();
}

void get_AD9361_BBPLL_N_Fractional_step(double& val)
{
  val = 1.;
}

/*! @brief Get the nominal in-situ value with exact precision
 *         of the
 *         BaseBand PLL frequency in Hz
 *         from an operating AD9361 IC controlled by the specified OpenCPI
 *         application instance of the ad9361_config_proxy.rcc worker.
 *
 *  @param[in]  app                 OpenCPI application reference
 *  @param[in]  app_inst_name_proxy OpenCPI application instance name of the
 *                                  OpenCPI ad9361_config_proxy.rcc worker
 *  @param[out] val                 Retrieved value.
 ******************************************************************************/
void get_AD9361_BBPLL_FREQ_Hz(
    OCPI::API::Application& app, const char* app_inst_name_proxy,
    double& val)
{
  double d_input_F_REF;
  double d_ref_scaler;
  double d_N_Integer;
  double d_N_Fractional;

  { // restrict scope so we don't accidentally use non-double values
    // for later calculation
    OA::ULong  input_F_REF;
    OA::Float  ref_scaler;
    OA::UShort N_Integer;
    OA::ULong  N_Fractional;

    const char* inst = app_inst_name_proxy;
    get_AD9361_BBPLL_input_F_REF( app, inst, input_F_REF );
    get_AD9361_BBPLL_ref_scaler(  app, inst, ref_scaler  );
    get_AD9361_BBPLL_N_Integer(   app, inst, N_Integer   );
    get_AD9361_BBPLL_N_Fractional(app, inst, N_Fractional);

    d_input_F_REF  = (double) input_F_REF;
    d_ref_scaler   = (double) ref_scaler;
    d_N_Integer    = (double) N_Integer;
    d_N_Fractional = (double) N_Fractional;
  }

  // see "BBPLL_freq formula" for explanation of the following;
  double x = d_input_F_REF * d_ref_scaler;
  x *= (d_N_Integer+(d_N_Fractional/BBPLL_MODULUS));
  val = x;

  //log_debug("BBPLL input_F_REF= %.15f", d_input_F_REF);
  //log_debug("BBPLL ref_scaler = %.15f", d_ref_scaler);
  //log_debug("BBPLL N_Integer= %.15f", d_N_Integer);
  //log_debug("BBPLL N_Fractional= %.15f", d_N_Fractional);
  //log_debug("calculated BBPLL frequency = %.15f Hz", val);
}

/*! @brief Get the nominal in-situ value with double floating point precision
 *         of the
 *         AD9361 Baseband PLL frequency step size above or below the current
 *         PLL frequency in Hz
 *         from an operating AD9361 IC controlled by the specified OpenCPI
 *         application instance of the ad9361_config_proxy.rcc worker.
 *
 *  @param[in]  app                 OpenCPI application reference
 *  @param[in]  app_inst_name_proxy OpenCPI application instance name of the
 *                                  OpenCPI ad9361_config_proxy.rcc worker
 *  @param[out] val                 Retrieved value.
 ******************************************************************************/
void get_AD9361_BBPLL_FREQ_step_Hz(
    OCPI::API::Application& app, const char* app_inst_name_proxy,
    double& val)
{
  double d_input_F_REF;
  double d_ref_scaler;
  double d_N_Integer_step;
  double d_N_Fractional_step;

  { // restrict scope so we don't accidentally use non-double values
    // for later calculation
    OA::ULong  input_F_REF;
    OA::Float  ref_scaler;
    double     N_Integer_step;
    double     N_Fractional_step;

    const char* inst = app_inst_name_proxy;
    get_AD9361_BBPLL_input_F_REF(      app, inst, input_F_REF      );
    get_AD9361_BBPLL_ref_scaler(       app, inst, ref_scaler       );
    get_AD9361_BBPLL_N_Integer_step(              N_Integer_step   );
    get_AD9361_BBPLL_N_Fractional_step(           N_Fractional_step);

    d_input_F_REF       = (double) input_F_REF;
    d_ref_scaler        = (double) ref_scaler;
    d_N_Integer_step    = (double) N_Integer_step;
    d_N_Fractional_step = (double) N_Fractional_step;
  }

  double x = d_input_F_REF * d_ref_scaler;
  x *= (d_N_Integer_step+(d_N_Fractional_step/BBPLL_MODULUS));
  val = x;
}

/*! @brief Get the nominal in-situ value of the AD9361 BaseBand PLL divider
 *         using OpenCPI.
 *
 *  @param[in]  app                 OpenCPI application reference
 *  @param[in]  app_inst_name_proxy OpenCPI application instance name of the
 *                                  OpenCPI ad9361_config_proxy.rcc worker
 *  @param[out] val                 Retrieved value.
 ******************************************************************************/
void get_AD9361_BBPLL_Divider(
    OCPI::API::Application& app, const char* app_inst_name_proxy,
    uint8_t& val)
{
  std::string enum_str;
  app.getProperty(app_inst_name_proxy, "BBPLL_Divider", enum_str);
  if(     enum_str == "1") { val = 1; }
  else if(enum_str == "2") { val = 2; }
  else if(enum_str == "3") { val = 3; }
  else if(enum_str == "4") { val = 4; }
  else if(enum_str == "5") { val = 5; }
  else if(enum_str == "6") { val = 6; }
  else
  {
    std::string err;
    err = "Invalid value read for ad9361_config_proxy.rcc ";
    err += "BBPLL_Divider property: " + enum_str;
    throw err;
  }
}

#endif //_READERS_AD9361_BBPLL_H
