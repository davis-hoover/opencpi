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
 *   This file contains the implementation for the Message based transfer driver
 *   base classes.
 *
 * Revision History:

   09/4/11 - John Miller
   Initial version.

 *
 *
 */

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ezxml.h>
#include "OsAssert.hh"
#include "OsMisc.hh"
#include "UtilAutoMutex.hh"
#include "UtilEzxml.hh"
#include "BasePValue.hh"
#include "TransportMsgDriver.hh"

namespace OX = OCPI::Util::EzXml;
namespace OU = OCPI::Util;
namespace OB = OCPI::Base;
namespace OS = OCPI::OS;
namespace OP = OCPI::Base::Plugin;
namespace OCPI {
namespace Msg {
  const char *msg_transfer="ocpi_msg_tx";

// These defaults are pre-configuration
FactoryConfig::
FactoryConfig(uint32_t retryCount)
  : m_retryCount(8)
{
  if (retryCount)
    m_retryCount = retryCount;
}

// Parse and default from parent
void 
FactoryConfig::
parse(FactoryConfig *parent, ezxml_t x) {
  if (parent)
    *this = *parent;
  m_xml = x;
  if (x) {
    const char *err;
    // Note we are not writing defaults here because they are set
    // in the constructor, and they need to be set even when there is no xml
    if ((err = OX::checkAttrs(x, "TxRetryCount", NULL)) ||
	(err = OX::getNumber(x, "TxRetryCount", &m_retryCount, NULL, 0, false)))
      throw err; // FIXME configuration api error exception class
  }
}


// Configure this manager.  The drivers will be configured by the base class
void 
XferFactoryManager::
configure( ezxml_t x)
{
  if (!m_configured) {
    m_configured = true;
    parse(NULL, x);

    /*
    // Allow the environment to override config files here
    const char* env = getenv("OCPI_SMB_SIZE");
    if ( env && OX::getUNum(env, &m_SMBSize))
      throw "Invalid OCPI_SMB_SIZE value";
    */

    // Now configure the drivers
    OP::Manager::configure(x);

  }
}

XferFactory* 
XferFactoryManager::
findFactory(const char* url,
	    const OB::PValue *our_props,
	    const OB::PValue *other_props) {
  parent().configure();
  OU::AutoMutex guard ( m_mutex, true );
  for (XferFactory* d = firstDriver(); d; d = d->nextDriver())
    if (d->supportsTx(url,our_props,other_props))
      return d;
  return NULL;

}

XferFactoryManager::
XferFactoryManager() : m_configured(false)
{

}

XferFactoryManager::
~XferFactoryManager()
{


}



XferFactory::
XferFactory(const char *a_name)
  : OP::DriverType<XferFactoryManager, XferFactory>(a_name, *this) {
}

void 
XferFactory::
configure(ezxml_t x) {
  // parse generic attributes and default from parent
  parse(&XferFactoryManager::getFactoryManager(), x);
  // base class does device config if present
  OP::Driver::configure(x); 
}


void 
Device::
configure(ezxml_t x)
{
  OP::Device::configure(x); // give the base class a chance to do generic configuration
  parse(&driverBase(), x);
}

XferFactory::
~XferFactory()
{
}
}
}
