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
WmemiPort::
WmemiPort(Worker &w, ezxml_t x, Port *sp, int ordinal, const char *&err)
  : OcpPort(w, x, sp, ordinal, WMemIPort, "mem", err) {
  bool memFound = false;
  if ((err = OE::checkAttrs(x, "Name", "Clock", "DataWidth", "PreciseBurst", "ImpreciseBurst",
			    "MemoryWords", "ByteWidth", "MaxBurstLength",
			    "WriteDataFlowControl", "ReadDataFlowControl", "Count", "Pattern",
			    "master", "myclock", (void*)0)) ||
      (err = OE::getNumber64(x, "MemoryWords", &m_memoryWords, &memFound, 0)) ||
      (err = OE::getNumber(x, "MaxBurstLength", &m_maxBurstLength, 0, 0)) ||
      (err = OE::getBoolean(x, "WriteDataFlowControl", &m_writeDataFlowControl)) ||
      (err = OE::getBoolean(x, "ReadDataFlowControl", &m_readDataFlowControl)))
    return;
  if (!memFound || !m_memoryWords)
    err = "Missing \"MemoryWords\" attribute in MemoryInterface";
  else if (!m_preciseBurst && !m_impreciseBurst) {
    if (m_maxBurstLength > 0)
      err = "MaxBurstLength specified when no bursts are enabled";
    if (m_writeDataFlowControl || m_readDataFlowControl)
      err = "Read or WriteDataFlowControl enabled when no bursts are enabled";
  }
  if (!err && (m_byteWidth < 8 || m_dataWidth % m_byteWidth))
    err = OU::esprintf("Bytewidth (%zu) < 8 or doesn't evenly divide into DataWidth (%zu)",
		       m_byteWidth, m_dataWidth);
}

// Virtual constructor
Port &WmemiPort::
clone(Worker &, std::string &, size_t, OM::Assembly::Role *, const char *&) const {
  throw OU::Error("Port type: %u cannot be cloned", m_type);
#if 0
  WmemiPort *p = new WmemiPort(*this);
  return *p;
#endif
}

void WmemiPort::
emitPortDescription(FILE *f, Language lang) const {
  OcpPort::emitPortDescription(f, lang);
  const char *comment = hdlComment(lang);
  fprintf(f, "  %s   DataWidth: %zu\n", comment, m_dataWidth);
  fprintf(f, "  %s   ByteWidth: %zu\n", comment, m_byteWidth);
  fprintf(f, "  %s   ImpreciseBurst: %s\n", comment, BOOL(m_impreciseBurst));
  fprintf(f, "  %s   Preciseburst: %s\n", comment, BOOL(m_preciseBurst));
  fprintf(f, "  %s   MemoryWords: %llu\n", comment, (unsigned long long )m_memoryWords);
  fprintf(f, "  %s   MaxBurstLength: %zu\n", comment, m_maxBurstLength);
  fprintf(f, "  %s   WriteDataFlowControl: %s\n", comment, BOOL(m_writeDataFlowControl));
  fprintf(f, "  %s   ReadDataFlowControl: %s\n", comment, BOOL(m_readDataFlowControl));
}

const char *WmemiPort::
deriveOCP() {
  static uint8_t s[1]; // a non-zero string pointer
  OcpPort::deriveOCP();
  ocp.MCmd.width = 3;
  ocp.MAddr.width =
    OU::ceilLog2(m_memoryWords) + OU::ceilLog2(m_dataWidth/m_byteWidth);
  ocp.MAddr.value = s;
  if (m_preciseBurst)
    ocp.MBurstLength.width = OU::floorLog2(std::max<size_t>(2, m_maxBurstLength)) + 1;
  else if (m_impreciseBurst)
    ocp.MBurstLength.width = 2;
  if (m_preciseBurst && m_impreciseBurst) {
    ocp.MBurstPrecise.value = s;
    ocp.MBurstSingleReq.value = s;
  }
  ocp.MData.width =
    m_byteWidth != m_dataWidth && m_byteWidth != 8 ?
    8 * m_dataWidth / m_byteWidth : m_dataWidth;
  if (!m_preciseBurst && !m_impreciseBurst && m_byteWidth != m_dataWidth)
    ocp.MByteEn.width = m_dataWidth / m_byteWidth;
  if ((m_preciseBurst || m_impreciseBurst) && m_byteWidth != m_dataWidth)
    ocp.MDataByteEn.width = m_dataWidth / m_byteWidth;
  if (m_byteWidth != m_dataWidth && m_byteWidth != 8)
    ocp.MDataInfo.width = m_dataWidth - (8 * m_dataWidth / m_byteWidth);
  if (m_preciseBurst || m_impreciseBurst) {
    ocp.MDataLast.value = s;
    ocp.MDataValid.value = s;
    ocp.MReqLast.value = s;
    ocp.SRespLast.value = s;
  }
  ocp.MReset_n.value = s;
  if ((m_preciseBurst || m_impreciseBurst) &&
      m_readDataFlowControl)
    ocp.MRespAccept.value = s;
  ocp.SCmdAccept.value = s;
  ocp.SData.width =
    m_byteWidth != m_dataWidth && m_byteWidth != 8 ?
    8 * m_dataWidth / m_byteWidth : m_dataWidth;
  if ((m_preciseBurst || m_impreciseBurst) && m_writeDataFlowControl)
    ocp.SDataAccept.value = s;
  if (m_byteWidth != m_dataWidth && m_byteWidth != 8)
    ocp.SDataInfo.width = m_dataWidth - (8 * m_dataWidth / m_byteWidth);
  ocp.SResp.value = s;
  fixOCP();
  return NULL;
}
const char *WmemiPort::
finalizeExternal(Worker &aw, Worker &/*iw*/, InstancePort &ip,
		 bool &/*cantDataResetWhileSuspended*/) {
  const char *err;
  if (m_master && ip.m_attachments.empty() &&
      (err = aw.m_assembly->externalizePort(ip, "wmemi", &aw.m_assembly->m_nWmemi)))
    return err;
  return NULL;
}
