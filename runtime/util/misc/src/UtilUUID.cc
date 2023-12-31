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

#include <ctime>
#include <cstdlib>
#include "OsMisc.hh"
#include "UtilUUID.hh"

OCPI::Util::UUID::BinaryUUID
OCPI::Util::UUID::produceRandomUUID ()

{
  static bool isSeeded = false;
  BinaryUUID value;

  /*
   * No mutex needed because it doesn't matter if the seed is initialized
   * more than once.
   */

  if (!isSeeded) {
    unsigned int now = static_cast<unsigned int> (std::time (0));
    unsigned int pid = static_cast<unsigned int> (OCPI::OS::getProcessId ());
    unsigned int tid = static_cast<unsigned int> (OCPI::OS::getThreadId ());
    unsigned int seed = now % pid % tid;
    std::srand (seed);
    isSeeded = true;
  }

  for (unsigned int i=0; i<16; i++) {
    /*
     * The manual page for rand() suggests to ignore the lower-order bits
     * but to use the higher-order bits instead.
     *
     * ISO C says that RAND_MAX shall be at least 32767, so we use bits
     * 7-14.
     */

    value.data[i] = static_cast<unsigned char> (rand() >> 7);
  }

  /*
   * X.667, clause 15.1:
   *
   * - Set the two most significant bits (bits 7 and 6) of the
   *   "VariantAndClockSeqHigh" field to 1 and 0, respectively.
   * - Set the four most significant bits (bits 15 through 12)
   *   of the "VersionAndTimeHigh" field to the four-bit version
   *   number specified in 12.2.
   *
   * Clause 12.2 says to use the value 4 for random-number-based
   * UUIDs.
   */

  value.data[6] = (uint8_t)((value.data[6] & 0x0f) | 0x40);
  value.data[8] = (uint8_t)((value.data[8] & 0x3f) | 0x80);
  return value;
}

std::string
OCPI::Util::UUID::binaryToHex (const BinaryUUID &uuid)

{
  static const char * hexDigits = "0123456789abcdef";
  char tmp[36];
  char *ptr=tmp;

  for (unsigned int i=0; i<16; i++) {
    *ptr++ = hexDigits[uuid.data[i] >> 4];
    *ptr++ = hexDigits[uuid.data[i] & 15];

    if (i == 3 || i == 5 || i == 7 || i == 9) {
      *ptr++ = '-';
    }
  }

  return std::string (tmp, 36);
}
