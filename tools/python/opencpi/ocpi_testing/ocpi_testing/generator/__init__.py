#!/usr/bin/env python3

# Import testing protocol generators for different protocols
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


"""Protocol generators"""


from .boolean_generator import BooleanGenerator
from .character_generator import CharacterGenerator
from .short_generator import ShortGenerator
from .long_generator import LongGenerator
from .unsigned_character_generator import UnsignedCharacterGenerator
from .unsigned_short_generator import UnsignedShortGenerator
from .unsigned_long_generator import UnsignedLongGenerator
from .float_generator import FloatGenerator
from .double_generator import DoubleGenerator
from .complex_character_generator import ComplexCharacterGenerator
from .complex_short_generator import ComplexShortGenerator
from .complex_long_generator import ComplexLongGenerator
from .complex_float_generator import ComplexFloatGenerator
from .complex_double_generator import ComplexDoubleGenerator
