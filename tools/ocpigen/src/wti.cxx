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

#include "assembly.h"
#include "hdl.h"

WtiPort::
WtiPort(Worker &w, ezxml_t x, Port *sp, int ordinal, const char *&err)
  : OcpPort(w, x, sp, ordinal, WTIPort, "wti", err),
    m_secondsWidth(32), m_fractionWidth(0) {
  if ((err = OE::checkAttrs(x, "Name", "Clock", "SecondsWidth", "FractionWidth",
			    "AllowUnavailable", "Pattern", "master", "myclock", (void*)0)) ||
#if 1
      (err = OE::getExprNumber(x, "SecondsWidth", m_secondsWidth, NULL, m_secondsWidthExpr,
			       &w)) ||
      (err = OE::getExprNumber(x, "FractionWidth", m_fractionWidth, NULL, m_fractionWidthExpr,
			       &w)) ||
#else
      (err = OE::getNumber(x, "SecondsWidth", &m_secondsWidth, 0, 32)) ||
      (err = OE::getNumber(x, "FractionWidth", &m_fractionWidth, 0, 0)) ||
#endif
      (err = OE::getBoolean(x, "AllowUnavailable", &m_allowUnavailable)))
    return;
  for (unsigned i = 0; i < w.m_ports.size(); i++) {
    Port *p = w.m_ports[i];
    if (p->m_type == WTIPort && p != this) {
      err = "More than one WTI specified, which is not permitted";
      return;
    }
  }
  // not yet, need to adjustConnection non-data connections....
  // m_dataWidth = m_secondsWidth + m_fractionWidth;
  m_dataWidth = 64;
}

// Our special copy constructor
WtiPort::
WtiPort(const WtiPort &other, Worker &w , std::string &name, const char *&err)
  : OcpPort(other, w, name, 1, err) {
  if (err)
    return;
  m_secondsWidth = other.m_secondsWidth;
  m_fractionWidth = other.m_fractionWidth;
  m_allowUnavailable = other.m_allowUnavailable;
}

// Virtual constructor: the concrete instantiated classes must have a clone method,
// which calls the corresponding specialized copy constructor
Port &WtiPort::
clone(Worker &w, std::string &name, size_t count, OCPI::Util::Assembly::Role */*role*/,
      const char *&err) const {
  assert(count <= 1);
  return *new WtiPort(*this, w, name, err);
}

bool WtiPort::
haveWorkerOutputs() const {
  return m_allowUnavailable || clock != m_worker->m_wciClock;
}

void WtiPort::
emitPortDescription(FILE *f, Language lang) const {
  OcpPort::emitPortDescription(f, lang);
  const char *comment = hdlComment(lang);
  fprintf(f, "  %s   SecondsWidth: %zu\n", comment, m_secondsWidth);
  fprintf(f, "  %s   FractionWidth: %zu\n", comment, m_fractionWidth);
  fprintf(f, "  %s   AllowUnavailable: %s\n", comment, BOOL(m_allowUnavailable));
  fprintf(f, "  %s   DataWidth: %zu\n", comment, m_dataWidth);
}

const char *WtiPort::
deriveOCP() {
  static uint8_t s[1]; // a non-zero string pointer
  OcpPort::deriveOCP();
  // Time interfaces are quite flexible.
  // Actual scenarios:
  //   worker wants time in default clock domain
  //     says nothing, implies wci clock - no Clk signal
  //   worker wants time in some other of its clock domains
  //     assigns another clock to this port - no Clk signal here
  //   worker wants time in the native timekeepping clock domain
  //     specifies myclock - Clk signal here
  if (myClock) {
    ocp.Clk.master = false;
    ocp.Clk.value = s;
  }
  ocp.MCmd.width = 3;
  ocp.MData.width = m_dataWidth;
  // Note no MReset is present.  OCP says either reset must be present.
  // Thus MCmd is qualified by SReset
  ocp.SReset_n.value = s;
  ocp.SThreadBusy.value = s;
  fixOCP();
  return NULL;
}

void WtiPort::
emitImplSignals(FILE *f) {
  std::string in, out;
  OU::format(in, typeNameIn.c_str(), "");
  OU::format(out, typeNameOut.c_str(), "");
  fprintf(f,
	  "  -- Signals for the outer WTI converted to the inner worker ones\n"
	  "  signal worker_%s : worker_%s_t;\n", in.c_str(), in.c_str());
  if (m_allowUnavailable || clock != m_worker->m_wciClock)
    fprintf(f,
	    "  signal worker_%s : worker_%s_t;\n", out.c_str(), out.c_str());
}
void WtiPort::
emitVhdlShell(FILE *f, Port */*wci*/) {
  std::string in, out;
  OU::format(in, typeNameIn.c_str(), "");
  OU::format(out, typeNameOut.c_str(), "");
  if (clock != m_worker->m_wciClock) {
    fprintf(f, "  -- The WTI interface conversion between OCP and inner worker interfaces\n");
    if (myClock) {
      if (clock->m_output)
	fprintf(f,
		"  %s.Clk <= worker_%s.clk;\n"
		"  -- should be this, but isim crashes.\n"
		"  -- .SReset_n <= from_bool(not wci_reset);\n"
		"  %s.SReset_n <= '0' when its(worker_%s.reset) else '1';\n",
		out.c_str(), out.c_str(), out.c_str(), out.c_str());
      else
	fprintf(f,
		"  worker_%s.clk <= %s.Clk;\n"
		"  worker_%s.reset <= '0' when %s.SReset_n else '1';\n",
		in.c_str(), in.c_str(), in.c_str(), in.c_str());
    } else if (clock->port) {
      // The worker is expected to use the correct clock.
#if 0
      std::string other;
      Port &port = *clock->port;
      Clock &clk = *port.clock;
      OU::format(other, clk.m_output ? port.typeNameOut.c_str() : port.typeNameIn.c_str(), "");
      fprintf(f,
		"  worker_%s.clk <= %s.Clk;\n"
		"  worker_%s.reset <= '0' when %s.SReset_n else '1';\n",
	      in.c_str(), other.c_str(), in.c_str(), other.c_str()); 
#endif
    } else
      assert("No support for global clocks for wti" == 0);
  }     
  if (m_allowUnavailable)
    fprintf(f,
	    "  %s.SThreadBusy(0) <= not worker_%s.request;\n"
	    "  worker_%s.valid <= to_bool(wci_reset and %s.MCmd = ocp.MCmd_WRITE);\n",
	    out.c_str(), out.c_str(), in.c_str(), in.c_str());
  else
    fprintf(f,
	    "  %s.SThreadBusy(0) <= wci_reset;\n", out.c_str());
  if (m_secondsWidth)
    fprintf(f,
	    "  g%s_seconds: if ocpi_port_%s_seconds_width > 0 generate\n"
	    "    worker_%s.seconds <= unsigned(%s.MData(ocpi_port_%s_seconds_width+31 downto 32));\n"
	    "  end generate;\n",
	    pname(), pname(), in.c_str(), in.c_str(), pname());
  if (m_fractionWidth)
    fprintf(f,
	    "  g%s_fraction: if ocpi_port_%s_fraction_width > 0 generate\n"
	    "    worker_%s.fraction <= unsigned(%s.MData(31 downto 32 - ocpi_port_%s_fraction_width));\n"
	    "  end generate;\n",
	    pname(), pname(), in.c_str(), in.c_str(), pname());
}

