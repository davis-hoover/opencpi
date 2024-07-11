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
from _opencpi.assets.project2 import Project, test_Project


class ProjectRegistry():
    """ Component Development Guide section 14.3 """

    def __init__(
            self, do_discover_component_libraries=True,
            do_discover_hdl_primitives=True):
        self.abs_path = None
        self.projects = []
        self.discover(
                do_discover_component_libraries, do_discover_hdl_primitives)
        found = False
        for project in self.projects:
            if str(project.get_package_id()) == 'ocpi.core':
                found = True
        if not found:
            Logger().warn('ocpi.core is not registered')

    def get_project_dependencies_not_registered(self, project):
        registered_projects = []
        non_registered_projects = []
        for registered_project in self.projects:
            pid = str(registered_project.get_package_id())
            registered_projects.append(pid)
        for dep in project.project_dependencies:
            if dep not in registered_projects:
                non_registered_projects.append(dep)
        return non_registered_projects

    def get_abs_path_is_project(self, abs_path):
        """ return whether indicated path is a project """
        ret = False
        if os.path.isfile(abs_path + '/Project.xml'):
            ret = True
        # start pre-2.0 opencpi
        if os.path.isfile(abs_path + '/Project.mk'):
            ret = True
        # end pre-2.0 opencpi
        return ret

    def get_hdl_primitive_project(self, name, worker_project=None):
        """ get project which contains named hdl primitive, where HDL
            Development Guide section 4.4.1 defines the search precedence """
        # TODO make compliant with CDG section 8.1.11
        ret = None
        if worker_project is not None:
            for hdl_primitive in worker_project.hdl_primitives:
                if hdl_primitive.name == name:
                    ret = worker_project
            if ret is None:
                for project in self.projects:
                    if str(project.get_package_id()) == 'ocpi.core':
                        for hdl_primitive in project.hdl_primitives:
                            if hdl_primitive.name == name:
                                ret = project
        if ret is None:
            for project in self.projects:
                for hdl_primitive in project.hdl_primitives:
                    if hdl_primitive.name == name:
                        ret = project
        if ret is None:
            raise_not_found_in_projects('hdl primitive', name)
        return ret

    def get_worker_project(self, name, abs_path=None):
        """ get project which contains named worker """
        ret = None
        for project in self.projects:
            if project.get_worker_by_name(name) is not None:
                ret = project
        if ret is None:
            raise_not_found_in_projects('worker', name)
        return ret

    def get_hdl_assembly_project(self, name):
        """ get project which contains named assembly """
        ret = None
        for project in self.projects:
            for hdl_assembly in project.hdl_assemblies:
                if hdl_assembly.name == name:
                    ret = project
        if ret is None:
            raise_not_found_in_projects('hdl assembly', name)
        return ret

    def get_abs_path_project(self, abs_path):
        """ get project which contains indicated abs_path """
        ret = None
        for project in self.projects:
            if (project.abs_path + '/') in (abs_path + '/'):
                ret = project
        if ret is None:
            raise_not_found_in_projects('path', abs_path)
        return ret

    def get_core_project_assets(self, _type):
        ret = []
        for project in self.projects:
            if str(project.get_package_id()) == 'ocpi.core':
                if _type == 'hdl adapters':
                    discovery_path = project.abs_path + '/hdl/adapters'
                elif _type == 'hdl devices':
                    discovery_path = project.abs_path + '/hdl/devices'
                for entry in AssetBase.listdir_assets(discovery_path):
                    if '.hdl' in entry:
                        name = entry.split('.')[0]
                        owd_path = discovery_path + '/' + entry + '/' + \
                            name + '.xml'
                        if os.path.isfile(owd_path):
                            for clib in project.component_libraries:
                                for asset in clib.workers:
                                    if asset.get_xml_abs_path() == owd_path:
                                        ret.append(asset.name)
        return ret

    def discover(
            self, do_discover_component_libraries=True,
            do_discover_hdl_primitives=True):
        self.discover_abs_path()
        self.discover_projects(
                do_discover_component_libraries, do_discover_hdl_primitives)

    def discover_abs_path(self):
        ocpi_project_registry_dir = os.environ.get('OCPI_PROJECT_REGISTRY_DIR')
        if ocpi_project_registry_dir is None:
            ocpi_cdk_dir = os.environ.get('OCPI_CDK_DIR')
            if ocpi_cdk_dir is None:
                raise Exception('OpenCPI environment not setup')
            abs_path = ocpi_cdk_dir + '/../project-registry'  # undocumented
        else:
            abs_path = ocpi_project_registry_dir
        self.abs_path = abs_path

    def discover_projects(self, do_component_libraries, do_hdl_primitives):
        Logger().debug('start of project discovery')
        for _dir in AssetBase.listdir_assets(self.abs_path):
            abs_path = self.abs_path + '/' + _dir
            project_abs_path = os.path.realpath(abs_path)
            if (not os.path.exists(project_abs_path)) or \
                    not (self.get_abs_path_is_project(project_abs_path)):
                name = project_abs_path.split('/')[-1]
                msg = 'registry corrupted for ' + name
                msg += ' project entry (broken symlink: ' + abs_path + ')'
                Logger().warn(msg)
            if self.get_abs_path_is_project(project_abs_path):
                project = Project(project_abs_path, False)
                project.discover(do_component_libraries, do_hdl_primitives)
                self.projects.append(project)
        Logger().debug('end of project discovery')

    def show(self, _dir, cli_dict):
        if cli_dict['noun'] == 'registry':
            if (_dir == '') or \
               (_dir in self.abs_path):
                print(self.abs_path)
        json_dict = {}
        for project in self.projects:
            json_dict = project.show(_dir, cli_dict, json_dict)
        if cli_dict['simple']:
            print('')
        if cli_dict['json']:
            print(str(json_dict))

    def build(self, _dir, cli_dict):
        pass

    def create(self, _dir, cli_dict):
        pass


def unittest(cli_dict, project_registry):
    ret = True
    ret = test_ProjectRegistry(ret)
    ret = test_Project(ret)
    if not ret:
        raise Exception('unittest failed')


def test_ProjectRegistry(ret):
    passed = True
    try:
        project_registry = ProjectRegistry()
    except InvalidAssetError:
        passed = False
    log_pass_fail('testing ProjectRegistry', passed)
    if passed is False:
        ret = False
    return ret
