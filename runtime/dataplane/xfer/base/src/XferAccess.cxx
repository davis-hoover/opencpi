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

#include <inttypes.h>
#include "OsAssert.hh"
#include "OsMisc.hh"
#include "OcpiUtilMisc.h"
#include "XferAccess.h"

namespace DataTransfer {
namespace OU = OCPI::Util;

Access::
Access(volatile uint8_t *a_registers,  Accessor *accessor, RegisterOffset base)
  : m_accessor(NULL), m_child(false) {
  setAccess(a_registers, accessor, base); //, buffers);
}
// Take the content and ownership away from the other access structure
Access::
Access(Access &other) : m_accessor(NULL), m_child(false) {
  setAccess(other.m_registers, other.m_accessor); //, other.m_base);
}

Access::
~Access() {
  //      delete m_accessor;
}

void Access::
setAccess(volatile uint8_t *a_registers,  Accessor *accessor,
	  RegisterOffset base, bool child) {
  if (!m_child)
    delete m_accessor;
  m_child = child;
  m_registers = a_registers;
  m_accessor = accessor;
  m_base = OCPI_UTRUNCATE(DtOsDataTypes::Offset, base);
  //      m_buffers = buffers;
}

void Access::
closeAccess() {
  //      delete m_accessor;
  m_accessor = NULL;
}

void Access::
offsetRegisters(Access &offsettee, size_t offset) const {
  offsettee.setAccess(m_registers ? m_registers + offset : 0,
		      m_accessor,
		      m_base + offset, true);
}

static inline bool null64(uint64_t v, bool string) {
  if (string)
    for (unsigned n = sizeof(v); n; n--, v >>= 8)
      if ((v & 0xff) == 0)
	return true;
  return false;
}
static inline bool null32(uint32_t v, bool string) {
  if (string)
    for (unsigned n = sizeof(v); n; n--, v >>= 8)
      if ((v & 0xff) == 0)
	return true;
  return false;
}
static inline bool null16(uint16_t v, bool string) {
  if (string)
    for (unsigned n = sizeof(v); n; n--, v = (uint16_t)(v >> 8))
      if ((v & 0xff) == 0)
	return true;
  return false;
}

void Access::
getBytes(RegisterOffset offset, uint8_t *to8, size_t bytes, size_t elementBytes,
	 bool string) const {
  volatile uint8_t *from8 = m_registers + offset;
  if (elementBytes >= 4 && bytes >= 8 && !(((uintptr_t)to8 | offset) & 7)) {
    uint64_t *to64 = (uint64_t *)to8;
    volatile uint64_t *from64 = (uint64_t *)from8;
    do
      if (null64(*to64++ = *from64++, string))
	return;
    while ((bytes -= 8) >= 8);
    to8 = (uint8_t*)to64;
    from8 = (uint8_t *)from64;
  }
  if (elementBytes >= 4 && bytes >= 4 && !(((uintptr_t)to8 | offset) & 3)) {
    uint32_t *to32 = (uint32_t *)to8;
    volatile uint32_t *from32 = (uint32_t *)from8;
    do
      if (null32(*to32++ = *from32++, string))
	return;
    while ((bytes -= 4) >= 4);
    to8 = (uint8_t*)to32;
    from8 = (uint8_t *)from32;
  }
  if (elementBytes >= 2 && bytes >= 2 && !(((uintptr_t)to8 | offset) & 1)) {
    uint16_t *to16 = (uint16_t *)to8;
    volatile uint16_t *from16 = (uint16_t *)from8;
    do
      if (null16(*to16++ = *from16++, string))
	return;
    while ((bytes -= 2) >= 2);
    to8 = (uint8_t*)to16;
    from8 = (uint8_t *)from16;
  }
  while (bytes)
    *to8++ = *from8++, bytes--;
}
    
void Access::
setBytes(RegisterOffset offset, const uint8_t *from8, size_t bytes, size_t elementBytes) const {
  volatile uint8_t *to8 = m_registers + offset;
  ocpiDebug("setBytes %p off %" PRIx64 " from %p to %p bytes %zx elementBytes %zx",
	    this, (uint64_t)offset, from8, to8, bytes, elementBytes);
  if (elementBytes >= 4 && bytes >= 8 && !(((uintptr_t)from8 | offset) & 7)) {
    ocpiDebug("setBytes 64 bits: %zx", bytes);
    uint64_t *from64 = (uint64_t *)from8;
    volatile uint64_t *to64 = (uint64_t *)to8;
    do {
      *to64++ = *from64++;
    } while ((bytes -= 8) >= 8);
    to8 = (uint8_t*)to64;
    from8 = (uint8_t *)from64;
  }
  if (elementBytes >= 4 && bytes >= 4 && !(((uintptr_t)from8 | offset) & 3)) {
    ocpiDebug("setBytes 32 bits: %zx", bytes);
    uint32_t *from32 = (uint32_t *)from8;
    volatile uint32_t *to32 = (uint32_t *)to8;
    do
      *to32++ = *from32++;
    while ((bytes -= 4) >= 4);
    to8 = (uint8_t*)to32;
    from8 = (uint8_t *)from32;
  }
  if (elementBytes >= 2 && bytes >= 2 && !(((uintptr_t)from8 | offset) & 1)) {
    ocpiDebug("setBytes 16 bits: %zx", bytes);
    uint16_t *from16 = (uint16_t *)from8;
    volatile uint16_t *to16 = (uint16_t *)to8;
    do {
      //	  ocpiDebug("setBytes 16 bits before : %zx offset %zx val %x", bytes, to8 - (m_registers + offset), *to16);
      *to16 = *from16++;
      //	  ocpiDebug("setBytes 16 bits after  : %zx offset %zx val %x", bytes, to8 - (m_registers + offset), *to16);
      to16++;
    } while ((bytes -= 2) >= 2);
    to8 = (uint8_t*)to16;
    from8 = (uint8_t *)from16;
  }
  if (bytes)
    ocpiDebug("setBytes 8 bits: %zx", bytes);
  while (bytes)
    *to8++ = *from8++, bytes--;
}

}
