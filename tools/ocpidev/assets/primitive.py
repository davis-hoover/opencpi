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
Definition of classes for rcc and hdl primitives
"""
import sys
import jinja2
import _opencpi.util as ocpiutil
from . abstract import (BuildableAsset, HDLBuildableAsset, ReportableAsset, RCCBuildableAsset,
                        ShowableAsset, Asset)

#class HdlCore

class Primitive(BuildableAsset):
    """
    A base class for all primitives, which are buildable
    """
    all_primitive_xml_attrs = (
        """
        {% if args.include_dir: %}
            IncludeDirs='{{' '.join(args.include_dir)}}'
        {% endif %}
        {% if args.primitive_library: %}
            Libraries='{{' '.join(args.primitive_library)}}'
        {% endif %}
        {% if args.other: %}
            SourceFiles='{{' '.join(args.other)}}'
        {% endif %}
        {% if args.only_platform: %}
            OnlyPlatforms='{{' '.join(args.only_platform)}}'
        {% endif %}
        {% if args.exclude_platform: %}
            ExcludePlatforms='{{' '.join(args.exclude_platform)}}'
        {% endif %}
        {% if args.no_libraries: %}
            NoLibraries='1'
        {% endif %}""")

    all_primitive_xml_elems = ''

    @staticmethod
    def do_create(name, directory, pretty_type, asset_type, template, verbose=None,
                  **kwargs):
        """
        Create a primitive - called by each derived class
        """
        dir_path, name, parent_path = \
            Asset.start_creation(directory, name, pretty_type, kwargs)
        if not parent_path.exists():
            kwargs.pop('name',None)
            HdlPrimitivesCollection.create(parent_path.name, parent_path.parent, verbose=verbose,
                                           **kwargs)
        dir_path.mkdir(parents=True)
        ocpiutil.write_file_from_string(dir_path.joinpath(name.split('.')[0] + ".xml"),
                                        Asset.process_template(template).render({'name' : name,
                                                                                 'args' : kwargs}))
        Asset.finish_creation(asset_type, name, dir_path, verbose)

class HdlPrimitive(Primitive,HDLBuildableAsset):
    """
    An HDL primitive, whether a core or a library
    """
    all_primitive_xml_attrs = (Primitive.all_primitive_xml_attrs +
        """
        {% if args.only_target: %}
            OnlyTargets='{{' '.join(args.only_target)}}'
        {% endif %}
        {% if args.exclude_target: %}
            ExcludeTargets='{{' '.join(args.exclude_target)}}'
        {% endif %}
        """
        )
    all_primitive_xml_elems = (
        """
        """
    )

class HdlPrimitiveLibrary(HdlPrimitive):
    """
    An HDL primitive library
    """
    def __init__(self, directory, name=None, **kwargs):
        """
        Construct HdlPrimitiveLibrary instance, and initialize configurations of this worker.
        Forward kwargs to configuration initialization.
        """
        self.asset_type = 'hdl-library'
        super().__init__(directory, name, **kwargs)
        self.check_dirtype('hdl-library', self.directory)

    template_xml = (
        """
        <!-- This file defines the {{name}} HDL primitive library. -->
        <HdlLibrary"""+HdlPrimitive.all_primitive_xml_attrs+
        """{% if args.core: %}
            Cores='{{' '.join(args.core)}}'
        {% endif %}
        {% if args.no_elaboration: %}
            HdlNoElaboration='1'
        {% endif %}
            >"""+HdlPrimitive.all_primitive_xml_elems+
        """</HdlLibrary>
        """)

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create an HDL library worker
        """
        Primitive.do_create(name, directory, 'HDL primitive library', 'hdl-library',
                            __class__.template_xml, **kwargs)

