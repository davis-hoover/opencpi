// methods about clocks, including methods of the Clock class itself.

#include "wip.hh"
#include "clock.hh"

const char *Worker::
parseClocks() {
  // Now we do clocks before interfaces since they may refer to clocks
  for (ezxml_t xc = ezxml_cchild(m_xml, "Clock"); xc; xc = ezxml_cnext(xc)) {
    const char *err;
    if ((err = OE::checkAttrs(xc, "Name", "Signal", "Home", "direction", "frequency", (void*)0)))
      return err;
    const char
      *l_name = ezxml_cattr(xc, "Name"),
      *direction = ezxml_cattr(xc, "direction"),
      *signal = ezxml_cattr(xc, "signal");
    if (!l_name)
      return "Missing Name attribute in Clock subelement of HdlWorker";
    Clock *c;
    if ((err = addClock(l_name, direction, c)))
      return err;
    c->m_exported = true;  // If you mention it here at the top level, exporting is implied
    c->m_signal = signal ? signal : "";
    c->m_exportedSignal = c->m_signal;
    return NULL;
  }
  return NULL;
}
// Add/define a worker clock based on XML, no need to return the clock
const char *Worker::
addClock(ezxml_t x) {
  const char *err;
  if ((err = OE::checkAttrs(x, "Name", "Signal", "direction", (void*)0)))
    return err;
  const char
    *l_name = ezxml_cattr(x, "name"),
    *direction = ezxml_cattr(x, "direction"),
    *signal = ezxml_cattr(x, "Signal");
  Clock *c;
  if (!(err = addClock(l_name, direction, c)))
    c->m_signal = signal? signal : "";
  return err;
}

const char *Worker::
addClock(const char *a_name, const char *direction, Clock *&clk) {
  if (!a_name)
    return OU::esprintf("Missing \"name\" attribute for clock");
  if (findClock(a_name))
    return OU::esprintf("Duplicate clock \"%s\" for worker \"%s\"", a_name, m_implName);
  bool output = false;
  if (direction) {
    if (!strcasecmp(direction, "out"))
      output = true;
    else if (strcasecmp(direction, "in"))
      return OU::esprintf("Signal direction \"%s\" is not valid for clocks", direction);
  }
  clk = &addClock(a_name, output);
  return NULL;
}

Clock &Worker::
addClock(const char *a_name, bool output) {
  Clock &c = *new Clock(*this);
  c.m_ordinal = m_clocks.size();
  if (a_name) {
    ocpiCheck(!findClock(a_name));
    c.m_name = a_name;
  }
  m_clocks.push_back(&c);
  c.m_output = output;
  OU::format(c.m_signal, "%s_Clk", a_name);
  return c;
}

Clock &Worker::
addWciClockReset() {
  // If there is no control port, then we synthesize the clock as wci_clk
  if (!m_wciClock) {
    assert(!findClock("ctl"));
    Clock *clock;
    ocpiCheck(!addClock("wci", "in", clock));
    clock->m_reset = "wci_Reset_n";
    clock->m_exported = true;
    clock->m_exportedSignal = clock->m_signal;
    m_wciClock = clock;
  }
  return *m_wciClock;
}

Clock *Worker::
findClock(const char *a_name) const {
  for (auto ci = m_clocks.begin(); ci != m_clocks.end(); ci++) {
    Clock *c = *ci;
    if (!strcasecmp(a_name, c->cname()))
      return c;
  }
  return NULL;
}

const char *Port::
addMyClock(const char *direction) {
  const char *err;
  if ((err = m_worker->addClock(pname(), direction, m_clock)))
    return err;
  m_clock->m_port = this;
  m_myClock = true;
  return NULL;
}

Clock &Port::
addMyClock(bool output) {
  m_clock = &m_worker->addClock(pname(), output);
  m_clock->m_port = this;
  m_myClock = true;
  deriveOCP(); // this might have changed the port's clock signals
  return *m_clock;
}

// Check the clocking in a second pass after all the worker clocks and ports exist
// The only reason why the clock is not set is if it refers to another port's clock
const char *Port::
checkClock() {
  if (m_clock)
    return NULL;
  assert(!ezxml_cattr(m_xml, "clockDirection"));
  const char *clock = ezxml_cattr(m_xml, "clock");
  if (clock) {
    if (!(m_clock = m_worker->findClock(clock)))
      return OU::esprintf("There is no clock or port named \"%s\" defined for this worker", clock);
  } else if (needsControlClock()) {
    m_worker->addWciClockReset();
    m_clock = m_worker->m_wciClock;
  }
  return NULL;
}

