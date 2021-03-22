#!/usr/bin/env python3

import json
import os
from pathlib import Path
from urllib.request import urlopen
from . import ci_asset

class Platform():

    def __init__(self, name, model, path, project, assets=None,
                 linked_platforms=None, cross_platforms=None, is_host=False, 
                 is_sim=False, config=None):
        self.name = name
        self.model = model
        self.path = path
        self.is_host = is_host
        self.is_sim = is_sim
        self.project = project
        self.linked_platforms = linked_platforms or []
        self.cross_platforms = cross_platforms or []
        self.assets = assets or ci_asset.discover_assets(
            self.path, whitelist=['devices'])
        self.ip = None
        self.user = None
        self.password = None 
        self.do_deploy = True

        if config:
            attributes = ['ip', 'port', 'user', 'password']
            for attribute in attributes:
                try:
                    self.__dict__[attribute] = config[attribute]
                except:
                    self.__dict__[attribute] = None
            if 'deploy' in config:
                self.do_deploy = config['deploy']


def discover_platforms(projects, whitelist=None, config=None):
    """Discovers opencpi platforms in passed Project(s)
    
    Args:
        projects:  Project or List of Projects to discover platforms for
        whitelist: Whitelist of Platforms
        config:    Dictionary with platform names as keys and
                   additional platform configs as values

    Returns:
        List of Platforms discovered for passed Project(s)
    """
    platforms = []

    if not isinstance(projects, list):
        projects = [projects]

    for project in projects:
        project_platforms = []

        if project.path:
        # Project is local; discover local platforms
            project_platforms += discover_local(project, config=config)
        if project.id:
        # Project is remote; discover remote platforms
            project_platforms += discover_remote(project, config=config)

        platforms += project_platforms

    platforms = apply_whitelist(platforms, whitelist)
            
    return platforms


def discover_local(project, config=None):
    """Search opencpi projects for platforms

    Will search for hdl platforms in:
        <project.path>/hdl/platforms
    and for rcc platforms in:
        <project.path>/rcc/platforms
    Determines if a directory is a platform by existence of a
        Makefile
    or
        <platform_name>.mk
    Determines if an hdl platform is a simulator by existence of
        runSimExec.<platform_name>

    Args:
        project: Project to discover platforms for
        config:  Dictionary with platform names as keys and
                 additional platform configs as values

    Returns:
        platforms: List of opencpi Platforms
    """
    platforms = []

    hdl_platforms_path = Path(project.path, 'hdl', 'platforms')
    rcc_platforms_path = Path(project.path, 'rcc', 'platforms')

    for platforms_path in [hdl_platforms_path, rcc_platforms_path]:
        if platforms_path.is_dir():

            for platform_path in platforms_path.glob('*'):
                platform_name = platform_path.stem

                if platforms_path is hdl_platforms_path:
                    makefile = Path(platform_path, 'Makefile')
                    is_host = False
                    is_sim = Path(platform_path, 'runSimExec.{}'.format(
                        platform_name)).is_file()
                else:
                    makefile = Path(platform_path, '{}.mk'.format(
                        platform_path.stem))
                    is_host = Path(platform_path, '{}-check.sh'.format(
                        platform_path.stem)).is_file()
                    is_sim = False

                if not makefile.is_file():
                    continue

                platform_config = get_platform_config(platform_name, config)

                platform_model = platform_path.parents[1].stem
                platform = Platform(platform_name, platform_model, 
                                    platform_path, project,
                                    is_host=is_host, is_sim=is_sim, 
                                    config=platform_config)
                platforms.append(platform)

    return platforms


def discover_remote(project, config=None):
    """ Discovers platforms for remote projects

    Uses curl command to call gitlab api to collect project repo data.

    Args:
        project: Project to discover platforms for
        config:  Dictionary with platform names as keys and
                 additional platform configs as values

    Returns:
        platforms: List of opencpi Platforms
    """
    platforms = []
    url = '/'.join([
        'https://gitlab.com/api/v4/projects',
        str(project.id),
        'repository/tree'
    ])
    
    rcc_url = '?'.join([url, 'path=rcc/platforms'])
    hdl_url = '?'.join([url, 'path=hdl/platforms'])

    for model_url,model in zip([rcc_url, hdl_url], ['rcc', 'hdl']):
        try:
            with urlopen(model_url) as response:
                osp_platforms = json.load(response)

                for osp_platform in osp_platforms:
                    platform_name = osp_platform['name']
                    platform_path = None

                    if platform_name == 'Makefile':
                        continue

                    platform_config = get_platform_config(platform_name, 
                                                          config)
                    platform = Platform(platform_name, model, 
                                        platform_path, project,
                                        is_host=False, is_sim=False, 
                                        config=platform_config)
                    platforms.append(platform)
        except:
            continue
    
    return platforms


