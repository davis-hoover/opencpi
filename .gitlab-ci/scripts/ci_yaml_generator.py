#!/usr/bin/env python3

import os
import yaml
from pathlib import Path
from ci_utils import ci_project, ci_platform, ci_job


def main():
    opencpi_path = Path(__file__, '..', '..', '..').resolve()
    os.chdir(opencpi_path)
    gitlab_ci_path = Path('.gitlab-ci')
    yaml_path = Path(gitlab_ci_path, 'yaml')
    projects_path = Path('projects')
    host_platforms_path = Path(gitlab_ci_path, 'scripts', 
                                        'host_platforms.yml')
    overrides_path = Path(gitlab_ci_path, 'scripts', 'overrides.yml')

    with open(host_platforms_path) as yml:
        host_platforms = yaml.safe_load(yml)

    with open(overrides_path) as yml:
        overrides_dict = yaml.safe_load(yml)

    projects_blacklist = ['tutorial']
    projects = ci_project.discover_projects(projects_path, projects_blacklist)
    platforms = ci_platform.discover_platforms(projects, host_platforms)

    stages = ['prereqs', 'build-host', 'build-rcc', 'build-primitives-core', 
              'build-primitives', 'build-libraries', 'build-platforms', 
              'build-assemblies', 'build-sdcards', 'test', 'deploy']

    host_platforms = ci_platform.get_host_platforms(platforms)
    cross_platforms = ci_platform.get_cross_platforms(platforms)

    for host_platform in host_platforms:
        print('Generating yaml for host platform: {}'.format(
              host_platform.name))

        for cross_platform in cross_platforms:
            print('\t{}'.format(cross_platform.name))

            overrides = get_overrides(cross_platform, overrides_dict)
            cross_jobs = ci_job.make_jobs(stages, cross_platform, projects, 
                                          platforms=platforms, 
                                          host_platform=host_platform,
                                          overrides=overrides)
            cross_path = Path(yaml_path, host_platform.name, 
                              '{}.yml'.format(cross_platform.name))
            ci_job.dump(cross_jobs, cross_path)

        overrides = get_overrides(host_platform, overrides_dict)
        host_jobs = ci_job.make_jobs(stages, host_platform, projects, 
                                     overrides=overrides)
        host_path = Path(yaml_path, '{}.yml'.format(host_platform.name))
        ci_job.dump(host_jobs, host_path)
        
        host_include = [str(path) for path in 
            Path(yaml_path, host_platform.name).glob('*.yml')]
        host_dict = {'include': host_include}
        dump(host_dict, host_path, 'a')

    print('\nUpdating "include" section of .gitlab-ci.yml')
    gitlab_yml_path = Path('.gitlab-ci.yml')
    gitlab_yml_include = [str(path) for path in Path(yaml_path).glob('*.yml')]
    gitlab_yml_dict = {
        'include': gitlab_yml_include,
        'stages': stages
    }
    dump(gitlab_yml_dict, gitlab_yml_path, 'w+')

    print('\nYaml files available at: {}/'
          '\n*IMPORTANT: If any files were created for a new platform,'
          ' be sure to commit them.'.format(Path(Path.cwd(), yaml_path)))


def get_overrides(platform, overrides_dict):
    yaml.SafeDumper.ignore_aliases = lambda *args : True
    
    if platform.name in overrides_dict.keys():
        return overrides_dict[platform.name]

    return {}


def dump(yaml_dict, yaml_path, mode):
    with open(yaml_path, mode) as yml:
        yaml.safe_dump(yaml_dict, yml, width=1000, default_flow_style=False)


if __name__ == '__main__':
    main()