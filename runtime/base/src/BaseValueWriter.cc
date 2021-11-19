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

#include <assert.h>
#include <string.h>
#include "BaseValueWriter.hh"
namespace OA = OCPI::API;
namespace OCPI {
namespace Base {

// Class to "write" marshalled/serialized data into "Value" data structure.

void ValueWriter::
newItem(const Member &m) {
  if (!m_parent) {
    assert(m_n < m_nArgs);
    m_values[m_n++] = m_v = new Value(m, NULL);
  } else if (m_parent->m_vt->m_baseType == OA::OCPI_Type) {
    assert((size_t)(m_parent->m_typeNext - m_parent->m_types) < m_parent->m_nTotal);
    m_v = m_parent->m_typeNext++;
  } else if (m_parent->m_vt->m_baseType == OA::OCPI_Struct)
    m_v = new Value(m, m_parent);
  else
    assert("recursive type not struct/type"==0);
  m_v->m_nTotal = m_v->m_vt->m_nItems;
  if (m_v->m_vt->m_isSequence) {
    m_v->m_nElements = m_nElements;
    m_v->m_nTotal *= m_nElements;
  }
  m_v->allocate();
  if (m_parent && m_parent->m_vt->m_baseType == OA::OCPI_Struct) {
    StructValue sv = m_parent->m_vt->m_arrayRank || m_parent->m_vt->m_isSequence ?
      m_parent->m_pStruct[m_parent->m_next] : m_parent->m_Struct;
    sv[m.m_ordinal] = m_v;
    if (m.m_ordinal == m_parent->m_vt->m_nMembers - 1)
      m_parent->m_next++;
  }
}
ValueWriter::
ValueWriter(Value **v, size_t nArgs)
  : m_values(v), m_v(NULL), m_parent(NULL), m_nElements(0), m_n(0),
    m_nArgs(nArgs) {
}
void ValueWriter::
beginSequence(const Member &m, size_t nElements) {
  m_nElements = nElements;
  if (!nElements)
    newItem(m);
}
void ValueWriter::
beginStruct(const Member &m) {
  newItem(m);
  if (m.m_isSequence || m.m_arrayRank)
    for (unsigned n = 0; n < m_v->m_nTotal; n++)
      m_v->m_pStruct[n] = &m_v->m_struct[n * m.m_nMembers];
  else
    m_v->m_Struct = m_v->m_struct;
  m_parent = m_v;
}
void ValueWriter::
endStruct(const Member &) {
  m_parent = m_parent->m_parent;
}
void ValueWriter::
beginType(const Member &m) {
  newItem(m);
  if (m.m_isSequence || m.m_arrayRank)
    for (unsigned n = 0; n < m_v->m_nTotal; n++)
      m_v->m_pType[n] = &m_v->m_types[n];
  else
    m_v->m_Type = &m_v->m_types[0];
  m_parent = m_v;
}
void ValueWriter::
endType(const Member &) {
  m_parent = m_parent->m_parent;
}
void ValueWriter::
writeString(const Member &m, WriteDataPtr p, size_t strLen, bool start, bool /*top*/) {
  if (start)
    newItem(m);
  // We are in charge of managing string space here, which is ugly
  // FIXME: properly share this code with OCPI::Util::Value::parse()
  //        this is slightly different from add-to-sequence etc.
  // FIXME: consider using std::string for string space here if it simplifies things
  char *old = m_v->m_stringSpace;
  size_t oldLength = m_v->m_stringSpaceLength;
  // the space required will never be larger than the input...
  m_v->m_stringSpaceLength += strLen + 1;
  m_v->m_stringNext = m_v->m_stringSpace = new char[m_v->m_stringSpaceLength];
  if (old) {
    assert(m.m_isSequence || m.m_arrayDimensions);
    // Do the realloc of the string space, and adjust
    m_v->m_stringNext += oldLength;
    memcpy(m_v->m_stringSpace, old, oldLength);
    // Relocate string pointers
    for (unsigned n = 0; n < m_v->m_nElements; n++)
      m_v->m_pString[n] = m_v->m_stringSpace + (m_v->m_pString[n] - old);
  }
  (m.m_arrayRank || m.m_isSequence ? m_v->m_pString[m_v->m_next++] : m_v->m_String) = 
    m_v->m_stringNext;
  if (strLen)
    memcpy(m_v->m_stringNext, p.data, strLen);
  m_v->m_stringNext += strLen;
  *m_v->m_stringNext++ = 0;
  // autoexpand.
}
void ValueWriter::
writeData(const Member &m, WriteDataPtr p, size_t nBytes, size_t ) {
  newItem(m);
  assert(nBytes <= m_v->m_length);
  memcpy((void *)(m.m_isSequence || m.m_arrayRank ? m_v->m_pULong : &m_v->m_ULong),
	 p.data, nBytes);
}

  }
}

