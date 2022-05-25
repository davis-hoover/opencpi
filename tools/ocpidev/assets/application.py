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
import sys
import os.path
import fnmatch
import logging
from pathlib import Path
import _opencpi.util as ocpiutil
import jinja2
import _opencpi.assets.template as ocpitemplate
from .factory import AssetFactory
from .abstract import RunnableAsset, RCCBuildableAsset, Asset

class Application(RunnableAsset, RCCBuildableAsset):
    """
    This class represents an OpenCPI ACI Application.
    """
    valid_settings = ["run_before", "run_after", "run_arg"]
    def __init__(self, directory, name=None, run_before=None, run_after=None, run_arg=None, **kwargs):
        """
        Initializes Application member data  and calls the super class __init__.  Throws an
        exception if the directory passed in is not a valid application directory.
        valid kwargs handled at this level are:
            None
        """
        self.asset_type = 'application'
        super().__init__(directory, name, **kwargs)
        if name:
            if fnmatch.fnmatch(name, '*.xml'): # explicit .xml implies non-dir app
                self.check_dirtype("applications", self.parent)
            elif self.parent.name == "applications" and \
                self.parent.joinpath(name + ".xml").exists():
                name = name + ".xml"
        else:
            self.check_dirtype("application", self.directory)
        self.run_before = run_before
        self.run_after = run_after
        self.run_arg = run_arg

    def run(self, verbose=False, **kwargs):
        """
        Runs the Application with the settings specified in the object
        """
        if Path(self.directory).suffix == '.xml':
            directory = self.parent
            name = self.name+'.xml'
            type = "applications"
        else:
            directory = self.directory
            name = self.name
            type = "application"
        args = ["run", "Applications="+name]
        if verbose:
            args.append("OcpiVerbose=1")
        makefile = ocpiutil.get_makefile(directory, type)[0]
        return ocpiutil.execute_cmd(self.get_settings(),
                                    directory,
                                    action=args,
                                    file=makefile,
                                    verbose=verbose)

    def clean(self, verbose=False, **kwargs):
        """
        Cleans the application if it is not an XML one.
        """
        if self.path.is_dir():
            super().clean(verbose=verbose, **kwargs)
        elif verbose:
            print(f'The clean operation on the file-based application "{self.name}" was ignored.')

    def build(self, verbose=0, **kwargs):

        """
        Builds the application by handing over the user specifications to execute command
        """
        if self.path.is_dir():
            super().build(verbose=verbose, **kwargs)
        elif verbose:
            print(f'The build operation on the file-based application "{self.name}" was ignored.')

    @staticmethod
    def create(name, directory, xml_app=False, xml_dir_app=False, verbose=None, **kwargs):
        """
        Static method to create a new application
        """
        if name.endswith('.xml'):
            file_only = True
        elif xml_app:
            file_only = True
            name += '.xml'
        else:
            file_only = False
        apps_path = Path(directory)
        app_path = Path(apps_path, name)
        if app_path.exists():
            raise ocpiutil.OCPIException('application "{}" already exists at {}'.format(
                name, str(app_path)))
        if not apps_path.exists():
            apps_path.mkdir()
            template = jinja2.Template(ocpitemplate.APP_APPLICATIONS_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(apps_path.joinpath('applications.xml'),
                                            template.render({}))
        xml_template = jinja2.Template(ocpitemplate.APP_APPLICATION_XML, trim_blocks=True)
        if file_only:
            ocpiutil.write_file_from_string(app_path, xml_template.render({'app' : name}))
        else:
            app_path.mkdir()
            if xml_dir_app:
                ocpiutil.write_file_from_string(app_path.joinpath(name + '.xml'),
                                                xml_template.render({'app' : name}))
            else:
                template = jinja2.Template(ocpitemplate.APP_APPLICATION_APP_CC, trim_blocks=True)
                ocpiutil.write_file_from_string(app_path.joinpath(name + '.cc'),
                                                template.render({'app' : name}))
            template = jinja2.Template(ocpitemplate.APP_APPLICATION_ATTR_XML, trim_blocks=True)
            ocpiutil.write_file_from_string(app_path.joinpath(name + '.xml'),
                                            xml_template.render({'app' : name}))
        Asset.finish_creation('application', app_path.stem, app_path, verbose)

class ApplicationsCollection(RunnableAsset, RCCBuildableAsset):
    """
    This class represents an OpenCPI applications directory.  Ability act on multiple applications
    with a single instance are located in this class.
    """
    valid_settings = ["run_before", "run_after", "run_arg"]
    def __init__(self, directory, name=None, verb=None, **kwargs):
        """
        Initializes ApplicationsCoclletion member data  and calls the super class __init__.
        Throws an exception if the directory passed in is not a valid applications directory.
        valid kwargs handled at this level are:
            run_before (list) - Arguments to insert before the ACI executable or ocpirun
            run_after (list) - Arguments to insert at the end of the execution command line A
            run_arg (list) - Arguments to insert immediately after the ACI executable or ocpirun
        """
        self.asset_type = 'applications'
        super().__init__(directory, name, **kwargs)
        self.check_dirtype("applications", self.directory)
        self.applications = kwargs.get('assets')
        self.apps_list = None
        if verb == 'run' or (verb == 'show' and self.verbose):
            self.apps_list = []
            logging.debug("ApplicationsCollection constructor creating Applications Objects")
            for app_path in self.get_applications():
                self.apps_list.append(AssetFactory.factory("application", str(app_path),
                                                           verb=verb, **kwargs))

    @classmethod
    def resolve_child(cls, parent_path, asset_type, args):
        assert asset_type == 'application'
        xml_app = getattr(args, 'xml_all', None)
        if args.name.endswith('.xml'):
            args.name = args.name[:-4]
            xml_only = True
            args.xml_app = True
            args.xml_dir_app = False
        elif xml_app:
            xml_only = True
        elif parent_path.joinpath(args.name + '.xml').exists() and args.verb != 'create':
            xml_only = True
        else:
            xml_only = False
        dir_path = parent_path.joinpath(args.name)
        if xml_only and dir_path.exists():
            raise ocpiutil.OCPIException(f'A directory-based app exists at "{dir_path}" when an '+
                                         f'XML-only app was requested')
        xml_path = parent_path.joinpath(args.name + '.xml')
        if not xml_only and xml_path.exists():
            raise ocpiutil.OCPIException(f'An XML-based app exists at "{xml_path}" when an '+
                                         f'directory-based app was requested')
        args.child_path = Path(args.name + ('.xml' if xml_only else ''))

    def get_applications(self, **kwargs):
        """
        Gets a list of all directories of type applications in the project and puts that
        applications directory and the basename of that directory into a dictionary to return
        """
        if self.applications:
            return self.applications
        apps=[]
        for entry in Path(self.directory).iterdir():
            if entry.is_dir() and ocpiutil.get_dirtype(str(entry)) == 'application':
                apps.append(entry)
            elif entry.suffix == 'xml':
                # check xml root
                apps.append(entry)
        self.applications = apps
        return apps

    def run(self, verbose=False, **kwargs):
        """
        Runs the ApplicationsCollection with the settings specified in the object.  Running a
        ApplicationsCollection will run all the applications that are contained in the
        ApplicationsCollection
        """
        make_file=ocpiutil.get_makefile(self.directory, "applications")[0]
        return ocpiutil.execute_cmd(self.get_settings(),
                                    self.directory,
                                    action=['run'],
                                    file=make_file,
                                    verbose=verbose)
