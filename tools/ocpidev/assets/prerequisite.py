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
"""
A Prerequisite directory and prerequisites within it
"""

from json import JSONEncoder
import os
import json
import sys
from pathlib import Path
from _opencpi.util import OCPIException, print_table, get_make_vars_rcc_targets, logging, TableCell

# pylint: disable=R0903
class DictWrapper:
    """
    Wrap dicts in classes so that access isn't all stringly typed
    """

    def get_dict(self):
        """
        Get the underlying dict which contains the pertinent info.
        This is different from the python self.__dict__ in that it is where the
        information about the prereq is stored, and how the subclasses store everything.
        Using this dict gives more flexibilty around it's formatting and contents
        """
        raise NotImplementedError("Unimplemented")


class PrereqEncoder(JSONEncoder):
    """
    Each DictWrapper might be a composition of other dict wrappers
    so enable them to be jsonified
    """
    # pylint: disable=W0221
    def default(self, obj: DictWrapper):
        return obj.get_dict()


class Prerequisite(DictWrapper):
    """
    Each individual prerequisite
    """


    def __init__(self, path: Path):
        """
        Args:
            path:   Absolute path to its installed root, eg OCPI_PREREQUISITES_DIR/gtest

        """
        # Path isn't json serializable so stringify it
        self.__dict = {'path': str(path), 'platforms': []}

    @staticmethod
    def get_all_rcc_platforms():
        # An assumption has been made the prerequisites is only ever Rcc based.
        # This is a nice assumption because getting the list of Hdl Platforms supported takes a while
        # so it makes this command really slow if we have to get that too.
        # In the future if Hdl is required here there needs to be a bit of a think about how to either
        # speed up the Hdl Platforms getting, or to cache it so it's ready to be retrieved
        # when needed instead of recalculated. The bulk of the delay when using the show command seems
        # to be from this method, so there might be scope to optimize this too

        # This function call also requires ocpi to have a core project set up and the CDK_DIR to be
        # pointing to valid things. This isn't the case with lots of the unit tests in particular, 
        # although it is in normal usage. If unable to get the list of RccPlatforms then just return 
        # an empty list so that processing can continue
        try:
            return get_make_vars_rcc_targets()["RccAllPlatforms"]
        except Exception as e:
            logging.error(f"Error getting all RCC Platforms: {e}")
            raise e

    def add_platform(self, platform: str):
        """
        Adds a supported platform name to this prerequisite
        Args:
            platform: a string which is the platform name supported.
        """
        self.__dict['platforms'].append(platform)

    def get_location(self):
        """
        Get the absolute path to the prereq root
        """
        return self.__dict['path']

    def get_platforms(self):
        """
        Get a list of platform names supported
        """
        return self.__dict['platforms']

    def get_dict(self):
        """
        See superclass docstring
        """
        return self.__dict

    @staticmethod
    def _platform_valid(platforms: [str], platform: Path):
        """
        Test if a platform is valid by testing the list of platform names.
        There are occassions where no platform names have been found, in which case
        we assume all are valid platform names. 
        Args:
            platforms:  A list of platform name strings
            platform:   The platform to test, must have a .name member (as in Path)
        """
        return (platforms is not None and platform.name in platforms) or platforms is None
    

    @staticmethod
    def create(root: Path, platforms: [str]):
        """
        Factory method to unpack the directory and populate the dict, this assumes that the
        prerequisites directory is structured as follows:
            name_of_prereq/platform_supported
                          /another_platform_supported
        If the platform directory isn't supported by the system eg it's not named correctly,
        then it wont be added to the supported platform for this prerequisite.
        This also means that if it's a header only thing then no platform will be shown,
        this is intended because it's not built for a specific platform
        Args:
            root:       The abs path to the prereq root directory
            platforms:  A list of strings which are valid platforms, optionally None
        """
        prereq = Prerequisite(root)

        for platform in root.iterdir():
            if platform.is_dir() and Prerequisite._platform_valid(platforms, platform):
                    prereq.add_platform(platform.name)
            else:
                logging.debug(f"{platform} isn't a directory, or isn't in the recognised"+
                               " list of RCC platforms")
        return prereq


