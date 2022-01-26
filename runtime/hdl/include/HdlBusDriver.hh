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

#ifndef BUSDRIVER_H
#define BUSDRIVER_H
#ifndef __KERNEL__
#include <stdint.h>
#endif
#ifdef __cplusplus
#include <string>
#include "BasePValue.hh"
#include "HdlDevice.hh"


namespace OCPI {
  namespace HDL {
    namespace Zynq {
      class Device;
      class Driver {
	int m_memFd;
	friend class Device;
      protected:
	Driver();
	virtual ~Driver();
	uint8_t *map(size_t size, uint32_t offset, std::string &error);
	bool unmap(uint8_t *addr, size_t size, std::string &error);
      public:
	unsigned
	search(const OCPI::Base::PValue *props, const char **exclude, bool discoveryOnly,
	       std::string &error);
	OCPI::HDL::Device *
	open(const char *busName, bool forLoad, const OCPI::Base::PValue *params, 
	     std::string &err);
	// Callback when found
	virtual bool found(OCPI::HDL::Device &dev, const char **excludes, bool discoveryOnly,
			   std::string &error) = 0;
      };
    }
  }
}
#endif
#endif
