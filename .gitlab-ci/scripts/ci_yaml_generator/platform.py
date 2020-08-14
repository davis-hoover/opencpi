#!/usr/bin/env python3

from pathlib import Path
from .project import Project
import requests

class Platform():

    def __init__(self, name, model, is_host=False, is_osp=False, links=None, repo=None):
        self.name = name
        self.model = model
        self.links = links
        self.is_host = is_host
        self.is_osp = is_osp
        self.repo = repo

    @classmethod
    def discover_platforms(cls, projects, platform_filter=None, platform_links=None, only_child=None, do_osp_search=True):
        platforms = []

        if isinstance(projects, Project):
            projects = [projects]
        elif not all(isinstance(project, Project) for project in projects):
            raise TypeError('projects must be a Project or Project list')

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

                        if only_child and not is_host and platform_name != only_child:
                            continue

                        if makefile.is_file():

                            if platform_links:
                                links = platform_links[platform_name]
                            else:
                                links = []

                            platform_model = platform_path.parents[1].stem
                            platform = cls(name=platform_name, model=platform_model,
                                                is_host=is_host, is_osp=False, links=links)
                            platforms.append(platform)

        if not do_osp_search:
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
            platform = Platform(name=platform_name, model='hdl', is_osp=True, repo=platform_repo, links=links)
            platforms.append(platform)

        return platforms   

    # @classmethod
    # def link_platforms(cls, platforms, links_dict):
    #     for platform_name, links in links_dict.items():
    #         platform = cls.get_platform(platform_name, platforms)

    #         if platform:
    #             for link in links:
    #                 linked_platform = cls.get_platform(link, platforms)

    #                 if linked_platform:
    #                     platform.linked_platforms.append(linked_platform)

    @staticmethod
    def get_platform(platform_name, platforms):
        for platform in platforms:
            if platform_name == platform.name:
                return platform

    @staticmethod
    def get_cross_platforms(platforms):
        cross_platforms = []
        for platform in platforms:
            if not platform.is_host:
                cross_platforms.append(platform)

        return cross_platforms

    @staticmethod
    def get_host_platforms(platforms):
        host_platforms = []
        for platform in platforms:
            if platform.is_host:
                host_platforms.append(platform)

        return host_platforms