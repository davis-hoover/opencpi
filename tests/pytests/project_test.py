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
# You should have received a copy of the GNU Lesser General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.
import unittest
import sys
import os
sys.path.insert(0, os.path.realpath(os.getenv('OCPI_CDK_DIR') + '/scripts/'))
import ocpiutil
import ocpiassets

"""
This file contains the unit tests for the Project object
"""
class ProjectTest(unittest.TestCase):
    asset_type = "project"
    def test_prj_bad_dir(self):
        """
        create a project in an invalid directory and an exception should be thrown
        """
        self.assertRaises(ocpiutil.OCPIException,
                          ocpiassets.AssetFactory.factory,
                          self.asset_type,
                          "/dev")

    def test_prj_good_no_name(self):
        """
        create a project and use the default name and just initialize the applications.  Then run
        the applications in the project
        """
        my_asset = ocpiassets.AssetFactory.factory(self.asset_type,
                                                  "../av-test",
                                                  init_apps=True)
        assert my_asset.run() == 0
        ocpiassets.AssetFactory.remove("../av-test")

    def test_prj_no_init(self):
        """
        create a without initializing apps or libraries an exception is thrown when trying to run
        """
        my_asset = ocpiassets.AssetFactory.factory(self.asset_type,
                                                  "../av-test")
        self.assertRaises(ocpiutil.OCPIException, my_asset.run)

    def test_prj_good(self):
        """
        create a project in the default way
        """
        my_asset = ocpiassets.AssetFactory.factory(self.asset_type,
                                                  "../av-test",
                                                  "av-test",
                                                  init_tests=True,
                                                  init_libs=True)
        assert my_asset.run() == 0
        ocpiassets.AssetFactory.remove(instance=my_asset)

if __name__ == '__main__':
    unittest.main()