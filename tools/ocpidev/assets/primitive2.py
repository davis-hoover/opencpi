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
from _opencpi.assets.abstract2 import *
from _opencpi.assets.abstract2 import AssetBase


class HdlLibrary(AssetBase):
    """ Reference HDL Development Guide section 5.2. A HdlLibrary is
        represented by a directory and knows nothing about the project it
        is in or its package ID. """

    def __init__(self, dir_abs_path):
        AssetBase.__init__(self, dir_abs_path)
        self.libraries = []
        self.source_files = []  # HDG section 5.2.1
        self.parse()

    def get_root_tags(self):
        ret = ['HdlLibrary']  # HDG section 5.2
        ret += ['HdlCore']  # HDG section 5.3
        return ret

    def parse(self):
        paths = []
        # start pre-2.0 opencpi
        paths += [self.abs_path + '/Makefile']
        # intentionally put xml last so that its attributes take precedence
        # end pre-2.0 opencpi
        paths.append(self.get_xml_abs_path())
        paths = self.get_list_of_existing_abs_paths_to_parse(paths)
        libraries = self.get_attr_list('Libraries', None, paths)
        if len(libraries) > 0:
            self.libraries = libraries
        files = self.get_attr_list('SourceFiles', None, paths)
        if len(files) > 0:
            self.source_files = files

    def get_type(self):
        return 'hdl primitive'


def test_HdlLibrary(ret):
    fs = TemporaryFilesystem()
    dir_abs_path = fs.abs_path + '/' + 'library'
    xml_abs_path = dir_abs_path + '/' + 'library.xml'
    for test in [0, 1]:
        passed = True
        try:
            os.system('mkdir -p ' + dir_abs_path)
            ff = open(xml_abs_path, 'w')
            ff.write('<HdlLibrary Libraries=\'foo\' SourceFiles=\'x.vhd\'>\n')
            ff.write('</HdlLibrary>\n')
            ff.close()
            uut = HdlLibrary(dir_abs_path)
            if Environment().ocpi_log_level >= 10:
                print(uut.__dict__.keys())
                os.system('cat ' + xml_abs_path)
            if test == 0:
                passed = uut.libraries == ['foo']
            if test == 1:
                passed = uut.source_files == ['x.vhd']
        except InvalidAssetError:
            passed = False
        if test == 0:
            log_pass_fail('testing HdlLibrary libraries ', passed)
        if test == 1:
            log_pass_fail('testing HdlLibrary source_files ', passed)
        if passed is False:
            ret = False
    return ret
