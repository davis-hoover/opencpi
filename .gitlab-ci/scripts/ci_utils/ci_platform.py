#!/usr/bin/env python3

from collections import namedtuple
from pathlib import Path


_Platform = namedtuple('platform', 'name model ip port is_host is_sim')


def Platform(name, model, is_host=False, is_sim=False, ip=None, port=None):
    """Creates a Platform namedtuple

    Args:
        name:    Name of platform
        model:   Model of platform
        is_host: Whether platform is a host platform
        is_sim:  Whether platform is a simulator
        ip:      IP adress of platform device
        port:    Port of platform device
    
    Returns:
        a Platform
    """

    return _Platform(name=name, model=model, is_host=is_host, is_sim=is_sim, 
                     ip=ip, port=port)


def discover_platforms(projects, config=None):
    """Search opencpi projects for platforms

    Will search for hdl platforms in:
        <projects>/<project>/hdl/platforms 
    and for rcc platforms in:
        <projects>/<project>/rcc/platforms
    Determines if a directory is a platform by existence of a 
        Makefile 
    or
        <platform_name>.mk
    Determines if an hdl platform is a simulator by existence of 
        runSimExec.<platform_name>

    Args:
        projects:       List of opencpi projects to search for 
                        platforms
        config:         Dictionary with platform names as keys and
                        additional platform configs as values

    Returns:
        platforms: List of opencpi platforms
    """
    platforms = []

    for project in projects:
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
                    
                    if config and platform_name in config:
                        platform_data = {key:value for key,value 
                                         in config[platform_name].items()
                                         if key in ['ip', 'port']}
                    else:
                        platform_data = {}

                    platform_model = platform_path.parents[1].stem
                    platform = Platform(name=platform_name, 
                                        model=platform_model, is_host=is_host, 
                                        is_sim=is_sim, **platform_data)
                    platforms.append(platform)

    return platforms 


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


def get_platforms_by_type(platforms, platform_type):
    """Searches list of platforms for platforms by type

        Platform types are 'host' or 'cross'.

    Args:
        platforms:     List of platforms to search through
        platform_type: The type of platforms to search for

    Returns:
        List of platforms matching platform_type arg
    """
    return_platforms = []
    for platform in platforms:
        if platform_type == 'host' and platform.is_host:
            return_platforms.append(platform)
        elif platform_type == 'cross' and not platform.is_host:
            return_platforms.append(platform)

    return return_platforms


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