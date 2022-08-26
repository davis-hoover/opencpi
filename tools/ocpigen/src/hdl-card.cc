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
#include "hdl-device.hh"
#include "hdl-card.hh"

Cards Card::s_cards;        // registry of card types

// A slot may have a default mapping to the external platform's signals,
// ie. <slot-name>_signal.
Card::
Card(ezxml_t xml, const char *name, SlotType &a_type, const char *parentFile, Worker *parent,
     const char *&err)
  : Board(a_type.m_sigmap, a_type.m_signals), m_name(name), m_type(a_type)
{
  // Initialize a card's signals from the slot type, overriding those that are 
  // mapped, and removing those that are not present on the card
  for (SignalsIter si = m_type.m_signals.begin(); si != m_type.m_signals.end(); si++) {
    std::string slot, card;
    for (ezxml_t xs = ezxml_cchild(xml, "Signal"); xs; xs = ezxml_cnext(xs)) {
      if ((err = OE::getRequiredString(xs, slot, "slot")) ||
	  (err = OE::getRequiredString(xs, card, "card")))
	return;
      if (!strcasecmp(slot.c_str(), (*si)->cname()))
	break;
    }
    if (!slot.empty() && card.empty())
      continue; // slot signal does not exist on this card
    // map from card's signal name to underlying slot type signal
    m_extmap[card.empty() ? (*si)->cname() : card.c_str()] = *si;
    m_extsignals.push_back(*si);
  }
#if 0
  // process non-default signals: slot=pfsig, platform=dddd
  for (ezxml_t xs = ezxml_cchild(xml, "Signal"); xs; xs = ezxml_cnext(xs)) {
    std::string slot, card;
    if ((err = OE::getRequiredString(xs, slot, "slot")) ||
	(err = OE::getRequiredString(xs, card, "card")))
      break;
    const Signal *s = Signal::find(m_type.m_signals, slot.c_str());
    if (!s) {
      err = OU::esprintf("Slot signal '%s' does not exist for slot type '%s'",
			 slot.c_str(), m_type.m_name.c_str());
      break;
    } else if (m_sigmap.find(s) != m_sigmap.end()) {
      err = OU::esprintf("Duplicate slot signal: %s", slot.c_str());
      break;
    } else
      m_signals[s] = card;
  }
#endif
  if (!err)
    err = parseDevices(xml, &m_type, parentFile, parent);
  if (err)
    err = OU::esprintf("Error for card '%s': %s", m_name.c_str(), err);
}

Card::
~Card() {
}

// Cards are interned, and we want the type to be a reference.
// Hence we check the type first.
Card *Card::
get(const char *file, const char *parentFile, Worker *parent, const char *&err) {
  ezxml_t xml;
  std::string xfile;
  if ((err = parseFile(file, parentFile, NULL, &xml, xfile)))
    return NULL;
  std::string name;
  OE::getOptionalString(xml, name, "name");
  std::string base;
  OU::baseName(xfile.c_str(), base);
  if (name.empty())
    name = base;
  else if (name != base)
    err = OU::esprintf("File name (%s) does not match name attribute in XML (%s)",
		       xfile.c_str(), name.c_str());
  Card *c = Card::find(name.c_str());
  if (c)
    return c;
  std::string type;
  if ((err = OE::getRequiredString(xml, type, "type"))) {
    err = OU::esprintf("%s is not a valid card (has no slot type)", file);
    return NULL;
  }
  SlotType *st = SlotType::get(type.c_str(), parentFile, err);
  if (!st)
    return NULL;
  c = new Card(xml, name.c_str(), *st, parentFile, parent, err);
  if (err) {
    delete c;
    return NULL;
  }
  return s_cards[c->m_name] = c;
}

Card *Card::
find(const char *name) {
  CardsIter si = s_cards.find(name);
  return si == s_cards.end() ? NULL : si->second;
}


