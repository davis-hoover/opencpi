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
 *   This file defines the PValue class for types property value lists
 *
 * Revision History: 
 * 
 *    Author: Jim Kulp
 *    Date: 7/2009
 *    Revision Detail: Created
 *
 */

#ifndef OCPI_PVALUE_API_H
#define OCPI_PVALUE_API_H

#include "OcpiUtilDataTypesApi.h"

namespace OCPI {
  
  namespace API {
    // Convenience class for type safe property values for "simplest" api.
    // Only non-type-safe aspect is PVEnd()
    // Typical syntax would be like:
    // PValue props[] = { PVString("label", "foolabel"), PVULong("nbuffers", 10), PVEnd()};

    class PValue {
    public:
      inline PValue(const char *aName, BaseType aType)
	: name(aName), type(aType), owned(false) {}
      inline PValue()
	: name(0), type(OCPI_none), owned(false) {}
      inline PValue(const PValue &other) { *this = other; } // swap idiom would be better here
      inline ~PValue() { if (owned) delete [] vString; }
      PValue &operator=(const PValue &);
      unsigned length() const;
      const std::string &unparse(std::string &value, bool append = false) const;
      const char *name; // NULL name is end of list
      BaseType type;
      bool owned;
      // Anonymous union here for convenience even though redundant with ValueType.
      union {
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store) run v##pretty;
	OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
      };
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store) friend class PV##pretty;
      OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE  
    };
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store)   \
    class PV##pretty : public PValue {				 \
    public:							 \
      inline PV##pretty(const char *aname, const run val = 0) :	 \
      PValue(aname,						 \
	     OCPI_##pretty/*,					 \
			    sizeof(v##pretty)*/) {		 \
	v##pretty = (run)val;					 \
      }								 \
    };
    OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
    // an experiment: working maybe too hard to avoid std::vector and/or std__auto_ptr
    class PVarray {
      PValue *_p;
    public:
      inline PVarray(unsigned n) : _p(new PValue[n]){}
      inline PValue &operator[](size_t n) { return *(_p + n); }
      ~PVarray() { delete [] _p; }
      operator PValue*() const { return _p; }
    };
    extern PVULong PVEnd;
  }
} // OCPI
#endif

