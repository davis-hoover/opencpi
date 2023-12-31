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

#include "hdl.h"
#include "assembly.h"

SdpPort::
SdpPort(Worker &w, ezxml_t x, Port *sp, int ordinal, const char *&err)
  : Port(w, x, sp, ordinal, SDPPort, "sdp", err) {
  // This clock is a bit phony.  This is not an OCP port, and the clock is embedded in the SDP signal bundle.
  // Since it is not OCP, it will not be explicitly wired in any case.
  if (!err && !m_master && !(m_clock = w.findClock("sdp")) && !(err = w.addClock("sdp", "in", m_clock))) {
    m_clock->m_exported = true;
    m_clock->m_exportedSignal = m_clock->m_signal; // no internal/external difference
    m_clock->m_reset = "sdp_reset";
  }
}

// Our special copy constructor
SdpPort::
SdpPort(const SdpPort &other, Worker &w , std::string &a_name, size_t a_count,
		const char *&err)
  : Port(other, w, a_name, a_count, err) {
}

// Virtual constructor: the concrete instantiated classes must have a clone method,
// which calls the corresponding specialized copy constructor
Port &SdpPort::
clone(Worker &w, std::string &arg_name, size_t a_count, OM::Assembly::Role */*role*/,
      const char *&err) const {
  return *new SdpPort(*this, w, arg_name, a_count, err);
}

void SdpPort::
emitRecordInterfaceConstants(FILE *f) {
  Port::emitRecordInterfaceConstants(f); // for our "arrayness"
}
void SdpPort::
emitInterfaceConstants(FILE *f, Language lang) {
  Port::emitInterfaceConstants(f, lang);
}

// This is basically a clone of the RawPropPort - a platform port type with fixed type,
// that may be an array.  FIXME: have a base class for this behavior
void SdpPort::
emitRecordInterface(FILE *f, const char *implName) {
  std::string in, out;
  OU::format(in, typeNameIn.c_str(), "");
  OU::format(out, typeNameOut.c_str(), "");
  fprintf(f,
	  "\n"
	  "  -- Record for the %s input signals for port \"%s\" of worker \"%s\"\n"
	  "  alias %s_t is sdp.sdp.%s_t;\n"
	  "  -- Record for the %s output signals for port \"%s\" of worker \"%s\"\n"
	  "  alias %s_t is sdp.sdp.%s_t;\n",
	  typeName(), pname(), implName,
	  in.c_str(), m_master ? "s2m" : "m2s",
	  typeName(), pname(), implName,
	  out.c_str(), m_master ? "m2s" : "s2m");
  emitRecordArray(f);
  fprintf(f,
	  "  subtype %s_data_t is dword_array_t(0 to to_integer(sdp_width)-1);\n"
	  "  subtype %s_data_t is dword_array_t(0 to to_integer(sdp_width)-1);\n",
	  in.c_str(), out.c_str());
  // When we have a count, we define the data array type
  if (isArray())
      fprintf(f,
	      "  type %s_data_array_t is array(0 to ocpi_port_%s_count-1) of %s_data_t;\n"
	      "  type %s_data_array_t is array(0 to ocpi_port_%s_count-1) of %s_data_t;\n",
	      in.c_str(), pname(), in.c_str(), out.c_str(), pname(), out.c_str());
#if 0
      fprintf(f,
	      "  type %s_data_array_t is array(0 to ocpi_port_%s_count-1) of "
	      "dword_array_t(0 to to_integer(sdp_width)-1);\n"
	      "  type %s_data_array_t is array(0 to ocpi_port_%s_count-1) of "
	      "dword_array_t(0 to to_integer(sdp_width)-1);\n",
	      in.c_str(), pname(), out.c_str(), pname());
  std::string in, out;
  OU::format(in, typeNameIn.c_str(), "");
  OU::format(out, typeNameOut.c_str(), "");
  fprintf(f,
	  "\n"
	  "  -- Record for the %s input signals for port \"%s\" of worker \"%s\"\n"
	  "  alias %s_t is sdp.sdp.%s_t;\n"
	  "  -- Record for the %s output signals for port \"%s\" of worker \"%s\"\n"
	  "  alias %s_t is sdp.sdp.%s_t;\n",
	  typeName(), pname(), implName, in.c_str(), m_master ? "s2m" : "m2s",
	  typeName(), pname(), implName, out.c_str(), m_master ? "m2s" : "s2m");
  emitRecordArray(f);
  fprintf(f, "  subtype %s_data_t is dword_array_t(0 to integer(sdp_width)-1);\n", pname());
  if (isArray()) {
    std::string scount;
    if (m_countExpr.length())
      OU::format(scount, "ocpi_port_%s_count", pname());
    else
      OU::format(scount, "%zu", m_arrayCount);
    fprintf(f,
	    "  type %s_data_array_t is array(0 to %s-1) of %s_data_t;\n"
	    "  type %s_data_array_t is array(0 to %s-1) of %s_data_t;\n",
	    in.c_str(), scount.c_str(), pname(),
	    out.c_str(), scount.c_str(), pname());
  }
#endif
}

