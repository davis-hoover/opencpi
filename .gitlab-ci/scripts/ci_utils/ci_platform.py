#!/usr/bin/env python3

from collections import namedtuple
from pathlib import Path

Platform = namedtuple('platform', 'name model is_host')

def discover_platforms(projects, host_platform_whitelist):
    platforms = []

    for project in projects:
        hdl_platforms_path = Path(project.path, 'hdl', 'platforms')
        rcc_platforms_path = Path(project.path, 'rcc', 'platforms')

        for platforms_path in [hdl_platforms_path, rcc_platforms_path]:
            if platforms_path.is_dir():

                for platform_path in platforms_path.glob('*'):
                    platform_name = platform_path.stem

                    
                    if platform_path is hdl_platforms_path:
                        makefile = Path(platform_path, 'Makefile')
                        is_host = False
                    else:
                        makefile = Path(platform_path, '{}.mk'.format(
                            platform_path.stem))
                        is_host = Path(platform_path, '{}-check.sh'.format(
                            platform_path.stem)).is_file()

                    if is_host and host_platform_whitelist:
                        if platform_name not in host_platform_whitelist:
                            continue

                    if makefile.is_file():
                        platform_model = platform_path.parents[1].stem
                        platform = Platform(name=platform_name, 
                                            model=platform_model,
                                            is_host=is_host)
                        platforms.append(platform)

    return platforms   


def get_platform(platform_name, platforms):
    for platform in platforms:
        if platform_name == platform.name:
            return platform


def get_platforms_by_type(platforms, platform_type):
    return_platforms = []
    for platform in platforms:
        if platform_type == 'host' and platform.is_host:
            return_platforms.append(platform)
        elif platform_type == 'cross' and not platform.is_host:
            return_platforms.append(platform)

    return return_platforms


def get_cross_platforms(platforms):
    return get_platforms_by_type(platforms, 'cross')


def get_host_platforms(platforms):
    return get_platforms_by_type(platforms, 'host')


def get_platforms_by_model(platforms, model, do_host=False):
    return_platforms = []
    for platform in platforms:
        if platform.model == model:
            if not do_host and platform.is_host:
                continue
            return_platforms.append(platform)

    return return_platforms


def get_rcc_platforms(platforms, do_host=False):
    return get_platforms_by_model(platforms, 'rcc', do_host)


def get_hdl_platforms(platforms):
    return get_platforms_by_model(platforms, 'hdl')