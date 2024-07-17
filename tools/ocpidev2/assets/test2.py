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


test_rst_template = """
.. {{asset.name}} test detail


:orphan:


``{{asset.name}}`` Test Detail
==================================================================================================================================
.. ocpi_documentation_test_detail::

"""

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
        self.name = self.name.split('.test')[0]  # TODO

    def get_attr_infos(self):
        ret = []
        ret.append(AttributeInfo('Spec', cli=('-S', '--component')))
        # This CLI Argument is NOT defined in the ocpidev-create Manpage
        ret.append(AttributeInfo('UseHDLFileIo', is_bool=True,
                                 cli=('-i', '--use-hdl-file-io')))
        return ret

    def get_type(self):
        return 'test'

    def get_templates(self):
        templates = {}
        templates[self.name + '-test.rst'] = test_rst_template
        templates['generate.py'] = test_generate_template
        templates['verify.py'] = test_verify_template
        templates['view.sh'] = test_view_template
        templates[self.name + '.xml'] = g_asset_template
        return templates

    def parse(self, cli_dict=None):
        AssetBase.parse(self, cli_dict)


def test_Test_create(ret):
    fs = TemporaryFilesystem()
    test_name = 'test_Test_create: '
    name = 'cmp.test'
    dir_abs_path = fs.abs_path + '/foo/components/' + name
    try:
        Test(
            dir_abs_path, False, None
        ).create()
        passed = True
    except Exception as e:
        Logger().debug(test_name + str(e))
        passed = False
    # Test for file existence
    test_files = ['cmp-test.xml', 'generate.py', 'verify.py', 'view.sh']
    for test_file in test_files:
        path = dir_abs_path + '/' + test_file
        if not os.path.exists(path):
            passed = False
    # Test for file integrity
    msg = 'invalid expected md5sum for file: '
    test_xml_path = dir_abs_path + '/' + test_files[0]
    test_xml_md5 = hashlib.md5(open(test_xml_path, 'rb').read()).hexdigest()
    if test_xml_md5 != '9378ade51ac6d9f75f815be71065fbbc':
        passed = False
        Logger().error(test_name + str(msg + test_xml_path))
    generate_path = dir_abs_path + '/' + test_files[1]
    generate_md5 = hashlib.md5(open(generate_path, 'rb').read()).hexdigest()
    if generate_md5 != 'a61331e02a4b59c3065dc2796d121e9c':
        passed = False
        Logger().error(test_name + str(msg + generate_path))
    verify_path = dir_abs_path + '/' + test_files[2]
    verify_md5 = hashlib.md5(open(verify_path, 'rb').read()).hexdigest()
    if verify_md5 != '9f85d1473e2dfc85063b75f6833d8ea4':
        passed = False
        Logger().error(test_name + str(msg + verify_path))
    view_path = dir_abs_path + '/' + test_files[3]
    view_md5 = hashlib.md5(open(view_path, 'rb').read()).hexdigest()
    if view_md5 != '5ba0ae964a22a6b65da5ae48409b2369':
        passed = False
        Logger().error(test_name + str(msg + view_path))
    # os.system('tree ' + fs.abs_path + '/foo')
    log_pass_fail('testing Test create()', passed)
    if passed is False:
        ret = False
