#!/usr/bin/env python3

# Clean documentation (delete built documentation files and folders)
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


import pathlib
import shutil

from .conf import BUILD_FOLDER


def clean(directory, recursive=False, _startdir=None, **kwargs):
    """ Delete built documentation files and folders

    Args:
        directory (``str``): Directory to remove built documentation from.
        recursive (``bool``, optional): Search subdirectories for built
            documentation folders and remove these.
        _startdir (``str``): Starting directory, used by the recursive feature
            to ensure recursive searches do not go any heigher than the
            starting directory.
        kwards (optional): Other keyword arguments, provided for compatibility
            interfacing. Values not used.
    """
    current_directory = pathlib.Path(directory).resolve().absolute()
    if _startdir is None:
        _startdir = current_directory

    if recursive and current_directory.is_dir():
        for path in current_directory.glob(f"**/gen/{BUILD_FOLDER}"):
            if path != current_directory.joinpath("gen/"+BUILD_FOLDER):
                clean(path, _startdir=_startdir)

    directory = current_directory
    if current_directory == _startdir:
        directory = directory.joinpath("gen/"+BUILD_FOLDER)

    if directory.is_dir():
        shutil.rmtree(directory)
        print(f"Deleted built documentation directory: {directory}")
        if directory.parent.name == "gen" and \
                any(directory.parent.iterdir()) is False:
            shutil.rmtree(directory.parent)
            print(f"Deleted empty gen folder: {directory.parent}")
