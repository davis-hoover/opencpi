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

// This module will be a submodule under the opencpi package
%module "aci"
// The following is needed so python3 will interpret
// strings as bytes objects instead of unicode objects.
//%begin %{
//#define SWIG_PYTHON_STRICT_BYTE_CHAR
//%}
%include <exception.i>
%include <std_string.i>
%include <cstring.i>
%include <cpointer.i>
%include <stdint.i>
%include <typemaps.i>

 //%ignore "";
 //%rename("%s") OCPI::API::Application;
 //%rename("%s") OCPI::API::Application::Application;
 //%rename("%s") ExternalPort;
 //%rename("%s") ExternalBuffer;

%ignore OCPI::API::PValue::length() const;
%ignore OCPI::API::PValue::unparse(std::string &value, bool append = false) const;
%ignore OCPI::API::AccessUnion;
%ignore OCPI::API::Access;
%ignore OCPI::API::PValue;
%ignore OCPI::API::PVChar;
%ignore OCPI::API::PVULong;
%ignore OCPI::API::PVLongLong;
%ignore OCPI::API::PVULongLong;
%ignore OCPI::API::PVBool;
%ignore OCPI::API::PVFloat;
%ignore OCPI::API::PVDouble;
%ignore OCPI::API::PVUShort;
%ignore OCPI::API::PVLong;
%ignore OCPI::API::PVShort;
%ignore OCPI::API::PVString;
%ignore OCPI::API::PVUChar;
%ignore OCPI::API::Connection;
%ignore OCPI::API::PropertyAccess;
%apply std::string& OUTPUT {std::string& value};
%ignore put();
%ignore getBuffer(uint8_t *&data, size_t &length);
%ignore getBuffer(uint8_t *&data, size_t &length, uint8_t &opCode, bool &endOfData);
%ignore getProperty(const std::string &a_name, std::string &value, AccessList &list = emptyList,
		    PropertyOptionList &options = noPropertyOptions,
		    PropertyAttributes *attributes = NULL) const;
%ignore getProperty(unsigned ordinal, std::string &value, AccessList &list = emptyList,
		    PropertyOptionList &options = noPropertyOptions,
		    PropertyAttributes *attributes = NULL) const;
%ignore getProperty(unsigned ordinal, std::string &name, std::string &value,
		    bool hex = false, bool *parameterp = NULL, bool *cachedp = NULL,
		    bool uncached = false, bool *hiddenp = NULL);
%ignore getProperty(const char* instance_name, const char* prop_name, std::string &value,
			 bool hex = false);
%ignore setProperty(const std::string &prop_name, const std::string &value, AccessList &list = emptyList);
%ignore setProperty(const char* prop_name, const char* prop_name, const char *value,
		    OA::AccessList &list = emptyList);
%ignore setProperty(const char* instance_name, const char* prop_name, const char *value);

// ExternalBuffer *getBuffer(uint8_t *&data, size_t &length, uint8_t &opCode, bool &endOfData)
// Typemaps to adapt the c++ return by reference calls into return values.
// Allows for data to be read FROM an external port.
%typemap(in, numinputs=0) (uint8_t *&data, size_t &length, uint8_t &opCode, bool &endOfData) (uint8_t *tdata, size_t tlength, uint8_t topCode, bool tendOfData) {
    tdata = NULL;
    tlength = 0;
    topCode = 0;
    tendOfData = false;
    $1 = &tdata;
    $2 = &tlength;
    $3 = &topCode;
    $4 = &tendOfData;
}

%typemap(argout) (uint8_t *&data, size_t &length, uint8_t &opCode, bool &endOfData) {
  if (!result) {
    PyObject *none= PyTuple_New(5);
    for (unsigned i = 0; i < 5; ++i)
      PyTuple_SetItem(none, i, Py_None);
    %append_output(none);
  } else {
    %append_output(PyMemoryView_FromMemory((char *)tdata$argnum, result ? tlength$argnum : 0,
					   PyBUF_READ));
    %append_output(PyInt_FromSize_t(*$2));
    %append_output(PyInt_FromLong(*$3));
    %append_output(PyBool_FromLong(*$4));
  }
}

// ExternalBuffer *getBuffer(uint8_t *&data, size_t &length)
// Typemaps to adapt the c++ return by reference calls into return values.
// Allows for data to be written TO an external port.
%typemap(in, numinputs=0) (uint8_t *&data, size_t &length) (uint8_t *tdata, size_t tlength) {
  tdata = NULL;
  tlength = 0;

  $1 = &tdata;
  $2 = &tlength;
}

