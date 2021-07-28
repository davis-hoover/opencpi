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

// This contains generic port declarations
#ifndef OCPI_INPUTOUTPUT_H_
#define OCPI_INPUTOUTPUT_H_

enum MsConfig {bypass, metadata, throttle, full};
struct InputOutput {
  // this is a singleton in this context
  // Given a worker, see if it is what we want, either matching a spec, or emulating a device
  std::string m_name, m_file, m_script, m_view;
  const DataPort *m_port;
  size_t m_messageSize;
  bool m_messagesInFile, m_suppressEOF, m_disableBackpressure, m_stopOnEOF, m_testOptional;
  MsConfig m_msMode;
  InputOutput(); 
  const char *parse(ezxml_t x, std::vector<InputOutput> *inouts); 
};  
typedef std::vector<InputOutput> InputOutputs;

#endif
