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

// -*- c++ -*-

#ifndef CommandOption_H
#define CommandOption_H

#include <assert.h>
#include <vector>
#include "BaseDataTypes.hh"
#include "BaseValue.hh"

namespace OCPI {
  namespace Base {
    class BaseCommandOptions {
      const char **m_beforeArgv;
      std::vector<const char *> m_argv;
    protected:
      size_t m_argvCount;
      Member *m_options;
      bool *m_seen;
      const char **m_defaults;
      std::vector<std::string> m_names; // names with underscore translated to hyphen
      unsigned m_nOptions;
      std::string m_error;
      const char *m_help;
      BaseCommandOptions(Member *members, unsigned nMembers, const char *help, const char **defaults);
      ~BaseCommandOptions();
      const char *setError(const char *);
      const char *doValue(Member &m, const char *value, const char **&argv);
    public:
      int usage(); // will return 1 so caller can return usage()
      const char *setArgv(const char **argv);
      const char **argv() { return &m_argv[0]; }
      size_t argvCount() const { return m_argvCount; }
      std::string &error() { return m_error; }
      int main(const char **argv, int (*main)(const char **argv));
      void exitbad(const char *e);
      void bad(const char *fmt, ...);
    };
  }
}
#ifndef OCPI_OPTIONS
#define OCPI_OPTIONS
#endif
#define CMD_OPTION_S(n,b,d,t,v) CMD_OPTION(n,b,d,t,v)
namespace {
#if !defined(OCPI_OPTIONS_CLASS_NAME)
#define OCPI_OPTIONS_CLASS_NAME CommandOptions
#endif
#if !defined(OCPI_OPTIONS_NAME)
#define OCPI_OPTIONS_NAME options
#endif
#if !defined(OCPI_OPTIONS_HELP)
#define OCPI_OPTIONS_HELP ""
#endif
  class OCPI_OPTIONS_CLASS_NAME : public OCPI::Base::BaseCommandOptions {
    // Define the enumeration of options, and the limit
    enum Option {
#define CMD_OPTION(n,b,t,v,d) Option_##n,
     OCPI_OPTIONS
#undef CMD_OPTION
     CMD_OPTION_LIMIT_
    };
    static OCPI::Base::Member s_options[CMD_OPTION_LIMIT_];
    static const char *s_defaults[CMD_OPTION_LIMIT_];
#undef  CMD_OPTION_S
    //    static OCPI::Base::Value s_values[CMD_OPTION_LIMIT_];
  public:
#define CMD_OPTION(n,b,t,v,d)						\
    OCPI::API::t n() const { return m_options[Option_##n].m_default->m_##t; }
#define CMD_OPTION_S(n,b,t,v,d)		   \
    OCPI::API::t *n(size_t &num) const {                         \
      OCPI::Base::Value *val_ = m_options[Option_##n].m_default; \
      assert(val_);                                              \
      assert(val_->m_vt);                                        \
      assert(val_->m_vt->m_isSequence);                          \
      num = val_->m_nElements;                                   \
      return num ? val_->m_p##t : NULL;				 \
    }								 \
    OCPI::API::t *n() const {					 \
      size_t unused;						 \
      return n(unused);					         \
    }
    OCPI_OPTIONS
#undef CMD_OPTION
#undef CMD_OPTION_S
    OCPI_OPTIONS_CLASS_NAME()
      : BaseCommandOptions(s_options, CMD_OPTION_LIMIT_, OCPI_OPTIONS_HELP, s_defaults) {
    };
  };
#define CMD_OPTION(n,b,t,v,d) OCPI::Base::Member(#n,#b,d,OCPI::API::OCPI_##t,false,v),
#define CMD_OPTION_S(n,b,t,v,d) OCPI::Base::Member(#n,#b,d,OCPI::API::OCPI_##t,true,v),
  OCPI::Base::Member OCPI_OPTIONS_CLASS_NAME::s_options[CMD_OPTION_LIMIT_] = { OCPI_OPTIONS };
#undef CMD_OPTION
#undef CMD_OPTION_S
#define CMD_OPTION(n,b,t,v,d) v,
#define CMD_OPTION_S(n,b,t,v,d) v,
  const char *OCPI_OPTIONS_CLASS_NAME::s_defaults[CMD_OPTION_LIMIT_] = { OCPI_OPTIONS };
#undef CMD_OPTION
#undef CMD_OPTION_S
  OCPI_OPTIONS_CLASS_NAME OCPI_OPTIONS_NAME;
}
//#endif // ifdef CMD_OPTIONS


#ifndef OCPI_OPTIONS_NO_MAIN
#ifndef OCPI_OPTIONS_MAIN
#define OCPI_OPTIONS_MAIN mymain
static int mymain(const char **);
#endif
int
main(int /*argc*/, const char **argv) {
  return options.main(argv, OCPI_OPTIONS_MAIN);
}
#endif

#endif
