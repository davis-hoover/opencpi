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
Definition of Application and ApplicationCollection classes
"""

import os.path
import fnmatch
import logging
from pathlib import Path
import _opencpi.util as ocpiutil
import jinja2
import _opencpi.assets.template as ocpitemplate
from .factory import AssetFactory
from .abstract import RunnableAsset, RCCBuildableAsset

class Application(RunnableAsset, RCCBuildableAsset):
    """
    This class represents an OpenCPI ACI Application.
    """
    valid_settings = ["run_before", "run_after", "run_arg"]
    def __init__(self, directory, name=None, **kwargs):
        """
        Initializes Application member data  and calls the super class __init__.  Throws an
        exception if the directory passed in is not a valid application directory.
        valid kwargs handled at this level are:
            None
        """
        if name:
            if fnmatch.fnmatch(name, '*.xml'): # explicit .xml implies non-dir app
                # parent_dir = str(Path(directory).parent)
                self.check_dirtype("applications", directory)
            elif os.path.basename(directory) == "applications" and \
                os.path.exists(directory + "/" + name + ".xml"):
                name = name + ".xml"
        else:
            self.check_dirtype("application", directory)
        super().__init__(directory, name, **kwargs)
        self.run_before = kwargs.get("run_before", None)
        self.run_after = kwargs.get("run_after", None)
        self.run_arg = kwargs.get("run_arg", None)

    def run(self):
        """
        Runs the Application with the settings specified in the object
        """
        return ocpiutil.execute_cmd(self.get_settings(), self.directory, ["run"],
                                    ocpiutil.get_makefile(self.directory, "application")[0])
    def build(self):
        """
        This is a placeholder function will be the function that builds this Asset
        """
        raise NotImplementedError("Application.build() is not implemented")

    @staticmethod
    def get_working_dir(name, ensure_exists=True, **kwargs):
        """
        return the directory of an Application given the name (name) and
        library specifiers (library, hdl_library, hdl_platform)
        """
        if ocpiutil.get_dirtype() not in ["application", "applications", "project"]:
            ocpiutil.throw_not_valid_dirtype_e(["applications", "project"])
        if not name: 
            ocpiutil.throw_not_blank_e("application", "name", True)
        
        project_path = Path(ocpiutil.get_path_to_project_top())
        apps_path = Path(project_path, 'applications')
        app_path = Path(apps_path, name)
        xml_path = Path(apps_path, name+'.xml')
        if ensure_exists:
            if xml_path.exists():
                working_path = xml_path
            elif app_path.exists():
                working_path = app_path
            else:
                err_msg = ' '.join(['Unable to find application "{}"'.format(name), 
                                    'in directory {}'.format(str(apps_path))])
                raise ocpiutil.OCPIException(err_msg)
        elif kwargs.get('xml_app', False):
            working_path = xml_path
        else:
            working_path = app_path

        return str(working_path)


    def _get_template_dict(name, directory, **kwargs):
        """
        used by the create function/verb to generate the dictionary of viabales to send to the
        jinja2 template.
        valid kwargs handled at this level are:
            app            (string)      - Applicatin name
        """
        template_dict = {
                        "app" : name,
                        }
        return template_dict


    @staticmethod
    def create(name, directory, **kwargs):
        """
        Static method to create a new Application
        """
        apps_path = Path(directory)
        app_path = Path(apps_path, name)
        if not apps_path.exists():
            apps_path.mkdir()
        os.chdir(str(apps_path))
        application_xml_path = Path(apps_path, 'application.xml')
        template_dict = Application._get_template_dict(name, directory, **kwargs)
        if not application_xml_path.exists():
            template = jinja2.Template(ocpitemplate.APP_APPLICATION_XML, trim_blocks=True)
            ocpiutil.write_file_from_string("application.xml", template.render(**template_dict))
        if app_path.exists():
            raise ocpiutil.OCPIException('application "{}" already exists at {}'.format(
                name, str(app_path)))
        if kwargs.get("xml_app", False):
            template = jinja2.Template(ocpitemplate.APP_APPLICATION_APP_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(name, template.render(**template_dict))
            if kwargs.get("verbose", False):
                print("XML application '" + name + "' was created as 'applications/" + directory)
            return

        app_path.mkdir()
        os.chdir(str(app_path))
        if kwargs.get("verbose", False):
            print("Application '" + name +"' was created in the directory 'applications/" + name + "'")
        if not kwargs.get("xml_dir_app", True):
            template = jinja2.Template(ocpitemplate.APP_APPLICATION_APP_CC, trim_blocks=True)
            ocpiutil.write_file_from_string(name + ".cc", template.render(**template_dict))
        template = jinja2.Template(ocpitemplate.APP_APPLICATION_APP_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(name + ".xml", template.render(**template_dict))
        if kwargs.get("verbose", False):
            print("XML application '" + name + "' was created as 'applications/" + name +
              "/" + name + ".xml'")


class ApplicationsCollection(RunnableAsset, RCCBuildableAsset):
    """
    This class represents an OpenCPI applications directory.  Ability act on multiple applications
    with a single instance are located in this class.
    """
    valid_settings = ["run_before", "run_after", "run_arg"]
    def __init__(self, directory, name=None, **kwargs):
        """
        Initializes ApplicationsCoclletion member data  and calls the super class __init__.
        Throws an exception if the directory passed in is not a valid applications directory.
        valid kwargs handled at this level are:
            run_before (list) - Arguments to insert before the ACI executable or ocpirun
            run_after (list) - Arguments to insert at the end of the execution command line A
            run_arg (list) - Arguments to insert immediately after the ACI executable or ocpirun
        """
        self.check_dirtype("applications", directory)
        super().__init__(directory, name, **kwargs)

        self.apps_list = None
        if kwargs.get("init_apps_col", False):
            self.apps_list = []
            logging.debug("ApplicationsCollection constructor creating Applications Objects")
            for app_directory in self.get_valid_apps():
                self.apps_list.append(AssetFactory.factory("application", app_directory, **kwargs))

        self.run_before = kwargs.get("run_before", None)
        self.run_after = kwargs.get("run_after", None)
        self.run_arg = kwargs.get("run_arg", None)

    def get_valid_apps(self):
        """
        Gets a list of all directories of type applications in the project and puts that
        applications directory and the basename of that directory into a dictionary to return
        """
        return ocpiutil.get_subdirs_of_type("application", self.directory)

    def run(self):
        """
        Runs the ApplicationsCollection with the settings specified in the object.  Running a
        ApplicationsCollection will run all the applications that are contained in the
        ApplicationsCollection
        """
        return ocpiutil.execute_cmd(self.get_settings(),
                                    self.directory, ["run"])

    def build(self):
        """
        This is a placeholder function will be the function that builds this Asset
        """
        raise NotImplementedError("ApplicationsCollection.build() is not implemented")

    @staticmethod
    def get_working_dir(name, library, hdl_library, hdl_platform):
        """
        return the directory of an Application Collection given the name (name) and
        library specifiers (library, hdl_library, hdl_platform)
        """
        ocpiutil.check_no_libs("applications", library, hdl_library, hdl_platform)
        if name: ocpiutil.throw_not_blank_e("applications", "name", False)
        if ocpiutil.get_dirtype() not in ["applications", "project"]:
            ocpiutil.throw_not_valid_dirtype_e(["applications", "project"])
        #assume the only valid place for a applications collection in a project is in the
        #applications directory
        return ocpiutil.get_path_to_project_top() + "/applications"