class HdlPrimitiveCore(HdlPrimitive):
    """
    An HDL primitive core:
    """
    def __init__(self, directory, name=None, **kwargs):
        """
        Construct HdlPrimitiveLibrary instance, and initialize configurations of this worker.
        Forward kwargs to configuration initialization.
        """
        self.asset_type = 'hdl-core'
        super().__init__(directory, name, **kwargs)
        self.check_dirtype('hdl-core', self.directory)

    template_xml = (
        """
        <!-- This file defines the {{name}} HDL primitive core. -->
        <HdlCore"""+HdlPrimitive.all_primitive_xml_attrs+
        """{% if args.top_module: %}
            HdlTop='{{args.top_module}}'
        {% endif %}
        {% if args.prebuilt_core: %}
            HdlPrebuiltCore='{{args.prebuilt_core}}'
        {% endif %}
            >"""+HdlPrimitive.all_primitive_xml_elems+
        """</HdlCore>
        """)

    @staticmethod
    def create(name, directory, verbose=None, **kwargs):
        """
        Create an HDL primitive core
        """
        assert kwargs.get('model')
        HdlPrimitive.do_create(name, directory, 'HDL primitive core', 'hdl-core',
                               __class__.template_xml, **kwargs)

class PrimitivesCollection(ShowableAsset):

    @classmethod
    def create(cls, name, directory, verbose=None, model=None, template_xml=None, **kwargs):
        """
        Create a primitives collection, which is only a directory with a fixed XML file
        """
        assert model and template_xml
        dir_path, name, parent_path = \
            Asset.start_creation(directory, name, f'{model.upper()} Primitives', kwargs)
        assert name == 'primitives'
        dir_path.mkdir(parents=True)
        template = jinja2.Template(template_xml, trim_blocks=True)
        ocpiutil.write_file_from_string(dir_path.joinpath('primitives.xml'),
                                        template.render(**{}))
        Asset.finish_creation(f'{model}-primitives', name, dir_path, verbose)

class HdlPrimitivesCollection(HDLBuildableAsset, PrimitivesCollection):
    """
    A collection of HDL primitive cores and/or libraries:
    """
    template_xml = (
        """
	<!-- The XML file for the hdl/primitives directory:
	     To restrict the primitives that are built or run, you can set the Libraries or Cores
	     attributes to the specific list of which ones you want to build and run, e.g.:
	     Libraries='lib1 lib2'
	     Cores=core1 core2
	     Otherwise all primitives will be built-->
	<hdlprimitives/>
        """)

    def __init__(self, directory, name=None, verbose=None, verb=None, assets=None, **kwargs):
        """
        Create an HDL Primitives collection
        This will be called in two cases:
        1. When there is a "show" of primitives based on the add_assets of some parent
        2. When it is created on-demand when a primitive is created
        """
        if assets != None:
            self.out_of_project = True
        super().__init__(directory, name, **kwargs)
        self.make_type = 'hdl-primitives'
        self.primitives = None
        if assets != None:
            self.primitives = []
            for primitive_dir, is_library, parent_package_id in assets:
                primitive_name = Path(primitive_dir).name
                self.workers.append((HdlPrimitiveLibrary if is_library else HdlPrimitiveCore)
                                    (primitive_dir, None,
                                     package_id=parent_package_id + '.' + primitive_name))
        else:
            self.primitives = []
            if not self.path.exists():
                return
            self.check_dirtype("hdl-primitives", self.path)
            kwargs['name'] = None
            if verb == 'show':
                for primitive in self.path.iterdir():
                    if primitive.isdir():
                        type = ocpiutil.get_dirtype(primitive)
                        if ocpiutil.get_dirtype(primitive) in ['hdl-library','hdl-core']:
                             self.primitives.append(AssetFactory.factory(type, primitive,
                                                                         **kwargs))

    @staticmethod
    def create(name, directory, **kwargs):
        """ Pass our template into the generate creation method """
        PrimitivesCollection.create(name, directory, template_xml=__class__.template_xml, **kwargs)

    def build(self, **kwargs):
        """
        This method will build the primitives if there are any
        """
        if self.path.exists():
            super().build(**kwargs)


    def show(self, format, verbose, **kwargs):
        """
        Not implemented and not intended to be implemented
        """
        raise NotImplementedError("show() is not implemented")

