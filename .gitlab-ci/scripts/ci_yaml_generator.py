#!/usr/bin/env python3

import os
import yaml
from pathlib import Path
from ci_utils import ci_project, ci_platform, ci_job


def main():
    """Creates yaml files for jobs based on projects and platforms

    Discovers opencpi projects and platforms, constructs jobs, and dumps
    them out to yaml files.
    """
    opencpi_path = Path(__file__, '..', '..', '..').resolve()
    os.chdir(str(opencpi_path))
    gitlab_ci_path = Path('.gitlab-ci')
    yaml_path = Path(gitlab_ci_path, 'yaml')
    projects_path = Path('projects')
    platform_data_path = Path(gitlab_ci_path, 'scripts', 'platform_data.yml')

    with open(str(platform_data_path)) as yml:
        platform_data = yaml.safe_load(yml)

    projects_blacklist = ['tutorial']
    projects = ci_project.discover_projects(projects_path, projects_blacklist)
    platforms = ci_platform.discover_platforms(projects, platform_data)

    # for platform in platforms:
    #     print(platform)

    stages = ['.pre', 'prereqs', 'build-host', 'build-rcc', 
              'build-primitives-core', 'build-primitives', 'build-libraries', 
              'build-platforms', 'build-assemblies', 'build-sdcards', 'test', 
              'deploy']

    host_platforms = ci_platform.get_host_platforms(platforms)
    cross_platforms = ci_platform.get_cross_platforms(platforms)
    rcc_platforms = ci_platform.get_rcc_platforms(platforms)

    for host_platform in host_platforms:
        print('Generating yaml for host platform: {}'.format(
              host_platform.name))

        for cross_platform in cross_platforms:
            print('\t{}'.format(cross_platform.name))

            overrides = get_overrides(cross_platform, platform_data)
            cross_jobs = ci_job.make_jobs(stages, cross_platform, projects, 
                                          rcc_platforms=rcc_platforms, 
                                          host_platform=host_platform,
                                          overrides=overrides)
            cross_path = Path(yaml_path, host_platform.name, 
                              '{}.yml'.format(cross_platform.name))
            ci_job.dump(cross_jobs, cross_path)

        overrides = get_overrides(host_platform, platform_data)
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

    print('\nYaml files available at: {}'.format(Path(Path.cwd(), yaml_path)))
    print('*IMPORTANT: If a new platform was added,'
          ' be sure to commit any newly generated yaml files.')


def get_overrides(platform, platform_data):
    """Gets job overrides for a platform from a dictionary of platforms

    Overrides will replace default job values (tags, script, etc.).

    Args:
        platform:       Platform to get overrides for
        platforms_data: Dictionary with platform names as keys

    Returns:
        A dictionary of job overrides for a specified platform
    """
    try:
        return platform_data[platform.name]['overrides']
    except:
        return {}


def dump(yaml_dict, yaml_path, mode):
    """Dumps a dictionary to a yaml file

    Args:
        yaml_dict:  Dictionary to dump to a yaml file
        yaml_path:  Path of yaml file to dump dictionary to
        mode:       Mode to open file in
    """
    yaml.SafeDumper.ignore_aliases = lambda *args : True

    with open(yaml_path, mode) as yml:
        yaml.safe_dump(yaml_dict, yml, width=1000, default_flow_style=False)


if __name__ == '__main__':
    main()