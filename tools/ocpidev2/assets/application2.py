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
# A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import os
import hashlib
from _opencpi.assets.abstract2 import *
from _opencpi.assets.abstract2 import AssetBase


# TODO iherit from, and consolidate functionality from, AssetBase
class Application(AssetBase):
    """ Reference Application Development Guide section 3 """

    def __init__(self, dir_abs_path, enable_path_existence_check=True,
                 cli_dict=None):
        self.root_tags = ['Application']
        AssetBase.__init__(self, dir_abs_path, enable_path_existence_check)
        # TODO investigate whether below line is necessary
        # if not os.path.isfile(self.get_xml_abs_path()):
        #     self.raise_abs_path_does_not_exist()
        if enable_path_existence_check:
            if not os.path.isfile(self.get_xml_abs_path()):
                tmp = self.get_dir_abs_path() + '/' + self.name
                if not os.path.isfile(tmp + '.cc'):
                    if not os.path.isfile(tmp + '.c'):
                        if not os.path.isfile(tmp + '.cxx'):
                            if not os.path.isfile(tmp + '.cpp'):
                                tag = self.get_root_tags()[0]
                                msg = self.abs_path + ' is not a ' + tag
                                raise InvalidAssetError(msg)
        self.parse(cli_dict)

    def get_type(self):
        return 'application'
