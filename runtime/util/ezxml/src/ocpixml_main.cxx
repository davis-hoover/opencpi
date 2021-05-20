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

// Replaces the original ocpixml script with C++ version (AV-2501)

#include <cstring> // strcmp
#include <string>
#include <iostream>
#include <fstream>
#include <sstream>
#include <map>
#include <stdexcept>
#include "OcpiXmlEmbedded.h"
#include "OcpiOsFileSystem.h" // This is NOT fully OCPI::OS-enabled, e.g. path names, etc.
#include "OcpiUtilEzxml.h"
#include "OcpiUtilMisc.h"

namespace OU = OCPI::Util;
namespace OX = OCPI::Util::EzXml;
namespace OS = OCPI::OS;

#define OCPI_OPTIONS_HELP \
"This program performs functions relating to the XML inside artifact files.\n"\
"Usage is: ocpixml [<options>] <command> <file> [<file2>]\n"\
"Commands are:\n"\
"  get   - extract the XML from the file to standard output.\n"\
"  strip - remove the XML from the file while copying artifact to <file2>.\n"\
"  add   - add the XML file <file2> to the file, in place. file2 can be '-' for standard input.\n" \
"  parse - parse top-level attributes from an XML file\n"

#define OCPI_OPTIONS \
    CMD_OPTION(log_level  ,  l, ULong,  0, "<log-level>\n" \
	                               "set log level during execution, overriding OCPI_LOG_LEVEL") \
    CMD_OPTION_S(top      ,  t, String, 0, "<top-element>\n" \
	                                   "specify allowable top-level elements") \
    CMD_OPTION_S(attribute,  a, String, 0, "<attribute>\n" \
                                           "specify attribute to print, one per line\n" \
                                           "if name starts with ?, it is optional (blank line output)\n" \
                                           "otherwise its an error if attr is missing\n"\
                                           "if no attributes are specified top element name is printed\n") \
    CMD_OPTION(silent,       s, Bool,  0, "<silent>") \

#include "CmdOption.h"

static void bad(const char *fmt, ...) {
  if (options.silent())
    exit(1);
  va_list ap;
  va_start(ap, fmt);
  const char *err = OU::evsprintf(fmt, ap);
  va_end(ap);
  options.bad(err);
}

static int mymain(const char **argv) {
  // C++11: const std::map<std::string, int> valid_verbs = {{"get",3}, {"strip",4}, {"add",4}};
  std::map<std::string, unsigned> valid_verbs;
  valid_verbs["get"]=1;
  valid_verbs["strip"]=2;
  valid_verbs["add"]=2;
  valid_verbs["check"]=1;
  valid_verbs["parse"]=1;

  if (!argv[0])
    throw std::invalid_argument("missing verb");
  if (not valid_verbs.count(argv[0]))
    throw std::invalid_argument(OU::esprintf("Invalid verb: %s", argv[0]));
  if (options.argvCount()-1 != valid_verbs[argv[0]])
    throw std::invalid_argument(OU::esprintf("Incorrect number of parameters for '%s'", argv[0]));

  // Start "real" work
  std::string xml;

  // add
  if (0 == strcmp("add", argv[0])) {
    std::stringstream buffer;
    if (0 == strcmp("-", argv[2])) { // Special case of stdin
      buffer << std::cin.rdbuf();
    } else {
      std::ifstream src(argv[2], std::ios::binary);
      buffer << src.rdbuf();
    }
    xml = buffer.str();
    OX::artifact_addXML(argv[1],xml); // Throws if invalid XML
  }

  // get
  if (0 == strcmp("get", argv[0])) {
    OX::artifact_getXML(argv[1], xml);
    if (xml.empty()) {
      std::cerr << "This file \"" << argv[1] << "\" is not an artifact file.\n";
      return 1;
    }
    std::cout << xml;
  }

  // check
  if (0 == strcmp("check", argv[0])) {
    OX::artifact_getXML(argv[1], xml);
    return xml.empty() ? 1 : 0;
  }

  // strip
  if (0 == strcmp("strip", argv[0])) {
    OS::FileSystem::copy(argv[1], argv[2]);
    if (!OX::artifact_stripXML(argv[2])) {
      std::cerr << "This file \"" << argv[1] << "\" is not an artifact file.\n";
      OS::FileSystem::remove(argv[2]);
      return 1;
    }
  }

  // parse
  if (0 == strcmp("parse", argv[0])) {
    const char *err;
    std::string parent, file;
    ezxml_t x;
    argv++;
    if ((err = OX::ezxml_parse_file(argv[0], x)))
      bad("For XML file %s:  %s", argv[0], err);
    size_t n;
    if (options.top(n)) {
      for (const char **tops = options.top(n); *tops; ++tops, --n)
	if (!strcasecmp(*tops, ezxml_name(x)))
	  break;
      if (!n)
	bad("For XML file %s:  top element <%s> is invalid", argv[0], ezxml_name(x));
    }
    if (options.attribute(n)) {
      const char *attr;
      std::string out;
      for (const char **attrs = options.attribute(n); *attrs; ++attrs, --n) {
	const char *aname = *attrs;
	if (aname[0] == '?')
	  aname++;
	if ((attr = ezxml_cattr(x, aname)))
	  out += attr;
	else if (attrs[0][0] != '?')
	  bad("For XML file %s:  attribute \"%s\" is misssing", argv[0], aname);
	out += "\n";
      }
      std::cout << out;
    } else
      std::cout << ezxml_name(x) << std::endl;
  }
  return 0;
}
