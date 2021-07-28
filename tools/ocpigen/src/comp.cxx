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

#include "comp.h"

inline bool comp::operator()(const WorkerConfig &lhs, const WorkerConfig &rhs) const
{
  // Are all the non-impl parameter values the same?
  // Since they are all from the same spec the order will be the same
  if (lhs.second < rhs.second)
    return false;
  if (lhs.second > rhs.second)
    return true;
  for (unsigned p = 0; p < lhs.first->params.size(); ++p)
  {
    //      if (lhs.first->params[p].m_param->m_isImpl)
    //        break;
    int c = lhs.first->params[p].m_uValue.compare(rhs.first->params[p].m_uValue);
    if (c < 0)
      return true;
    if (c > 0)
      break;
  }
  return false;
}