void SdpPort::
emitRecordTypes(FILE */*f*/) {
}

void SdpPort::
emitConnectionSignal(FILE *f, bool output, Language /*lang*/, bool /*clock*/, std::string &signal) {
  std::string in, out;
  OU::format(in, typeNameIn.c_str(), "");
  OU::format(out, typeNameOut.c_str(), "");
  std::string suff;
  m_worker->addParamConfigSuffix(suff);
  fprintf(f, "  signal %s : %s%s.%s_defs.%s%s_t;\n",
	  signal.c_str(), m_worker->m_implName, suff.c_str(), m_worker->m_implName,
	  output ? out.c_str() : in.c_str(), isArray() ? "_array" : "");
  //  if (m_arrayCount || m_countExpr.length())
  //    fprintf(f, "(0 to %s.%s_constants.ocpi_port_%s_count-1)", m_worker->m_implName,
  //	    m_worker->m_implName, pname());
  //  fprintf(f, ";\n");
  fprintf(f, "  signal %s_data : %s%s.%s_defs.%s_data%s_t;\n", signal.c_str(),
	  m_worker->m_implName, suff.c_str(), m_worker->m_implName,
	  output ? out.c_str() : in.c_str(),
	  isArray() ? "_array" : "");
#if 0
  if (isArray())
      fprintf(f,
	      "  signal %s : %s_%s_array_t;\n"
	      "  signal %s_data : %s_%s_data_array_t;\n",
	      signal.c_str(), pname(), output ? "out" : "in",
	      signal.c_str(), pname(), output ? "out" : "in"); 
  else
    fprintf(f,
	    "  signal %s : %s_%s_t;\n"
	    "  signal %s_data : dword_array_t(0 to to_integer(sdp_width)-1);\n",
	    signal.c_str(), pname(), output ? "_out" : "_in",
	    signal.c_str());
#endif
}

void SdpPort::
emitRecordSignal(FILE *f, std::string &last, const char *aprefix, bool inRecord, bool inPackage,
		 bool inWorker, const char *defaultIn, const char *defaultOut) {
  Port::emitRecordSignal(f, last, aprefix, inRecord, inPackage, inWorker, defaultIn, defaultOut);
  fprintf(f, last.c_str(), ";\n");
  std::string in, out;
  OU::format(in, "%s_in_data", pname());
  OU::format(out, "%s_out_data", pname());
  if (isArray()) {
    std::string scount;
    if (m_countExpr.length())
      OU::format(scount, "ocpi_port_%s_count", pname());
    else
      OU::format(scount, "%zu", m_arrayCount);
    OU::format(last,
	       "  %-*s : in  %s_array_t;\n"
	       "  %-*s : out %s_array_t%%s",
	       (int)m_worker->m_maxPortTypeName, in.c_str(), in.c_str(),
	       (int)m_worker->m_maxPortTypeName, out.c_str(), out.c_str());
  } else
    OU::format(last,
	       "  %-*s : in  dword_array_t(0 to to_integer(%s)-1);\n"
	       "  %-*s : out dword_array_t(0 to to_integer(%s)-1)%%s",
	       (int)m_worker->m_maxPortTypeName, in.c_str(),
	       inRecord ? "sdp_width" : "unsigned(sdp_width)",
	       (int)m_worker->m_maxPortTypeName, out.c_str(),
	       inRecord ? "sdp_width" : "unsigned(sdp_width)");
}

