#!/usr/bin/env python3

# Generate a test seed value from some test inputs
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


def get_test_seed(*args):
    """ Will generate a number from the input arguments

    The resulting number from the input arguments is intended to be used as a
    seed for random number generation.

    The returned number is generated from the sum of:
     * Magnitude of integer inputs
     * Magnitude of the closest integer of floats
     * Every character in a string being converted to an integer using
       ``ord()``

    Args:
        args (various, multiple): A number of inputs to be used to generate an
            integer. All inputs provided are used.

    Returns:
        An integer, which can be used to seed random number generation.
    """
    if len(args) == 0:
        raise TypeError(
            "At least one argument must be passed to get_test_seed()")

    seed = 0
    for argument in args:
        if isinstance(argument, str):
            for character in argument:
                seed = seed + ord(character)
        elif isinstance(argument, int):
            seed = seed + abs(argument)
        elif isinstance(argument, float):
            seed = seed + abs(round(argument))
        else:
            TypeError("Unsupported input argument type of " +
                      f"{type(argument).__name__} to get_test_seed()")

    return seed