%typemap(argout) (uint8_t *&data, size_t &length) {
  if (!result) {
    PyObject *none= PyTuple_New(3);
    for (unsigned i = 0; i < 3; ++i)
      PyTuple_SetItem(none, i, Py_None);
    %append_output(none);
  } else {
    %append_output(PyMemoryView_FromMemory((char *)tdata$argnum, result ? tlength$argnum : 0,
					   PyBUF_WRITE));
    %append_output(PyInt_FromSize_t(*$2));
  }
}

// getproperty
// Provide temp std::string for the C++ call
%typemap(in,numinputs=0) std::string &value (std::string temp) {
  $1 = &temp;
}
// Avoid providing any output for the temp
%typemap(argout) (std::string &value) {
}

%typemap(typecheck) OCPI::API::AccessList & {
}
%typemap(in) OCPI::API::AccessList & (OCPI::API::AccessList accesslist= {0,0,0,0,0,0,0,0,0,0}) {
  SWIG_contract_assert(PySequence_Check($input),"OCPI::API::AccessList arguments must be python sequence types");
  unsigned length = PySequence_Length($input);
  SWIG_contract_assert(length <= 10,"OCPI::API::AccessList arguments are limited to 10 items");
  auto alit = accesslist.begin();
  for (unsigned i = 0; i < length; ++i, ++alit) {
    const OCPI::API::Access &a = *alit;
    PyObject *item = PySequence_GetItem($input, i);
    if (PyNumber_Check(item)) {
      a.m_number = true;
      a.m_u.m_index = PyNumber_AsSsize_t(item, NULL);
    } else if (PyBytes_Check(item)) {
      a.m_number = false;
      a.m_u.m_member = PyBytes_AsString(item);
    } else if (PyUnicode_Check(item)) {
      a.m_number = false;
      a.m_u.m_member = PyUnicode_AsUTF8(item);
    } else
      SWIG_Error(SWIG_RuntimeError, "Item in OCPI::API::Access list argument not a number or string");
  }
  if (length < 10) {
    alit->m_number = false;
    alit->m_u.m_member = NULL;
  }
  $1 = &accesslist;
}
%typemap(typecheck) const OCPI::API::PValue * {
}
%typemap(in) const OCPI::API::PValue * (OB::PValueList temppv) {
  if ($input != Py_None) {
    SWIG_contract_assert(PyDict_Check($input),
			 "const OCPI::API::PValue* arguments must be python dictionaries");
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    while (PyDict_Next($input, &pos, &key, &value)) {
      SWIG_contract_assert(PyUnicode_Check(key),
			   "const OCPI::API::PValue* dictionary keys must be strings");
      const char *name = PyUnicode_AsUTF8(key);
      const OCPI::Base::PValue *pv = OB::find(OB::allPVParams, name);
      std::string msg;
      if (!pv) {
	OU::format(msg, "unknown PValue name: \"%s\"", name);
	SWIG_Error(SWIG_RuntimeError, msg.c_str());
	SWIG_fail;
      }
      if (python2PValue(name, pv->type, value, temppv)) {
	OU::format(msg, "Invalid value for PValue name: \"%s\"", name);
	SWIG_Error(SWIG_RuntimeError, msg.c_str());
	SWIG_fail;
      }
    }
    $1 = (OA::PValue *)temppv.list();
  }
}
%ignore OCPI::API::PValue::length() const;
%ignore OCPI::API::PValue::unparse(std::string &value, bool append = false) const;


#if 1
%typemap(in) const char * {
  if (PyBytes_Check($input))
    $1 = (char *)PyBytes_AsString($input);
  else if (PyUnicode_Check($input))
    $1 = (char *)PyUnicode_AsUTF8($input); // cast unnecessary as of 3.7?
  else
    SWIG_exception_fail(SWIG_RuntimeError, "Argument of type \"const char *\" is not a string");
}
%typemap(freearg) const char*{}
%typemap(typecheck) const char*{}
%typemap(varin) const char*{}
#endif
// OCPI::API::BaseType getOperationInfo(uint8_t opCode, size_t &nbytes)
// Typemap to adapt the c++ return by reference calls into return values.
// This is a trivial case so we can just use %apply
%apply size_t &OUTPUT { size_t &nbytes }

