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

#include <stdint.h>
#include <map>
#include "UtilMisc.hh"
#include "UtilEzxml.hh"
#include "assembly.hh"
#include "hdl.hh"
#include "hdl-platform.hh"

HdlPlatform *HdlPlatform::
create(ezxml_t xml, const char *xfile, const std::string &parentFile, Worker *parent, const char *&err) {
  err = NULL;
  HdlPlatform *p = new HdlPlatform(xml, xfile, parentFile, parent, err);
  if (err) {
    delete p;
    return NULL;
  }
  return p;
}

HdlPlatform::
HdlPlatform(ezxml_t xml, const char *xfile, const std::string &parentFile, Worker *parent, const char *&err)
  : HdlDevice(xml, xfile, parentFile, parent, Worker::Platform, NULL, err), Board(m_sigmap, m_signals),
    ::Device(*this, *this, cname(), xml, true, 0, NULL, err),
    m_control(false) {
  m_isDevice = true;
  // Platforms are overloaded:  they are a device worker, but they also are a device *on* that platform.
  if (err ||
      (err = OE::checkAttrs(xml, HDL_PLATFORM_ATTRS, (void*)0)) ||
      (err = OE::checkElements(xml, HDL_PLATFORM_ELEMS, (void*)0)) ||
      (err = parseDevices(xml, NULL, xfile, this)))
    return;
  unsigned n = 0;
  for (ezxml_t xs = ezxml_cchild(xml, "slot"); xs; xs = ezxml_cnext(xs), n++) {
    const char *type = ezxml_cattr(xs, "type");
    unsigned ordinal = 0, count = 0;
    for (ezxml_t x = ezxml_cchild(xml, "slot"); x; x = ezxml_cnext(x)) {
      const char *otype = ezxml_cattr(x, "type");
      if (!strcasecmp(type, otype)) {
	if (x == xs)
	  ordinal = count;
	count++;
      }
    }
    // First, figure out how many there are of the same type
    Slot *s = Slot::create(xs, OE::ezxml_tag(xml), m_slots, ordinal, count, n, err);
    if (!s)
      return;
  }
}

HdlPlatform::
~HdlPlatform() {
  while (m_devices.size()) {
    ::Device *d = m_devices.front();
    m_devices.pop_front();
    delete d;
  }
}

Slot *HdlPlatform::
findSlot(const char *a_name, const char *&err) const {
  return Slot::find(a_name, m_slots, err);
}
