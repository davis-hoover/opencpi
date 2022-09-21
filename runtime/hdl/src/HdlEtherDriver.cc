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

#include "HdlEtherDriver.hh"

namespace OCPI {
  namespace HDL {
    namespace Ether {
      namespace OS = OCPI::OS;
      namespace OU = OCPI::Util;
      namespace OB = OCPI::Base;
      namespace OE = OCPI::OS::Ether;

      class Device
	: public OCPI::HDL::Net::Device {
	friend class Driver;
      protected:
	Device(Driver &driver, OS::Ether::Interface &ifc, std::string &a_name,
	       OE::Address &a_addr, bool discovery, bool forLoad, const OB::PValue *params,
	       std::string &error)
	  : Net::Device(driver, ifc, a_name, a_addr, discovery, forLoad, "ocpi-ether-rdma", 0,
			(uint64_t)1 << 32, ((uint64_t)1 << 32) - sizeof(OccpSpace), 0, params,
			error) {
	}
      public:
	~Device() {
	}
	// Load a bitstream via jtag
	bool load(const char *fileName, std::string &error) {
	  return loadJtag(fileName, error);
	}
	bool unload(std::string &error) {
	  return unloadJtag(error);
	}

	bool configure(ezxml_t config, std::string &err) {
	  if (!m_isAlive) {
	    // similar to code in HDL::Device::configure which relies on
	    // reading m_platform and m_part from the hardware
	    // this is necessary in the case when forLoad is set
	    // so that the load() function above finds these set
	    OU::EzXml::getOptionalString(config, m_esn, "esn");
	    OU::EzXml::getOptionalString(config, m_platform, "platform");
	    OU::EzXml::getOptionalString(config, m_part, "device");
	    OU::EzXml::getOptionalString(config, m_position, "position");
          }

	  return OCPI::HDL::Device::configure(config, err);
        }

      };
      Driver::
      ~Driver() {
      }
      Net::Device *Driver::
      createDevice(OS::Ether::Interface &ifc, OS::Ether::Address &addr, bool discovery,
		   bool forLoad, const OB::PValue *params, std::string &error) {
	std::string name("Ether:" + ifc.name + "/" + addr.pretty());
	Device *d = new Device(*this, ifc, name, addr, discovery, forLoad, params, error);
	if (error.empty())
	  return d;
	delete d;
	return NULL;
      }
    } // namespace Ether
  } // namespace HDL
} // namespace OCPI
