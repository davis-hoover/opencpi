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

#include <limits.h>
#include <algorithm>
#include <vector>

#include "OsFileSystem.hh"

#include "assembly.h"
#include "data.h"
#include "rcc.h"

// Generate the readonly implementation file.
// What implementations must explicitly (verilog) or implicitly (VHDL) include.
#define RCC_C_HEADER ".h"
#define RCC_C_IMPL "_Worker"
#define RCC_CC_HEADER ".hh"
#define RCC_CC_IMPL "-worker"
#define RCC_CC_SLAVES "-slaves"
#define RCC_CC_SLAVETYPES "-slavetypes"
#define RCCMAP "_map"

static char *
upperdup(const char *s) {
  char *upper = (char *)calloc(strlen(s) + 1, sizeof(char));
  for (char *u = upper; (*u++ = (char)toupper(*s)); s++)    ;
  return upper;
}

static const char *rccTypes[] = {"none",
                                 "RCCBoolean", "RCCChar", "RCCDouble", "RCCFloat", "int16_t", "int32_t", "uint8_t",
                                 "uint32_t", "uint16_t", "int64_t", "uint64_t", "RCCChar" };

static void camel(std::string &s, const char *s1, const char *s2 = NULL, const char *s3 = NULL, const char *s4 = NULL) {
  s.clear();
  // When all code is C++11... for (const char *p :{s1, s2, s3})
  if (s1) {
    s += static_cast<char>(toupper(s1[0]));
    s += (s1+1); // rest of string
  }
  if (s2) {
    s += static_cast<char>(toupper(s2[0]));
    s += (s2+1);
  }
  if (s3) {
    s += static_cast<char>(toupper(s3[0]));
    s += (s3+1);
  }
  if (s4) {
    s += static_cast<char>(toupper(s4[0]));
    s += (s4+1);
  }
}

static const char *
upperconstant(std::string &s, const char *s1, const char *s2 = NULL, const char *s3 = NULL) {
  if (s1) // string.append(NULL) is undefined
    s += s1;
  if (s2) {
    if (s1)
      s += "_";
    upperconstant(s, s2, s3);
  }
  std::transform(s.begin(), s.end(), s.begin(), ::toupper);
  return s.c_str();
}

// Emit a constant expression either from a numeric field or from an expression of parameters
void Worker::
rccEmitDimension(size_t numeric, const std::string &expr, const char *surround,
                 std::string &out) {
  if (surround)
    out += surround[0];
  if (expr.length() && !m_isSlave) {
    std::string prefix, cexpr;
    if (m_language == CC)
      upperconstant(prefix, m_implName, "");
    else
      OU::format(prefix, "OCPI_PARAM_%s_", m_implName);
    OB::makeCexpression(expr.c_str(), prefix.c_str(), m_language == CC ? "" : "()",
                        m_language == CC, cexpr);
    out += cexpr;
  } else
    OU::formatAdd(out, "%zu", numeric);
  if (surround)
    out += surround[1];
}

static void
rccEnd(OB::Member &m, bool topSeq, std::string &type) {
  // End of declarator.
  OU::formatAdd(type, "; /* 0x%02zX%s */\n", m.m_offset, topSeq?" this is a top level sequence of fixed size elements":"");
#if 0
  OU::formatAdd(type, "; /* %8zxx", m.m_offset);
  if (topSeq)
    type += " this is a top level sequence of fixed size elements";
  type += " */\n";
#endif
}

void Worker::
rccArray(std::string &type, OB::Member &m, bool isFixed, bool &isLast, bool topSeq, bool end) {
  if (m.m_arrayRank)
    for (unsigned n = 0; n < m.m_arrayRank; n++)
      rccEmitDimension(m.m_arrayDimensions[n], m.m_arrayDimensionsExprs[n], "[]", type);
  if (topSeq) {
    if (m.m_sequenceLength)
      OU::formatAdd(type, "[%zu]", m.m_sequenceLength);
    else
      type += "[1]";
  }
  // We align strings on a 4 byte boundary, and implicitly pad them to a 4 byte boundary too
  if (m.m_baseType == OA::OCPI_String) {
    std::string expr = "(";
    rccEmitDimension(m.m_stringLength, m.m_stringLengthExpr, "()", expr);
    expr += " + 4) & ~3";
    OU::formatAdd(type, "[%s]", isFixed ? expr.c_str() : "4");
    if (m.m_stringLength == 0)
      isLast = true;
  }
  if (end)
    rccEnd(m, topSeq, type);
}
// Just print the data type, not the "member", with names or arrays etc.
void Worker::
rccBaseType(std::string &type, OB::Member &m, unsigned level, size_t &offset, unsigned &pad,
            const char *parent, bool isFixed, bool &isLast, unsigned predefine, bool isCnst) {
  if (level > m_maxLevel)
    m_maxLevel = level;
  int indent = (int)level * 2 + 2;
  const char *cnst = isCnst ? "const " : "";
  if (m.m_baseType == OA::OCPI_Struct) {
    std::string s;
    camel(s, parent, m.m_name.c_str());
    if (level == predefine || predefine == UINT_MAX-1) {
      OU::formatAdd(type, "%*s%sstruct __attribute__ ((__packed__)) %s {\n", indent, "", cnst, s.c_str());
      rccStruct(type, m.m_nMembers, m.m_members, level + 1, s.c_str(), isFixed, isLast,
                    false, predefine, m.m_elementBytes);
      OU::formatAdd(type, "%*s}%s", indent, "", predefine == UINT_MAX-1 ? "" : ";\n");
    } else if (level > predefine)
      OU::formatAdd(type, "%*s%sstruct %s", indent, "", cnst, s.c_str());
    else
      rccStruct(type, m.m_nMembers, m.m_members, level + 1, s.c_str(), isFixed, isLast,
                    false, predefine);
  } else if (m.m_baseType == OA::OCPI_Type)
    rccType(type, *m.m_type, level + 1, offset, pad, parent, isFixed, isLast, false, predefine,
            isCnst);
  else if (m.m_baseType == OA::OCPI_Enum) {
    if (strcasecmp("ocpi_endian", m.m_name.c_str()) &&
        (level == predefine || predefine == UINT_MAX-1)) {
      OU::formatAdd(type, "%*s%senum %c%s%c%s {\n", indent, "", cnst,
                    m_language == CC || m_isSlave ? ' ' : toupper(m_implName[0]),
                    m_language == CC || m_isSlave ? "" : m_implName+1,
                    toupper(*m.cname()), m.cname()+1);
      for (const char **ep = m.m_enums; *ep; ep++) {
        std::string s;
        upperconstant(s, parent, m.m_name.c_str(), *ep);
        OU::formatAdd(type, "%*s  %s,\n", indent, "", s.c_str());
      }
      std::string s;
      upperconstant(s, parent, m.m_name.c_str(), "PAD_ = 0x7fffffff");
      OU::formatAdd(type, "%*s  %s\n%*s} __attribute__((__packed__))%s", indent, "", s.c_str(), indent, "",
              predefine == UINT_MAX-1 ? "" : ";\n");
    } else if (level > predefine || predefine == UINT_MAX-1) {
      if (!strcasecmp("ocpi_endian", m.m_name.c_str()))
        OU::formatAdd(type, "%*s%s%sRCCEndian", indent, "", cnst,
                      m_language == CC ? "OCPI::RCC::" : "");
      else
        OU::formatAdd(type, "%*s%senum %c%s%c%s", indent, "", cnst,
                      m_language == CC || m_isSlave ? ' ' : toupper(m_implName[0]),
                      m_language == CC || m_isSlave ? "" : m_implName+1,
                      toupper(*m.cname()), m.cname()+1);
    }
  } else if (level > predefine || predefine == UINT_MAX-1) {
    const char *baseType = m_baseTypes[m.m_baseType];
    if (m_language == C)
      OU::formatAdd(type, "%*s%s%-*s", indent, "", cnst, indent ? 13 : 0, baseType);
    else {
      std::string mytype = !strncmp("RCC", baseType, 3) ? "OCPI::RCC::" : "";
      mytype += baseType;
      OU::formatAdd(type, "%*s%s%-*s", indent, "", cnst, indent ? 24 : 0, mytype.c_str());
    }
  }
}
// Print type for a member, including sequence type etc.
// Note this is called for two different purposes:
// 1. When a higher level structure is being defined (like Properties) and thus
//    the type will be immediately and anonymously used as the type of a struct member
// 2. When a type for a parameter is being defined in advance of its value being defined.
// predefine is UINT_MAX when we are just traversing the type for determining max depth
// otherwise the level of data structure with 0 being the lowest leaf, in order to
// define structures/types from leaf to root.
// predefine is 0 when the top level (like actual properties)
void Worker::
rccType(std::string &type, OB::Member &m, unsigned level, size_t &offset, unsigned &pad,
        const char *parent, bool isFixed, bool &isLast, bool topSeq, unsigned predefine,
        bool cnst) {
  int indent = (int)level * 2 + 2;
  if (m.m_isSequence && !topSeq) {
    if (level > predefine || predefine == UINT_MAX-1) {
      OU::formatAdd(type, "%*s%sstruct __attribute__ ((__packed__)) {\n", indent, "", cnst ? "const " : "");
      if (m_language != C)
        OU::formatAdd(type,
                      "%*s  inline size_t capacity() const { return %zu; }\n"
                      "%*s  inline void resize(size_t n) { assert(n <= %zu); length = n; }\n"
                      "%*s  inline size_t size() const { return length; }\n",
                      indent, "", m.m_sequenceLength, indent, "", m.m_sequenceLength, indent, "");
      OU::formatAdd(type, "%*s  uint32_t length;\n", indent, "");
      if (m.m_dataAlign > sizeof(uint32_t)) {
        size_t align = m.m_dataAlign - (unsigned)sizeof(uint32_t);
        OU::formatAdd(type, "%*s  char pad%u_[%zu];\n", indent, "", pad++, align);
      }
    }
    type += "  ";
    rccBaseType(type, m, level, offset, pad, parent, isFixed, isLast, predefine, false);
    if (level > predefine || predefine == UINT_MAX-1) {
      OU::formatAdd(type, " data");
      if (m.m_sequenceLength && isFixed)
        rccEmitDimension(m.m_sequenceLength, m.m_sequenceLengthExpr, "[]", type);
      else {
        type += "[]";
        isLast = true;
      }
      rccArray(type, m, isFixed, isLast, false, true);
      OU::formatAdd(type, "%*s}", indent, "");
    }
  } else
    rccBaseType(type, m, level, offset, pad, parent, isFixed, isLast, predefine, cnst);
}