def apply_whitelist(platforms, whitelist):
    """Applies whitelist to list of opencpi platforms

    Args:
        platforms: List of Platforms to apply whitelis to
        whitelist: whitelist to apply to list of Platforms

    Returns:
        List of Platforms with whitelist applied
    """

    host_platforms = get_host_platforms(platforms)
    cross_platforms = get_cross_platforms(platforms)

    if not whitelist:
        for host_platform in host_platforms:
            host_platform.cross_platforms = cross_platforms

        return host_platforms

    filtered_platforms = []
    for host_platform in host_platforms:
        if host_platform.name not in whitelist:
            continue

        # Filter cross_platforms for each host_platform
        platform_whitelist = whitelist[host_platform.name]
        for cross_platform in cross_platforms:
            if cross_platform.name not in platform_whitelist:
                continue

            linked_whitelist = platform_whitelist[cross_platform.name]
            if linked_whitelist:
                linked_platforms = []
                for linked_platform_name in linked_whitelist:
                    linked_platform = get_platform(linked_platform_name, 
                                                   cross_platforms)
                    if linked_platform:
                        linked_platforms.append(linked_platform)
                cross_platform.linked_platforms = linked_platforms
            
            # If cross_platform is in both whitelist, add to host_platform
            host_platform.cross_platforms.append(cross_platform)

        filtered_platforms.append(host_platform)

    return filtered_platforms


def get_platform_config(platform_name, config):
    """Gets the config data for a platform

    Args:
        platform_name: The name of the platform to get config data for
        config:        Dictionary whit platform names as keys and config
                       data for the platform as values

    Returns:
        The config for the platform if found; None otherwise
    """
    try:
        return config[platform_name]
    except:
        return None


def get_platform(platform_name, platforms):
    """Searches list of platforms for platform by name

    Args:
        platform_name: Name of platform to search for
        platforms:     List of platforms to search through

    Returns:
        Platform with name matching platform_name arg
    """
    for platform in platforms:
        if platform_name == platform.name:
            return platform

    return None


def get_platforms_by_type(platforms, platform_type):
    """Searches list of platforms for platforms by type

        Platform types are 'host' or 'cross'.

    Args:
        platforms:     List of platforms to search through
        platform_type: The type of platforms to search for

    Returns:
        List of platforms matching platform_type arg
    """
    return_platforms = set()
    for platform in platforms:
        if platform_type == 'host' and platform.is_host:
            return_platforms.add(platform)
        elif platform_type == 'cross':
            if not platform.is_host:
                return_platforms.add(platform)
            else:
                return_platforms.update(platform.cross_platforms)

    return list(return_platforms)


def get_cross_platforms(platforms):
    """Searches list of platforms for platforms with type 'cross'

        Calls get_platforms_by_type() with 'cross' passed as
        platform_type arg.

    Args:
        platforms: List of platforms to search through

    Returns:
        List of platforms matching platform_type 'cross'
    """
    return get_platforms_by_type(platforms, 'cross')


def get_host_platforms(platforms):
    """Searches list of platforms for platforms with type 'host'

        Calls get_platforms_by_type() with 'host' passed as
        platform_type arg.

    Args:
        platforms: List of platforms to search through

    Returns:
        List of platforms matching platform_type 'host'
    """
    return get_platforms_by_type(platforms, 'host')


def get_platforms_by_model(platforms, model, do_host=False, do_sim=True):
    """Searches list of platforms for platforms by model

        Platform models are 'hdl' or 'rcc'.

    Args:
        platforms: List of platforms to search through
        model:     The model of platforms to search for
        do_host:   Whether to include host platforms
        do_sim:    Whether to include simulators

    Returns:
        List of platforms matching model arg
    """
    return_platforms = []
    for platform in platforms:
        if platform.model == model:
            if not do_host and platform.is_host:
                continue
            if not do_sim and platform.is_sim:
                continue

            return_platforms.append(platform)

    return return_platforms


def get_rcc_platforms(platforms, do_host=False):
    """Searches list of platforms for platforms with model 'rcc'

    Args:
        platforms: List of platforms to search through
        do_host:   Whether to include host platforms

    Returns:
        List of platforms matching model 'rcc'
    """
    return get_platforms_by_model(platforms, 'rcc', do_host)


def get_hdl_platforms(platforms, do_sim=True):
    """Searches list of platforms for platforms with model 'hdl'

    Args:
        platforms: List of platforms to search through
        do_sim:    Whether to include simulators

    Returns:
        List of platforms matching model 'hdl'
    """
    return get_platforms_by_model(platforms, 'hdl', do_sim)


def get_simulators(platforms):
    """Searches list of platforms for simulators

    Args:
        platforms: List of platforms to search through

    Returns:
        List of platforms that are simulators
    """
    return_platforms = []
    for platform in platforms:
        if platform.is_sim:
            return_platforms.append(platform)

    return return_platforms


def get_linked_platforms(platform, platforms, platform_directive):
    """Gets a platform's linked platforms

    Args:
        platform:           Platform to find linked platforms for
        platforms:          List of all platforms available
        platform_directive: Dictionary with platform names as keys and names of
                            associated platforms as values

    Returns:
        List of associated platforms for a given platform
    """
    linked_platforms = []
    
    if platform.name not in platform_directive:
        return linked_platforms
    
    for linked_platform_name in platform_directive[platform.name]:
        linked_platform = get_platform(linked_platform_name, platforms)

        if linked_platform:
            linked_platforms.append(linked_platform)
    
    return linked_platforms
