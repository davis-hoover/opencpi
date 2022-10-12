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

#include <limits>
#include "OsAssert.hh"
#include "MetadataProperty.hh"
#include "UtilException.hh"
#include "BaseValue.hh"
#include "OcpiContainerApi.hh"

namespace OU = OCPI::Util;
namespace OB = OCPI::Base;
namespace OS = OCPI::OS;
namespace OCPI {
  namespace API {
    PropertyAccess::~PropertyAccess(){}
    void Property::
    checkTypeAlways(const OB::Member &m, BaseType ctype, size_t n, bool write) const {
      ocpiDebug("checkTypeAlways on %s, for %s which is %s", OB::baseTypeNames[ctype],
		m_info.cname(), OB::baseTypeNames[m_info.m_baseType]);
      const char *err = NULL;
      if (write && !m_info.m_isWritable)
	err = "trying to write a non-writable property";
      else if (write && !m_worker.beforeStart() && m_info.m_isInitial)
	err = "trying to write a an initial property after worker is started";
#if 0 // this cannot happen anymore
      else if (!write && !m_info.m_isReadable)
	err = "trying to read a non-readable property";
#endif
      else if (m.m_baseType == OCPI_Struct)
	err = "struct type used as scalar type";
      else if (ctype != m.m_baseType)
	err = "incorrect type for this property";
      else if (n && m.m_isSequence) {
	if (n % m.m_nItems)
	  err = "number of items not a multiple of array size";
	else {
	  n /= m.m_nItems;
	  if (write && n > m.m_sequenceLength)
	    err = "sequence or array too long for this property";
	  else if (!write && n < m.m_sequenceLength)
	    err = "sequence or array not large enough for this property";
	}
      } else if (n && n != m.m_nItems)
	  err = "wrong number of values for non-sequence type";
      if (err)
	throwError(err);
    }
    void Property::init() {
      m_readVaddr = NULL;
      m_writeVaddr = NULL;
      m_readSync = m_info.m_readSync;
      m_writeSync = m_info.m_writeSync;
      m_ordinal = m_info.m_ordinal;
    }
    // This is user-visible, initialized from information in the metadata
    // It is intended to be constructed on the user's stack - a cache of
    // just the items needed for fastest access
    Property::Property(const Worker &w, const char *aname) :
      m_worker(w), m_info(w.setupProperty(aname, m_writeVaddr, m_readVaddr)), m_member(m_info) {
      init();
    }
    Property::Property(const Worker &w, const std::string &aname) :
      m_worker(w), m_info(w.setupProperty(aname.c_str(), m_writeVaddr, m_readVaddr)), m_member(m_info) {
      init();
    }
    // This is a sort of side-door from the application code
    // that already knows the property ordinal
    Property::Property(const Worker &w, unsigned n) :
      m_worker(w), m_info(w.setupProperty(n, m_writeVaddr, m_readVaddr)), m_member(m_info) {
      init();
    }
    const OB::Member &Property::
    descend(AccessList &list, size_t &offset, size_t *dimensionp) const {
      const OB::Member *m;
      const char *err = m_info.descend(list, m, NULL, &offset, dimensionp);
      if (err)
	throwError(err);
      return *m;
    }
    BaseType Property::baseType() const {return m_info.m_baseType;}
    size_t Property::stringBufferLength() const {
      if (m_info.m_baseType != OCPI_String)
	throwError("cannot use stringBufferLength() on properties that are not strings");
      return m_info.m_stringLength + 1;
    }
    size_t Property::
    getSequenceLength(AccessList &list, bool uncached) const {
      size_t dimension, offset;
      const OB::Member *m;
      const OB::Value *vp; // when we are reading a default value from a parameter
      const char *err;
      if ((err = m_info.descend(list, m, m_info.m_isParameter ? &vp : NULL, &offset, &dimension)))
	throwError(err);
      if (!m->m_isSequence || dimension)
	throwError("getting sequence length from property or struct member that is not a sequence");
      if (m_info.m_isParameter)
	return vp->m_nElements;
      if (m_readVaddr && uncached) {
	if (m_readSync)
	  m_worker.propertyRead(m_ordinal);
	return *(uint32_t *)(m_readVaddr + offset);
      }
      return uncached ?
	m_worker.getSequenceLengthProperty(m_info, *m, offset) :
	m_worker.getSequenceLengthCached(m_info, *m, offset);
    }
    void Property::throwError(const char *err) const {
      throw OU::Error("Access error for property \"%s\":  %s", m_info.cname(), err);
    }

// yes, we really do want to compare floats with zero here
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wfloat-equal"
#if __GNUC__ < 4 || (__GNUC__ == 4 && (__GNUC_MINOR__ <= 7 ) )
#pragma GCC diagnostic ignored "-Wtype-limits"
#pragma GCC diagnostic ignored "-Wsign-compare"
#endif
    // This internal template method is called after all error checking is done and is not called
    // on strings, so the static_casts should not cause any unexpected results.
    template <typename val_t> void Property::
    setValueInternal(const OB::Member &m, size_t offset, const val_t val) const {
      switch (m.m_baseType) {

#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
	case OCPI_##pretty: {						\
	  ocpiDebug("setting internal: " #pretty " %u %u %u",		\
		    std::numeric_limits<run>::is_integer,		\
		    std::numeric_limits<val_t>::digits,			\
		    std::numeric_limits<run>::digits);			\
	  if (!std::numeric_limits<run>::is_integer &&			\
	      std::numeric_limits<val_t>::digits > std::numeric_limits<run>::digits) \
	    throwError("setting property will lose precision");	\
	  if (std::numeric_limits<val_t>::is_signed && !std::numeric_limits<run>::is_signed && \
	      val < 0)							\
	    throwError("setting unsigned property to negative value");	\
	  /* complicated only to avoid signed/unsigned integer comparison warnings */ \
	  if ((!std::numeric_limits<val_t>::is_signed || val >= 0) &&	\
	      ((std::numeric_limits<run>::is_signed ==			\
		std::numeric_limits<val_t>::is_signed ||		\
		!std::numeric_limits<run>::is_integer ||		\
		!std::numeric_limits<val_t>::is_integer) ?		\
	       val > std::numeric_limits<run>::max() :			\
	       /* here when integer sign mismatch */			\
	       static_cast<uint64_t>(val) >				\
	       static_cast<uint64_t>(std::numeric_limits<run>::max()))) \
	    throwError("setting value greater than maximum allowed");	\
	  const run mymin = std::numeric_limits<run>::is_integer ?	\
	    std::numeric_limits<run>::min() :				\
	    static_cast<run>(-std::numeric_limits<run>::max());		\
	  if (std::numeric_limits<val_t>::is_signed &&			\
	      ((std::numeric_limits<run>::is_signed ==			\
		std::numeric_limits<val_t>::is_signed ||		\
		!std::numeric_limits<run>::is_integer ||		\
		!std::numeric_limits<val_t>::is_integer) ?		\
	       val < mymin :						\
	       /* here when integer sign mismatch */			\
	       static_cast<int64_t>(val) < static_cast<int64_t>(mymin))) \
	    throwError("setting value less than minimum allowed");	\
	  set##pretty##Value(m, offset, static_cast<run>(val));	\
	  break;							\
	}
	OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S OCPI_DATA_TYPE

      default:;
      }
    }
    template <typename val_t> val_t Property::
    getValueInternal(const OB::Member &m, size_t offset) const {
      switch (m.m_baseType) {
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
      case OCPI_##pretty: {						\
	ocpiDebug("getting internal: " #pretty);			\
	run val = get##pretty##Value(m, offset);			\
	if (!std::numeric_limits<val_t>::is_integer &&			\
	    std::numeric_limits<run>::digits > std::numeric_limits<val_t>::digits) \
	  throwError("getting property will lose precision");		\
	if (std::numeric_limits<run>::is_signed && !std::numeric_limits<val_t>::is_signed && \
	    val < 0)							\
	  throwError("value is negative when unsigned value requested"); \
	/* complicated only to avoid signed/unsigned integer comparison warnings */ \
	if ((!std::numeric_limits<run>::is_signed || val >= 0) &&	\
	    ((std::numeric_limits<val_t>::is_signed ==			\
	      std::numeric_limits<run>::is_signed ||			\
	      !std::numeric_limits<val_t>::is_integer ||		\
	      !std::numeric_limits<run>::is_integer) ?			\
	     val > std::numeric_limits<val_t>::max() :			\
	     /* here when integer sign mismatch */			\
	     static_cast<uint64_t>(val) >				\
	     static_cast<uint64_t>(std::numeric_limits<val_t>::max()))) \
	  throwError("value greater than maximum allowed for requested type"); \
	const val_t mymin = std::numeric_limits<val_t>::is_integer ?	\
	  std::numeric_limits<val_t>::min() :				\
	  -std::numeric_limits<val_t>::max();				\
	if (std::numeric_limits<run>::is_signed &&			\
	    ((std::numeric_limits<val_t>::is_signed ==			\
	      std::numeric_limits<run>::is_signed ||			\
	      !std::numeric_limits<val_t>::is_integer ||		\
	      !std::numeric_limits<run>::is_integer) ?			\
	     val < mymin :						\
	     /* here when integer sign mismatch */			\
	     static_cast<int64_t>(val) < static_cast<int64_t>(mymin)))	\
	  throwError("value less than minimum allowed for requested type"); \
	return static_cast<val_t>(val);					\
      }
      OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S OCPI_DATA_TYPE

      default:;
      }
      return 0; // not reached
    }
    // type specific scalar property setters
    // the argument type is NOT the base type of the property, but the API caller's type
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S(sca,corba,letter,bits,run,pretty,store)	\
    template <> void Property::						\
    setValue<run>(const run val, AccessList &list) const {		\
      size_t offset;							\
      const OB::Member &m = descend(list, offset);			\
      ocpiDebug("Property::setValue on %s %s->%s\n", m_info.cname(),	\
		OB::baseTypeNames[OCPI_##pretty], OB::baseTypeNames[m_info.m_baseType]); \
      if (m.m_baseType != OCPI_String)				\
	throwError("setting non-string property with string value");	\
      set##pretty##Value(m, offset, val);				\
    }
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)		\
    template <> void Property::						\
    setValue<run>(run val, AccessList &list) const {			\
      size_t offset;							\
      const OB::Member &m = descend(list, offset);			\
      ocpiDebug("setValue on %s %s->%s\n", m_info.cname(),		\
		OB::baseTypeNames[OCPI_##pretty], OB::baseTypeNames[m_info.m_baseType]); \
      if (m.m_baseType == OCPI_##pretty)				\
	set##pretty##Value(m, offset, val);				\
      else if (m_info.m_baseType == OCPI_String)			\
	throwError("setting string property with " #run " value");	\
      else								\
	setValueInternal<run>(m, offset, val);				\
    }									\
    template <> run Property::						\
    getValue<run>(AccessList &list) const {				\
      size_t offset;							\
      const OB::Member &m = descend(list, offset);			\
      ocpiDebug("getValue on %s %s->%s\n", m_info.cname(),		\
		OB::baseTypeNames[OCPI_##pretty], OB::baseTypeNames[m_info.m_baseType]);  \
      if (m.m_baseType == OCPI_String)					\
	throwError("getting a " #run " value from a string property");	\
      return m.m_baseType == OCPI_##pretty ?				\
	get##pretty##Value(m, offset) : getValueInternal<run>(m, offset); \
    }
    OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
#undef OCPI_DATA_TYPE_S
#define OCPI_DATA_TYPE_S OCPI_DATA_TYPE
// re-allow the -Wfloat-equal warning
#pragma GCC diagnostic pop

    template <> void Property::
    setValue<std::string>(std::string val, AccessList &list) const {
      setValue<String>(val.c_str(), list);
    }
    void Property::setValue(const std::string &val, AccessList &list) const {
      setValue<String>(val.c_str(), list);
    }
    template <> std::string Property::
    getValue<std::string>(AccessList &list) const {
      size_t offset;
      const OB::Member &m = descend(list, offset);
      ocpiDebug("getValue on %s %s->%s\n", m_info.cname(),
		OB::baseTypeNames[OCPI_String], OB::baseTypeNames[m_info.m_baseType]);
      if (m.m_baseType != OCPI_String)
	throwError("getting a string value from a non-string property");
      std::vector<char> s(m.m_stringLength + 1);
      getStringValue(m, offset, &s[0], s.size());
      return &s[0];
    }
#if 1
// easier in C++11 with std::enable_if etc.
#ifdef __APPLE__
    template <> long Property::
    getValue<long>(AccessList &list) const {
      size_t offset;
      const OB::Member &m = descend(list, offset);
      ocpiDebug("getValue on %s %s->%s\n", m_info.cname(),
		OB::baseTypeNames[OCPI_Long], OB::baseTypeNames[m_info.m_baseType]);
      if (m.m_baseType == OCPI_String)
	throwError("getting a " "Long" " value from a string property");
      return m.m_baseType == OCPI_Long ?
	getLongValue(m, offset) : getValueInternal<Long>(m, offset);
    }
    template <> unsigned long Property::
    getValue<unsigned long>(AccessList &list) const {
      size_t offset;
      const OB::Member &m = descend(list, offset);
      ocpiDebug("getValue on %s %s->%s\n", m_info.cname(),
		OB::baseTypeNames[OCPI_ULong], OB::baseTypeNames[m_info.m_baseType]);
      if (m.m_baseType == OCPI_String)
	throwError("getting a " "ULong" " value from a string property");
      return m.m_baseType == OCPI_ULong ?
	getULongValue(m, offset) : getValueInternal<ULong>(m, offset);
    }
#endif
#endif
  }
}
