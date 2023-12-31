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

#ifndef _WRITERS_AD9361_TX_GAIN_H
#define _WRITERS_AD9361_TX_GAIN_H

/*! @file
 *  @brief Provides functions for writing in-situ Transmit (TX) gain-related
 *         values to an operating AD9361 IC using an OpenCPI application.
 ******************************************************************************/

#include "OcpiApi.hh" // OA namespace
#include "worker_prop_parsers_ad9361_config_proxy.h" // parse()

namespace OA = OCPI::API;

/*! @brief Set the nominal in-situ value with exact precision
 *         of the
 *         Tx attenuation for the TX1 channel in mdB
 *         to an operating AD9361 IC controlled by the specified OpenCPI
 *         application instance of the ad9361_config_proxy.rcc worker.
 *
 *  @param[in]  app                 OpenCPI application reference
 *  @param[in]  app_inst_name_proxy OpenCPI application instance name of the
 *                                  OpenCPI ad9361_config_proxy.rcc worker
 *  @param[in]  val                 Value to assign.
 ******************************************************************************/
void set_AD9361_tx_attenuation_TX1_mdB(
    OA::Application& app, const char* app_inst_name_proxy,
    const OA::ULong& val)
{
  std::string vstr;
  app.getProperty(app_inst_name_proxy, "tx_attenuation", vstr);

  ad9361_config_proxy_tx_attenuation_t tx_attenuation;

  parse(vstr.c_str(), tx_attenuation);

  //!@ todo TODO/FIXME - I don't think the below line is correct
  tx_attenuation[0] = val; // 0 corresponds to TX1

  std::string tx_attenuation_str = to_string(tx_attenuation);
  app.setProperty(app_inst_name_proxy, "tx_attenuation", tx_attenuation_str.c_str());
}

/*! @brief Set the nominal in-situ value with exact precision
 *         of the
 *         Tx attenuation for the TX2 channel in mdB
 *         to an operating AD9361 IC controlled by the specified OpenCPI
 *         application instance of the ad9361_config_proxy.rcc worker.
 *
 *  @param[in]  app                 OpenCPI application reference
 *  @param[in]  app_inst_name_proxy OpenCPI application instance name of the
 *                                  OpenCPI ad9361_config_proxy.rcc worker
 *  @param[in]  val                 Value to assign.
 ******************************************************************************/
void set_AD9361_tx_attenuation_TX2_mdB(
    OA::Application& app, const char* app_inst_name_proxy,
    const OA::ULong& val)
{
  std::string vstr;
  app.getProperty(app_inst_name_proxy, "tx_attenuation", vstr);

  ad9361_config_proxy_tx_attenuation_t tx_attenuation;

  parse(vstr.c_str(), tx_attenuation);

  //!@ todo TODO/FIXME - I don't think the below line is correct
  tx_attenuation[1] = val; // 1 corresponds to TX2

  std::string tx_attenuation_str = to_string(tx_attenuation);
  app.setProperty(app_inst_name_proxy, "tx_attenuation", tx_attenuation_str.c_str());
}

#endif // _WRITERS_AD9361_TX_GAIN_H
