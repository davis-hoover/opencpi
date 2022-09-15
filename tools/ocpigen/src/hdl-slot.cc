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

#include "cdkutils.hh"
#include "hdl-slot.hh"

SlotTypes SlotType::s_slotTypes;

SlotType::
SlotType(const char *file, const std::string &parent, const char *&err) {
  ezxml_t xml;
  std::string xfile;
  err = NULL;
  if ((err = parseFile(file, parent, "slottype", &xml, xfile))) {
    size_t len = strlen(file);
    if (len > 5 && !strcasecmp(file + len - 5, "-slot"))
      return;
    std::string slot(file);
    slot += "-slot";
    if ((err = parseFile(slot.c_str(), parent, "slot", &xml, xfile)))
      return;
  }
  if ((err = Signal::parseSignals(xml, parent, m_signals, m_sigmap, NULL)))
    return;
  OE::getOptionalString(xml, m_name, "name");
  char *cp = strdup(xfile.c_str());
  char *slash = strrchr(cp, '/');
  if (slash)
    slash++;
  else
    slash = cp;
  char *dot = strchr(slash, '.');
  if (dot)
    *dot = '\0';
  if (m_name.empty())
    m_name = slash;
  else if (m_name != slash)
    err = OU::esprintf("File name (%s) does not match name attribute in XML (%s)",
		       xfile.c_str(), m_name.c_str());
  free(cp);
}

SlotType::
~SlotType() {
  Signal::deleteSignals(m_signals);
}

// Slot types are interned (only created when not already there)
// They are not inlined or included, but simply referenced by attributes.
SlotType *SlotType::
get(const char *name, const char *parent, const char *&err) {
  SlotType *st = find(name);
  if (!st) {
    st = new SlotType(name, parent, err);
    if (err) {
      delete st;
      st = NULL;
    } else
      s_slotTypes[st->m_name.c_str()] = st;
  }
  return st;
}

SlotType *SlotType::
find(const char *name) {
  SlotTypesIter sti = s_slotTypes.find(name);
  return sti == s_slotTypes.end() ? NULL : sti->second;
}

#if 0
// static
SlotType * SlotType::
find(const std::string &type, const char *&err) {
  SlotTypesIter ti = s_slotTypes.find(type.c_str());
  if (ti == s_slotTypes.end()) {
    err = OU::esprintf("Card '%s' refers to slot type '%s' that is not on this platform",
		       name.c_str(), type.c_str());
    return NULL;
  }
  return *ti->second;
}
#endif

// A slot may have a default mapping to the external platform's signals,
// ie. <slot-name>_signal.
Slot::
Slot(ezxml_t xml, const char */*parent*/, const std::string &name, const SlotType &a_type,
     unsigned ordinal, const char *&err)
  : m_name(name), m_type(a_type), m_ordinal(ordinal)
{
  err = NULL;
  std::string defPrefix(name + "_");
  OE::getOptionalString(xml, m_prefix, "prefix", defPrefix.c_str());
  // process non-default signals: slot=pfsig, platform=dddd
  for (ezxml_t xs = ezxml_cchild(xml, "Signal"); xs && !err; xs = ezxml_cnext(xs)) {
    std::string slot, platform;
    if ((err = OE::getRequiredString(xs, slot, "slot")) ||
	(err = OE::getRequiredString(xs, platform, "platform")))
      break;
    const Signal *s = m_type.m_sigmap.findSignal(slot);
    if (!s)
      err = OU::esprintf("Slot signal '%s' does not exist for slot type '%s'",
			 slot.c_str(), m_type.m_name.c_str());
    else if (m_signals.find(s) != m_signals.end())
      err = OU::esprintf("Duplicate slot signal: %s", slot.c_str());
    else
      m_signals[s] = platform;
  }
  if (err)
    err = OU::esprintf("Error for slot '%s': %s", m_name.c_str(), err);
}

Slot::
~Slot() {
}

// Slots are not interned, and we want the type to be a reference.
// Hence we check the type first.
Slot *Slot::
create(ezxml_t xml, const char *parent, Slots &slots, unsigned typeOrdinal,
       unsigned typeTotal, unsigned ordinal, const char *&err) {
  std::string type;
  SlotType *t;
  if ((err = OE::getRequiredString(xml, type, "type")) ||
      !(t = SlotType::get(type.c_str(), OE::ezxml_tag(xml), err)))
    return NULL;
  std::string name;
  if (!OE::getOptionalString(xml, name, "name")) {
    name = type;
    if (typeTotal > 1)
      OU::format(name, "%s%u", type.c_str(), typeOrdinal);
  }
  if (find(name.c_str(), slots, err)) {
    err = OU::esprintf("Duplicate slot name (%s) in '%s' element", name.c_str(), parent);
    return NULL;
  }
  Slot *s = new Slot(xml, parent, name, *t, ordinal, err);
  if (err) {
    delete s;
    return NULL;
  }
  return slots[s->m_name.c_str()] = s;
}

Slot *Slot::
find(const char *name, const Slots &slots, const char *&err) {
  SlotsIter si = slots.find(name);
  if (si == slots.end()) {
    err = OU::esprintf("There is no slot named (%s) in the platform", name);
    return NULL;
  }
  return si->second;
}