void SdpPort::
emitVHDLShellPortMap(FILE *f, std::string &last) {
  Port::emitVHDLShellPortMap(f, last);
  std::string in;
  OU::format(in, typeNameIn.c_str(), "");
  fprintf(f,
	  "%s"
	  "    %s_in_data => %s_in_data,\n"
	  "    %s_out_data => %s_out_data\n",
	  last.c_str(), pname(), pname(), pname(), pname());
}

void SdpPort::
emitPortSignal(std::string *pmaps, bool any, const char *indent, const std::string &fName,
	       const std::string &aName, const std::string &fIndex, const std::string &aIndex,
	       size_t a_count, bool output, const Port *signalPort, bool external) {
  std::string
    formal(fName + fIndex), formal_data(fName + "_data" + fIndex),
    actual(aName), actual_data(aName + "_data"),
    empty;
  actual += aIndex;
  actual_data += aIndex;
  if (signalPort) {
    std::string suff;
    if (output) {
      if (aName == "open") {
	actual = "open";
	actual_data = "open";
      } else {
	signalPort->worker().addParamConfigSuffix(suff);
	OU::format(formal, "%s%s.%s_defs.%s%s",
		   external ? "work" : signalPort->worker().m_implName,
		   external ? "" : signalPort->worker().addParamConfigSuffix(suff),
		   signalPort->worker().m_implName, signalPort->pname(),
		   external ? "_out" : "_in");
	formal_data = formal + "_data";
	if (aIndex.empty() && signalPort->isArray()) {
	  formal += "_array";
	  formal_data += "_array";
	}
	OU::formatAdd(formal, "_t(%s)", fName.c_str());
	OU::formatAdd(formal_data, "_t(%s_data)", fName.c_str());
      }
    } else {
      if (aName.empty()) {
	actual = m_master ? slaveMissing() : masterMissing();
	actual_data = "(others => (others => '0'))";
      } else {
	m_worker->addParamConfigSuffix(suff);
	bool fArray = isArray() && (!fIndex.size() || a_count > 1);
	OU::format(actual, "%s%s.%s_defs.%s%s_t%s%s%s)",
		   m_worker->m_implName, suff.c_str(), m_worker->m_implName, fName.c_str(),
		   fArray ? "_array" : "", fArray && !signalPort->isArray() ? "'(0 => " : "(",
		   aName.c_str(), aIndex.c_str());
	OU::format(actual_data, "%s%s.%s_defs.%s_data%s_t%s%s_data%s)", m_worker->m_implName,
		   suff.c_str(), m_worker->m_implName, fName.c_str(),
		   fArray? "_array" : "", fArray && !signalPort->isArray() ? "'(0 => " : "(",
		   aName.c_str(), aIndex.c_str());
      }
    }
  }
  Port::emitPortSignal(&pmaps[0], any, indent, formal, actual, empty, empty, a_count, output, NULL, false);
  Port::emitPortSignal(&pmaps[1], true, indent, formal_data, actual_data, empty, empty, a_count, output, NULL, false);
}

void SdpPort::
emitExtAssignment(FILE *f, bool int2ext, const std::string &extName, const std::string &intName,
		  const Attachment &extAt, const Attachment &intAt, size_t connCount) const {
  std::string left, right, left_data, right_data;
  emitExtAssignmentSides(int2ext, extName, intName, extAt, intAt, connCount, left, right);
  emitExtAssignmentSides(int2ext, extName + "_data", intName + "_data", extAt, intAt, connCount,
			 left_data, right_data);
  if (int2ext) {
    std::string type, type_data;
    OU::format(type, "work.%s_defs.%s_out",
	       extAt.m_instPort.m_port->worker().m_implName, extAt.m_instPort.m_port->pname());
    type_data = type + "_data";
    if (extAt.m_instPort.m_port->isArray() and connCount != 1) {
      type += "_array";
      type_data += "_array";
    }
    OU::formatAdd(type, "_t(%s)", right.c_str());
    OU::formatAdd(type_data, "_t(%s)", right_data.c_str());
    fprintf(f, "  %s <= %s;\n  %s <= %s;\n",
	    left.c_str(), type.c_str(), left_data.c_str(), type_data.c_str());
  } else // will this ever happen?
    fprintf(f, "  %s <= %s;\n  %s <= %s;\n",
	    left.c_str(), right.c_str(), left_data.c_str(), right_data.c_str());
}