// Parse the clock options for a port's XML.  This is the first pass as the ports are being created,
// So all we are doing is error checking and creating the port's own clock.
// If it refers to another port's clock, m_clock remains NULL
const char *Port::
parseClock(ezxml_t xml) {
  assert(!m_clock);
  const char
    *clock = ezxml_cattr(xml, "clock"),
    *direction = ezxml_cattr(xml, "clockDirection");
  // Start Compatibility - these may disappear
  const char
    *myClockAttr = ezxml_cattr(xml, "myClock"),
    *myOutputClockAttr = ezxml_cattr(xml, "myOutputClock");
  if (myClockAttr && myOutputClockAttr)
    return OU::esprintf("the \"myclock\" and \"myoutputclock\" attributes cannot both be specified");
  if (myClockAttr || myOutputClockAttr) {
    if (clock || direction)
      return OU::esprintf("the \"myclock\" and \"myoutputclock\" attributes cannot be set with \"clock\"");
    bool myClock, output;
    const char *err;
    if ((err = OE::getBoolean(xml, "MyClock", &myClock)) ||
	(err = OE::getBoolean(xml, "MyOutputClock", &myClock, false, false, &output)))
      return err;
    if (myClock)
      direction = output ? "out" : "in";
  }
  // End Compatibility - these may disappear
  if (clock) {
    Port *port = m_worker->findPort(clock, this);
    if (port) { // use the clock that another port uses
      if (direction)
	return OU::esprintf("For port \"%s\", specifying a clock direction (\"%s\") when referring "
			    "to another port's clock (\"%s\") is invalid",
			    pname(), direction, clock);
      if (!port->isOCP() && port->m_type != SDPPort)
	return OU::esprintf("For port \"%s\", specifying another port's clock (\"%s\") is invalid "
			    "because that port is not a type that has a clock",
			    pname(), clock);
      m_clockPort = port->m_ordinal; // defer actual clock resolution until later
    } else if ((m_clock = m_worker->findClock(clock))) { // a worker-defined clock, maybe this port
      if (direction)
	return OU::esprintf("For port \"%s\", specifying a clock direction (\"%s\") for a clock "
			    "(\"%s\") that is already defined is invalid",
			    pname(), direction, clock);
    } else if (strcasecmp(clock, pname()))
      ocpiDebug("There is no clock named \"%s\" defined yet for this worker", clock);
    else
      addMyClock(direction);
  } else if (direction)
    return m_worker->findClock(pname()) ?
      OU::esprintf("For port \"%s\", specifying a clock direction (\"%s\") for a clock "
		   "(\"%s\") that is already defined is invalid",
		   pname(), direction, pname()) :
      addMyClock(direction);
  return NULL;
}

Clock::
Clock(Worker &w) : m_worker(w), m_port(NULL), m_ordinal(0), m_output(false), m_internal(false), m_exported(false) {
}

void Clock::
rename(const char *name, Port *port) {
  if (name)
    m_name = name;
  OU::format(m_signal, "%s_wClk", cname());
  if ((m_port = port)) {
    m_port->m_myClock = true;
    m_port->deriveOCP();
    m_port->m_clock = this;
  }
}

// The name of the signal inside the worker shell for the clock signal
const char *Clock::
internalName() const {
  if (m_internalName.empty()) {
    if (m_port) {
      if (m_output) {
	if (m_port->isDataProducer())
	  m_internalName = m_port->typeNameOut + "_temp.";
	else
	  m_internalName = m_port->pname(), m_internalName += "_";
      } else
	m_internalName = m_port->typeNameIn + ".";
      m_internalName += "Clk";
    } else
      m_internalName = m_signal;
  }
  return m_internalName.c_str();
}

void Clock::
emitDataClockCDCs(FILE *f, const Clock &wciClock, std::string &instances) const {
  fprintf(f,
	  "  signal wsi_reset_%s        : Bool_t;\n"
	  "  signal wsi_is_operating_%s : Bool_t;\n",
	  cname(), cname());
  OU::formatAdd(instances,
		"  clock_%s_wsi_reset_inst : component cdc.cdc.reset\n"
		"    generic map(RST_DELAY    => num_reset_cycles)\n"
		"    port map   (src_rst      => wci_reset,\n"
		"                dst_clk      => %s,\n"
		"                dst_rst      => wsi_reset_%s);\n"
		"  clock_%s_wsi_is_operating_inst : component cdc.cdc.single_bit\n"
		"    generic map(IREG      => '1',\n"
		"                RST_LEVEL => '0')\n"
		"    port map   (src_clk      => %s,\n"
		"                src_rst      => wci_reset,\n"
		"                src_en       => '1',\n"
		"                src_in       => wci_is_operating,\n"
		"                dst_clk      => %s,\n"
		"                dst_rst      => wsi_reset_%s,\n"
		"                dst_out      => wsi_is_operating_%s);\n",
		cname(), internalName(), cname(),
		cname(), wciClock.internalName(), internalName(), cname(), cname());
}
