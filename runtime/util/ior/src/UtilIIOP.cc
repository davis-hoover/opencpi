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

#include <string>
#include <cstring>
#include <vector>

#include "OsAssert.hh"
#include "UtilCDR.hh"
#include "UtilIOP.hh"
#include "UtilIIOP.hh"

/*
 * ----------------------------------------------------------------------
 * IIOP::ProfileBody
 * ----------------------------------------------------------------------
 */

OCPI::Util::IIOP::ProfileBody::
ProfileBody ()

{
}

OCPI::Util::IIOP::ProfileBody::
ProfileBody (const std::string & data)

{
  decode (data);
}

OCPI::Util::IIOP::ProfileBody::
ProfileBody (const ProfileBody & other)

  : iiop_version (other.iiop_version),
    host (other.host),
    port (other.port),
    object_key (other.object_key),
    components (other.components)
{
}

OCPI::Util::IIOP::ProfileBody &
OCPI::Util::IIOP::ProfileBody::
operator= (const ProfileBody & other)

{
  iiop_version = other.iiop_version;
  host = other.host;
  port = other.port;
  object_key = other.object_key;
  components = other.components;
  return *this;
}

void
OCPI::Util::IIOP::ProfileBody::
decode (const std::string & data)

{
  try {
    OCPI::Util::CDR::Decoder cd (data);

    bool bo;
    cd.getBoolean (bo);
    cd.byteorder (bo);

    cd.getOctet (iiop_version.major);
    cd.getOctet (iiop_version.minor);

    if (iiop_version.major != 1 ||
        iiop_version.minor > 3) {
      throw std::string ("unknown IIOP version");
    }

    cd.getString (host);
    cd.getUShort (port);
    cd.getOctetSeq (object_key);

    if (iiop_version.minor >= 1) {
      OCPI::OS::uint32_t numComps;
      cd.getULong (numComps);

      if (numComps*8 > cd.remainingData()) {
        throw OCPI::Util::CDR::Decoder::InvalidData();
      }

      components.resize (numComps);
      
      for (OCPI::OS::uint32_t pi=0; pi<numComps; pi++) {
        cd.getULong (components[pi].tag);
        cd.getOctetSeq (components[pi].component_data);
      }
    }
    else {
      components.clear ();
    }
  }
  catch (const OCPI::Util::CDR::Decoder::InvalidData &) {
    iiop_version.major = iiop_version.minor = 0;
    host = object_key = "";
    port = 0;
    components.clear ();
    throw std::string ("invalid data");
  }
}

std::string
OCPI::Util::IIOP::ProfileBody::
encode () const

{
  if (iiop_version.major != 1 ||
      iiop_version.minor > 3) {
    throw std::string ("unknown IIOP version");
  }

  OCPI::Util::CDR::Encoder ce;

  bool bo = OCPI::Util::CDR::nativeByteorder ();
  ce.putBoolean (bo);

  ce.putOctet (iiop_version.major);
  ce.putOctet (iiop_version.minor);

  ce.putString (host);
  ce.putUShort (port);
  ce.putOctetSeq (object_key);

  if (iiop_version.minor >= 1) {
    size_t numComps = components.size ();
    ce.putULong ((uint32_t)numComps);

    for (unsigned long pi=0; pi<numComps; pi++) {
      ce.putULong (components[pi].tag);
      ce.putOctetSeq (components[pi].component_data);
    }
  }

  return ce.data ();
}

void
OCPI::Util::IIOP::ProfileBody::
addComponent (OCPI::Util::IOP::ComponentId tag, const void * data, unsigned long len)

{
  unsigned long numComps = components.size ();
  components.resize (numComps+1);
  components[numComps].tag = tag;
  components[numComps].component_data.assign (reinterpret_cast<const char *> (data), len);
}

void
OCPI::Util::IIOP::ProfileBody::
addComponent (OCPI::Util::IOP::ComponentId tag, const std::string & data)

{
  addComponent (tag, data.data(), data.length());
}

bool
OCPI::Util::IIOP::ProfileBody::
hasComponent (OCPI::Util::IOP::ComponentId tag)

{
  unsigned long numComps = components.size ();

  for (unsigned long pi=0; pi<numComps; pi++) {
    if (components[pi].tag == tag) {
      return true;
    }
  }

  return false;
}

std::string &
OCPI::Util::IIOP::ProfileBody::
componentData (OCPI::Util::IOP::ComponentId tag)

{
  unsigned long numComps = components.size ();
  unsigned long pi;

  for (pi=0; pi<numComps; pi++) {
    if (components[pi].tag == tag) {
      break;
    }
  }

  if (pi >= numComps) {
    throw std::string ("tag not found");
  }

  return components[pi].component_data;
}

const std::string &
OCPI::Util::IIOP::ProfileBody::
componentData (OCPI::Util::IOP::ComponentId tag) const

{
  unsigned long numComps = components.size ();
  unsigned long pi;

  for (pi=0; pi<numComps; pi++) {
    if (components[pi].tag == tag) {
      break;
    }
  }

  if (pi >= numComps) {
    throw std::string ("tag not found");
  }

  return components[pi].component_data;
}

unsigned long
OCPI::Util::IIOP::ProfileBody::
numComponents () const

{
  return components.size ();
}

OCPI::Util::IOP::TaggedComponent &
OCPI::Util::IIOP::ProfileBody::
getComponent (unsigned long idx)

{
  if (idx >= components.size()) {
    throw std::string ("invalid index");
  }

  return components[idx];
}

const OCPI::Util::IOP::TaggedComponent &
OCPI::Util::IIOP::ProfileBody::
getComponent (unsigned long idx) const

{
  if (idx >= components.size()) {
    throw std::string ("invalid index");
  }

  return components[idx];
}