%{
#include <climits>
#include "OcpiApi.hh"
#include "BasePValue.hh"
#include "UtilMisc.hh"
  namespace OA=OCPI::API;
  namespace OU=OCPI::Util;
  namespace OB=OCPI::Base;
  // Convert python type to PV given, return true on error
  bool python2PValue(const char *name, OA::BaseType type, PyObject *value, OB::PValueList &list) {
    int check;
    switch (type) {
    case OA::OCPI_Bool:
      {
	bool b;
	if ((check = PyBool_Check(value)))
	   b = value == Py_True;
	else if ((check = PyLong_Check(value))) {
	  long l = PyLong_AsLong(value);
	  b = l != 0;
	}
	if (check)
	  list.addBool(name, b);
	break;
      }
    case OA::OCPI_Char:
      {
	signed char c;
	if ((check = PyLong_Check(value))) {
	  long l = PyLong_AsLong(value);
	  if ((check = l >= CHAR_MIN && l <= CHAR_MAX))
	    c = (signed char)l;
	} else if ((check = PyBytes_Check(value) && PyBytes_Size(value) == 1)) {
	  c = PyBytes_AsString(value)[0];
	} else if ((check = PyUnicode_Check(value) && PyUnicode_GET_LENGTH(value) == 1)) {
	  Py_UCS4 uc = PyUnicode_READ_CHAR(value, 0);
	  if ((check = uc <= UCHAR_MAX))
	    c = (signed char)uc;
	}
	if (check)
	  list.addChar(name, c);
      }
      break;
    case OA::OCPI_Double:
      {
	double d;
	if ((check = PyLong_Check(value)))
	  d = PyLong_AsDouble(value);
	else if ((check = PyFloat_Check(value)))
	  d = PyFloat_AsDouble(value);
	if (check)
	  list.addDouble(name, d);
      }
      break;
    case OA::OCPI_Float:
      {
	double d;
	if ((check = PyLong_Check(value)))
	  d = PyLong_AsDouble(value);
	else if ((check = PyFloat_Check(value)))
	  d = PyFloat_AsDouble(value);
	if (check)
	  list.addFloat(name, (float)d);
      }
    case OA::OCPI_Short:
      if ((check = PyLong_Check(value))) {
	long l = PyLong_AsLong(value);
	if ((check = l >= INT16_MIN && l <= INT16_MAX))
	  list.addShort(name, (int16_t)l);
      }
      break;
    case OA::OCPI_Long:
      if ((check = PyLong_Check(value))) {
	long l = PyLong_AsLong(value);
	if ((check = l >= INT32_MIN && l <= INT32_MAX))
	  list.addShort(name, (int32_t)l);
      }
      break;
    case OA::OCPI_UChar:
      if ((check = PyLong_Check(value))) {
	long l = PyLong_AsLong(value);
	if ((check = l >= 0 && l <= UCHAR_MAX))
	  list.addUChar(name, (uint8_t)l);
      }
      break;
    case OA::OCPI_ULong:
      if ((check = PyLong_Check(value))) {
	long long ll = PyLong_AsLongLong(value);
	if ((check = ll >= 0 && ll <= UINT32_MAX))
	  list.addULong(name, (uint32_t)ll);
      }
      break;
    case OA::OCPI_UShort:
      if ((check = PyLong_Check(value))) {
	unsigned long ul = PyLong_AsUnsignedLong(value);
	if ((check = ul >= 0 && ul <= UINT16_MAX))
	  list.addUShort(name, (uint16_t)ul);
      }
      break;
    case OA::OCPI_LongLong:
      if ((check = PyLong_Check(value))) {
	long long ll = PyLong_AsLongLong(value);
	if ((check = ll >= INT64_MIN && ll <= INT64_MAX))
	  list.addLongLong(name, (int64_t)ll);
      }
      break;
    case OA::OCPI_ULongLong:
      if ((check = PyLong_Check(value))) {
	unsigned long long ull = PyLong_AsUnsignedLongLong(value);
	if ((check = ull >= 0 && ull <= UINT64_MAX))
	  list.addULongLong(name, (uint64_t)ull);
      }
      break;
    case OA::OCPI_String:
      {
	const char *cp;
	Py_ssize_t len;
	if ((check = PyBytes_Check(value)))
	  (void)PyBytes_AsStringAndSize(value, (char **)&cp, &len);
	else if ((check = PyUnicode_Check(value)))
	  cp = PyUnicode_AsUTF8(value);
	if (check)
	  list.addString(name, cp);
      }
      break;
    default: ;
      ocpiCheck("Unexpected type for registereg PValue"==0);
    }
  }
%}

%exception {
    try {
        $action
    } catch (std::string &e) {
        SWIG_exception(SWIG_RuntimeError, e.c_str());
    } catch (...) {
        SWIG_exception(SWIG_RuntimeError, "Unknown Exception");
    }
}

// m_info is a predeclared pointer in the ContainerAPI. Make it 'immutable' so
// swig doesn't try to create a setter for it
%immutable OCPI::API::Property::m_info;

%include "OcpiDataTypesApi.hh"
%include "OcpiPValueApi.hh"
%include "OcpiPropertyApi.hh"
%include "OcpiExceptionApi.hh"
%include "OcpiLibraryApi.hh"
%include "OcpiContainerApi.hh"
%include "OcpiApplicationApi.hh"
%include "OcpiApi.hh"