// FIXME: a tool-time member class should have this...OCPI::Tools::RCC::Member...
// Returns true when something is variable length.
// strings or sequences are like that unless then are bounded.
void Worker::
rccMember(std::string &type, OB::Member &m, unsigned level, size_t &offset, unsigned &pad,
          const char *parent, bool isFixed, bool &isLast, bool topSeq, unsigned predefine,
          bool cnst) {
  int indent = (int)level * 2 + 2;
  if (level > predefine || predefine == UINT_MAX-1) {
    if (offset < m.m_offset) {
      OU::formatAdd(type, "%*schar pad%u_[%zu];\n",
                    indent, "", pad++, m.m_offset - offset);
      offset = m.m_offset;
    }
    rccType(type, m, level, offset, pad, parent, isFixed, isLast, topSeq, predefine, cnst);
    OU::formatAdd(type, " %s", m.m_name.c_str());
    if (m.m_isSequence && !topSeq) // sequences put the dimensions inside the length/data struct
      rccEnd(m, topSeq, type);
    else
      rccArray(type, m, isFixed, isLast, topSeq, true);
    offset += m.m_nBytes;
  } else
    rccType(type, m, level, offset, pad, parent, isFixed, isLast, topSeq, predefine, cnst);
}

const char *Worker::
rccMethodName(const char *method, const char *&mName) {
  const char *pat = m_pattern ? m_pattern : m_staticPattern;
  if (!pat) {
    mName = strdup(method);
    return 0;
  }
  size_t length =
    strlen(m_implName) + strlen(method) + strlen(pat) + 1;
  char c, *s = (char *)malloc(length);
  mName = s;
  while ((c = *pat++)) {
    if (c != '%')
      *s++ = c;
    else if (!*pat)
      *s++ = '%';
    else switch (*pat++) {
    case '%':
      *s++ = '%';
      break;
    case 'm':
      strcpy(s, method);
      while (*s)
        s++;
      break;
    case 'M':
      *s++ = (char)toupper(method[0]);
      strcpy(s, method + 1);
      while (*s)
        s++;
      break;
    case 'w':
      strcpy(s, m_implName);
      while (*s)
        s++;
      break;
    case 'W':
      *s++ = (char)toupper(m_implName[0]);
      strcpy(s, m_implName + 1);
      while (*s)
        s++;
      break;
    default:
      return OU::esprintf("Invalid pattern rule: %s", m_pattern);
    }
  }
  *s++ = 0;
  return 0;
}

void Worker::
rccStruct(std::string &type, size_t nMembers, OB::Member *members, unsigned level,
          const char *parent, bool isFixed, bool &isLast, bool topSeq, unsigned predefine,
          size_t elementBytes) {
  size_t offset = 0;
  unsigned pad = 0;
  for (unsigned n = 0; !isLast && n < nMembers; n++, members++)
    rccMember(type, *members, level, offset, pad, parent, isFixed, isLast, topSeq, predefine);

  // perform trailing struct padding if necessary
  int indent = (int)level * 2 + 2;
  if (offset < elementBytes)
    OU::formatAdd(type, "%*schar pad%u_[%zu];\n", indent, "", pad++, elementBytes - offset);
}

// An unparser specialized for C
struct C_Unparser : public OB::Unparser {
  const Worker &m_worker;
  const OB::Member &m_member;
  C_Unparser(const Worker &w, const OB::Member &mem) : m_worker(w), m_member(mem) {
  }
  bool
  dimensionUnparse(const OB::Value &v, std::string &s, unsigned nseq, size_t dim,
                   size_t offset, size_t nItems, bool hex, char comma,
                   const Unparser &up) const {
    if (dim == 0)
      s += "{ ";
    bool r = Unparser::dimensionUnparse(v, s, nseq, dim, offset, nItems, hex, comma, up);
    if (dim == 0)
      s += "}";
    return r;
  }
  bool
  unparseBool(std::string &s, bool val, bool) const {
    s += val ? "1" : "0";
    return !val;
  }
  bool
  unparseEnum(std::string &s, OB::EnumValue val, const char **enums, size_t nEnums,
              bool /*hex*/) const {
    if (val >= nEnums)
      throw OU::Error("Invalid enumberation value: 0x%x", val);
    if (!strcasecmp("ocpi_endian", m_member.m_name.c_str()))
      upperconstant(s, "RCC", enums[val]);
    else
      upperconstant(s, m_worker.m_implName, m_member.m_name.c_str(), enums[val]);
    return val == 0;
  }
  bool
  unparseString(std::string &s, const char *val, bool hex) const {
    if (val && *val)
      s += '\"';
    Unparser::unparseString(s, val, hex);
    if (val && *val)
      s += '\"';
    return !val || *val == '\0';
  }
  bool
  sequenceUnparse(const OB::Value &v, std::string &s, bool hex, char comma) const {
    OU::formatAdd(s, "{ %zu", v.m_nElements);
    bool ret;
    if (v.m_nElements) {
      s += ", {";
      ret = OB::Unparser::sequenceUnparse(v, s, hex, comma);
      s += "}";
    } else
      ret = true;
    s += "}";
    return ret;
  }
};

struct CC_Unparser : public C_Unparser {
  CC_Unparser(const Worker &w, const OB::Member &mem) : C_Unparser(w, mem) {}
  bool
  unparseBool(std::string &s, bool val, bool) const {
    s += val ? "true" : "false";
    return !val;
  }
  bool
  unparseEnum(std::string &s, OB::EnumValue val, const char **enums, size_t nEnums, bool hex)
    const {
    if (!strcasecmp("ocpi_endian", m_member.m_name.c_str())) {
      s = "OCPI::RCC::";
      upperconstant(s, "RCC", enums[val]);
      return val == 0;
    }
    return C_Unparser::unparseEnum(s, val, enums, nEnums, hex);
  }
};

const char *Worker::
rccValue(OB::Value &v, std::string &value, const OB::Member &param) {
  if (m_language == CC) {
    CC_Unparser p(*this, param);
    v.unparse(value, &p);
  } else {
    C_Unparser p(*this, param);
    v.unparse(value, &p);
  }
  return value.c_str();
}



const char *Worker::
rccPropValue(OM::Property &p, std::string &value) {
  if (p.m_default)
    return rccValue(*p.m_default, value, p);
  // Generate a default value
  switch(p.m_baseType) {
  case OA::OCPI_Bool:
  case OA::OCPI_Char:
  case OA::OCPI_Double:
  case OA::OCPI_Float:
  case OA::OCPI_Short:
  case OA::OCPI_Long:
  case OA::OCPI_UChar:
  case OA::OCPI_Enum:
  case OA::OCPI_ULong:
  case OA::OCPI_UShort:
  case OA::OCPI_LongLong:
  case OA::OCPI_ULongLong:
    value += "0";
    break;
  case OA::OCPI_String:
    value += "\"\""; // this is not NULL
  default:;
  }
  return value.c_str();
}

static const char *cctypes[] = {
  "None",
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store) #run,
  OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
  "Struct", "Enum", "Type",
  0
};
static const char *ccpretty[] = {
  "None",
#define OCPI_DATA_TYPE(sca,corba,letter,bits,run,pretty,store) #pretty,
  OCPI_PROPERTY_DATA_TYPES
#undef OCPI_DATA_TYPE
  "Struct", "Enum", "Type",
  0
};

void Worker::
emitCppTypesNamespace(FILE *f, std::string &nsName, const std::string &slaveName) {
  if (slaveName.empty())
    camel(nsName, m_implName, "WorkerTypes", NULL);
  else
    camel(nsName, slaveName.c_str(), "WorkerTypes", NULL);
  fprintf(f, "\nnamespace %s {\n", nsName.c_str());
  const char *last = "";
  const char *upper = upperdup(m_implName);
  for (unsigned n = 0; n < m_ports.size(); n++) {
    Port *port = m_ports[n];
    if (!port->isData())
      continue;
    if (!last[0])
      fprintf(f,
              "  // Enumeration of port ordinals for worker %s\n"
              "  enum %c%sPort {\n",
              m_implName, toupper(m_implName[0]), m_implName+1);
    fprintf(f, "%s  %s_%s", last, upper, upperdup(port->pname()));
    last = ",\n";
  }
  if (last[0])
    fprintf(f, "\n  };\n");
  m_maxLevel = 0;
  unsigned pad = 0;
  size_t offset = 0;
  bool isLastDummy = false;
  // First pass, determine max depth
  for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++)
    if ((*pi)->m_baseType == OA::OCPI_Enum || (*pi)->m_baseType == OA::OCPI_Struct) {
      std::string type;
      rccType(type, **pi, 0, offset, pad, NULL, true, isLastDummy, false, UINT_MAX);
    }
  bool first = true;
  // Second pass, define types bottom up
  for (unsigned l = m_maxLevel+1; l--; ) {
    pad = 0;
    offset = 0;
    isLastDummy = false;
    for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++) {
      if (((*pi)->m_baseType == OA::OCPI_Enum && (*pi)->m_name != "ocpi_endian") ||
           (*pi)->m_baseType == OA::OCPI_Struct) {
        if (first)
          fprintf(f,
                  "  /*\n"
                  "   * Property types for worker %s\n"
                  "   */\n",
                  m_implName);
        first = false;
        std::string type;
        rccType(type, **pi, 0, offset, pad, NULL, true, isLastDummy, false, l);
        fputs(type.c_str(), f);
      }
    }
  }
  fprintf(f,
          "  /*\n"
          "   * Property structure for worker %s\n"
          "   */\n",
          m_implName);
  fprintf(f,
          "  struct __attribute__ ((__packed__)) Properties {\n"
          "    Properties() // constructor to value-initialize const members\n"
          "      ");
  first = true;
  // These initializers are required for const properties
  for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++)
    if ((*pi)->m_isParameter && !(*pi)->m_isReadable)
      continue; // these are not in the property structure at all
    else if (!(*pi)->m_isVolatile && ((*pi)->m_isWritable || (*pi)->m_isReadable)) {
      fprintf(f, "%s%s()", first ? ": " : ", ", (*pi)->m_name.c_str());
      first = false;
    }
  fprintf(f, "    {}\n");
  offset = 0;
  pad = 0;
  isLastDummy = false;
  for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++)
    if ((*pi)->m_isParameter && !(*pi)->m_isReadable)
      continue; // these are not in the property structure at all
    else {
      std::string type;
      rccMember(type, **pi, 2, offset, pad, NULL, true, isLastDummy, false, 0,
		// it is const if the worker should not set it.
		(*pi)->m_isWritable && !(*pi)->m_isVolatile);
      fputs(type.c_str(), f);
    }
  fprintf(f, "  };\n");
  // Emit types for protocol operations
  first = true;
  for (unsigned n = 0; n < m_ports.size(); n++)
    m_ports[n]->emitRccArgTypes(f, first);
  // deferred until worker base class is out
  // fprintf(f, "}\n");
}

