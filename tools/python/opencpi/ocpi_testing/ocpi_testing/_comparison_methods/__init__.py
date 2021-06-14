#!/usr/bin/env python3

# Import OpenCPI testing comparison methods
#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of OpenCPI <http://www.opencpi.org>
#
# OpenCPI is free software: you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# OpenCPI is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for
# more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


"""Testing comparison methods"""


from .equal import Equal
from .bounded import Bounded
from .bounded_with_exception import BoundedWithException
from .relative import Relative
from .statistical import Statistical

COMPARISON_METHODS = {"equal": Equal,
                      "bounded": Bounded,
                      "bounded_with_exception": BoundedWithException,
                      "relative": Relative,
                      "statistical": Statistical}
