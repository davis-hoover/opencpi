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

/*
 * Abstract:
 *   This file contains the constant definitions for the node manager.
 *
 * Revision History: 
 * 
 *    Author: John F. Miller
 *    Date: 7/2004
 *    Revision Detail: Created
 *
 */

#ifndef OCPI_DataTransport__Constants_H_
#define OCPI_DataTransport__Constants_H_

#include "XferEndPoint.hh"

namespace OCPI {

namespace Transport {

  // maximum number of transport source contributers
  const uint32_t MAX_PCONTRIBS = OCPI::Xfer::MAX_SYSTEM_SMBS;

  // Maximum number of buffers
  const uint32_t MAX_BUFFERS = 255;

  // Maximum number of transfers
  const uint32_t MAX_TRANSFERS = 8;

  // Maximum number of transfers per buffer
  const uint32_t MAX_TRANSFERS_PER_BUFFER = 4;
}
}
#endif


