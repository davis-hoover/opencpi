#!/usr/bin/env python3

# Functions for manipulating file paths
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

"""Path related functions."""

import pathlib
import logging


def paths_are_relative(path_stack, path_needle):
    """Test if 2 paths are relative to each other.

    This requires that the paths are followed all the way to the full
    extent of the shorter of the two paths.

    Args:
        path_stack (PathLike): First path in comparison
        path_needle (PathLike): Second path in comparison

    Returns:
        bool: Whether the paths are fully relatable.
    """
    stack = pathlib.Path(path_stack).resolve()
    needle = pathlib.Path(path_needle).resolve()

    if (stack.anchor != needle.anchor or
        stack == pathlib.Path("/") or
            needle == pathlib.Path("/")):
        logging.debug("Different drives, or filesystem root has been given")
        return False
    for stacks, needles in zip(stack.parts, needle.parts):
        if stacks != needles:
            return False
    return True
