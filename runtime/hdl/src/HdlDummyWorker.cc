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

#include "ContainerWorker.hh"
#include "HdlWciControl.hh"
#include "HdlDummyWorker.hh"
#include "HdlDevice.hh"

namespace OCPI {
  namespace HDL {
    namespace OC = OCPI::Container;
    namespace OU = OCPI::Util;
    namespace OM = OCPI::Metadata;

DummyWorker::
DummyWorker(Device &device, ezxml_t impl, ezxml_t inst, const char *idx) 
  : OC::Worker(NULL, impl, inst, OC::NoWorkers, false, 0, 1),
    WciControl(device, impl, inst, properties(), false),
    m_name(ezxml_cattr(inst, "name")),
    m_wName(ezxml_cattr(impl, "name"))
{
  // We need to initialize the status of the worker since the OC::Worker class
  // object is being created without knowledge of previous state.
  // The worker's status register tells us the last control operation
  // that was performed.  It also has a sticky indication of
  // errors from the worker itself, but it doesn't remember whether the
  // previous control operation failed for other reasons (FIXME: the OCCP should
  // capture this information).  We do our best here by first bypassing the software.
  unsigned worker = (unsigned)atoi(idx);

  device.cAccess().offsetRegisters(m_wAccess, (uintptr_t)(&((OccpSpace*)0)->worker[worker]));
  uint32_t
    control = m_wAccess.get32Register(control, OccpWorkerRegisters),
    l_status =  m_wAccess.get32Register(status, OccpWorkerRegisters);
  OM::Worker::ControlState cs;
  OM::Worker::ControlOperation lastOp =
    (OM::Worker::ControlOperation)OCCP_STATUS_LAST_OP(l_status);
  if (!(control & OCCP_WORKER_CONTROL_ENABLE))
    cs = OM::Worker::EXISTS; // there is no specific reset state since it isn't hetero
  else if (!(l_status & OCCP_STATUS_CONFIG_OP_VALID) || lastOp == 4)
    cs = OM::Worker::EXISTS; // no control op since reset
  else if (l_status & OCCP_STATUS_CONTROL_ERRORS)
    cs = OM::Worker::UNUSABLE;
  else if (lastOp == OM::Worker::OpRelease)
    cs = OM::Worker::UNUSABLE;
  else if (l_status & OCCP_STATUS_FINISHED)
    cs = OM::Worker::FINISHED;
  else
    switch(lastOp) {
    case OM::Worker::OpInitialize: cs = OM::Worker::INITIALIZED; break;
    case OM::Worker::OpStart: cs = OM::Worker::OPERATING; break;
    case OM::Worker::OpStop: cs = OM::Worker::SUSPENDED; break;
    default:
      cs = OM::Worker::OPERATING;
      // FIXME:  the beforeQuery, and AfterConfig and test ops screw us up here.
    }
  setControlState(cs);
}
const char *DummyWorker::
status() {
  return m_wAccess.get32Register(control, OccpWorkerRegisters) & OCCP_WORKER_CONTROL_ENABLE ?
    OM::Worker::s_controlStateNames[getState()] : "RESET";
}
}
}