void DataPort::
emitRccArgTypes(FILE *f, bool &first) {
  if (operations()) {
    for (unsigned n = 0; n < ::Port::m_ordinal; n++)
      if (worker().m_ports[n]->isData()) {
        DataPort &other = *static_cast<DataPort*>(worker().m_ports[n]);
        if (other.operations() &&
            !strcasecmp(other.OM::Protocol::cname(), OM::Protocol::cname()))
          return;
      }
    if (first)
      fprintf(f,
              "  /*\n"
              "   * Data types for each protocol used by a port of this worker\n"
              "   */\n");
    first = false;
    OM::Operation *o = operations();
    std::string aprefix;
    if (nOperations()) {
      camel(aprefix, OM::Protocol::cname());
      fprintf(f,
              "  // Enumeration constants for the operations of protocol \"%s\"\n"
              "  enum %sOpCodes { \n",
              OM::Protocol::cname(), aprefix.c_str());
      for (unsigned nn = 0; nn < nOperations(); o++) {
        std::string s;
        camel(s, o->cname());
        fprintf(f,"    %s%s_OPERATION%s\n", aprefix.c_str(), s.c_str(),
                ++nn == nOperations() ? "" : ",");
      }
      fprintf(f, "  }; \n" );
    }
    bool pfirst = true;
    o = operations();
    for (unsigned n  = 0; n < nOperations(); n++, o++) {
      OB::Member *m = o->args();
      bool ofirst = true;
      for (unsigned nn = 0; nn < o->nArgs(); nn++, m++)
        if (m->m_baseType == OA::OCPI_Enum || m->m_baseType == OA::OCPI_Struct) {
          if (pfirst)
            fprintf(f,
                    "  /*\n"
                    "   * Argument data types for the \"%s\" protocol\n"
                    "   */\n",
                    OM::Protocol::cname());
          if (ofirst)
            fprintf(f,
                    "  /* Argument data types for the \"%s\" operation of the \"%s\" protocol */\n",
                    o->cname(), OM::Protocol::cname());
          pfirst = ofirst = false;
          camel(aprefix, OM::Protocol::cname(), o->cname(), NULL);

          worker().m_maxLevel = 0;
          unsigned pad = 0;
          size_t offset = 0;
          bool isLastDummy = false;
          // First pass, determine max depth
          std::string type;
          worker().rccType(type, *m, 0, offset, pad, NULL, true, isLastDummy,
                            nn == 0 && o->nArgs() == 1, UINT_MAX);
          // Second pass, define types bottom up
          for (unsigned l = worker().m_maxLevel+1; l--; ) {
            type.clear();
            worker().rccType(type, *m, 0, offset, pad, aprefix.c_str(), true, isLastDummy,
                              nn == 0 && o->nArgs() == 1, l);
            fputs(type.c_str(), f);
          }
        }
    }
  }
}

/*
 * Emit slave-related namespaced type definitions, *WHICH IS PARAMETER DEPENDENT*.
 * Since this can be a large amount of generation, we put it in a separate file.
 */
const char *Worker::
emitImplSlaveTypes(FILE *parent) {
  fprintf(parent,
          "// This worker is a proxy with slaves, so include the slave types definitions file.\n"
          "#include \"%s%s%s\"\n\n",
          m_implName, RCC_CC_SLAVETYPES, RCC_CC_HEADER);
  FILE *f;
  const char *err;
  if (!(err = openOutput(cname(), m_outDir, "", RCC_CC_SLAVETYPES, RCC_CC_HEADER, NULL, f))) {
    for (unsigned n = 0; n < m_paramConfigs.size(); ++n)
      if (m_paramConfigs[n]) {
	fprintf(f, "#if OCPI_PARAM_CONFIG() == %u\n", n);
	if ((err = emitImplSlaveTypesConfig(f, n)))
	  break;
	fprintf(f, "#endif\n");
      }
    fclose(f);
  }
  return err;
}
/*
 * Emit slave-related definitions, *WHICH IS PARAMETER DEPENDENT*.
 * Since this can be a large amount of generation, we put it in a separate file.
 */
const char *Worker::
emitImplSlaves(FILE *parent) {
  fprintf(parent,
          "// This worker is a proxy with slaves, so include the slave definitions file.\n"
          "#include \"%s%s%s\"\n\n",
          m_implName, RCC_CC_SLAVES, RCC_CC_HEADER);
  FILE *f;
  const char *err;
  if (!(err = openOutput(cname(), m_outDir, "", RCC_CC_SLAVES, RCC_CC_HEADER, NULL, f))) {
    for (unsigned n = 0; n < m_paramConfigs.size(); ++n)
      if (m_paramConfigs[n]) {
	fprintf(f, "#if OCPI_PARAM_CONFIG() == %u\n", n);
	if ((err = emitImplSlavesConfig(f, n)))
	  break;
	fprintf(f, "#endif\n");
      }
    fclose(f);
  }
  return err;
}

const char *Worker::
emitImplSlaveTypesConfig(FILE *f, unsigned pc) {
  ParamConfig &paramConfig = *m_paramConfigs[pc];
  // save each slave's original base types and replace with rcc types for code gen here
  for (auto it = paramConfig.m_slaves.begin(); it != paramConfig.m_slaves.end(); ++it) {
    paramConfig.m_slaveBaseTypes.push_back((*it).second->m_baseTypes); // patch basetypes
    (*it).second->m_baseTypes = rccTypes;

    std::string curSlaveTypes;
    (*it).second->emitCppTypesNamespace(f, curSlaveTypes, (*it).first);
    fprintf(f, "}\n");
    paramConfig.m_slaveTypes.push_back(curSlaveTypes); // remember types namespace for slave
  }
  return NULL;
}

