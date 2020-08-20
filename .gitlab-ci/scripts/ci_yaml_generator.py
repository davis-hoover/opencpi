#!/usr/bin/env python3

import os
import yaml
from collections import defaultdict
import re
from pathlib import Path
import subprocess
from ci_utils import ci_project, ci_platform, ci_job, ci_env


def main():
    opencpi_path = Path(__file__, '..', '..', '..').resolve()
    os.chdir(opencpi_path)
    gitlab_yml_path = Path('.gitlab-ci')
    yaml_path = Path(gitlab_yml_path, 'yaml')
    projects_path = Path('projects')
    host_platform_whitelist_path = Path(gitlab_yml_path, 'scripts', 
                                        'host_platform_whitelist.txt')

    with open(host_platform_whitelist_path) as f:
        host_platform_whitelist = f.read().splitlines()

    projects_blacklist = ['tutorials']
    projects = ci_project.discover_projects(projects_path, projects_blacklist)
    platforms = ci_platform.discover_platforms(projects, 
                                               host_platform_whitelist)

    stages = ['prereqs', 'build-host', 'build-rcc', 'build-primitives', 
              'build-primitives', 'build-libraries', 'build-platforms', 
              'build-assemblies', 'build-sdcards', 'test', 'deploy']

    host_platforms = ci_platform.get_host_platforms(platforms)
    cross_platforms = ci_platform.get_cross_platforms(platforms)

    for host_platform in host_platforms:
        print('Generating yaml for host platform: {}'.format(
              host_platform.name))

        for cross_platform in cross_platforms:
            print('\t{}'.format(cross_platform.name))

            cross_jobs = ci_job.make_jobs(stages, cross_platform, projects, 
                                          platforms=platforms, 
                                          host_platform=host_platform)
            cross_path = Path(yaml_path, host_platform.name, 
                              '{}.yml'.format(cross_platform.name))
            ci_job.dump(cross_jobs, cross_path)

        host_jobs = ci_job.make_jobs(stages, host_platform, projects)
        host_path = Path(yaml_path, '{}.yml'.format(host_platform.name))
        ci_job.dump(host_jobs, host_path)
        
        host_include = [str(path) for path in 
            Path(yaml_path, host_platform.name).glob('*.yml')]
        host_dict = {'include': host_include}
        dump(host_dict, host_path, 'a')

    print('Updating .gitlab-ci.yml')
    gitlab_yml_path = Path('.gitlab-ci.yml')
    gitlab_yml_include = [str(path) for path in Path(yaml_path).glob('*.yml')]
    gitlab_yml_dict = {
        'include': gitlab_yml_include,
        'stages': stages
    }
    dump(gitlab_yml_dict, gitlab_yml_path, 'w+')


def dump(yaml_dict, yaml_path, mode):
    with open(yaml_path, mode) as yml:
        yaml.safe_dump(yaml_dict, yml, width=1000, default_flow_style=False)


if __name__ == '__main__':
    main()