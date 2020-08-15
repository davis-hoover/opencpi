#!/usr/bin/env python3

import requests
from collections import namedtuple
from pathlib import Path
from .ci_project import Project

Platform = namedtuple('platform', 'name model is_host is_osp links repo')

def discover_platforms(projects, platform_filter=None, platform_links=None, do_osps=True):
    platforms = []

    for project in projects:
        hdl_platforms_path = Path(project.path, 'hdl', 'platforms')
        rcc_platforms_path = Path(project.path, 'rcc', 'platforms')

        for platforms_path in [hdl_platforms_path, rcc_platforms_path]:
            if platforms_path.is_dir():

                for platform_path in platforms_path.glob('*'):
                    platform_name = platform_path.stem

                    if platform_filter and platform_name not in platform_filter:
                        continue
                    
                    if platform_path is hdl_platforms_path:
                        makefile = Path(platform_path, 'Makefile')
                        is_host = False
                    else:
                        makefile = Path(platform_path, '{}.mk'.format(platform_path.stem))
                        is_host = Path(platform_path, '{}-check.sh'.format(platform_path.stem)).is_file()

                    if makefile.is_file():

                        if platform_links:
                            links = platform_links[platform_name]
                        else:
                            links = []

                        platform_model = platform_path.parents[1].stem
                        platform = Platform(name=platform_name, model=platform_model,
                                            is_host=is_host, is_osp=False, links=links,
                                            repo=None)
                        platforms.append(platform)

    if not do_osps:
        return platforms

    response = requests.get('https://gitlab.com/api/v4/groups/6009537/projects').json()

    for osp in response:
        platform_name = osp['name'].lower().replace(' ', '')

        if platform_filter and platform_name not in platform_filter:
            continue

        if platform_links:
            links = platform_links[platform_name]
        else:
            links = []

        platform_repo = osp['path_with_namespace']
        platform = Platform(name=platform_name, model='hdl', is_host=False, 
                            is_osp=True, repo=platform_repo, links=links)
        platforms.append(platform)

    return platforms   


def get_platform(platform_name, platforms):
    for platform in platforms:
        if platform_name == platform.name:
            return platform


def get_cross_platforms(platforms):
    cross_platforms = []
    for platform in platforms:
        if not platform.is_host:
            cross_platforms.append(platform)

    return cross_platforms


def get_host_platforms(platforms):
    host_platforms = []
    for platform in platforms:
        if platform.is_host:
            host_platforms.append(platform)

    return host_platforms