const char *Worker::
emitImplSlavesConfig(FILE *f, unsigned pc) {
  unsigned int index = 0;
  ParamConfig &paramConfig = *m_paramConfigs[pc];
  // for each slave declare the slave class which extends RCCUserSlave and is named generically
  // Slave1, Slave2 ... etc
  for (auto it = paramConfig.m_slaves.begin(); it != paramConfig.m_slaves.end(); ++it) {
    const char *l_name = (*it).first.c_str();
    // This worker is a proxy.  Give it access to each of its slaves
    fprintf(f,
	    "  /*\n"
	    "   * This class defines the properties of a slave for convenient access.\n"
	    "   */\n"
	    "  class Slave%u : public OCPI::RCC::RCCUserSlave {\n"
	    "  private:\n"
	    "    std::string dont_care_temp;\n"
	    "  public:\n"
	    "    Slave%u(): RCCUserSlave(%u){/* Default constructor */}\n",
	    index+1, index+1, index);
    for (auto prop_it = (*it).second->m_ctl.properties.begin();
	 prop_it != (*it).second->m_ctl.properties.end(); ++prop_it) {
      OM::Property &p = **prop_it;
      std::string cast, type, pretty;
      // This is the bare minimum for enum types and base types.
      // FIXME: more types
      if (p.m_baseType == OA::OCPI_Enum) {
	if (!strcasecmp(p.m_name.c_str(), "ocpi_endian")) {
	  type = "OCPI::RCC::RCCEndian";
	} else
	  OU::format(type, "%s::%c%s", paramConfig.m_slaveTypes[index].c_str(), toupper(p.m_name.c_str()[0]),
		     p.m_name.c_str() + 1);
	pretty = "ULong";
	OU::format(cast, "(%s)", type.c_str());
      } else {
	type = cctypes[p.m_baseType];
	pretty = ccpretty[p.m_baseType];
      }
      std::vector<std::string> offsets(p.m_arrayRank);
      if (p.m_arrayRank) {
	size_t n = p.m_arrayRank - 1;
	offsets[n] = "1";
	while (n > 0) {
	  std::string dimExpr;
	  rccEmitDimension(p.m_arrayDimensions[n], p.m_arrayDimensionsExprs[n], "()", dimExpr);
	  offsets[n-1] = offsets[n] + "*" + dimExpr;
	  n--;
	}
      }
      if (p.m_baseType == OA::OCPI_String)
	fprintf(f, "    inline size_t getLength_%s() { return %zu; }\n", p.m_name.c_str(),
		p.m_stringLength);
      std::string dims, offset;
      const char *comma = "";
      for (unsigned n = 0; n < p.m_arrayRank; n++)
	OU::formatAdd(dims, "%sunsigned idx%u", n ? ", " : "", n);
      if (p.m_arrayRank) {
	for (unsigned n = 0; n < p.m_arrayRank; n++)
	  OU::formatAdd(offset, "%sidx%u*%s", n ? " + " : "", n, offsets[n].c_str());
	comma = ", ";
      } else
	offset = ", 0";
      if (!p.m_isPadding) {
	// always expose the string based interface to the property
	fprintf(f,
		"    inline const char *getProperty_%s(std::string &val,\n"
		"                                      OCPI::API::AccessList &list = "
		"OCPI::API::emptyList,\n"
		"                                      OCPI::API::PropertyOptionList &options = "
		"OCPI::API::noPropertyOptions,\n"
		"                                      OCPI::API::PropertyAttributes *attrs = "
		"NULL) {\n"
		"      checkSlave(\"%s\");\n"
		"      // get the string value of the property based on the ordinal\n"
		"      m_worker->getProperty(%uu, val, list, options, attrs);\n"
		"      return val.c_str();\n"
		"    }\n",
		p.cname(), l_name, p.m_ordinal);
	// expose the faster/typed non-string based interface if it exists
	if (p.m_baseType == OA::OCPI_String && !p.m_isSequence)
	  fprintf(f,
		  "    inline char *get_%s(%s%schar *buf, size_t length) {\n"
		  "      checkSlave(\"%s\");\n"
		  "      m_worker->get%s%s(%uu, buf, length%s%s);\n"
		  "      return buf;\n"
		  "    }\n"
		  "    std::string &get_%s(%s%sstd::string &s) {\n"
		  "      checkSlave(\"%s\");\n"
		  "      size_t len = getLength_%s() + 1;\n"
		  "      char *buf = new char[len];\n"
		  "      m_worker->get%s%s(%uu, buf, len%s%s);\n"
		  "      s = buf;\n"
		  "      delete [] buf;\n"
		  "      return s;\n"
		  "   }\n",
		  p.m_name.c_str(), dims.c_str(), comma, l_name, pretty.c_str(),
		  p.m_isParameter ? "Parameter" : "PropertyOrd", p.m_ordinal, comma,
		  offset.c_str(), p.m_name.c_str(), dims.c_str(), comma, l_name, p.m_name.c_str(),
		  pretty.c_str(), p.m_isParameter ? "Parameter" : "PropertyOrd", p.m_ordinal,
		  comma, offset.c_str());
	else if (p.m_baseType != OA::OCPI_Struct && !p.m_isSequence)
	  fprintf(f,
		  "    inline %s get_%s(%s) {\n"
		  "      checkSlave(\"%s\");\n"
		  "      return %sm_worker->get%s%s(%u%s%s);\n"
		  "    }\n",
		  type.c_str(), p.m_name.c_str(), dims.c_str(), l_name,
		  cast.c_str(),  // if val needs to be cast in the case of an enum
		  pretty.c_str(), p.m_isParameter ? "Parameter" : "PropertyOrd", p.m_ordinal,
		  comma, offset.c_str());
      }
      if (p.m_isWritable) {
	// always expose the string interface to the property
	fprintf(f,
		"    inline void setProperty_%s(const char* val, OCPI::API::AccessList &list "
		"= OCPI::API::emptyList) {\n"
		"      checkSlave(\"%s\");\n"
		"      m_worker->setProperty(\"%s\", val, list);\n",
		p.cname(), l_name, p.cname());
	fprintf(f,
		"#if !defined(NDEBUG)\n"
		"      debugLog(\"Setting slave.setProperty_%s",
		p.cname());
	fprintf(f,
		": %%p\", val);\n");
	fprintf(f,
		"#endif\n"
		"    }\n"
		"    inline void setProperty_%s(const std::string &val, OCPI::API::AccessList "
		"&list  = OCPI::API::emptyList) {\n"
		"      setProperty_%s(val.c_str(), list);\n"
		"    }\n",
		p.cname(), p.cname());
	// expose the faster/typed non-string based interface to the property
	if (p.m_baseType != OA::OCPI_Struct && !p.m_isSequence) {
	  fprintf(f,
		  "    inline void set_%s(%s%s%s val) {\n"
		  "      checkSlave(\"%s\");\n",
		  p.m_name.c_str(), dims.c_str(), comma, type.c_str(), l_name);
	  if (p.m_arrayRank) {
	    fprintf(f,
		    "      unsigned idx = %s;\n"
		    "      m_worker->set%sPropertyOrd(%u, %sval, idx);\n",
		    offset.c_str(), pretty.c_str(), p.m_ordinal,
		    cast.c_str());  // if val needs to be cast in the case of an enum
	  } else
	    fprintf(f,
		    "      m_worker->set%sPropertyOrd(%u, %sval, 0);\n",
		    pretty.c_str(), p.m_ordinal,
		    cast.c_str());  // if val needs to be cast in the case of an enum
	  fprintf(f,
		  "#if !defined(NDEBUG)\n"
		  "      debugLog(\"Setting slave.set_%s",
		  p.m_name.c_str());
	  if (p.m_arrayRank && p.m_baseType != OA::OCPI_Struct)
	    fprintf(f,
		    " at index %%u(0x%%x): 0x%%llx\", idx, idx, (unsigned long long)val);\n");
	  else
	    fprintf(f,
		    ": 0x%%llx\", (unsigned long long)val);\n");
	  fprintf(f,
		  "#endif\n"
		  "    }\n");
	}
	if (p.m_baseType == OA::OCPI_String && !p.m_isSequence)
	  fprintf(f,
		  "    inline void set_%s(%s%sconst std::string &val) {\n"
		  "      checkSlave(\"%s\");\n"
		  "      m_worker->setStringPropertyOrd(%u, val.c_str()%s%s);\n"
		  "    }\n",
		  p.m_name.c_str(), dims.c_str(), comma, l_name, p.m_ordinal, comma, offset.c_str());
      }
    } // for iterate over m_ctl.properties
    fprintf(f,
	    "  } slave%u;\n", index+1);
    index++;
  } // for iterate over m_slaves

  // for backwards compatibility in old single slave interface
  fprintf(f,
	  "\n  Slave1& slave;\n"
	  "  struct Slaves {\n");
  index = 0;
  // declare the slaves structure which will contain a reference to each of the proxies slaves
  // by name.  This structure is how the Worker author will access the slaves.
  for (auto it = paramConfig.m_slaves.begin(); it != paramConfig.m_slaves.end(); ++it, index++)
    fprintf(f, "    Slave%u& %s;\n", index+1, (*it).first.c_str());
  fprintf(f,
	  "  } slaves;\n"
	  "#define OCPI_SLAVE_MEMBER_INITIALIZERS slave(slave1), slaves({");
  auto baseTypes_it = paramConfig.m_slaveBaseTypes.begin();
  unsigned n = 1;
  for (auto it = paramConfig.m_slaves.begin(); it != paramConfig.m_slaves.end();
       ++it, ++baseTypes_it, ++n) {
    auto &slave = *it;
    slave.second->m_baseTypes = *baseTypes_it; // restore the original baseTypes for slaves
    fprintf(f, "%sslave%u", n == 1 ? "" : ", ", n);
  }
  fprintf(f, "})\n");
  return NULL;
}

/*
 * This Function creates the generated header file for the worker named workerName-worker.hh
 */
