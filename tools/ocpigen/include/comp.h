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
#ifndef OCPI_COMP_H_
#define OCPI_COMP_H_
#include "parameters.h"
#include "hdl-device.h"
#include "data.h"
#include "tests.h"
class WorkerConfig;
// The package serves two purposes: the spec and the impl.
// If the spec already has a package prefix, then it will only
// be used as the package of the impl.
// FIXME: share this with the one in parse.cxx
struct comp
{
  inline bool operator()(const WorkerConfig &lhs, const WorkerConfig &rhs) const;
};
typedef std::set<WorkerConfig, comp> WorkerConfigs;
#endif
