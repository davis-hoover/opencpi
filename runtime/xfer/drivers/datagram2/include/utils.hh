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

#ifndef Xfer_Utils_H_
#define Xfer_Utils_H_

#include <unordered_set>
#include <queue>
#include <inttypes.h>

template<typename T>
class duplicate_filter {
    std::unordered_set<T> m_set;
    std::queue<T> m_queue;
    size_t m_max_size;
  public:
    duplicate_filter(size_t max_size) {
        m_max_size = max_size;
    }

    bool check(T val) {
        // second element element of insert return value is true if the insertion
        // took place, false if the element was already in the set
        bool result = m_set.insert(val).second;

        // if this is not a duplicate, also record it in the queue (removing oldest
        // element if we are full)
        if (result) {
            if (m_queue.size() + 1 >= m_max_size) {
                m_set.erase(m_queue.front());
                m_queue.pop();
            }

            m_queue.push(val);
        }

        return result;
    }
};

#endif // Xfer_Utils_H_