const char *Worker::
emitImplRCC() {
  const char *err;
  FILE *f;
  if ((err = openOutput(cname(), m_outDir, "",
                        m_language == C ? RCC_C_IMPL : RCC_CC_IMPL,
                        m_language == C ? RCC_C_HEADER : RCC_CC_HEADER, m_implName, f))) {
    return err;
  }
  fprintf(f, "/*\n");
  printgen(f, " *", m_file.c_str());
  fprintf(f, " *\n");
  char *upper = upperdup(m_implName);
  fprintf(f,
          " * This file contains the implementation declarations for the %s worker in %s\n"
          " */\n\n"
          "#ifndef OCPI_RCC_WORKER_%s_H__\n"
          "#define OCPI_RCC_WORKER_%s_H__\n"
          "#include <assert.h>\n"
          "#include <string.h>\n"
          "#include \"RCC_Worker.hh\"\n",
          m_implName, m_language == C ? "C" : "C++", upper, upper);
  if ( m_language == CC )
    fprintf(f, "#include <vector>\n" );
  const char *last;
  fprintf(f,
          "#ifndef OCPI_WORKER_NAME\n"
	  "#define OCPI_WORKER_NAME %s\n"
	  "#define OCPI_WORKER_PREFIX %c%s\n"
	  "#endif\n",
	  upper, toupper(m_implName[0]), m_implName+1);
  if (m_language == C) {
    unsigned in = 0, out = 0;
    if (m_ports.size()) {
      fprintf(f,
              "/*\n"
              " * Enumeration of port ordinals for worker %s\n"
              " */\n"
              "typedef enum {\n",
              m_implName);
      last = "";
      for (unsigned n = 0; n < m_ports.size(); n++) {
        Port *port = m_ports[n];
        fprintf(f, "%s  %s_%s", last, upper, upperdup(port->pname()));
        // FIXME TWO WAY
        last = ",\n";
        if (port->isDataProducer())
          out++;
        else
          in++;
      }
      fprintf(f, "\n} %c%sPort;\n", toupper(m_implName[0]), m_implName+1);
    }
    fprintf(f, "#define %s_N_INPUT_PORTS %u\n"
            "#define %s_N_OUTPUT_PORTS %u\n",
            upper, in, upper, out);
  }
  if (m_ctl.nRunProperties < m_ctl.properties.size()) {
    fprintf(f,
            "/*\n"
            " * Definitions for default values of parameter properties.\n"
            " */\n");
    for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++) {
      OM::Property &p = **pi;
      if (p.m_isParameter) {
        fprintf(f,
                "/* The constant value of the parameter property named: %s */\n"
                "static const ", p.m_name.c_str());
        m_maxLevel = 0;
        size_t offset = 0;
        unsigned pad = 0;
        bool isLast = false;
        std::string type;
        rccType(type, p, 0, offset, pad, m_implName, true, isLast, false, UINT_MAX-1);
        std::string param;
        upperconstant(param, m_implName, p.m_name.c_str());
        OU::formatAdd(type, " %s", param.c_str());
	if (!p.m_isSequence) // sequence has array aspects internal to the struct for it
	  rccArray(type, p, true, isLast, false, false);
	fprintf(f, "%s = OCPI_PARAM_%s_%s();\n", type.c_str(), m_implName, p.m_name.c_str());
      }
    }
  }
  if (m_language == CC) {
    if (!m_paramConfig->m_slaves.empty() && (err = emitImplSlaveTypes(f)))
      return err;
    std::string myTypes;
    emitCppTypesNamespace(f, myTypes);
    std::string s;
    camel(s, m_implName, "WorkerBase", NULL);
    fprintf(f,
            "/*\n"
            " * This is the customized class that is inherited by the actual\n"
            " * derived class implemented by the worker author.  That class\n"
            " * which inherits this one is declared in the skeleton/implementation file.\n"
            " */\n"
            "class %s : public OCPI::RCC::RCCUserWorker {\n"
            "protected:\n",
            s.c_str());

    if (m_scalable) {
      fprintf(f,
              "  unsigned getNearestNeighbor( unsigned next ) const;   // next=0 is nearest, next=1 next nearest etc.\n\n"
              );
    }
    // Note we assume that if the first paramconfig has slaves, they all do
    if (m_paramConfig->m_slaves.empty())
      fprintf(f, "%s()", s.c_str());
    else if ((err = emitImplSlaves(f)))
      return err;
    else
      fprintf(f, "%s(): OCPI_SLAVE_MEMBER_INITIALIZERS", s.c_str());

    bool notifiers = false, writeNotifiers = false, readNotifiers = false;

    // the memory space for properties if m_ctl.nRunProperties is true
    // Output any member initializations dictated by slaves
    fprintf(f, "{");
    if (m_ctl.nRunProperties){
      fprintf(f,"memset((void*)&m_properties, 0, sizeof(m_properties));");
    }
    fprintf(f, "}\n");
    if (m_ctl.nRunProperties){
      fprintf(f,
              "  %s::Properties m_properties;\n"
              "  uint8_t *rawProperties(size_t &size) const {\n"
              "    size = sizeof(m_properties);\n"
              "    return (uint8_t*)&m_properties;\n"
              "  }\n"
              "  inline %s::Properties &properties() { return m_properties; }\n",
              myTypes.c_str(), myTypes.c_str());
      for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++)
        if ((**pi).m_writeSync || (**pi).m_readSync) {
          if (!notifiers)
            fprintf(f, "  typedef OCPI::RCC::RCCResult (%s::*Notification)();\n", s.c_str());
          notifiers = true;
          if ((**pi).m_writeSync) {
            if (!writeNotifiers)
              fprintf(f,
                      "  static Notification s_write_notifiers[];\n"
                      "  void propertyWritten(unsigned ordinal) {\n"
                      "    Notification n = s_write_notifiers[ordinal];\n"
                      "    if (n) (this->*n)(); \n"
                      "  }\n");
            writeNotifiers = true;
            fprintf(f,
                    "  virtual OCPI::RCC::RCCResult %s_written() = 0;\n", (**pi).m_name.c_str());
          }
          if ((**pi).m_readSync) {
            if (!readNotifiers)
              fprintf(f,
                      "  static Notification s_read_notifiers[];\n"
                      "  void propertyRead(unsigned ordinal) {\n"
                      "    Notification n = s_read_notifiers[ordinal];\n"
                      "    if (n) (this->*n)(); \n"
                      "  }\n");
            readNotifiers = true;
            fprintf(f,
                    "  virtual OCPI::RCC::RCCResult %s_read() = 0;\n", (**pi).m_name.c_str());
          }
        }
    }
    for (unsigned n = 0; n < m_ports.size(); n++)
      if ((err = m_ports[n]->emitRccCppImpl(f)))
        return err;
    fprintf(f, "}; // end of worker class\n");
    if (writeNotifiers) {
      fprintf(f, "  %s::Notification %s::s_write_notifiers[] = {\\\n", s.c_str(), s.c_str());
      for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++) {
        OM::Property &p = **pi;
        if (!p.m_isParameter && p.m_writeSync)
          fprintf(f, "  &%c%sWorkerBase::%s_written,\\\n", toupper(m_implName[0]),
                  m_implName + 1, p.m_name.c_str());
        else
          fprintf(f, "  NULL,\\\n");
      }
      fprintf(f, "  };\\\n");
    }
    if (readNotifiers) {
      fprintf(f, "  %s::Notification %s::s_read_notifiers[] = {\\\n", s.c_str(), s.c_str());
      for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++) {
        OM::Property &p = **pi;
        if (!p.m_isParameter && p.m_readSync)
          fprintf(f, "  &%c%sWorkerBase::%s_read,\\\n", toupper(m_implName[0]),
                  m_implName + 1, p.m_name.c_str());
        else
          fprintf(f, "  NULL,\\\n");
      }
      fprintf(f, "  };\\\n");
    }
    fprintf(f,
	    "  typedef %c%sWorkerBase WorkerBase;\n"
            "}\n // end the namespace\n"
            "#define %s_START_INFO \\\n"
            "  extern \"C\" {\\\n"
            "    OCPI::RCC::RCCConstruct ocpi_%s;\\\n"
            "    OCPI::RCC::RCCUserWorker *\\\n"
            "    ocpi_%s(void *place, OCPI::RCC::RCCWorkerInfo &info) {\\\n"
            "      info.size = sizeof(%c%sWorker);\\\n",
	    toupper(m_implName[0]), m_implName + 1,
            upper, m_implName, m_implName,
            toupper(m_implName[0]), m_implName + 1);
    fprintf(f,
            "\n"
            "#define %s_END_INFO \\\n"
            "      return place ? new /*((%c%sWorker *)place)*/ %c%sWorker : NULL;\\\n"
            "    }\\\n"
            "  }\\\n\n",
            upper,
            toupper(m_implName[0]), m_implName + 1,
            toupper(m_implName[0]), m_implName + 1);
  } else {
    if (m_ctl.nRunProperties) {
      fprintf(f,
              "/*\n"
              " * Property structure for worker %s\n"
              " */\n",
              m_implName);
      fprintf(f, "typedef struct __attribute__ ((__packed__)) {\n");
      unsigned pad = 0;
      size_t offset = 0;
      bool isLastDummy = false;
      std::string type;
      for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++)
        if (!(*pi)->m_isParameter || (*pi)->m_isReadable || (*pi)->m_isWritable)
          rccMember(type, **pi, 0, offset, pad, m_implName, true, isLastDummy, false, UINT_MAX-1,
                    !(*pi)->m_isPadding && !(*pi)->m_isVolatile &&
                    ((*pi)->m_isWritable || !(*pi)->m_isReadable));
      fprintf(f, "%s} %c%sProperties;\n\n", type.c_str(),
              toupper(m_implName[0]), m_implName + 1);
    }
    const char *mName;
    fprintf(f,
            "/*\n"
            " * Use this macro, followed by a semicolon, to declare methods before\n"
            " * implementing them, and before defining the RCCDispatch for the worker\n"
            " * e.g.:\n"
            " * %s_METHOD_DECLARATIONS;\n"
            " */\n"
            "#define %s_METHOD_DECLARATIONS \\\n",
            upper, upper);
    if (m_ctl.controlOps) {
      last = "";
      fprintf(f, " %s RCCMethod ", m_pattern ? "extern" : "static");
      unsigned op = 0;
      for (const char **cp = OM::Worker::s_controlOpNames; *cp; cp++, op++)
        if (m_ctl.controlOps & (1u << op)) {
          if ((err = rccMethodName(*cp, mName))) {
            free((void *)mName);
            return err;
          }
          fprintf(f, "%s%s", last, mName);
          last = ", ";
        }
      fprintf(f, ";\\\n");
    }
    if ((err = rccMethodName("run", mName))) {
      free((void *)mName);
      return err;
    }
    fprintf(f,
            " %s RCCRunMethod %s\\\n",
            m_pattern ? "extern" : "static", mName);
    fprintf(f, "/**/\n");
    fprintf(f,
            "/*\n"
            " * This macro defines the initialization of the RCCDispatch structure\n"
            " * for the %s worker. Insert it AFTER any customized initializations\n"
            " * of members: memSizes, runCondition.\n"
            " * E.g.: \n"
            " * static RCCRunCondition myRunCondition { ... };\n"
            " * %s_METHOD_DECLARATIONS;\n"
            " * RCCDispatch xyz_dispatch = {\n"
            " * .runCondition = &myRunCondition,\n"
            " * %s_DISPATCH\n"
            " * };\n"
            " */\n"
            "#define %s_DISPATCH \\\n"
            " .version = RCC_VERSION,\\\n"
            " .numInputs = %s_N_INPUT_PORTS,\\\n"
            " .numOutputs = %s_N_OUTPUT_PORTS,\\\n"
            " .threadProfile = %u,\\\n",
            m_implName, upper, upper, upper, upper, upper, m_isThreaded ? 1 : 0);
    if (m_ctl.nRunProperties)
      fprintf(f, " .propertySize = sizeof(%c%sProperties),\\\n",
              toupper(m_implName[0]), m_implName + 1);
    unsigned op = 0;
    for (const char **cp = OM::Worker::s_controlOpNames; *cp; cp++, op++)
      if (m_ctl.controlOps & (1u << op)) {
        if ((err = rccMethodName(*cp, mName))) {
          free((void *)mName);
          return err;
        }
        fprintf(f, " .%s = %s,\\\n", *cp, mName);
      }
    if ((err = rccMethodName("run", mName))) {
      free((void *)mName);
      return err;
    }
    fprintf(f, " .run = %s,\\\n", mName);
    uint32_t optionals = 0;
    for (unsigned n = 0; n < m_ports.size(); n++) {
      Port *port = m_ports[n];
      if (port->isDataOptional())
        optionals |= 1u << n;
    }
    if (optionals)
      fprintf(f, " .optionallyConnectedPorts = 0x%x,\\\n", optionals);
    fprintf(f, "/**/\n");
    for (unsigned n = 0; n < m_ports.size(); n++)
      m_ports[n]->emitRccCImpl(f);
    for (unsigned n = 0; n < m_ports.size(); n++)
      m_ports[n]->emitRccCImpl1(f);
    free((void *)mName);
  }
  fprintf(f, "#endif /* ifndef OCPI_RCC_WORKER_%s_H__ */\n", upper);
  fclose(f);
  if ((err = openOutput(nsname(), m_outDir, "", RCCMAP, RCC_C_HEADER, NULL, f)))
    return err;
  fprintf(f, "#define RCC_FILE_WORKER_%s %s\n", nsname(), m_implName);
  fprintf(f, "#define RCC_FILE_WORKER_ENTRY_%s %s%s\n", nsname(),
          m_language == C ? "" : "ocpi_", m_implName);
  fclose(f);
  return 0;
}