void WtiPort::
emitVHDLShellPortMap(FILE *f, std::string &last) {
  std::string in, out;
  OU::format(in, typeNameIn.c_str(), "");
  OU::format(out, typeNameOut.c_str(), "");
  fprintf(f,
	  "%s    %s_in => worker_%s",
	  last.c_str(), pname(), in.c_str());
  if (m_allowUnavailable || clock != m_worker->m_wciClock)
    fprintf(f, ",\n    %s_out => worker_%s", pname(), out.c_str());
  last = ",\n";
}

void WtiPort::
emitRecordInputs(FILE *f) {
  if (m_allowUnavailable)
    fprintf(f, "    valid    : Bool_t;\n");
  if (m_secondsWidth)
    fprintf(f, "    seconds  : unsigned(ocpi_port_%s_seconds_width-1 downto 0);\n", pname());
  if (m_fractionWidth)
    fprintf(f, "    fraction : unsigned(ocpi_port_%s_fraction_width-1 downto 0);\n", pname());
}

void WtiPort::
emitRecordOutputs(FILE *f) {
  if (clock != m_worker->m_wciClock)
    fprintf(f,
	    "    clk        : std_logic; -- this ports clk, different from wci_clk\n");
  if (m_allowUnavailable)
    fprintf(f,
	    "    request    : Bool_t; -- worker wants the clock to be valid\n");
}

#if 0
void WtiPort::
emitRecordSignal(FILE *f, std::string &last, const char *prefix, bool inRecord, bool inPackage,
		 bool inWorker) {
  ocpiAssert(!m_master);
  fprintf(f, "%s    -- Signals for %s %s port named \"%s\".  See record type(s) above.\n",
	  last.c_str(), typeName(), masterIn() ? "slave" : "master", pname());

  fprintf(f,
	  "    %-*s : in  worker_%s_t",
	  maxPropName, typeNameIn.c_str(), typeNameIn.c_str());
  if (m_allowUnavailable)
    fprintf(f,
	    ";\n    %-*s : out worker_%s_t",
	    maxPropName, typeNameOut.c_str(), typeNameOut.c_str());
  last = ";\n";
}
#endif
const char *WtiPort::
finalizeExternal(Worker &aw, Worker &/*iw*/, InstancePort &ip,
		 bool &/*cantDataResetWhileSuspended*/) {
  // We don't share ports since the whole point of WTi is to get
  // intra-chip accuracy via replication of the time clients.
  // We could have an option to use wires instead to make things smaller
  // and less accurate...
  const char *err;
  if (!m_master && ip.m_attachments.empty() &&
      (err = aw.m_assembly->externalizePort(ip, "wti", &aw.m_assembly->m_nWti)))
    return err;
  return NULL;
}

const char *WtiPort::
resolveExpressions(OCPI::Util::IdentResolver &ir) {
  const char *err;
  if ((m_secondsWidthExpr.length() &&
       (err = parseExprNumber(m_secondsWidthExpr.c_str(), m_secondsWidth, NULL, &ir))) ||
      (m_fractionWidthExpr.length() &&
       (err = parseExprNumber(m_fractionWidthExpr.c_str(), m_fractionWidth, NULL, &ir))))
    return err;
  // not yet, need to adjustConnection non-data connections....
  // m_dataWidth = m_secondsWidth + m_fractionWidth;
  return OcpPort::resolveExpressions(ir);
}

void WtiPort::
emitRecordInterfaceConstants(FILE *f) {
  OcpPort::emitRecordInterfaceConstants(f);
  // This signal is available to worker code.
  fprintf(f,
	  "  constant ocpi_port_%s_seconds_width : natural;\n"
	  "  constant ocpi_port_%s_fraction_width : natural;\n", pname(), pname());
}

void WtiPort::
emitInterfaceConstants(FILE *f, Language lang) {
  OcpPort::emitInterfaceConstants(f, lang);
  emitConstant(f, "ocpi_port_%s_seconds_width", lang, m_secondsWidth);
  emitConstant(f, "ocpi_port_%s_fraction_width", lang, m_fractionWidth);
}
