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
Defines the AssetFactory class
"""


from functools import partial
import os,sys
from pathlib import Path
import _opencpi.util as ocpiutil
from .abstract import Asset

class AssetFactory():
    """
    This class is used for intelligent construction of supported OpenCPI Assets. Given an asset type
    and arguments, the factory will provide an instance of the relevant class.
    """
    # __assets is a dictionary to keep track of existing instances for each asset subclass. Only
    # assets that use the __get_or_create function for construction will be tracked in this dict.
    # It can be used to determine whether an instance needs to be created or already exists.
    # {
    #     <asset-subclass> : {
    #                            <directory> : <asset-subclass-instance>
    #                        }
    # }
    __assets = {}
    __asset_type_to_class_map = None

    @classmethod
    def get_class_from_asset_type(cls, asset_type, name):
        """"
        Return the class object corresponding to the asset type
        """
        if not cls.__asset_type_to_class_map:
            import _opencpi.assets.application
            import _opencpi.assets.test
            import _opencpi.assets.worker
            import _opencpi.assets.platform
            import _opencpi.assets.assembly
            import _opencpi.assets.library
            import _opencpi.assets.primitive
            import _opencpi.assets.project
            import _opencpi.assets.registry
            import _opencpi.assets.component
            import _opencpi.assets.prerequisite
            # alphabetical order and include plurals
            # THIS LIST SHOULD CORRESPOND TO ALL ALLOWABLE NOUNS IN OCPIDEV
            # But there will be ones here that are not (yet) available from ocpidev
            # And some do not yet have plurals/collections
            cls.__asset_type_to_class_map =  {
                'application':             _opencpi.assets.application.Application,
                'applications':            _opencpi.assets.application.ApplicationsCollection,
                'component':               _opencpi.assets.component.Component,
                'components':              _opencpi.assets.component.ComponentsCollection,
                'hdl-assemblies':          _opencpi.assets.assembly.HdlAssembliesCollection,
                'hdl-assembly':            _opencpi.assets.assembly.HdlApplicationAssembly,
                'hdl-card':                _opencpi.assets.component.HdlCard,
                'hdl-cards':               None,
                'hdl-container':           _opencpi.assets.assembly.HdlContainer,
                'hdl-containers':          None,
                'hdl-core':                _opencpi.assets.primitive.HdlPrimitiveCore,
                'hdl-device':              _opencpi.assets.worker.HdlDeviceWorker,
                'hdl-devices':             None,
                'hdl-library':             _opencpi.assets.primitive.HdlPrimitiveLibrary,
                'hdl-platform':            _opencpi.assets.platform.HdlPlatformWorker,
                'hdl-platforms':           _opencpi.assets.platform.HdlPlatformsCollection,
                'hdl-primitives':          _opencpi.assets.primitive.HdlPrimitivesCollection,
                'hdl-slot':                _opencpi.assets.component.HdlSlot,
                'hdl-slots':               None,
                'hdl-targets':             _opencpi.assets.platform.HdlTargetsCollection,
                'hdl-worker':              _opencpi.assets.worker.HdlLibraryWorker,
                'libraries':               _opencpi.assets.library.LibrariesCollection,
                'library':                 _opencpi.assets.library.Library,
                'platforms':               _opencpi.assets.platform.PlatformsCollection,
                'prerequisite':            _opencpi.assets.prerequisite.Prerequisite,
                'prerequisites':           _opencpi.assets.prerequisite.PrerequisitesCollection,
                'project':                 _opencpi.assets.project.Project,
                'projects':                _opencpi.assets.project.ProjectsCollection,
                'protocol':                _opencpi.assets.component.Protocol,
                'protocols':               None,
                'rcc-platform':            _opencpi.assets.platform.RccPlatform,
                'rcc-platforms':           _opencpi.assets.platform.RccPlatformsCollection,
                'rcc-worker':              _opencpi.assets.worker.RccWorker,
                'registry':                _opencpi.assets.registry.Registry,
                'test':                    _opencpi.assets.test.Test,
                'tests':                   _opencpi.assets.test.TestsCollection,
                'worker':                  None,
                'workers':                 _opencpi.assets.worker.WorkersCollection,
            }

        if asset_type == 'worker':
            words = name.split('.')
            if len(words) != 2:
                raise ocpiutil.OCPIException(f'Bad worker name "{name}", does not have model suffix')
            asset_type = words[1] + "-worker"
        asset_class = cls.__asset_type_to_class_map.get(asset_type)
        if not asset_class:
            raise NotImplementedError(f'Bad asset type, "{asset_type}" not supported')
        return asset_class

    @classmethod
    def factory(cls, asset_type, directory, name=None, **kwargs):
        """
        Class method that is the intended wrapper to create all instances of any Asset subclass.
        Returns a constructed object of the type specified by asset_type. Throws an exception for
        an invalid type.

        Every asset must have a directory, and may provide a name and other args.
        Some assets will be created via the corresponding subclass constructor.
        Others will use an auxiliary function to first check if a matching instance
        already exists.
        """
        if not directory:
            raise ocpiutil.OCPIException("directory passed to  AssetFactory is None.  Pass a " +
                                         "valid directory to the factory")
        directory = str(Path(directory).resolve())
        # Call the action for this type and hand it the arguments provided
        asset_name = name if name else os.path.basename(directory)
        asset_class = AssetFactory.get_class_from_asset_type(asset_type, asset_name)
        return asset_class(directory, name, **kwargs)

    @classmethod
    def remove_all(cls):
        """
        Removes all instances from the static class variable __assets
        """
        cls.__assets = {}

    @classmethod
    def remove(cls, directory=None, instance=None):
        """
        Removes an instance from the static class variable __assets by directory or the instance
        itself.  Throws an exception if neither optional argument is provided.
        """
        if directory is not None:
            real_dir = os.path.realpath(directory)
            import _opencpi.assets.project
            import _opencpi.assets.registry
            dirtype_dict = {"project": _opencpi.assets.project.Project,
                            "registry": _opencpi.assets.registry.Registry}
            dirtype = ocpiutil.get_dirtype(real_dir)
            cls.__assets[dirtype_dict[dirtype]].pop(real_dir, None)
        elif instance is not None:
            cls.__assets[instance.__class__] = {
                k:v for k, v in cls.__assets[instance.__class__].items() if v is not instance}
        else:
            raise ocpiutil.OCPIException("Invalid use of AssetFactory.remove() both directory " +
                                         "and instance are None.")

    @classmethod
    def get_instance(cls, asset_cls, directory=None, name=None, **kwargs):
        """
        Ask the asset class whether instances should be cached.
        If the asset class says no, simply construct the asset and return it.
        Otherwise, check whether an instance of the
        asset class already exists for the provided directory. If so, return
        that instance. Otherwise, call the asset class constructor and return
        the new instance.
        """
        if isinstance(asset_cls,str):
            asset_cls = AssetFactory.get_class_from_asset_type(asset_cls,name)

        if asset_cls.instances_should_be_cached:
            # If instances should be cached, determine the sub-dictionary in __assets
            # corresponding to the provided class (asset_cls)
            if asset_cls not in cls.__assets:
                cls.__assets[asset_cls] = {}
            asset_inst_dict = cls.__assets[asset_cls]
            asset_path, asset_name, asset_parent = Asset.get_asset_path(directory, name, kwargs)

            real_dir = str(asset_path)
            asset = asset_inst_dict.get(real_dir)
            if not asset:
                asset = asset_inst_dict[real_dir] = asset_cls(directory, name, **kwargs)
        else:
            asset = asset_cls(directory, name, **kwargs)
        return asset
