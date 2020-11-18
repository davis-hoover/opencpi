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

#ifndef _READ_AD9361_H
#define _READ_AD9361_H

/*! @file
 *  @brief Provides functions for reading values from an AD9361 IC.
 ******************************************************************************/

extern "C" {
#include "ad9361.h" // ad9361_rf_phy
}
const char
  *get_ad9361_rx_sampl_freq_hz(const struct ad9361_rf_phy *phy,
			       double reference_clock_rate_Hz, double &val),
  *get_ad9361_tx_sampl_freq_hz(const struct ad9361_rf_phy *phy,
			       double reference_clock_rate_Hz, double &val),
  *get_ad9361_rx_rfpll_lo_freq_hz(const struct ad9361_rf_phy *phy,
				  double reference_clock_rate_Hz, double &val),
  *get_ad9361_tx_rfpll_lo_freq_hz(const struct ad9361_rf_phy *phy,
				  double AD9361_reference_clock_rate_Hz, double &val);
#endif // _READ_AD9361_H