class Prerequisites(DictWrapper):
    """
    The Prerequisites directory itself
    """
    def __init__(self, location: Path):
        """
        Args:
            location: A string which is the abspath to the users prerequisites directory

        """
        # Path isn't json serializable so stringify it
        self.__dict = {"location": str(location), 'prereqs': {}}

    def add_prerequisite(self, name: str, prereq: Prerequisite):
        """
        Add a prerequisite object to the prerequisites directory model
        Args:
            name: a string whichis the name of the prereq
            prereq: a Prerequisite object with all of it's details
        """
        self.__dict['prereqs'][name] = prereq

    def get_location(self):
        """
        Get a the abspath of the directory as a string
        """
        return self.__dict['location']

    def get_prerequisites(self):
        """
        Get the prereqs in the directory as a dictionary
        """
        return self.__dict['prereqs']

    def get_dict(self):
        """
        See superclass docstring
        """
        return self.__dict

    @staticmethod
    def get_default_location():
        """
        Get the default prereq dir from the environment setup. Check in the following order:
        If nothing in OCPI_PREREQUISITES_DIR env var, then use OCPI_CDK_DIR/../prerequisites,
        finally if nothing configured in OCPI_CDK_DIR then use /opt/opencpi/prerequisites

        Exception raised if nothing found in any of those paths
        """
        directory = os.environ.get('OCPI_PREREQUISITES_DIR')
        if directory:
            directory = Path(directory)
            if directory.is_dir():
                logging.debug(f"Found OCPI_PREREQUISITES_DIR = {directory}")
                return directory
            else:
                logging.debug(f"{directory} is not a directory")

        cdkdirectory = os.environ.get('OCPI_CDK_DIR')
        if cdkdirectory:
            directory = Path(cdkdirectory).parent.joinpath("prerequisites").resolve()
            if directory.is_dir():
                logging.debug(f"Found a prerequisites directory  = {directory}")
                return directory
            else:
                logging.debug(f"{directory} is not a directory")

        directory = Path(os.path.join("/", "opt","opencpi","prerequisites"))
        if directory.is_dir():
            logging.debug(f"Found a prerequisites directory  = {directory}")
            return directory
        else:
            logging.debug(f"{directory} is not a directory")

        raise OCPIException("Unable to find a prerequisites directory. " +
                            "Ensure OCPI_PREREQUISITES_DIR is set")

    @staticmethod
    def create():
        """
        Factor method to populate the prerequisites directory wrapped dict
        """
        root = Prerequisites.get_default_location()
        prereq_directory = Prerequisites(root)
        try:
            platforms = Prerequisite.get_all_rcc_platforms()
        except OCPIException:
            platforms = None

        for directory in root.iterdir():
            if directory.is_dir():
                prereq_directory.add_prerequisite(directory.name, Prerequisite.create(directory, platforms))

        return prereq_directory

    def print_simple(self):
        """
        Print the prereqs as a list of names
        """
        print(" ".join(sorted(self.get_prerequisites())))

    def print_table(self):
        """
        Print the prereqs as a table
        """
        # pylint: disable=C0103
        header = [TableCell("Prerequisite", f'Relative to installation directory "{self.get_location()}"'), "Platform(s) installed for"]
        rows = [header]
        prereqs = self.get_prerequisites()
        for p in prereqs:
            rows.append([p,
                         ", ".join(prereqs[p].get_platforms())])

        print_table(rows, underline="-")

    def get_json(self):
        """
        Get the json string
        """
        return json.dumps(self, cls=PrereqEncoder)

    def print_json(self):
        """
        Print the prereqs as a json
        """
        print(self.get_json())

    @staticmethod
    def show_all(details: str):
        """
        args:
            details: string -  one of json, table, simple
        """
        # pylint: disable=C0103
        pdir = Prerequisites.create()

        if details == "simple":
            pdir.print_simple()
        elif details == "table":
            pdir.print_table()
        elif details == "json":
            pdir.print_json()
        else:
            raise OCPIException(f"{details} isn't a recognised method of printing")
