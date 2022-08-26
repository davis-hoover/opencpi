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

#ifndef Xfer_Config_H_
#define Xfer_Config_H_

namespace OCPI {
namespace Xfer {

// This is the base class for a factory configuration sheet
// that is common to the manager, drivers, and devices
class FactoryConfig {
public:
  // These are arguments to allow different defaults
  FactoryConfig(size_t smbSize = 0, size_t retryCount = 0);
  void parse(FactoryConfig *p, ezxml_t config );
  size_t getSMBSize() const { return m_SMBSize; }
  size_t m_SMBSize;
  size_t m_retryCount;
  ezxml_t  m_xml; // the element that these attributes were parsed from
};

}
}
#endif
