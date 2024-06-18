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

test_generate_template = ("""#!/usr/bin/env python3

\"\"\"
Use this file to generate your input data.
Args: <list-of-user-defined-args> <input-file>
\"\"\"
\n""")

test_verify_template = ("""#!/usr/bin/env python3

\"\"\"
Use this script to validate your output data against your input data.
Args: <list-of-user-defined-args> <output-file> <input-files>
\"\"\"
\n""")

test_view_template = ("""#!/bin/bash --noprofile

# Use this script to view your input and output data.
# Args: <list-of-user-defined-args> <output-file> <input-files>
\n""")


import os
from _opencpi.assets.abstract2 import *
from _opencpi.assets.abstract2 import AssetBase

def create_templates(name):
    test_templates = {}
    name = name.split('.')[0]
    test_templates[name + '-test.xml'] = g_asset_template
    test_templates['generate.py'] = test_generate_template
    test_templates['verify.py'] = test_verify_template
    test_templates['view.sh'] = test_view_template
    return test_templates

class Test(AssetBase):
    """ Reference Component Guide section 13. A <component>.test directory
        is created to hold a test suite for all workers in the library that
        implement the same spec (OCS) """

    def __init__(self, dir_abs_path, enable_path_existence_check=True,
                 cli_dict=None):
        self.root_tags = ['Tests']
        AssetBase.__init__(self, dir_abs_path, enable_path_existence_check)
        Logger().debug('parsing ' + self.get_xml_abs_path())
        self.parse(cli_dict)

    def create(self):
       test_xml_templates = create_templates(self.name)
       AssetBase.create_files(self, test_xml_templates)

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Spec', cli=('-S', '--component')))
        # This CLI Argument is NOT defined in the ocpidev-create Manpage
        ret.append(AttributeInfo('UseHDLFileIo', is_bool=True,
                                 cli=('-i', '--use-hdl-file-io'),
                                 action='store_true'))
        return ret

    def get_type(self):
        return 'tests'

    def parse(self, cli_dict=None):
        AssetBase.parse(self, cli_dict)
