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
    def get_working_dir(name, library, hdl_library, hdl_platform):
        """
        return the directory of an Application given the name (name) and
        library specifiers (library, hdl_library, hdl_platform)
        """
        ocpiutil.check_no_libs("application", library, hdl_library, hdl_platform)
        if ocpiutil.get_dirtype() not in ["application", "applications", "project"]:
            ocpiutil.throw_not_valid_dirtype_e(["applications", "project"])
        if not name: ocpiutil.throw_not_blank_e("application", "name", True)
        #assume the only valid place for a application in a project is in the applications directory
        top = ocpiutil.get_path_to_project_top() + "/applications/";
        if fnmatch.fnmatch(name, '*.xml') or os.path.exists(top + name + ".xml"):
            return top
        return top + name

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
        dirtype = ocpiutil.get_dirtype(directory)
        if dirtype != "project" and dirtype != "applications":
           raise ocpiutil.OCPIException(directory + " must be a project or applications directory")

        if dirtype == "project":
            if kwargs.get("verbose", True):
                print("Executing application create method in project directory: " + directory)
            appdir = directory + "/applications/"
            if not os.path.isdir(appdir):
                os.mkdir(appdir)
                if kwargs.get("verbose", True):
                    basename = os.path.basename(directory)
                    print("The 'applications' directory was created for the project '" + basename + "'")
            os.chdir(appdir)

        currdir = os.getcwd()
        currtype = ocpiutil.get_dirtype(currdir)
        if not currtype == "applications":
            raise ocpiutil.OCPIException(currdir + " must be of type applications")
        appdir = currdir
        namedir = currdir + "/" + name

        template_dict = Application._get_template_dict(name, appdir, **kwargs)
        template = jinja2.Template(ocpitemplate.APP_APPLICATION_XML, trim_blocks=True)
        ocpiutil.write_file_from_string("application.xml", template.render(**template_dict))
        if kwargs.get("xml_app", True):
            template = jinja2.Template(ocpitemplate.APP_APPLICATION_APP_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(name + ".xml", template.render(**template_dict))
            if kwargs.get("verbose", True):
                print("XML application '" + name + "' was created as 'applications/" + name + ".xml'")
            return

        if os.path.exists(namedir):
            raise ocpiutil.OCPIException(namedir + " already exists.")
        os.mkdir(namedir)
        os.chdir(namedir)
        if kwargs.get("verbose", True):
            print("Application '" + name +"' was created in the directory 'applications/" + name + "'")
        if not kwargs.get("xml_dir_app", True):
            template = jinja2.Template(ocpitemplate.APP_APPLICATION_APP_CC, trim_blocks=True)
            ocpiutil.write_file_from_string(name + ".cc", template.render(**template_dict))
        template = jinja2.Template(ocpitemplate.APP_APPLICATION_APP_XML, trim_blocks=True)
        ocpiutil.write_file_from_string(name + ".xml", template.render(**template_dict))
        if kwargs.get("verbose", True):
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
                                    self.directory, ["run"],
                                    ocpiutil.get_makefile(self.directory, "applications")[0])

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