const char *Worker::
emitSkelRCC() {
  const char *err;
  FILE *f;
  if ((err = openOutput(cname(), m_outDir, "", "-skel",
                        m_language == C ? ".c" : ".cc", NULL, f)))
    return err;
  fprintf(f, "/*\n");
  printgen(f, " *", m_file.c_str(), true);
  fprintf(f,
          " *\n"
          " * This file contains the implementation skeleton for the %s worker in %s\n"
          " */\n\n"
          "#include \"%s%s%s\"\n\n",
          m_implName, m_language == C ? "C" : "C++", m_implName,
          m_language == C ? RCC_C_IMPL : RCC_CC_IMPL,
          m_language == C ? RCC_C_HEADER : RCC_CC_HEADER);
  const char *upper = upperdup(m_implName); // Should move to C++11 unique pointer. Or even better, use string functions.
  if (m_language == C) {
    fprintf(f,
            "%s_METHOD_DECLARATIONS;\n"
            "RCCDispatch %s = {\n"
            " /* insert any custom initializations here */\n"
            " %s_DISPATCH\n"
            "};\n\n"
            "/*\n"
            " * Methods to implement for worker %s, based on metadata.\n"
            " */\n",
            upper, m_implName,
            upper, m_implName);
  } else {
    fprintf(f,
            "using namespace OCPI::RCC; // for easy access to RCC data types and constants\n"
            "using namespace %c%sWorkerTypes;\n"
            "\n"
            "class %c%sWorker : public %c%sWorkerBase {\n",
            toupper(m_implName[0]), m_implName + 1,
            toupper(m_implName[0]), m_implName + 1,
            toupper(m_implName[0]), m_implName + 1);
  }
  unsigned op = 0;
  const char **cp;
  const char *mName; // TODO: Move to std::string to stop worrying
  for (cp = OM::Worker::s_controlOpNames; *cp; cp++, op++)
    if (m_ctl.controlOps & (1u << op)) {
      if ((err = rccMethodName(*cp, mName))) {
        free((void *)mName);
        free((void *)upper);
        return err;
      }
      if (m_language == C)
        fprintf(f,
                "\n"
                "%s RCCResult\n%s(RCCWorker *self) {\n"
                " return RCC_OK;\n"
                "}\n",
                m_pattern ? "extern" : "static", mName);
      else
        fprintf(f,
                "  RCCResult %s() {\n"
                "    return RCC_OK;\n"
                "  }\n", mName);
    }

  if ((err = rccMethodName("run", mName))) {
    free((void *)mName);
    free((void *)upper);
    return err;
  }
  if (m_language == C)
    fprintf(f,
            "\n"
            "%s RCCResult\n%s(RCCWorker *self, RCCBoolean timedOut, RCCBoolean *newRunCondition) {\n"
            " (void)self;(void)timedOut;(void)newRunCondition;\n"
            " return RCC_DONE; // change this as needed for this worker to do something useful\n"
            " // return RCC_ADVANCE; when all inputs/outputs should be advanced each time \"run\" is called.\n"
            " // return RCC_ADVANCE_DONE; when all inputs/outputs should be advanced, and there is nothing more to do.\n"
            " // return RCC_DONE; when there is nothing more to do, and inputs/outputs do not need to be advanced.\n"
            "}\n",
            m_pattern ? "extern" : "static", mName);
  else {
    for (PropertiesIter pi = m_ctl.properties.begin(); pi != m_ctl.properties.end(); pi++) {
      if ((**pi).m_writeSync)
        fprintf(f,
                "  // notification that %s property has been written\n"
                "  RCCResult %s_written() {\n"
                "    return RCC_OK;\n"
                "  }\n",
                (**pi).m_name.c_str(), (**pi).m_name.c_str());
      if ((**pi).m_readSync)
        fprintf(f,
                "  // notification that %s property will be read\n"
                "  RCCResult %s_read() {\n"
                "    return RCC_OK;\n"
                "  }\n",
                (**pi).m_name.c_str(), (**pi).m_name.c_str());
    }
    fprintf(f,
            "  RCCResult run(bool /*timedout*/) {\n"
            "    return RCC_DONE; // change this as needed for this worker to do something useful\n"
            "    // return RCC_ADVANCE; when all inputs/outputs should be advanced each time \"run\" is called.\n"
            "    // return RCC_ADVANCE_DONE; when all inputs/outputs should be advanced, and there is nothing more to do.\n"
            "    // return RCC_DONE; when there is nothing more to do, and inputs/outputs do not need to be advanced.\n"
            "  }\n");
  }
  if (m_language == CC) {
    fprintf(f,
            "};\n\n"
            "%s_START_INFO\n"
            "// Insert any static info assignments here (memSize, memSizes, portInfo)\n"
            "// e.g.: info.memSize = sizeof(MyMemoryStruct);\n"
            "// YOU MUST LEAVE THE *START_INFO and *END_INFO macros here and uncommented in any case\n"
            "%s_END_INFO\n",
            upper, upper);
  }
  fclose(f);
  free((void *)mName);
  free((void *)upper);
  return 0;
}

const char *ParamConfig::
addSlavesConfig(ezxml_t a_slaves) {
  m_slavesString = ezxml_toxml(a_slaves);
  m_slavesXml = ezxml_parse_str(m_slavesString, strlen(m_slavesString));
  assert(m_slavesXml);
  const char *err;
  ocpiInfo("For config %zu, slave before conditional is:"
	   "\n===Original:\n%s\n===Copy:\n%s",
	   nConfig, ezxml_toxml(a_slaves), ezxml_toxml(m_slavesXml));
  if ((err = OB::parseConditionals(m_slavesXml, *this)))
    return OU::esprintf("Error processing conditional slave assembly: %s", err);
  ocpiInfo("===After processing:\n%s", ezxml_toxml(m_slavesXml));
  //cout << ezxml_toxml(m_xml);
  m_slavesAssembly = new ::Assembly(m_worker);
  static const char *instAttrs[] = {INST_ATTRS, "optional"};
  if ((err = m_slavesAssembly->parseAssy(m_slavesXml, NULL, instAttrs)))
    return err;
  Instance *i = &m_slavesAssembly->m_instances[0];
  for (unsigned n = 0; n < m_slavesAssembly->m_instances.size(); n++, i++) {
    unsigned np = 0;
    Port *slavePort = NULL, *port = NULL;
    bool hasIndex = false;
    size_t index = 0;
    for (InstancePort *ip = &i->m_ports[0]; !port && np < i->m_worker->m_ports.size(); np++, ip++)
      for (auto pit = ip->m_attachments.begin(); !port && pit != ip->m_attachments.end(); ++pit)
	if ((*pit)->m_connection.m_external) {
	  port = (*pit)->m_connection.m_external->m_instPort.m_port;
	  slavePort = ip->m_port;
	  hasIndex = (*pit)->m_connection.m_count != 0;
	  index = (*pit)->m_index;
	  break;
	}
    Worker &wkr = *i->m_worker;
    wkr.m_isSlave = true;
    if ((err = OE::getBoolean(i->m_xml, "optional", &wkr.m_isOptional)))
      return err;
    wkr.m_slavePort = slavePort; // an external connection to this port
    wkr.m_proxyPort = port;      // the proxy port
    if (hasIndex) // from connection
      wkr.m_proxyPortIndex = index;
    if (!m_slaveNames.insert(i->m_name).second)
      return OU::esprintf("Duplicate slave name: %s", i->m_name.c_str());
    m_slaves.emplace_back(i->m_name, &wkr);
  }
  return NULL;
}

/*
 * This function parses the xml for the slaves of the RCC worker (if there are any).
 * There are 2 ways to specify slaves the legacy way as a "slave" attribute at the top level worker
 * element. This way is still supported for backwards compatibility reasons.  The second way is
 * "slave" elements underneath the worker element.  Both in the same xml is not supported.  This
 * function pulls information out of the xml and puts it into the m_slaves class variable which is
 * a vector of pairs of Worker pointer(pointer to slave object) and string (name of worker).  The
 * name of the worker can be specified in xml.  If it is not specified it is auto generated as the
 * "workerName" if there is only one and if there is more then one as "workerName_X".
 * there is also the "optional" issue:  it is optional if it is not present in all assemblies
 */
const char* Worker::
parseSlaves() {
  const char *err;
  std::string l_slave;
  bool attr = OE::getOptionalString(m_xml, l_slave, "slave");
  ezxml_t
    firstSlave = ezxml_cchild(m_xml, "slave"),
    l_slaves = ezxml_child(m_xml, "slaves");
  switch (!!attr + !!firstSlave + !!l_slaves) {
  case 0:
    return NULL;
  case 1:
    break;
  default:
    return OU::esprintf("Only one of slave-attribute, slave elements, or slaves element is allowed");
  }
  // Add the slaves to all parameter configurations
  // Note that slave assemblies may actually be conditional based on parameter values
  for (unsigned n = 0; n < m_paramConfigs.size(); ++n) {
    if (!m_paramConfigs[n])
      continue;
    if (!l_slaves) {
      // Make fake assemblies out of the non-assembly attribute or elements
      std::string xml("<slaves>");
      if (attr) {
	std::string instanceName = l_slave.substr(0, l_slave.find(".", 0));
	OU::formatAdd(xml, "<instance name='%s' worker='%s'/>",
		      l_slave.substr(0, l_slave.find(".", 0)).c_str(), l_slave.c_str());
      } else {
	for (ezxml_t slave = ezxml_cchild(m_xml, "slave"); slave; slave = ezxml_cnext(slave)) {
	  if ((err = OE::checkAttrs(slave, "name", "worker", "optional", NULL)))
	    return err;
	  const char
	    *worker = ezxml_cattr(slave, "worker"),
	    *l_name = ezxml_cattr(slave, "name");
	  bool optional = false;
	  if ((err = OE::getBoolean(slave, "optional", &optional)))
	    return err;
	  if (!worker)
	    return OU::esprintf("Missing \"worker\" attribute in <slave> element");
	  OU::formatAdd(xml, "\n  <instance worker='%s'", worker);
	  if (l_name)
	      OU::formatAdd(xml, " name='%s'", l_name);
	  if (optional)
	    OU::formatAdd(xml, " optional='true'");
	  xml += "/>";
	}
	xml += "</slaves>";
      }
      l_slaves = ezxml_parse_str(strdup(xml.c_str()), xml.size()); // leak
      assert(l_slaves);
    }
    if ((err = m_paramConfigs[n]->addSlavesConfig(l_slaves)))
      return OU::esprintf("slave processing error: %s", err);
  }
  return NULL;
}

/*
 * What implementation-specific attributes does an RCC worker have?
 * And which are not available at runtime?
 * And if they are indeed available at runtime, do we really retreive them from the
 * container or just let the container use what it knows?
 * This function parses the RCC OWD and fills in the information (that is RCC specific) into
 * the Worker object member variables.
 */
const char *Worker::
parseRccImpl(const char *a_package) {
  const char *err = NULL;
  if ((err = OE::checkAttrs(m_xml, RCC_IMPL_ATTRS, (void*)0)) ||
      (err = OE::checkElements(m_xml, RCC_IMPL_ELEMS, "port", (void*)0))) {
    return err;
  }
  // We use the pattern value as the method naming for RCC
  // and its presence indicates "extern" methods.
  m_pattern = ezxml_cattr(m_xml, "ExternMethods");
  m_staticPattern = ezxml_cattr(m_xml, "StaticMethods");
  ezxml_t xctl;
  if ((err = parseSpec(a_package)) ||
      (err = parseImplControl(xctl)) ||
      (xctl && (err = OE::checkAttrs(xctl, GENERIC_IMPL_CONTROL_ATTRS, "Threaded", (void *)0))) ||
      (err = OE::getBoolean(m_xml, "Threaded", &m_isThreaded)))
    return err;
  // Parse data port implementation metadata: maxlength, minbuffers.
  for (ezxml_t x = ezxml_cchild(m_xml, "Port"); x; x = ezxml_cnext(x)) {
    const char *internal = ezxml_cattr(x, "internal");
    if (internal) {
      const char
        *input = ezxml_cattr(x, "inputname"),
        *output = ezxml_cattr(x, "outputname"),
        *inDist = ezxml_cattr(x, "inDistribution"),
        *outDist = ezxml_cattr(x, "outDistribution"),
        *dist = ezxml_cattr(x, "distribution");

      std::string in, out;
      if (!input && !output) {
        in = internal;
        in += "_in";
        input = in.c_str();
        out = internal;
        out += "_out";
        output = out.c_str();
      } else if (!input || !output)
        return
          OU::esprintf("Both \"inputname\" and \"outputname\" must be specified or neither");
      ezxml_set_attr(x, "optional", "1");
      char *copy = ezxml_toxml(x); // snapshot a copy for the output port
      // Create the input port
      ezxml_set_attr(x, "producer", "0");
      ezxml_set_attr(x, "implname", input);
      if (!dist && inDist)
        ezxml_set_attr(x, "distribution", inDist);
      if (!createDataPort<RccPort>(*this, x, NULL, -1, err))
        return err;
      // The original XML has been patched to become the input side XML.
      // Now we need to clone it (NOT share it) to become the output side XML
      ezxml_t ox = ezxml_parse_str(copy, strlen(copy));
      ezxml_set_attr(ox, "producer", "1");
      ezxml_set_attr(ox, "implname", output);
      if (!dist && outDist)
        ezxml_set_attr(ox, "distribution", outDist);
      if (!createDataPort<RccPort>(*this, ox, NULL, -1, err))
        return err;
    } else {
      DataPort *dp;
      if ((err = checkDataPort(x, dp)) || !createDataPort<RccPort>(*this, x, dp, -1, err))
        return err;
    }
  }
  for (unsigned i = 0; i < m_ports.size(); i++)
    m_ports[i]->finalizeRccDataPort();
  return NULL;
}
// slave parsing depends on proxy port expressions
const char *Worker::
finalizeRCC() {
  // don't parse slaves if we are not doing codegen since it depends on other workers
  return m_parentFile.empty() || (m_parent && m_parent->m_type == Assembly) ? parseSlaves() : NULL;
}


// RCC assemblies are collections of reusable instances with no connections.
const char *Worker::
parseRccAssy() {
  const char *err;
  ::Assembly *a = m_assembly = new ::Assembly(*this);
  // Do the generic assembly parsing, then to more specific to RCC
  static const char *instAttrs[] = { "paramconfig", NULL };
  if ((err = a->parseAssy(m_xml, NULL, instAttrs)))
    return err;
  m_dynamic = g_dynamic;
  m_optimized = g_optimized;
  return NULL;
}

// This is an RCC file, and perhaps an assembly or a platform
const char *Worker::
parseRcc(const char *a_package) {
  const char *lang = ezxml_cattr(m_xml, "Language");
  if (!lang)
    m_language = C;
  else if (!strcasecmp(lang, "C"))
    m_language = C;
  else if (!strcasecmp(lang, "C++"))
    m_language = CC;
  else
    return OU::esprintf("Language attribute \"%s\" is not \"C\" or \"C++\""
                        " in RccWorker xml file: '%s'", lang, m_file.c_str());
  const char *err;
  m_model = RccModel;
  m_modelString = "rcc";
  m_baseTypes = rccTypes;
  // Here is where there is a difference between a implementation and an assembly
  if (!strcasecmp(m_xml->name, "RccWorker") ||
      !strcasecmp(m_xml->name, "RccImplementation") ||
      !strcasecmp(m_xml->name, "ComponentSpec")) {
    if ((err = parseRccImpl(a_package)))
      return OU::esprintf("in %s for %s: %s", m_xml->name, m_implName, err);
  } else if (!strcasecmp(m_xml->name, "RccAssembly")) {
    if ((err = parseRccAssy()))
      return OU::esprintf("in %s for %s: %s", m_xml->name, m_implName, err);
  } else
      return "file contains neither a ComponentSpec, RccWorker, nor an RccAssembly";
  m_reusable = true;
  return NULL;
}

RccAssembly *RccAssembly::
create(ezxml_t xml, const char *xfile, const std::string &parentFile, const char *&err) {
  RccAssembly *ha = new RccAssembly(xml, xfile, parentFile, err);
  if (err) {
    delete ha;
    ha = NULL;
  }
  return ha;
}

RccAssembly::
RccAssembly(ezxml_t xml, const char *xfile, const std::string &parentFile, const char *&err)
  : Worker(xml, xfile, parentFile, Worker::Assembly, NULL, NULL, err) {
  if (!err)
    err = parseRcc();
}

RccAssembly::
~RccAssembly() {
}

const char * DataPort::
emitRccCppImpl(FILE *f) {
  // Define the union of structures for messages for operations
  fprintf(f,
          "  class %c%sPort : public OCPI::RCC::RCCUserPort {\n",
          toupper(cname()[0]), cname()+1);
  // Now emit structs for messages
  OM::Operation *o = operations();
  if (o) {
    std::string ops;
    OU::format(ops, "%c%sOperations", toupper(cname()[0]), cname()+1);
    // Constructor
    fprintf(f,
            "  public:\n"
            "    %c%sPort()",
            toupper(cname()[0]), &cname()[1]);
    o = operations();
    bool first = true;
    for (unsigned nn = 0; nn < nOperations(); nn++, o++)
      if (o->nArgs()) {
        std::string s;
        camel(s, o->cname());
        fprintf(f, "%s m_%sOp(*this)", first ? " :" : ",", s.c_str());
        first = false;
      }
    fprintf(f, " {\n    }\n");

    // Start Op class

    // Now we need a class for each operation
    o = operations();
    for (unsigned nn = 0; nn < nOperations(); nn++, o++) {
      std::string s;
      camel(s, o->cname());
      fprintf(f, "    //////// %s (%zu arguments) ////////\n", s.c_str(), o->nArgs());
      if (o->nArgs()) {
        std::string op;
        camel(op, worker().m_implName, "WorkerTypes::", OM::Protocol::cname(),
              o->cname());
        fprintf(f,
                "    class %sOp : public OCPI::RCC::RCCPortOperation {\n"
                "    public:\n"
                "       %sOp(RCCUserPort &p)\n"
                "         : OCPI::RCC::RCCPortOperation(p, %s_OPERATION),\n",
                s.c_str(), s.c_str(), op.c_str());
        OB::Member *m = o->args();
        for (unsigned n = 0; n < o->nArgs(); m++) {
          std::string a;
          camel(a, m->m_name.c_str());
          fprintf(f, "           m_%sArg(*this)%s", a.c_str(), ++n == o->nArgs() ? "" : ", ");
        }
        fprintf(f,
                " {\n"
                "         }\n"
                "       %sOp(RCCUserPort &p, const %sOp &rhs)\n"
                "         : OCPI::RCC::RCCPortOperation(p, %s_%s),\n",
                s.c_str(), s.c_str(), upperdup(worker().m_implName), upperdup(cname()));
        m = o->args();
        for (unsigned n = 0; n < o->nArgs(); m++) {
          std::string a;
          camel(a, m->m_name.c_str());
          fprintf(f, "           m_%sArg(*this)%s", a.c_str(), ++n == o->nArgs() ? "" : ", ");
        }
        fprintf(f,
                " {\n"
                "         setBuffer(rhs.m_buffer);\n"
                "       }\n"
                "       void setBuffer(RCCUserBuffer* buffer) {\n"
                "         m_buffer = buffer;\n"
                "       }\n"
                );

        // Arg enums
        m = o->args();
        fprintf(f, "       enum { \n" );
        for (unsigned n = 0; n < o->nArgs(); n++, m++) {
          std::string a;
          camel(a, m->m_name.c_str() );
          fprintf(f,"         %s_ARG%s\n",  a.c_str(), n == o->nArgs() - 1 ? "" : ",");
        }
        fprintf(f, "       }; \n" );

        // And a class for each arg in the operation
        m = o->args();
        for (unsigned n = 0; n < o->nArgs(); n++, m++) { // TODO: Why void * when we know the type?
          std::string a;
          camel(a, m->m_name.c_str() );
          std::string p;
          camel(p, cname() );
          std::string on;
          camel(on, worker().m_implName, "WorkerTypes::", OM::Protocol::cname(),
                o->cname());
          std::string type;
          size_t offset;
          unsigned pad;
          bool isLast;
          //      m_worker->rccType(type, *m, 1, offset, pad, on.c_str(), false, isLast,
          worker().rccBaseType(type, *m, 1, offset, pad, on.c_str(), false, isLast, 0);
          fprintf(f,
                  "       class %sArg : public OCPI::RCC::RCCPortOperationArg { \n"
                  "       private:\n"
                  "          mutable %s *m_myptr;\n",
                  a.c_str(), type.c_str());
          std::string get;
          // FIXME: CACHE THIS UNTIL BUFFER CHANGES...
          OU::format(get, "m_myptr = (%s *)getArgAddress(%s, %s);\n",
                     type.c_str(), m->m_isSequence ? "&m_size" : "NULL",
                     m->m_isSequence ? "&m_capacity" : "NULL");
          if (m->m_isSequence)
            fprintf(f, "          mutable size_t m_size, m_capacity;\n");
          fprintf(f,
                  "       public:\n"
                  "          %sArg(RCCPortOperation &po) : RCCPortOperationArg(po, %s_ARG), m_myptr(NULL) {}\n"
                  "          inline%s %s *data() %s{\n"
                  "            %s"
                  "            return m_myptr;\n"
                  "          }\n",
                  a.c_str(), a.c_str(),
                  m_isProducer ? "" : " const", type.c_str(), m_isProducer ? "" : "const ",
                  get.c_str());
          if (m->m_isSequence) {
            fprintf(f,
                    "         inline size_t size() %s{\n"
                    "           %s"
                    "           return m_size;\n"
                    "         }\n"
                    "         inline size_t capacity() %s{\n"
                    "           %s"
                    "           return m_capacity;\n"
                    "         }\n",
                    m_isProducer ? "" : "const ", get.c_str(),
                    m_isProducer ? "" : "const ", get.c_str());
            if (m_isProducer) {
              if (n != o->nArgs() - 1)
                return OU::esprintf("for protocol \"%s\" operation \"%s\" argument \"%s\": "
                                    "sequences can only be last argument in operation",
                                    OM::Protocol::cname(), o->cname(),
                                    m->cname());
              fprintf(f,
                      "         inline void resize(size_t size) {\n"
                      "           setArgSize(size);\n"
                      "         }\n");
            }
          }
          if (!m_opScaling.empty() && m_opScaling[n] != NULL)
              fprintf(f,
                      "          bool endOfWhole() const; \n"
                      "          void partSize(%sOCPI::RCC::RCCPartInfo &part) const;\n",
                      m->m_arrayRank ? "unsigned dimension, " : "");

            fprintf(f,
                    "       } m_%sArg;\n",
                    a.c_str());
            // Add an accessor for each argument in case they are variable length.
            type.clear();
            worker().rccType(type, *m, 1, offset, pad, on.c_str(), false, isLast,
                              o->isTopFixedSequence(), 0);
            if (m->m_isSequence || m->m_arrayRank)
              fprintf(f,
                      "      %s%sArg %s() %s{ return m_%sArg; }\n",
                      m_isProducer ? "" : "const ", a.c_str(),
                      m->m_name.c_str(), m_isProducer ? "" : "const ",
                      a.c_str());
            else if (m->m_baseType == OA::OCPI_String)
              fprintf(f,
                      "      %s%s *%s() %s{ return m_%sArg.data(); }\n",
                      m_isProducer ? "" : "const ", type.c_str(), m->m_name.c_str(),
                      m_isProducer ? "" : "const ", a.c_str());
            else
              fprintf(f,
                      "      %s%s &%s() %s{ return *m_%sArg.data(); }\n",
                      m_isProducer ? "" : "const ", type.c_str(), m->m_name.c_str(),
                      m_isProducer ? "" : "const ", a.c_str());
        }
        // End args
        fprintf(f,
                "    } m_%sOp;\n"
                "    // Conversion operators\n"
                "    inline operator %sOp &() { m_%sOp.setBuffer(this); return m_%sOp; }\n"
                "    // Factories, used to take messages\n"
                "    inline %sOp* take(%sOp &rhs) const {\n"
                "      %sOp *so = new %sOp(rhs);\n"
                "      return so;\n"
                "    }\n",
                s.c_str(), s.c_str(), s.c_str(), s.c_str(), s.c_str(), s.c_str(), s.c_str(),
                s.c_str());
      // End Op class
      }
    }
    first = true;
    o = operations();
    for (unsigned nn = 0; nn < nOperations(); nn++, o++)
      if (o->nArgs()) {
        std::string s, prot, aprefix;
        camel(s, o->cname());
        camel(prot, OM::Protocol::cname());
        camel(aprefix, worker().m_implName, "WorkerTypes::", prot.c_str(),
              o->cname());
        if (first) {
          fprintf(f, "  public:\n");
          first = false;
        }
        fprintf(f,
                "    %s%sOp &%s() {\n"
                "      assert(hasBuffer());\n"
                "      return m_%sOp;\n"
                "    }\n"
                "    inline %s%sOp &%s_op() { return %s(); }\n",
                !m_isProducer ? "const " : "", s.c_str(), o->cname(), s.c_str(),
                !m_isProducer ? "const " : "", s.c_str(), o->cname(), o->cname());
      }
  }
  fprintf(f, "  } %s;\n", cname());
  return NULL;
}
void DataPort::
emitRccCImpl(FILE *f) {
  if (operations()) {
    unsigned nn;
    for (nn = 0; nn < ::Port::m_ordinal; nn++)
      if (worker().m_ports[nn]->isData()) {
        DataPort *dp = static_cast<DataPort*>(worker().m_ports[nn]);

        if (dp->operations() &&
            !strcasecmp(dp->OM::Protocol::cname(), OM::Protocol::cname()))
          break;
      }
    if (nn >= ::Port::m_ordinal) {
      fprintf(f,
              "/*\n"
              " * Enumeration of operations for protocol %s (%s)\n"
              " */\n"
              "typedef enum {\n",
              OM::Protocol::m_name.c_str(), OM::Protocol::m_qualifiedName.c_str());
      OM::Operation *o = operations();
      char *puName = upperdup(OM::Protocol::cname());
      for (unsigned no = 0; no < nOperations(); no++, o++) {
        char *ouName = upperdup(o->cname());
        fprintf(f, " %s_%s,\n", puName, ouName);
        free((void*)ouName);
      }
      free(puName);
      fprintf(f, "} %c%sOperation;\n",
              toupper(*OM::Protocol::cname()),
              OM::Protocol::cname() + 1);
    }
  }
}

void DataPort::
emitRccCImpl1(FILE *f) {
  if (operations()) {
    char *upper = upperdup(worker().m_implName);
    fprintf(f,
            "/*\n"
            " * Enumeration of operations on port %s of worker %s\n"
            " */\n"
            "typedef enum {\n",
            cname(), worker().m_implName);
    OM::Operation *o = operations();
    char *puName = upperdup(cname());
    for (unsigned nn = 0; nn < nOperations(); nn++, o++) {
      char *ouName = upperdup(o->cname());
      fprintf(f, "  %s_%s_%s,\n", upper, puName, ouName);
      free(ouName);
    }
    free(puName);
    free(upper);
    fprintf(f, "} %c%s%c%sOperation;\n",
            toupper(worker().m_implName[0]), worker().m_implName+1,
            toupper(cname()[0]), cname()+1);
    // Now emit structs for messages
    o = operations();
    for (unsigned nn = 0; nn < nOperations(); nn++, o++)
      if (o->nArgs()) {
        fprintf(f,
                "/*\n"
                " * Structure for the \"%s\" operation on port \"%s\"\n"
                " */\n"
                "typedef struct __attribute__ ((__packed__)) {\n",
                o->cname(), cname());
        std::string s;
        camel(s, worker().m_implName, cname(), o->cname());
        bool isLast = false;
        std::string type;
        worker().rccStruct(type, o->nArgs(), o->args(), 0, s.c_str(), false, isLast,
                            o->isTopFixedSequence(), UINT_MAX-1);
        fprintf(f, "%s} %s;\n", type.c_str(), s.c_str());
        OpScaling *os = m_opScaling.empty() ? NULL : m_opScaling[nn];
        if (os && os->m_isPartitioned) {
          OB::Member *arg = o->m_args;
          fprintf(f,
                  "/*\n"
                  " * PartInfo Structure for the %s operation on port %s\n"
                  " */\n"
                  "typedef struct __attribute__ ((__packed__)) {\n",
                  o->cname(), cname());
          for (unsigned a = 0; a < o->m_nArgs; a++, arg++) {
            Partitioning *ap = os->m_partitioning[a];
            if (ap && ap->m_scaling.m_min) {
              char *upper_modelString = upperdup(worker().m_modelString);
              fprintf(f, "  %sPartInfo %s_info[%zu];\n",
                      upper_modelString, arg->m_name.c_str(),
                      arg->m_isSequence ? 1 : arg->m_arrayRank);
              free((void *) upper_modelString);
              size_t dummy1 = 0;
              unsigned dummy2 = 0;
              bool dummy3;
              // std::string type;
              type.clear();
              worker().rccBaseType(type, *arg, 2, dummy1, dummy2, "", false, dummy3, false);
              fprintf(f, "%s *%s;\n", type.c_str(), arg->m_name.c_str());
            }
          }
          fprintf(f,
                  "} %c%s%c%sPartInfo;\n",
                  toupper(worker().m_implName[0]), worker().m_implName+1,
                  toupper(o->cname()[0]), o->cname() + 1);
        }
      }
  }
}

const char *DataPort::
finalizeRccDataPort() {
  const char *err = NULL;
  if (m_type == WDIPort)
    createDataPort<RccPort>(worker(), NULL, this, -1, err);
  return err;
}
RccPort::
RccPort(Worker &w, ezxml_t x, DataPort *sp, int ordinal, const char *&err)
  : DataPort(w, x, sp, ordinal, RCCPort, err) {
  if (x && !err &&
      !(err = OE::checkAttrs(x, SPEC_DATA_PORT_ATTRS, "implname", "workerEOF",
                             "minbuffers", "minbuffercount", "buffersize",
                             DISTRIBUTION_ATTRS, PARTITION_ATTRS, (void*)0)))
    err = OE::checkElements(x, "operation" ,(void*)0);
}
